import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.api_service.evidence import EvidenceService


class EvidenceAdapterTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.out = self.root / 'output'
        self.out.mkdir()
        self.service = EvidenceService(self.out, self.root)
        self.identity = {'system_version': 'v1', 'order_id': 99999}

    def write_json(self, name, value):
        (self.out / name).write_text(json.dumps(value), encoding='utf-8')

    def publish_pod(self, status='ok', extraction_status='ok', version='v1', number=99999):
        ref = f'data/images/POD_{version}_{number}.jpg'
        original = self.root / ref
        original.parent.mkdir(parents=True, exist_ok=True)
        original.write_bytes(b'synthetic image reference, no extraction call')
        digest = hashlib.sha256(original.read_bytes()).hexdigest()
        record = {'source_id': f'pod:{version}:{number}', 'source_system': version, 'order_id': number,
                  'image_ref': ref, 'image_sha256': digest, 'status': status, 'flags': [],
                  'extraction': {'status': extraction_status},
                  'fields': {'delivered_at': {'value': '2026-01-02T10:00:00', 'confidence': 'high'},
                             'driver_code': {'value': 'DRV999', 'confidence': 'high'},
                             'received_by': {'value': 'Alice Private', 'confidence': 'high'},
                             'remarks': {'value': 'alice@example.invalid S1234567D', 'confidence': 'high'}}}
        (self.out / 'pod_records.jsonl').write_text(json.dumps(record) + '\n', encoding='utf-8')
        self.write_json('image_manifest.json', {'files': [{'ref': ref, 'sha256': digest, 'status': status}]})
        return original, record

    def test_original_verified_pod_is_cited_and_personal_fields_withheld(self):
        self.publish_pod()
        result = self.service.gather(self.identity, start_n=4)
        card = result['evidence'][0]
        self.assertEqual(card['status'], 'found')
        self.assertEqual(card['citations'], [4, 5])
        self.assertEqual(result['citations'][0]['record_key'], self.identity)
        self.assertIn(['Observed driver', 'DRV999'], card['facts'])
        rendered = json.dumps(result)
        for personal in ('Alice', 'alice@example', 'S1234567D'):
            self.assertNotIn(personal, rendered)

    def test_missing_artifacts_are_failed_not_no_match(self):
        result = self.service.gather(self.identity, 'late')
        self.assertEqual([card['status'] for card in result['evidence']], ['failed', 'failed'])
        self.assertEqual(result['citations'], [])

    def test_valid_empty_publication_is_a_real_no_match(self):
        (self.out / 'pod_records.jsonl').write_text('', encoding='utf-8')
        self.write_json('image_manifest.json', {'files': []})
        result = self.service.gather(self.identity)
        self.assertEqual(result['evidence'][0]['status'], 'not_found')
        self.assertEqual(result['evidence'][0]['summary'], 'No POD on file for this order in the supplied dataset.')

    def test_failed_extraction_stays_failed_despite_A_partial_envelope(self):
        self.publish_pod(status='failed', extraction_status='failed')
        result = self.service.gather(self.identity)
        self.assertEqual(result['evidence'][0]['status'], 'failed')
        self.assertEqual(result['citations'], [])

    def test_cross_system_card_is_never_reused_and_later_matching_v2_is_allowed(self):
        self.publish_pod()
        v2 = dict(self.identity, system_version='v2')
        self.assertEqual(self.service.gather(v2)['evidence'][0]['status'], 'not_found')
        self.publish_pod(version='v2')
        self.assertEqual(self.service.gather(v2)['evidence'][0]['status'], 'found')

    def test_changed_original_and_wrong_source_identity_are_rejected(self):
        original, record = self.publish_pod()
        original.write_bytes(b'changed source')
        self.assertEqual(self.service.gather(self.identity)['evidence'][0]['status'], 'failed')
        self.publish_pod()
        record['source_id'] = 'pod:v2:99999'
        (self.out / 'pod_records.jsonl').write_text(json.dumps(record) + '\n', encoding='utf-8')
        self.assertEqual(self.service.gather(self.identity)['evidence'][0]['status'], 'failed')

    def test_absolute_or_traversal_source_ref_is_rejected(self):
        _, record = self.publish_pod()
        for ref in ('/private/tmp/private.jpg', 'data/../../private.jpg'):
            record['image_ref'] = ref
            (self.out / 'pod_records.jsonl').write_text(json.dumps(record) + '\n', encoding='utf-8')
            self.assertEqual(self.service.gather(self.identity)['evidence'][0]['status'], 'failed')

    def test_exact_policy_category_survives_no_lexical_overlap(self):
        ref = 'data/tabular/guide.xlsx'
        original = self.root / ref
        original.parent.mkdir(parents=True)
        original.write_bytes(b'synthetic guide original')
        self.write_json('manifest.json', {'files': [{'kind': 'policy', 'ref': ref, 'status': 'ok',
                                                   'sha256': hashlib.sha256(original.read_bytes()).hexdigest()}]})
        chunk = {'source_id': 'policy:guide', 'text': 'Late delivery rule', 'heading': 'Late delivery',
                 'email_categories': ['late'], 'guide_version': 'v2', 'authority': 'Client Q02',
                 'fields': {}, 'ref': ref, 'locator': 'sheet:Resolution Guide|row:5'}
        (self.out / 'policy_chunks.jsonl').write_text(json.dumps(chunk) + '\n', encoding='utf-8')
        policy = self.service.gather(self.identity, 'late')['evidence'][1]
        self.assertEqual(policy['status'], 'found')
        no_rule = self.service.gather(self.identity, 'compliment')['evidence'][1]
        self.assertEqual(no_rule['status'], 'not_found')
        original.write_bytes(b'changed guide')
        self.assertEqual(self.service.gather(self.identity, 'late')['evidence'][1]['status'], 'failed')

    def test_interrupted_publication_never_labels_old_facts_with_new_fingerprints(self):
        self.publish_pod()

        def changed_policy(category, number, versions):
            (self.out / 'pod_records.jsonl').write_text('', encoding='utf-8')
            return self.service._card('policy', 'not_found', 'No selected category.'), []

        with patch.object(self.service, '_policy', side_effect=changed_policy):
            result = self.service.gather(self.identity)
        self.assertTrue(all(card['status'] == 'failed' for card in result['evidence']))
        self.assertEqual(result['citations'], [])
        self.assertTrue(all(not card['facts'] for card in result['evidence']))


if __name__ == '__main__':
    unittest.main()
