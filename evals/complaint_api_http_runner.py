"""Interim HTTP-01..03 case runner (C's starter role; E's shared runner supersedes).

    python -m evals.complaint_api_http_runner            # synthetic cases, sql cases SKIP
    python -m evals.complaint_api_http_runner --with-sql # also run sql cases (needs seeded MySQL)

Executes evals/complaint_api_http_cases.json steps against TestClient.
A `restart` step builds a fresh app instance on the SAME SQLite db_path with the
SAME provider object — genuine store-level recovery evidence. The sql cases
require `python -m scripts.check_sql_provider` to pass first; they are marked
SKIP (not FAIL) when MySQL is unavailable.
"""
from __future__ import annotations

import argparse
import json
import re
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from backend.api_service.app import create_app
from backend.api_service.sql_provider import MySqlProvider, SqlProviderError
from evals.complaint_api_fixture import SyntheticProvider


class CountingProvider:
    """Delegate with a call counter so provider_calls_delta works for any provider."""

    def __init__(self, delegate):
        self.delegate = delegate
        self.calls = 0

    @property
    def available(self):
        return getattr(self.delegate, 'available', True)

    def resolve(self, text):
        self.calls += 1
        return self.delegate.resolve(text)

    def revalidate(self, *args):
        self.calls += 1
        return self.delegate.revalidate(*args)


def expand(value):
    """Expand 'x20001' → 20001 x's (size-limit bodies)."""
    if isinstance(value, str) and (match := re.fullmatch(r'x(\d+)', value)):
        return 'x' * int(match.group(1))
    return value


def resolve_target(case, step, state):
    target = step.get('target')
    if target == '$first':
        return state.get('first_session_id') or ''
    if target:
        return target
    return state.get('session_id') or ''


def fill_body(body, state):
    if not isinstance(body, dict):
        return body
    return {key: (state.get('session_id') if value == '$session_id' else expand(value))
            for key, value in body.items()}


def check(expect, http, body, response, provider_calls_before, provider_calls, failures):
    def fail(message):
        failures.append(message)

    wanted_http = expect.get('http', 200)
    if http != wanted_http:
        fail(f"http {http} != {wanted_http}")
        return
    if http != 200:
        error = (body.get('error') or {}) if isinstance(body, dict) else {}
        if expect.get('error_code') and error.get('code') != expect['error_code']:
            fail(f"error_code {error.get('code')} != {expect['error_code']}")
        return
    if expect.get('status') and body.get('status') != expect['status']:
        fail(f"status {body.get('status')} != {expect['status']}")
    if expect.get('guardrail') and (body.get('guardrail') or {}).get('code') != expect['guardrail']:
        fail(f"guardrail {(body.get('guardrail') or {}).get('code')} != {expect['guardrail']}")
    if expect.get('candidates') is not None and len(body.get('candidates') or []) != expect['candidates']:
        fail(f"candidates {len(body.get('candidates') or [])} != {expect['candidates']}")
    if expect.get('citations_min') and len(body.get('citations') or []) < expect['citations_min']:
        fail(f"citations {len(body.get('citations') or [])} < {expect['citations_min']}")
    for key, status in (expect.get('evidence') or {}).items():
        card = next((item for item in body.get('evidence') or [] if item['key'] == key), None)
        if card is None or card['status'] != status:
            found = card['status'] if card else 'missing'
            fail(f"evidence[{key}] {found} != {status}")
    if expect.get('recommendation_null') and body.get('recommendation') is not None:
        fail('recommendation is not null')
    if expect.get('clarification') and body.get('clarification') is None:
        fail('clarification missing')
    if expect.get('follow_up_contains') and expect['follow_up_contains'] not in (body.get('follow_up_answer') or ''):
        fail(f"follow_up_answer does not contain {expect['follow_up_contains']!r}")
    if expect.get('recovered') and not body.get('recovered'):
        fail('recovered flag missing')
    if expect.get('messages_withheld'):
        messages = body.get('messages') or []
        if not messages or not all(m['text'].startswith('[') for m in messages if m['role'] == 'user'):
            fail('user messages are not withheld markers')
    if expect.get('provider_calls_delta') is not None:
        delta = provider_calls - provider_calls_before
        if delta != expect['provider_calls_delta']:
            fail(f"provider_calls_delta {delta} != {expect['provider_calls_delta']}")
    for forbidden in expect.get('text_absent') or []:
        if forbidden in response.text:
            fail(f"forbidden text present: {forbidden!r}")


def run_case(case, with_sql):
    requires = case['requires']
    if requires == 'parallel':
        return 'SKIP', ['parallel case — run manually or in the shared runner']
    provider, skip_reason = None, None
    if requires == 'sql':
        if not with_sql:
            return 'SKIP', ['sql case — run with --with-sql on a seeded database']
        try:
            MySqlProvider().resolve('')
        except SqlProviderError as exc:
            return 'SKIP', [f'sql case — MySQL unavailable ({exc})']
        provider = CountingProvider(MySqlProvider())
    else:
        provider = CountingProvider(SyntheticProvider())
    failures = []
    temp = tempfile.TemporaryDirectory()
    state = {}
    try:
        client = TestClient(create_app(provider, str(Path(temp.name) / 'sessions.db')))
        for step in case['steps']:
            action, expect = step['action'], step.get('expect', {})
            before = provider.calls
            if action == 'restart':
                client.close()
                client = TestClient(create_app(provider, str(Path(temp.name) / 'sessions.db')))
                continue
            if action == 'complaint':
                response = client.post('/api/complaints', json=fill_body(step.get('body'), state))
            elif action == 'message':
                response = client.post(f"/api/sessions/{resolve_target(case, step, state)}/messages",
                                       json=fill_body(step.get('body'), state))
            else:
                response = client.get(f"/api/sessions/{resolve_target(case, step, state)}")
            body = response.json()
            check(expect, response.status_code, body, response, before, provider.calls, failures)
            if isinstance(body, dict) and body.get('session_id'):
                state['first_session_id'] = state.setdefault('first_session_id', body['session_id'])
                if response.request.method == 'POST':
                    state['session_id'] = body['session_id']
        client.close()
    finally:
        temp.cleanup()
    return ('FAIL', failures) if failures else ('PASS', [])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--with-sql', action='store_true')
    args = parser.parse_args(argv)
    cases = json.loads(Path('evals/complaint_api_http_cases.json').read_text())['cases']
    tally = {}
    for case in cases:
        outcome, failures = run_case(case, args.with_sql)
        tally[outcome] = tally.get(outcome, 0) + 1
        print(f"{outcome} {case['id']} {case['name']}")
        for failure in failures:
            print(f"     - {failure}")
    print(f"\n{tally}")
    return 1 if tally.get('FAIL') else 0


if __name__ == '__main__':
    raise SystemExit(main())
