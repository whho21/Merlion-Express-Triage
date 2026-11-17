"""TOOL-05 reference implementation: live MySQL order-candidate provider.

Developer B (Jenn Fang) owns the structured lookup (team plan v0.5, task 5); this
module is a reviewed reference implementation she can adopt, own and extend.
It implements the injectable provider contract recorded in
docs/03-Handoffs/John_2026-11-17-complaint-session-api.md ("B -> C structured-
provider integration") and TOOL-05 in docs/02-Design/api-catalog_v0.9.1.md.

Contract summary:
- `resolve(text)`: extract order references from the complaint text and return
  read-only candidates from the seeded instructor `orders` table.
- `revalidate(version, received_date, identity)`: recheck one saved selection
  against the current published source fingerprint and the ORIGINAL complaint
  context; the API turns a mismatch into 409 SOURCE_CHANGED.
- Failures raise; they must never become a successful empty search. The API
  maps provider exceptions to 503 DEPENDENCY_UNAVAILABLE.

Honest limits (documented, not hidden):
- The pasted complaint text carries no trusted send date, so a fresh lookup uses
  the current Asia/Singapore calendar date as `received_date`. Case-log dated
  flows must pass their own date instead of relying on the clock.
- Candidates expose system_version/order_id/created/status only. Customer name,
  phone, address and postal values stay in MySQL until masking is agreed.
- Contact/case-log cross references (TOOL-05 contact_context) are not used as
  automatic matches; that evidence stays out until B reviews it.

Configuration (all optional, env overrides):
    CAPSTONE_DB_HOST (127.0.0.1), CAPSTONE_DB_PORT (3306),
    CAPSTONE_DB_USER (root), CAPSTONE_DB_PASSWORD (capstone),
    CAPSTONE_DB_NAME (merlion_express)

Requires `mysql-connector-python` (in backend/api_service/requirements.txt).
"""
from __future__ import annotations

import hashlib
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from .service import order_references

REPORT_ZONE = ZoneInfo('Asia/Singapore')
MAX_CANDIDATES = 50  # validate_source rejects more than 50; fail honestly instead.


class SqlProviderError(RuntimeError):
    """Live lookup failure. Any exception from the provider becomes a 503."""


def _config():
    return {
        'host': os.environ.get('CAPSTONE_DB_HOST', '127.0.0.1'),
        'port': int(os.environ.get('CAPSTONE_DB_PORT', '3306')),
        'user': os.environ.get('CAPSTONE_DB_USER', 'root'),
        'password': os.environ.get('CAPSTONE_DB_PASSWORD', 'capstone'),
        'database': os.environ.get('CAPSTONE_DB_NAME', 'merlion_express'),
    }


def _connect():
    # Imported lazily so the API service imports cleanly without the driver.
    import mysql.connector

    config = _config()
    try:
        return mysql.connector.connect(
            host=config['host'], port=config['port'], user=config['user'],
            password=config['password'], database=config['database'],
            connection_timeout=3, charset='utf8mb4',
        )
    except Exception as exc:  # credentials, network, server down
        raise SqlProviderError('orders lookup could not connect to MySQL') from exc


class MySqlProvider:
    """Live structured provider over the seeded instructor `orders` table."""

    available = True

    def __init__(self, connection_factory=_connect, today=None):
        self._connection_factory = connection_factory
        self._today = today or (lambda: datetime.now(REPORT_ZONE).date())

    # -- provider contract -------------------------------------------------
    def resolve(self, text):
        """Return the provider result shape for the order references in text."""
        refs = order_references(text)
        numbers = list(refs)
        with self._cursor() as cursor:
            version = self._fingerprint(cursor)
            rows = []
            for number in numbers:
                rows.extend(self._query(cursor, int(number), refs[number]))
        candidates = [self._candidate(row) for row in rows]
        if len(candidates) > MAX_CANDIDATES:
            raise SqlProviderError('orders lookup exceeded the candidate limit')
        status = 'found' if candidates else 'not_found'
        return self._result(status, candidates, version)

    def revalidate(self, saved_version, received_date, identity):
        """Recheck one saved identity; echo the saved received_date unchanged."""
        try:
            number = int(identity['order_id'])
            versions = [str(identity['system_version'])]
        except (KeyError, TypeError, ValueError) as exc:
            raise SqlProviderError('invalid revalidation identity') from exc
        with self._cursor() as cursor:
            version = self._fingerprint(cursor)
            rows = self._query(cursor, number, versions)
        return self._result('found' if rows else 'not_found',
                            [self._candidate(row) for row in rows],
                            version, received_date)

    # -- internals ----------------------------------------------------------
    def _cursor(self):
        try:
            connection = self._connection_factory()
        except SqlProviderError:
            raise
        except Exception as exc:
            raise SqlProviderError('orders lookup could not connect to MySQL') from exc
        return _CursorScope(connection)

    def _fingerprint(self, cursor):
        """Cheap deterministic snapshot identity of the published orders data."""
        cursor.execute(
            "SELECT COUNT(*), COALESCE(SUM(CRC32(CONCAT_WS('|', system_version,"
            " order_id, IFNULL(order_date, ''), IFNULL(promised_date, ''),"
            " IFNULL(status, '')))), 0) FROM orders")
        count, crc = cursor.fetchone()
        digest = hashlib.sha256(f'{int(count)}:{crc}'.encode()).hexdigest()[:16]
        return f'orders-{digest}'

    def _query(self, cursor, number, versions):
        if versions == ['v1', 'v2']:
            cursor.execute(
                'SELECT system_version, order_id, order_date, promised_date, status'
                ' FROM orders WHERE order_id = %s ORDER BY system_version', (number,))
        else:
            placeholders = ', '.join(['%s'] * len(versions))
            cursor.execute(
                'SELECT system_version, order_id, order_date, promised_date, status'
                f' FROM orders WHERE order_id = %s AND system_version IN ({placeholders})'
                ' ORDER BY system_version', (number, *versions))
        rows = cursor.fetchall()
        seen = set()
        for row in rows:
            key = (row[0], int(row[1]))
            if key in seen:
                # Numbering restarted on the v2 migration; the composite pair is
                # unique in the supplied dump. A duplicate is a data defect.
                raise SqlProviderError(f'duplicate order identity {key[0]}:{key[1]}')
            seen.add(key)
        return rows

    def _candidate(self, row):
        system_version, order_id, order_date, _promised, status = row
        identity = {'system_version': system_version, 'order_id': int(order_id)}
        return {
            **identity,
            'created': order_date.isoformat() if hasattr(order_date, 'isoformat') else str(order_date),
            'status': status,
            'citation': {
                'type': 'sql',
                'source_id': 'sql:orders',
                'ref': 'merlion_express.orders',
                'locator': 'order:row',
                'record_key': identity,
            },
        }

    def _result(self, status, candidates, version=None, received_date=None):
        return {
            'status': status,
            'source_version': version or '',
            'received_date': received_date or self._today().isoformat(),
            'candidates': candidates,
        }


class _CursorScope:
    """Open a connection/cursor pair; close both on exit."""

    def __init__(self, connection):
        self._connection = connection
        self._cursor = connection.cursor()

    def __enter__(self):
        return self._cursor

    def __exit__(self, *_):
        try:
            self._cursor.close()
        finally:
            self._connection.close()
        return False
