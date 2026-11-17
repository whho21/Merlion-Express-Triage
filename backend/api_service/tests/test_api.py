import unittest

from fastapi.testclient import TestClient

from backend.api_service.app import app


class BootstrapApiTests(unittest.TestCase):
    def test_health_is_liveness_with_unavailable_domain_features(self):
        with TestClient(app) as client:
            response = client.get('/api/health')
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data['service'], 'merlion-express-api')
            self.assertEqual(data['status'], 'degraded')
            self.assertTrue(all(value is False for value in data['features'].values()))
            self.assertTrue(data['limitations'])
            self.assertNotEqual(data['request_id'], client.get('/api/health').json()['request_id'])

    def test_openapi_does_not_advertise_unimplemented_routes(self):
        with TestClient(app) as client:
            self.assertEqual(set(client.get('/openapi.json').json()['paths']), {'/api/health'})
            self.assertEqual(client.post('/api/complaints', json={'email_text': 'synthetic'}).status_code, 404)
            self.assertEqual(client.get('/api/weekly').status_code, 404)

    def test_cors_allows_local_ui_but_not_unrelated_origins(self):
        with TestClient(app) as client:
            good = client.get('/api/health', headers={'Origin': 'http://127.0.0.1:5173'})
            self.assertEqual(good.headers['access-control-allow-origin'], 'http://127.0.0.1:5173')
            bad = client.get('/api/health', headers={'Origin': 'https://unrelated.invalid'})
            self.assertNotIn('access-control-allow-origin', bad.headers)


if __name__ == '__main__':
    unittest.main()
