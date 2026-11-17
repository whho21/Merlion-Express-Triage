"""Read cached A evidence without ingestion, model calls or unmasked free text."""
from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from datetime import datetime
from pathlib import Path, PurePosixPath

from backend.unstructured import pod, search
from .service import request_trace, session_trace

ROOT = Path(__file__).resolve().parents[2]
CATEGORIES = {'late', 'wrong_address', 'missing_item', 'where_is_parcel',
              'cod_wrong', 'thrown_over_gate', 'corporate', 'compliment'}
log = logging.getLogger('merlion.api')


class EvidenceService:
    """Project safe facts and retain logical locators plus source fingerprints.

    Missing artifacts and failed extraction are failed dependencies. An existing,
    valid published file with no matching record is a genuine not-found outcome.
    Free-text receiver names, remarks and policy snippets are deliberately withheld.
    """

    def __init__(self, out_dir=None, source_root=None):
        self.root = Path(source_root or ROOT).resolve()
        self.out_dir = Path(out_dir or self.root / 'output' / 'unstructured')

    @staticmethod
    def _bytes(path, limit=8_000_000):
        with path.open('rb') as stream:
            raw = stream.read(limit + 1)
        if len(raw) > limit:
            raise ValueError('artifact size')
        return raw

    def _json(self, name):
        return json.loads(self._bytes(self.out_dir / name))

    def _manifest(self, name):
        manifest = self._json(name)
        if (not isinstance(manifest, dict) or not isinstance(manifest.get('files'), list)
                or any(not isinstance(entry, dict) for entry in manifest['files'])):
            raise ValueError('manifest')
        return manifest

    def _records(self, name):
        records = [json.loads(line) for line in self._bytes(self.out_dir / name).splitlines() if line.strip()]
        if len(records) > 1000 or any(not isinstance(record, dict) for record in records):
            raise ValueError('artifact records')
        return records

    def _fingerprints(self):
        versions = {}
        for name in ('pod_records.jsonl', 'image_manifest.json', 'policy_chunks.jsonl', 'manifest.json'):
            try:
                versions[name] = hashlib.sha256(self._bytes(self.out_dir / name)).hexdigest()
            except (OSError, ValueError):
                versions[name] = 'unavailable'
        return versions

    def _verify_source(self, ref, manifest, versions):
        """Resolve repo-relative evidence only inside data/, including symlink checks."""
        if not isinstance(ref, str) or '\\' in ref:
            raise ValueError('source ref')
        logical = PurePosixPath(ref)
        if logical.is_absolute() or not logical.parts or logical.parts[0] != 'data' or '..' in logical.parts:
            raise ValueError('source ref')
        path = (self.root / logical).resolve()
        if not path.is_relative_to((self.root / 'data').resolve()):
            raise ValueError('source root')
        entries = [entry for entry in manifest.get('files', []) if entry.get('ref') == ref]
        if len(entries) != 1 or entries[0].get('status') == 'failed':
            raise ValueError('source manifest')
        digest = hashlib.sha256(self._bytes(path, limit=25_000_000)).hexdigest()
        if digest != entries[0].get('sha256'):
            raise ValueError('source changed')
        versions[ref] = digest

    @staticmethod
    def _card(key, status, summary, facts=None, citations=None):
        return {'key': key, 'title': 'Proof of delivery (POD)' if key == 'pod' else 'Resolution Guide',
                'status': status, 'summary': summary, 'facts': facts or [], 'citations': citations or []}

    def _policy(self, category, number, versions):
        if category not in CATEGORIES:
            return self._card('policy', 'not_found', 'No verified policy category has been selected.'), []
        manifest = self._manifest('manifest.json')
        self._records('policy_chunks.jsonl')  # Bound and validate artifacts before A reads them.
        # Exact category path avoids the reviewed category-plus-unrelated-query bug.
        result = search.search_policy(category=category, out_dir=self.out_dir)
        if result['status'] == 'failed':
            return self._card('policy', 'failed', 'Resolution Guide evidence is unavailable.'), []
        if result['status'] == 'not_found':
            return self._card('policy', 'not_found', 'The Resolution Guide has no rule for this category.'), []
        hits = result.get('data')
        if not isinstance(hits, list) or not hits:
            raise ValueError('policy result')
        citations = []
        for hit in hits:
            citation = hit['citation']
            self._verify_source(citation['ref'], manifest, versions)
            if not re.fullmatch(r'sheet:Resolution Guide\|row:[1-9][0-9]*', citation['locator']):
                raise ValueError('guide locator')
            if not re.fullmatch(r'policy:[A-Za-z0-9_.:-]+', citation['source_id']):
                raise ValueError('guide source')
            citations.append({'n': number + len(citations), 'source_id': citation['source_id'],
                              'type': 'document', 'ref': citation['ref'], 'locator': citation['locator'],
                              'record_key': None, 'label': 'Resolution Guide rule'})
        return self._card('policy', 'found',
                          'A cited Resolution Guide rule is available. Its conditions have not been assessed.',
                          citations=[entry['n'] for entry in citations]), citations

    def _pod(self, identity, number, versions):
        records = self._records('pod_records.jsonl')
        manifest = self._manifest('image_manifest.json')
        matching = [record for record in records if record.get('source_system') == identity['system_version']
                    and record.get('order_id') == identity['order_id']]
        if len(matching) > 1:
            raise ValueError('duplicate identity')
        # Keep A's lookup and identity rules; do not reuse another system's card.
        result = pod.find_pod(records, identity['system_version'], identity['order_id'])
        if result['status'] == 'not_found':
            return self._card('pod', 'not_found', 'No POD on file for this order in the supplied dataset.'), []
        record = result['data']
        if record.get('status') == 'failed' or record.get('extraction', {}).get('status') == 'failed':
            return self._card('pod', 'failed', 'POD extraction failed; no usable observation is available.'), []
        self._verify_source(record['image_ref'], manifest, versions)
        if (record['source_id'] != f"pod:{identity['system_version']}:{identity['order_id']}"
                or record.get('image_sha256') != versions[record['image_ref']]):
            raise ValueError('pod source')
        fields = record.get('fields', {})
        facts, citations = [], []
        for field, label in [('delivered_at', 'Observed delivery time'), ('driver_code', 'Observed driver')]:
            observation = fields.get(field, {})
            value = observation.get('value')
            if observation.get('confidence') not in ('high', 'medium') or not isinstance(value, str):
                continue
            if field == 'delivered_at':
                datetime.fromisoformat(value)
                if not re.fullmatch(r'[0-9TZ:+. -]+', value):
                    raise ValueError('delivery time')
            elif not re.fullmatch(r'DRV[0-9]{3}', value):
                raise ValueError('driver code')
            citation_number = number + len(citations)
            citations.append({'n': citation_number, 'source_id': record['source_id'], 'type': 'image',
                              'ref': record['image_ref'], 'locator': f'field:{field}',
                              'record_key': identity, 'label': label})
            facts.append([label, value])
        status = 'partial' if result['status'] == 'partial' or record.get('flags') or not facts else 'found'
        summary = 'Cached POD observations are available; they do not establish recipient identity.'
        if record.get('flags'):
            summary += ' Extraction uncertainty or conflicting observations require review.'
        return self._card('pod', status, summary, facts, [entry['n'] for entry in citations]), citations

    def gather(self, identity, category=None, start_n=1):
        if (identity.get('system_version') not in ('v1', 'v2') or
                type(identity.get('order_id')) is not int or identity['order_id'] <= 0):
            raise ValueError('identity')
        identity = {key: identity[key] for key in ('system_version', 'order_id')}
        bundle = {'evidence': [], 'citations': [], 'limitations': [], 'conflicts': [], 'source_versions': {}}
        before = self._fingerprints()
        for key, call in [('pod', lambda n: self._pod(identity, n, bundle['source_versions'])),
                          ('policy', lambda n: self._policy(category, n, bundle['source_versions']))]:
            started = time.monotonic()
            try:
                card, citations = call(start_n + len(bundle['citations']))
            except (OSError, ValueError, TypeError, KeyError, AttributeError):
                card, citations = self._card(key, 'failed', 'The cached source could not be verified.'), []
            bundle['evidence'].append(card)
            bundle['citations'].extend(citations)
            log.info('request_id=%s session_id=%s tool=%s status=%s latency_ms=%d',
                     request_trace.get(), session_trace.get(), key, card['status'],
                     int((time.monotonic()-started)*1000))
        changed = before != self._fingerprints()
        for ref, digest in bundle['source_versions'].items():
            try:
                changed |= hashlib.sha256(self._bytes(self.root / ref, limit=25_000_000)).hexdigest() != digest
            except (OSError, ValueError):
                changed = True
        bundle['source_versions'].update(before)
        if changed:
            bundle['evidence'] = [self._card(key, 'failed', 'Sources changed during the request; retry after publication.')
                                  for key in ('pod', 'policy')]
            bundle['citations'] = []
        bundle['limitations'].append('Delivery/GPS facts and full rate/policy assessment require the reviewed structured tools.')
        bundle['limitations'].append('Evidence is a saved source snapshot; session recovery does not refresh it.')
        return bundle
