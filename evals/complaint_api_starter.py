"""Synthetic HTTP smoke evaluation; run `python -m evals.complaint_api_starter`.

Requires the API's dev dependencies. No live database or model calls are made.
"""
import json
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
from backend.api_service.app import create_app
from evals.complaint_api_fixture import SyntheticProvider


def main():
    cases = json.loads(Path('evals/complaint_api_cases.json').read_text())
    with tempfile.TemporaryDirectory() as temp:
        provider = SyntheticProvider()
        with TestClient(create_app(provider, str(Path(temp) / 'sessions.db'))) as client:
            for case in cases:
                before = provider.calls
                response = client.post('/api/complaints', json={'email_text': case['email_text']})
                assert response.status_code == 200, case['name']
                result = response.json()
                assert result['status'] == case['expected_status'] and result['recommendation'] is None, case['name']
                if case['name'] in ('policy override', 'missing reference'):
                    assert provider.calls == before, case['name']
                if case['name'] in ('ambiguous order', 'follow-up and recovery'):
                    assert len(result['candidates']) == 2 and len(result['citations']) == 2, case['name']
                    assert all(c['citations'][0] in {x['n'] for x in result['citations']} for c in result['candidates'])
                if case['name'] == 'follow-up and recovery':
                    sid = result['session_id']
                    follow = client.post(f'/api/sessions/{sid}/messages', json={'message':'What does the policy say?'}).json()
                    calls = provider.calls
                    saved = client.get(f'/api/sessions/{sid}').json()
                    assert saved['recovered'] and saved['follow_up_answer'] == follow['follow_up_answer']
                    assert saved['candidates'] == follow['candidates'] and provider.calls == calls
                print(f"PASS {case['name']}")


if __name__ == '__main__':
    main()
