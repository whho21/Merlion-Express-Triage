"""HTTP-04/05 weekly endpoint tests: unavailable default and fixture source."""
import unittest

from fastapi.testclient import TestClient

from backend.api_service.app import create_app
from evals.weekly_fixture import FixtureWeeklySource


class UnavailableSourceTests(unittest.TestCase):
    """Production default: honest empty weeks and 503, never invented zeros."""

    def setUp(self):
        self.client = TestClient(create_app())

    def test_weeks_is_empty_with_timezone(self):
        r = self.client.get('/api/weekly/weeks')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {'weeks': [], 'timezone': 'Asia/Singapore', 'synthetic': False})

    def test_weekly_is_503_dependency_unavailable(self):
        r = self.client.get('/api/weekly', params={'week_start': '2026-02-16'})
        self.assertEqual(r.status_code, 503)
        body = r.json()
        self.assertEqual(body['error']['code'], 'DEPENDENCY_UNAVAILABLE')
        self.assertTrue(body['error']['retryable'])

    def test_health_reports_weekly_unavailable(self):
        self.assertFalse(self.client.get('/api/health').json()['features']['weekly'])


class FixtureSourceTests(unittest.TestCase):
    """Demo profile: the frozen contract shape D and E build against."""

    def setUp(self):
        self.client = TestClient(create_app(weekly_source=FixtureWeeklySource()))

    def test_weeks_sorted_ascending_and_labelled_synthetic(self):
        r = self.client.get('/api/weekly/weeks')
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body['weeks'], ['2026-02-09', '2026-02-16'])
        self.assertTrue(body['synthetic'])

    def test_valid_week_returns_full_contract_shape(self):
        r = self.client.get('/api/weekly', params={'week_start': '2026-02-16'})
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body['period']['week_start'], '2026-02-16')
        self.assertEqual(body['period']['timezone'], 'Asia/Singapore')
        self.assertEqual(body['totals']['complaints'], 25)
        self.assertTrue(body['definitions'])
        self.assertTrue(body['by_zone'] and body['by_driver'] and body['by_category'] and body['by_resolution'])
        self.assertTrue(body['zone_category']['rows'])
        self.assertTrue(body['trend'])
        self.assertTrue(body['limitations'])
        self.assertTrue(body['citations'])

    def test_unknown_valid_week_is_404_no_data(self):
        r = self.client.get('/api/weekly', params={'week_start': '2026-02-23'})
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.json()['error']['code'], 'NO_DATA')

    def test_non_monday_is_422(self):
        r = self.client.get('/api/weekly', params={'week_start': '2026-02-17'})
        self.assertEqual(r.status_code, 422)
        self.assertEqual(r.json()['error']['code'], 'VALIDATION_ERROR')

    def test_malformed_and_missing_week_start_are_422(self):
        self.assertEqual(self.client.get('/api/weekly', params={'week_start': 'soon'}).status_code, 422)
        self.assertEqual(self.client.get('/api/weekly').status_code, 422)

    def test_health_reports_weekly_available(self):
        self.assertTrue(self.client.get('/api/health').json()['features']['weekly'])


if __name__ == '__main__':
    unittest.main()
