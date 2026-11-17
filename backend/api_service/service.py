"""Conservative orchestration around the structured-record provider.

The provider must supply a source-backed complaint date, source version and
candidate records. Its records are treated as untrusted and projected onto a
small allowlist; no arbitrary provider text is returned or persisted.
"""
import re
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from threading import BoundedSemaphore
import logging
from contextvars import ContextVar, copy_context
import time
from datetime import date, datetime
from backend.unstructured.emails import ORDER_RE, BLOCK_BEFORE_RE
from uuid import uuid4

from .models import Candidate, Citation, ComplaintResult


request_trace = ContextVar('request_trace', default=None)
session_trace = ContextVar('session_trace', default=None)

def new_id(prefix):
    if prefix == 'req' and request_trace.get():
        return request_trace.get()
    return prefix + '-' + uuid4().hex


class UnavailableProvider:
    available = False

    def resolve(self, text):
        raise RuntimeError("unavailable")


class DependencyError(Exception):
    def __init__(self, timeout=False):
        self.timeout = timeout


class BoundedCalls:
    """A timed-out call occupies its slot until the provider really finishes.

    Providers must also set their own I/O deadlines; Python cannot stop a thread.
    """
    def __init__(self, capacity=4):
        self.pool = ThreadPoolExecutor(max_workers=capacity)
        self.slots = BoundedSemaphore(capacity)

    def close(self):
        self.pool.shutdown(wait=False, cancel_futures=True)

    def resolve(self, provider, text, timeout, tool="structured_lookup"):
        if not self.slots.acquire(blocking=False):
            raise DependencyError()
        started = time.monotonic()
        try:
            context = copy_context()
            future = self.pool.submit(context.run, provider.resolve, text)
        except Exception:
            self.slots.release()
            raise DependencyError()
        future.add_done_callback(lambda _: self.slots.release())
        try:
            result = future.result(timeout=timeout)
            logging.getLogger('merlion.api').info('request_id=%s session_id=%s tool=%s status=completed latency_ms=%d', request_trace.get(), session_trace.get(), tool, int((time.monotonic()-started)*1000))
            return result
        except TimeoutError as exc:
            logging.getLogger('merlion.api').info('request_id=%s session_id=%s tool=%s status=timeout latency_ms=%d', request_trace.get(), session_trace.get(), tool, int((time.monotonic()-started)*1000))
            raise DependencyError(timeout=True) from exc
        except Exception as exc:
            logging.getLogger('merlion.api').info('request_id=%s session_id=%s tool=%s status=failed latency_ms=%d', request_trace.get(), session_trace.get(), tool, int((time.monotonic()-started)*1000))
            raise DependencyError() from exc


def parse_time(value):
    if not isinstance(value, str):
        raise ValueError('invalid date')
    if 'T' in value or ' ' in value:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if parsed.utcoffset() is None:
            raise ValueError('timestamp requires an offset')
        return parsed
    return date.fromisoformat(value)


def eligible(created, received):
    if isinstance(created, datetime) and isinstance(received, datetime):
        return created <= received
    if isinstance(created, datetime) or isinstance(received, datetime):
        # A date without an offset is insufficient for a timestamp comparison.
        raise ValueError('incompatible date precision')
    return created <= received


def validate_source(raw):
    """Require explicit source date, batch and per-candidate composite SQL lineage."""
    if not isinstance(raw, dict) or raw.get('status') not in ('found', 'not_found'):
        raise DependencyError()
    batch = raw.get('source_version')
    if not isinstance(batch, str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,80}', batch):
        raise DependencyError()
    try:
        received = parse_time(raw['received_date'])
    except (KeyError, TypeError, ValueError) as exc:
        raise DependencyError() from exc
    records = raw.get('candidates')
    if not isinstance(records, list) or len(records) > 50:
        raise DependencyError()
    candidates, citations, seen = [], [], set()
    for item in records:
        if not isinstance(item, dict):
            raise DependencyError()
        try:
            version, number = item['system_version'], item['order_id']
            created = parse_time(item['created'])
            source = item['citation']
            if version not in ('v1', 'v2') or type(number) is not int or number <= 0:
                raise ValueError()
            if (version, number) in seen:
                raise ValueError()
            seen.add((version, number))
            if source['type'] != 'sql' or source['record_key'] != {'system_version': version, 'order_id': number}:
                raise ValueError()
            # Never expose arbitrary free text or filesystem paths from a provider.
            if not all(isinstance(source[k], str) and re.fullmatch(r'[A-Za-z0-9_.:-]{1,120}', source[k]) for k in ('source_id', 'ref', 'locator')):
                raise ValueError()
            if not eligible(created, received):
                continue
            n = len(citations) + 1
            citations.append(Citation(n=n, source_id=source['source_id'], type='sql', ref=source['ref'], locator=source['locator'], record_key=source['record_key']))
            candidates.append(Candidate(system_version=version, order_id=number, created=item['created'], evidence_for='Eligible source record predates the complaint.', citations=[n]))
        except (KeyError, TypeError, ValueError) as exc:
            raise DependencyError() from exc
    if raw['status'] == 'not_found' and records:
        raise DependencyError()
    return batch, raw['received_date'], candidates, citations


