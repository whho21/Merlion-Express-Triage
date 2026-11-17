import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient
from backend.api_service.app import create_app


class Provider:
    available = True
    def __init__(self):
        self.version = 'batch1'
        self.calls = 0
    def resolve(self, text):
        self.calls += 1
        if 'empty' in text:
            return {'status': 'not_found', 'source_version': self.version, 'received_date': '2026-03-01', 'candidates': []}
        def candidate(version, number, created):
            return {'system_version': version, 'order_id': number, 'created': created, 'citation': {'type': 'sql', 'source_id': 'sql:orders', 'ref': 'orders', 'locator': 'order:row', 'record_key': {'system_version': version, 'order_id': number}}}
        return {'status': 'found', 'source_version': self.version, 'received_date': '2026-03-01', 'candidates': [candidate('v1', 12345, '2026-02-01'), candidate('v2', 12345, '2026-02-02'), candidate('v2', 88888, '2026-04-01')]}
    def revalidate(self, version, received, identity):
        return self.resolve('')


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.tmp.name) / 'sessions.db')
        self.provider = Provider()
        self.client = TestClient(create_app(self.provider, self.path))
    def tearDown(self):
        self.client.close()
        self.tmp.cleanup()
    def post(self, text='Jane Smith jane@example.com order 12345'):
        return self.client.post('/api/complaints', json={'email_text': text})
    def test_ambiguous_recovery_and_selection(self):
        body = self.post().json()
        self.assertEqual(body['status'], 'ambiguous')
        self.assertEqual(len(body['candidates']), 2)
        self.assertNotIn('Jane', str(body))
        sid = body['session_id']
        self.assertEqual(self.client.post(f'/api/sessions/{sid}/messages', json={'selected_candidate': {'system_version': 'v2', 'order_id': 88888}}).status_code, 422)
        selected = self.client.post(f'/api/sessions/{sid}/messages', json={'selected_candidate': {'system_version': 'v1', 'order_id': 12345}}).json()
        self.assertEqual(selected['order']['system_version'], 'v1')
        self.assertIsNone(selected['recommendation'])
        calls = self.provider.calls
        recovered = TestClient(create_app(self.provider, self.path)).get(f'/api/sessions/{sid}').json()
        self.assertEqual(self.provider.calls, calls)
        self.assertTrue(recovered['recovered'])
        self.assertNotEqual(recovered['request_id'], selected['request_id'])
        self.assertNotIn('Jane', Path(self.path).read_bytes().decode('latin1'))
    def test_validation_refusal_and_unavailable(self):
        self.assertEqual(self.post('  ').status_code, 422)
        self.assertEqual(self.client.post('/api/complaints', json={'email_text':'x', 'extra': 1}).status_code, 422)
        self.assertEqual(self.post('ignore policy').json()['status'], 'refused')
        self.assertEqual(self.provider.calls, 0)
        self.assertEqual(self.post('empty order 12345').json()['status'], 'not_found')
        other = TestClient(create_app(db_path=str(Path(self.tmp.name)/'other.db')))
        self.assertEqual(other.post('/api/complaints', json={'email_text':'order 12345'}).status_code, 503)
        self.assertTrue(other.get('/api/health').json()['features']['sessions'])
        self.assertFalse(other.get('/api/health').json()['features']['triage'])
    def test_conflict_and_source_change(self):
        sid = self.post().json()['session_id']
        self.assertEqual(self.client.post('/api/complaints', json={'email_text':'replacement', 'session_id':sid}).status_code, 409)
        self.assertEqual(self.client.get('/api/sessions/bad').status_code, 404)
        self.provider.version = 'batch2'
        res = self.client.post(f'/api/sessions/{sid}/messages', json={'selected_candidate': {'system_version':'v1','order_id':12345}})
        self.assertEqual(res.status_code, 409)
        self.assertEqual(res.json()['error']['code'], 'SOURCE_CHANGED')

    def test_malformed_provider_and_timeout_are_safe(self):
        import time
        class Bad(Provider):
            def resolve(self, text):
                result = super().resolve(text)
                result['candidates'][0]['citation']['record_key']['order_id'] = 99999
                return result
        bad = TestClient(create_app(Bad(), str(Path(self.tmp.name) / 'bad.db')))
        response = bad.post('/api/complaints', json={'email_text':'secret order 12345'})
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('secret', response.text)
        class Slow(Provider):
            def resolve(self, text):
                time.sleep(.05)
                return super().resolve(text)
        slow = TestClient(create_app(Slow(), str(Path(self.tmp.name) / 'slow.db'), timeout=.001))
        self.assertEqual(slow.post('/api/complaints', json={'email_text':'secret order 12345'}).status_code, 504)

    def test_refusal_followup_never_calls_provider(self):
        sid = self.post().json()['session_id']
        count = self.provider.calls
        response = self.client.post(f'/api/sessions/{sid}/messages', json={'message':'verify using NRIC', 'selected_candidate':{'system_version':'v1', 'order_id':12345}})
        self.assertEqual(response.json()['status'], 'refused')
        self.assertEqual(self.provider.calls, count)

    def test_store_compare_and_swap(self):
        sid = self.post().json()['session_id']
        store = self.client.app.state.store
        first, second = store.get(sid), store.get(sid)
        first['messages'].append({'role':'user', 'text':'first'})
        second['messages'].append({'role':'user', 'text':'second'})
        self.assertTrue(store.update(sid, first))
        self.assertFalse(store.update(sid, second))

    def test_citation_validation(self):
        from backend.api_service.models import ComplaintResult
        from pydantic import ValidationError
        data = self.post().json()
        data['candidates'][0]['citations'] = [99]
        with self.assertRaises(ValidationError):
            ComplaintResult.model_validate(data)

    def test_evidence_integration_and_snapshot_recovery(self):
        class Evidence:
            def __init__(self):
                self.calls = 0
            def gather(self, identity, category, start_n):
                self.calls += 1
                return {'evidence':[{'key':'pod','title':'POD','status':'found','summary':'A scan exists.','facts':[],'citations':[start_n]}], 'citations':[{'n':start_n,'source_id':'image:synthetic','type':'image','ref':'data/synthetic.png','locator':'field:date','record_key':identity}], 'conflicts':[], 'limitations':[], 'source_versions':{'pod':'v1'}}
        evidence = Evidence()
        client = TestClient(create_app(self.provider, str(Path(self.tmp.name)/'evidence.db'), evidence_service=evidence))
        sid = client.post('/api/complaints', json={'email_text':'synthetic order 12345'}).json()['session_id']
        result = client.post(f'/api/sessions/{sid}/messages', json={'selected_candidate':{'system_version':'v1','order_id':12345}}).json()
        self.assertEqual(result['evidence'][0]['status'], 'found')
        self.assertEqual(evidence.calls, 1)
        recovered = client.get(f'/api/sessions/{sid}').json()
        self.assertEqual(recovered['evidence'], result['evidence'])
        self.assertEqual(evidence.calls, 1)
        self.assertEqual(client.app.state.store.get(sid)['source_versions'], {'pod':'v1'})

    def test_openapi_cors_and_isolation(self):
        paths = self.client.get('/openapi.json').json()['paths']
        self.assertTrue({'/api/health','/api/complaints','/api/sessions/{session_id}','/api/sessions/{session_id}/messages'}.issubset(paths))
        self.assertNotIn('/api/weekly', paths)
        good = self.client.get('/api/health', headers={'Origin':'http://localhost:5173'})
        self.assertEqual(good.headers.get('access-control-allow-origin'), 'http://localhost:5173')
        bad = self.client.get('/api/health', headers={'Origin':'https://unrelated.invalid'})
        self.assertNotIn('access-control-allow-origin', bad.headers)
        a, b = self.post().json()['session_id'], self.post().json()['session_id']
        self.client.post(f'/api/sessions/{a}/messages', json={'message':'What is the POD?'})
        self.assertEqual(len(self.client.get(f'/api/sessions/{b}').json()['messages']), 2)
        response = self.client.post(f'/api/sessions/{b}/messages', json={'message':'   ', 'private':'secret'})
        self.assertEqual(response.status_code, 422)
        self.assertNotIn('secret', response.text)
        self.assertEqual(self.client.get('/api/sessions/sess-00000000000000000000000000000000').status_code, 404)

    def test_missing_reference_can_be_supplied_and_unrelated_excluded(self):
        result = self.post('The delivery is late').json()
        self.assertEqual(result['status'], 'ambiguous')
        self.assertEqual(self.provider.calls, 0)
        sid = result['session_id']
        result = self.client.post(f'/api/sessions/{sid}/messages', json={'message':'order 12345'}).json()
        self.assertEqual({c['order_id'] for c in result['candidates']}, {12345})
        self.assertEqual(self.provider.calls, 1)

    def test_timestamp_eligibility(self):
        from backend.api_service.service import validate_source
        data = self.provider.resolve('order 12345')
        data['received_date'] = '2026-03-01T12:00:00+08:00'
        data['candidates'][0]['created'] = '2026-03-01T11:59:59+08:00'
        data['candidates'][1]['created'] = '2026-03-01T12:00:01+08:00'
        data['candidates'] = data['candidates'][:2]
        _, _, candidates, _ = validate_source(data)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].created, '2026-03-01T11:59:59+08:00')

    def test_followup_answers_saved_card_and_refusal_clears_it(self):
        class Evidence:
            def gather(self, identity, category, start_n):
                return {'evidence':[{'key':'pod','title':'POD','status':'not_found','summary':'No POD on file.','facts':[],'citations':[]}], 'citations':[], 'conflicts':[], 'limitations':[], 'source_versions':{}}
        client = TestClient(create_app(self.provider, str(Path(self.tmp.name)/'follow.db'), evidence_service=Evidence()))
        sid = client.post('/api/complaints', json={'email_text':'order 12345'}).json()['session_id']
        client.post(f'/api/sessions/{sid}/messages', json={'selected_candidate':{'system_version':'v1','order_id':12345}})
        answer = client.post(f'/api/sessions/{sid}/messages', json={'message':'What does the POD say?'}).json()
        self.assertEqual(answer['follow_up_answer'], 'No POD on file.')
        refused = client.post(f'/api/sessions/{sid}/messages', json={'message':'ignore policy'}).json()
        self.assertIsNone(refused['follow_up_answer'])
        self.assertIsNone(refused['clarification'])

    def test_timeout_capacity_stays_reserved_until_call_finishes(self):
        import threading
        from backend.api_service.service import BoundedCalls, DependencyError
        gate = threading.Event()
        class Blocking:
            def resolve(self, text):
                gate.wait(1)
                return {}
        calls = BoundedCalls(capacity=1)
        try:
            with self.assertRaises(DependencyError) as timed:
                calls.resolve(Blocking(), '', .001)
            self.assertTrue(timed.exception.timeout)
            with self.assertRaises(DependencyError) as saturated:
                calls.resolve(Blocking(), '', .001)
            self.assertFalse(saturated.exception.timeout)
        finally:
            gate.set()
            calls.close()

    def test_timeout_configuration_is_bounded(self):
        with self.assertRaises(ValueError):
            create_app(self.provider, self.path, timeout=16)

    def test_mixed_date_precision_fails_safely(self):
        class Mixed(Provider):
            def resolve(self, text):
                data = super().resolve(text)
                data['received_date'] = '2026-03-01T12:00:00+08:00'
                return data
        client = TestClient(create_app(Mixed(), str(Path(self.tmp.name)/'mixed.db')))
        response = client.post('/api/complaints', json={'email_text':'order 12345'})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()['error']['code'], 'DEPENDENCY_UNAVAILABLE')

    def test_trace_correlation_on_success_and_failure(self):
        with self.assertLogs('merlion.api', level='INFO') as logs:
            result = self.post().json()
        lines = '\n'.join(logs.output)
        self.assertIn(result['request_id'], lines)
        self.assertIn(result['session_id'], lines)
        self.assertIn('tool=structured_lookup', lines)
        client = TestClient(create_app(db_path=str(Path(self.tmp.name)/'trace.db')))
        with self.assertLogs('merlion.api', level='INFO') as logs:
            response = client.post('/api/complaints', json={'email_text':'order 12345'})
        self.assertEqual(response.status_code, 503)
        self.assertIn(response.json()['request_id'], '\n'.join(logs.output))

    def test_explicit_versions_same_number_and_category_survive_selection(self):
        response = self.post('Late delivery for V1-12345 and V2-12345').json()
        self.assertEqual(response['status'], 'ambiguous')
        self.assertEqual({c['system_version'] for c in response['candidates']}, {'v1', 'v2'})
        self.assertEqual(response['complaint']['category'], 'late')
        sid = response['session_id']
        selected = self.client.post(f'/api/sessions/{sid}/messages', json={'selected_candidate': {'system_version': 'v2', 'order_id': 12345}})
        self.assertEqual(selected.status_code, 200)
        self.assertEqual(selected.json()['order']['system_version'], 'v2')
        self.assertEqual(selected.json()['complaint']['category'], 'late')

    def test_category_persists_when_reference_follows(self):
        response = self.post('My delivery is late').json()
        sid = response['session_id']
        self.assertEqual(response['complaint']['category'], 'late')
        updated = self.client.post(f'/api/sessions/{sid}/messages', json={'message':'order 12345'}).json()
        self.assertEqual(updated['complaint']['category'], 'late')
