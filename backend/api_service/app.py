"""Complaint and persistent-session HTTP API; structured records are injectable."""
from __future__ import annotations

import logging
import copy
import os
import re
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.unstructured.emails import classify
from .evidence import EvidenceService
from .models import ComplaintRequest, ComplaintResult, MessageRequest
from .service import BoundedCalls, DependencyError, UnavailableProvider, initial, new_id, order_references, refusal, request_trace, session_trace, validate_source
from .store import SessionStore

log = logging.getLogger('merlion.api')
if not log.hasHandlers():
    log.addHandler(logging.StreamHandler())
log.setLevel(logging.INFO)
ID = re.compile(r'^sess-[0-9a-f]{32}$')


def create_app(provider=None, db_path=None, timeout=5, evidence_service=None):
    if not 0 < timeout <= 15:
        raise ValueError("timeout must be between 0 and 15 seconds")
    provider = provider or UnavailableProvider()
    store = SessionStore(db_path or os.environ.get('CAPSTONE_SESSION_DB', str(Path('output') / 'api' / 'sessions.sqlite3')))
    calls = BoundedCalls()
    @asynccontextmanager
    async def lifespan(app):
        try:
            yield
        finally:
            calls.close()
    app = FastAPI(title='Merlion Express API', version='0.2.0', lifespan=lifespan)
    app.state.provider, app.state.store = provider, store
    evidence_service = evidence_service or EvidenceService()
    frontend_port = int(os.environ.get('CAPSTONE_FRONTEND_PORT', '5173'))
    app.add_middleware(CORSMiddleware, allow_origins=[f'http://127.0.0.1:{frontend_port}', f'http://localhost:{frontend_port}'], allow_methods=['GET', 'POST'], allow_headers=['Content-Type'])

    @app.middleware('http')
    async def telemetry(request: Request, call_next):
        started = time.monotonic()
        request_trace.set(new_id('req'))
        path_session = request.url.path.split('/')[3] if request.url.path.startswith('/api/sessions/') else ''
        session_trace.set(path_session if ID.fullmatch(path_session) else None)
        request.state.trace = {'session_id': session_trace.get()}
        response = await call_next(request)
        log.info('request_id=%s session_id=%s method=%s route=%s status=%s latency_ms=%d', request_trace.get(), request.state.trace['session_id'], request.method, getattr(request.scope.get('route'), 'path', 'unmatched'), response.status_code, int((time.monotonic()-started)*1000))
        return response

    def error(status, code, message, retryable=False):
        return JSONResponse(status_code=status, content={'request_id': new_id('req'), 'error': {'code': code, 'message': message, 'retryable': retryable}})

    @app.exception_handler(RequestValidationError)
    async def invalid(request, exc):
        return error(422, 'VALIDATION_ERROR', 'The request is invalid.')

    @app.exception_handler(DependencyError)
    async def dependency(request, exc):
        if exc.timeout:
            return error(504, 'DEPENDENCY_TIMEOUT', 'Delivery records could not be checked in time. Please retry.', True)
        return error(503, 'DEPENDENCY_UNAVAILABLE', 'Delivery records could not be checked. Please retry.', True)

    @app.exception_handler(Exception)
    async def unexpected(request, exc):
        return error(500, 'INTERNAL_ERROR', 'The request could not be completed.', True)

    def load(session_id):
        if not ID.fullmatch(session_id):
            return None
        return store.get(session_id)

    def add_evidence(state, identity):
        result = copy.deepcopy(state['result'])
        class EvidenceCall:
            def resolve(self, _):
                return evidence_service.gather(identity, category=state['category'], start_n=len(result['citations']) + 1)
        try:
            bundle = calls.resolve(EvidenceCall(), '', timeout, tool='evidence')
            result['evidence'] = bundle['evidence']
            result['citations'].extend(bundle['citations'])
            result['conflicts'] = bundle['conflicts']
            result['limitations'].extend(bundle['limitations'])
            state['source_versions'] = bundle['source_versions']
            state['result'] = ComplaintResult.model_validate(result).model_dump()
        except Exception:
            state['result']['limitations'].append('Cached evidence could not be checked; no resolution can be recommended.')

    @app.get('/api/health')
    def health():
        return {'request_id': new_id('req'), 'service': 'merlion-express-api', 'status': 'degraded', 'features': {'triage': bool(getattr(provider, 'available', False)), 'weekly': False, 'sessions': True, 'semantic_retrieval': False}, 'limitations': ['Structured lookup requires a configured provider.', 'Weekly reporting and semantic retrieval are unavailable.']}

    @app.post('/api/complaints', response_model=ComplaintResult)
    def complaint(body: ComplaintRequest, request: Request):
        if body.session_id is not None:
            if load(body.session_id) is None:
                return error(404, 'SESSION_NOT_FOUND', 'Session not found.')
            return error(409, 'SESSION_CONFLICT', 'Use the session messages endpoint to continue this complaint.')
        sid = new_id('sess')
        request.state.trace['session_id'] = sid
        session_trace.set(sid)
        state = initial(body.email_text, provider, timeout, calls, sid)
        state['category'] = classify('', body.email_text)
        state['result']['complaint']['category'] = state['category']
        if state['result']['order']:
            order = state['result']['order']
            add_evidence(state, {'system_version': order['system_version'], 'order_id': order['order_id']})
        store.create(state['result']['session_id'], state)
        return state['result']

    @app.get('/api/sessions/{session_id}', response_model=ComplaintResult)
    def recover(session_id: str):
        state = load(session_id)
        if state is None:
            return error(404, 'SESSION_NOT_FOUND', 'Session not found.')
        result = dict(state['result'], request_id=new_id('req'), recovered=True, messages=state['messages'])
        return result

    @app.post('/api/sessions/{session_id}/messages', response_model=ComplaintResult)
    def message(session_id: str, body: MessageRequest):
        state = load(session_id)
        if state is None:
            return error(404, 'SESSION_NOT_FOUND', 'Session not found.')
        result = ComplaintResult.model_validate(state['result'])
        result.request_id = new_id('req')
        if body.message and refusal(body.message):
            result.status = 'refused'
            result.guardrail = {'code': 'PROHIBITED_REQUEST', 'pii_masked': []}
            result.abstention = {'reason': 'This request cannot be processed.'}
            result.recommendation = None
            result.follow_up_answer = None
            result.clarification = None
            result.request_id = new_id('req')
            state['result'] = ComplaintResult.model_validate(result.model_dump(warnings=False)).model_dump()
            state['messages'].extend([{'role': 'user', 'text': '[Refused request withheld]'}, {'role': 'assistant', 'text': 'The request was refused.'}])
            if not store.update(session_id, state):
                return error(409, 'SESSION_CONFLICT', 'The session changed. Please retry.')
            return state['result']
        if state.get('source_version') is None and not body.selected_candidate and body.message:
            if order_references(body.message):
                updated = initial(body.message, provider, timeout, calls, session_id)
                updated['category'] = state['category']
                updated['result']['complaint']['category'] = state['category']
                if updated['result']['order']:
                    order = updated['result']['order']
                    add_evidence(updated, {'system_version': order['system_version'], 'order_id': order['order_id']})
                updated['messages'] = state['messages'] + [{'role':'user', 'text':'[Order reference provided]'}, {'role':'assistant', 'text':'Order candidates checked; see the result.'}]
                updated['_stored'] = state['_stored']
                if not store.update(session_id, updated):
                    return error(409, 'SESSION_CONFLICT', 'The session changed. Please retry.')
                return updated['result']
        if body.selected_candidate:
            selected = body.selected_candidate
            if result.order and (result.order.system_version != selected.system_version or result.order.order_id != selected.order_id):
                return error(409, 'SESSION_CONFLICT', 'Start a new complaint to change the selected order.')
            needs_evidence = result.order is None
            offered = next((c for c in result.candidates if c.system_version == selected.system_version and c.order_id == selected.order_id), None)
            if offered is None:
                return error(422, 'VALIDATION_ERROR', 'The selected candidate is not eligible for this session.')
            # Revalidation uses a source snapshot/version, never browser-supplied dates.
            class Revalidator:
                def resolve(self, _):
                    return provider.revalidate(state['source_version'], state['received_date'], selected.model_dump())
            batch, received, candidates, _ = validate_source(calls.resolve(Revalidator(), '', timeout))
            candidates = [c for c in candidates if c.system_version in state.get('order_references', {}).get(str(c.order_id), [])]
            if batch != state['source_version'] or received != state['received_date'] or not any(c.system_version == selected.system_version and c.order_id == selected.order_id and c.created == offered.created for c in candidates):
                return error(409, 'SOURCE_CHANGED', 'The saved evidence can no longer be verified. Start a new complaint.')
            result.order = {'system_version': selected.system_version, 'order_id': selected.order_id, 'customer': None, 'postal_code': None, 'zone': None, 'driver_code': None, 'promised_date': None, 'citations': offered.citations}
            result.status = 'partial'
            result.clarification = None
            result.abstention = {'reason': 'The available records do not establish a supported resolution.'}
        if body.message:
            result.follow_up_answer = 'The question cannot be answered from the saved verified evidence.'
            if not body.selected_candidate:
                for key, words in [('pod', r'\b(pod|proof of delivery|signature)\b'), ('policy', r'\b(policy|guide|rule)\b'), ('gps', r'\b(gps|location|tracking)\b')]:
                    if re.search(words, body.message, re.I):
                        card = next((item for item in result.evidence if item.key == key), None)
                        if card:
                            result.follow_up_answer = card.summary
                        break
            if body.selected_candidate:
                result.clarification = {'question': 'Does your question concern the selected order?', 'hint': 'The message was not interpreted because free text may contain conflicting instructions.'}
        result.recovered, result.messages = False, None
        state['result'] = ComplaintResult.model_validate(result.model_dump(warnings=False)).model_dump()
        if body.selected_candidate and needs_evidence:
            add_evidence(state, body.selected_candidate.model_dump())
        state['messages'].extend([{'role': 'user', 'text': '[Follow-up withheld]'}, {'role': 'assistant', 'text': 'Follow-up processed; see the saved result.'}])
        if not store.update(session_id, state):
            return error(409, 'SESSION_CONFLICT', 'The session changed. Please retry.')
        return state['result']

    return app


app = create_app()