def refusal(text):
    return bool(re.search(r'\b(ignore|bypass|override)\b.{0,40}\b(policy|rules|instructions|guardrails)\b|\b(verify|verification|identify|authenticate)\b.{0,40}\bnric\b|\bnric\b.{0,40}\b(verify|verification|identify|authenticate)\b', text, re.I | re.S))


def order_references(text):
    """Map each submitted order number to the explicitly offered system(s).

    An unqualified occurrence permits both systems; repeated explicit references
    retain both rather than letting the first occurrence decide the hint.
    """
    refs = {}
    for match in ORDER_RE.finditer(text):
        if BLOCK_BEFORE_RE.search(text[:match.start()]):
            continue
        version, number = match.group(1), match.group(2)
        versions = refs.setdefault(number, set())
        versions.update([version.lower()] if version else ['v1', 'v2'])
    return {number: sorted(versions) for number, versions in refs.items()}


def initial(text, provider, timeout, calls, session_id=None):
    session_id = session_id or new_id('sess')
    session_trace.set(session_id)
    result = ComplaintResult(request_id=new_id('req'), session_id=session_id, status='refused' if refusal(text) else 'not_found')
    batch, received = None, None
    if result.status == 'refused':
        result.guardrail = {'code': 'POLICY_OVERRIDE_ATTEMPT', 'pii_masked': []}
        result.abstention = {'reason': 'This request cannot override the applicable rules.'}
    else:
        refs = order_references(text)
        if not refs:
            result.status = 'ambiguous'
            result.clarification = {'question': 'What is the order number?', 'hint': 'Provide the order reference to continue.'}
            result.abstention = {'reason': 'The complaint does not identify an order.'}
            return {'result': ComplaintResult.model_validate(result.model_dump(warnings=False)).model_dump(), 'source_version': None, 'received_date': None, 'order_references': {}, 'messages': [{'role': 'user', 'text': '[Complaint withheld]'}, {'role': 'assistant', 'text': 'An order reference is needed.'}]}
        batch, received, candidates, citations = validate_source(calls.resolve(provider, text, timeout))
        allowed = [(c, citations[c.citations[0]-1]) for c in candidates if c.system_version in refs.get(str(c.order_id), [])]
        candidates, citations = [], []
        for candidate, citation in allowed:
            citation.n = len(citations) + 1
            candidate.citations = [citation.n]
            candidates.append(candidate)
            citations.append(citation)
        result.candidates, result.citations = candidates, citations
        if len(candidates) > 1:
            result.status = 'ambiguous'
            result.clarification = {'question': 'Which order is relevant?', 'hint': 'Choose one of the listed candidates.'}
            result.abstention = {'reason': 'The order identity is ambiguous.'}
        elif len(candidates) == 1:
            result.status = 'partial'
            result.order = {'system_version': candidates[0].system_version, 'order_id': candidates[0].order_id, 'customer': None, 'postal_code': None, 'zone': None, 'driver_code': None, 'promised_date': None, 'citations': candidates[0].citations}
            result.abstention = {'reason': 'The available records do not establish a supported resolution.'}
        else:
            result.abstention = {'reason': 'No eligible order was found in the supplied records.'}
        result.limitations = ['Complaint text is withheld because free-text names cannot be reliably masked.', 'Delivery evidence and applicable policy have not been assessed.']
    return {'result': ComplaintResult.model_validate(result.model_dump(warnings=False)).model_dump(), 'source_version': batch, 'received_date': received, 'order_references': refs if result.status != 'refused' else {}, 'messages': [{'role': 'user', 'text': '[Complaint withheld]'}, {'role': 'assistant', 'text': 'Complaint processed; see the saved result.'}]}
