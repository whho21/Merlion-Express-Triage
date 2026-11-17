"""Unit tests for the TOOL-05 MySQL provider (fake connection, no live DB)."""
import unittest
from datetime import date
from unittest.mock import MagicMock

from backend.api_service.sql_provider import MySqlProvider, SqlProviderError


class FakeCursor:
    """Scripted cursor: executes recorded SQL, returns queued result sets."""

    def __init__(self, results):
        self.results = list(results)
        self.executed = []

    def execute(self, sql, params=()):
        self.executed.append((sql, params))
        sql_head = ' '.join(sql.split())[:40]
        if sql_head.startswith('SELECT COUNT'):
            self._current = self.results.pop(0)
        else:
            self._current = self.results.pop(0)

    def fetchone(self):
        return self._current

    def fetchall(self):
        return self._current

    def close(self):
        pass


def provider_with(results, today=date(2026, 11, 17)):
    cursor = FakeCursor(results)
    connection = MagicMock()
    connection.cursor.return_value = cursor
    return MySqlProvider(connection_factory=lambda: connection, today=lambda: today), cursor


ORDER_ROW = ('v1', 20095, date(2026, 1, 10), date(2026, 1, 12), 'DELIVERED')


class ResolveTests(unittest.TestCase):
    def test_found_returns_contract_shape(self):
        provider, cursor = provider_with([(250, '12345'), [ORDER_ROW]])
        result = provider.resolve('Problem with order 20095')
        self.assertEqual(result['status'], 'found')
        self.assertRegex(result['source_version'], r'^orders-[0-9a-f]{16}$')
        self.assertEqual(result['received_date'], '2026-11-17')
        candidate = result['candidates'][0]
        self.assertEqual(candidate['system_version'], 'v1')
        self.assertEqual(candidate['order_id'], 20095)
        self.assertEqual(candidate['created'], '2026-01-10')
        self.assertEqual(candidate['status'], 'DELIVERED')
        self.assertEqual(candidate['citation']['record_key'], {'system_version': 'v1', 'order_id': 20095})
        self.assertEqual(candidate['citation']['type'], 'sql')
        self.assertEqual(candidate['citation']['ref'], 'merlion_express.orders')
        # No personal columns are selected or exposed.
        sql = ' '.join(cursor.executed[1][0].split()).lower()
        self.assertNotIn('customer', sql)
        self.assertNotIn('phone', sql)
        self.assertNotIn('address', sql)
        self.assertNotIn('postal', sql)

    def test_explicit_hint_restricts_system_version(self):
        provider, cursor = provider_with([(250, '12345'), []])
        provider.resolve('Order V1-20095 arrived late')
        sql, params = cursor.executed[1]
        self.assertIn('system_version IN', sql)
        self.assertEqual(params, (20095, 'v1'))
        # Placeholder count must match the parameter count for the real driver.
        self.assertEqual(sql.count('%s'), len(params))

    def test_not_found_is_empty_success(self):
        provider, _ = provider_with([(250, '12345'), []])
        result = provider.resolve('order 20095')
        self.assertEqual(result['status'], 'not_found')
        self.assertEqual(result['candidates'], [])

    def test_both_systems_when_unqualified(self):
        provider, cursor = provider_with([(250, '12345'), []])
        provider.resolve('order 20095')
        sql, params = cursor.executed[1]
        self.assertNotIn('system_version IN', sql)
        self.assertEqual(params, (20095,))

    def test_duplicate_identity_is_a_data_defect(self):
        provider, _ = provider_with([(250, '12345'),
                                     [ORDER_ROW, (ORDER_ROW[0], 20095, ORDER_ROW[2], None, 'OPEN')]])
        with self.assertRaises(SqlProviderError):
            provider.resolve('order 20095')

    def test_database_failure_raises(self):
        def broken():
            raise ConnectionError('down')
        p = MySqlProvider(connection_factory=broken)
        with self.assertRaises(SqlProviderError):
            p.resolve('order 20095')

    def test_candidate_limit_is_enforced(self):
        rows = [(f'v{1 + i % 2}', i, date(2026, 1, 1), None, 'OPEN') for i in range(51)]
        provider, _ = provider_with([(250, '12345'), rows])
        with self.assertRaises(SqlProviderError):
            provider.resolve('order 20095')

    def test_result_passes_api_validate_source(self):
        """The whole point: the provider shape must survive the API's strict checks."""
        from backend.api_service.service import validate_source
        provider, _ = provider_with([(250, '12345'), [ORDER_ROW]])
        raw = provider.resolve('order V1-20095')
        batch, received, candidates, citations = validate_source(raw)
        self.assertEqual(batch, raw['source_version'])
        self.assertEqual(received, '2026-11-17')
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].citations, [1])


class RevalidateTests(unittest.TestCase):
    def test_revalidate_echoes_saved_context(self):
        provider, cursor = provider_with([(250, '12345'), [ORDER_ROW]])
        result = provider.revalidate('orders-abc', '2026-03-01',
                                     {'system_version': 'v1', 'order_id': 20095})
        self.assertEqual(result['status'], 'found')
        self.assertEqual(result['received_date'], '2026-03-01')
        self.assertNotEqual(result['source_version'], '')  # fresh fingerprint
        sql, params = cursor.executed[1]
        self.assertEqual(params, (20095, 'v1'))

    def test_revalidate_rejects_bad_identity(self):
        provider, _ = provider_with([(250, '12345'), []])
        with self.assertRaises(SqlProviderError):
            provider.revalidate('orders-abc', '2026-03-01', {'order_id': 'x'})


if __name__ == '__main__':
    unittest.main()
