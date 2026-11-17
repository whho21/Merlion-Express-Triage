import contextlib
import importlib.util
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('capstone_start_services', ROOT / 'scripts/start_services.py')
services = importlib.util.module_from_spec(spec)
spec.loader.exec_module(services)


class LauncherTests(unittest.TestCase):
    def setUp(self):
        # Unit tests never contact a real database; individual cases override this probe.
        probe = patch.object(services, 'local_mysql_running', return_value=False)
        probe.start()
        self.addCleanup(probe.stop)

    def test_missing_dependency_blocks_startup(self):
        def dependency(name):
            if name == 'uvicorn':
                raise ImportError('missing')
            return Mock()
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(services, 'ROOT', Path(folder)), \
                 patch.object(services.importlib, 'import_module', side_effect=dependency), \
                 patch.object(services, 'port_free', return_value=True), \
                 patch.object(services, 'launch') as launch, \
                 patch.object(services, 'compose') as compose, \
                 contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(services.main(['--skip-mysql', '--no-frontend']), 1)
                self.assertIn("-m pip install -r backend/api_service/requirements.txt", output.getvalue())
                launch.assert_not_called()
                compose.assert_not_called()
                self.assertFalse((Path(folder) / 'output').exists())

    def test_missing_node_and_docker_have_path_setup_actions(self):
        with patch.object(services, 'port_free', return_value=True), \
             patch.object(services.shutil, 'which', return_value=None), \
             patch.object(services, 'command', return_value=Mock(returncode=0)), \
             patch.object(services, 'launch') as launch, \
             patch.object(services, 'compose') as compose, \
             contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(services.main([]), 1)
            text = output.getvalue()
            self.assertIn('Docker CLI available on PATH', text)
            self.assertIn('Install Docker Desktop or enable its Docker CLI', text)
            self.assertIn('Node.js available on PATH', text)
            self.assertIn('load your Node version manager', text)
            launch.assert_not_called()
            compose.assert_not_called()

    def test_stopped_docker_blocks_startup_and_suggests_starting_desktop(self):
        def command(argv, **kwargs):
            return Mock(returncode=1 if argv == ['docker', 'info'] else 0)
        with patch.object(services, 'port_free', return_value=True), \
             patch.object(services.shutil, 'which', return_value='/test/docker'), \
             patch.object(services, 'command', side_effect=command), \
             patch.object(services, 'launch') as launch, \
             patch.object(services, 'compose') as compose, \
             contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(services.main(['--no-frontend']), 1)
            self.assertIn('[ ] Docker Desktop/daemon running', output.getvalue())
            self.assertIn('Start Docker Desktop and wait for the engine', output.getvalue())
            launch.assert_not_called()
            compose.assert_not_called()

    def test_inconsistent_python_dependencies_block_without_leaking_pip_output(self):
        with patch.object(services, 'port_free', return_value=True), \
             patch.object(services, 'command', return_value=Mock(returncode=1, stdout='PRIVATE DETAIL')), \
             patch.object(services, 'launch') as launch, \
             contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(services.main(['--skip-mysql', '--no-frontend']), 1)
            text = output.getvalue()
            self.assertIn('[ ] Installed Python dependency versions are consistent', text)
            self.assertIn('install/repair API packages', text)
            self.assertNotIn('PRIVATE DETAIL', text)
            launch.assert_not_called()

    def test_running_local_mysql_needs_no_docker_or_mysql_cli(self):
        args = services.arguments(['--no-frontend'])
        with patch.object(services, 'local_mysql_running', return_value=True), \
             patch.object(services, 'port_free', return_value=True), \
             patch.object(services.shutil, 'which') as which, \
             patch.object(services, 'command', return_value=Mock(returncode=0)) as command, \
             patch.object(services, 'compose') as compose, \
             contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertTrue(services.preflight(args))
            self.assertEqual(args._mysql_backend, 'local')
            services.start_database(args)
            self.assertIn('Docker not required', output.getvalue())
            which.assert_not_called()
            compose.assert_not_called()
            self.assertTrue(all(call.args[0][0] != 'docker' for call in command.call_args_list))

    def test_auto_mode_checks_docker_when_no_local_mysql_is_running(self):
        args = services.arguments(['--no-frontend'])
        with patch.object(services, 'port_free', return_value=True), \
             patch.object(services.shutil, 'which', return_value='/test/docker'), \
             patch.object(services, 'command', return_value=Mock(returncode=0)) as command, \
             patch.object(services, 'start_mysql') as docker, \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertTrue(services.preflight(args))
            self.assertEqual(args._mysql_backend, 'docker')
            services.start_database(args)
            docker.assert_called_once_with()
            self.assertIn(['docker', 'info'], [call.args[0] for call in command.call_args_list])
            self.assertIn(['docker', 'compose', 'version'], [call.args[0] for call in command.call_args_list])

    def test_local_mode_does_not_fall_back_to_docker_when_stopped(self):
        args = services.arguments(['--mysql-mode', 'local', '--no-frontend'])
        with patch.object(services, 'port_free', return_value=True), \
             patch.object(services.shutil, 'which') as which, \
             patch.object(services, 'command', return_value=Mock(returncode=0)), \
             contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertFalse(services.preflight(args))
            self.assertIn('Start your local MySQL service', output.getvalue())
            which.assert_not_called()

    def test_auto_mode_blocks_unknown_listener_without_starting_docker(self):
        args = services.arguments(['--no-frontend'])
        with patch.object(services, 'port_free', side_effect=lambda port: port != 3306), \
             patch.object(services.shutil, 'which') as which, \
             patch.object(services, 'command', return_value=Mock(returncode=0)), \
             contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertFalse(services.preflight(args))
            self.assertIn('occupied but did not return a MySQL greeting', output.getvalue())
            which.assert_not_called()

    def test_mysql_disappearing_after_preflight_does_not_start_docker(self):
        args = services.arguments(['--no-frontend'])
        args._mysql_backend = 'local'
        with patch.object(services, 'start_mysql') as docker, \
             self.assertRaisesRegex(RuntimeError, 'stopped responding'):
            services.start_database(args)
        docker.assert_not_called()

    def test_default_checks_before_starting_all_services(self):
        events = []
        api, frontend = Mock(), Mock()
        api.poll.return_value = frontend.poll.return_value = None

        def preflight(args):
            events.append('check')
            return True

        def launch(argv, *args):
            name = 'api' if 'uvicorn' in argv else 'frontend'
            events.append(name)
            return api if name == 'api' else frontend

        ready = {'service': 'merlion-express-api',
                 'features': {'triage': True, 'weekly': True, 'sessions': True}}
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(services, 'ROOT', Path(folder)), \
                 patch.object(services, 'preflight', side_effect=preflight), \
                 patch.object(services, 'start_mysql', side_effect=lambda: events.append('mysql')), \
                 patch.object(services, 'launch', side_effect=launch), \
                 patch.object(services, 'wait_http', side_effect=[ready, None]), \
                 patch.object(services.time, 'sleep', side_effect=KeyboardInterrupt), \
                 patch.object(services, 'stop_process') as stop, \
                 contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(services.main([]), 0)
                self.assertEqual(events, ['check', 'mysql', 'api', 'frontend'])
                self.assertEqual([call.args[0] for call in stop.call_args_list], [frontend, api])

    def test_mysql_start_only_probes_and_never_imports(self):
        responses = [Mock(returncode=0), Mock(returncode=0), Mock(returncode=0, stdout='3\n')]
        with patch.object(services, 'compose', side_effect=responses) as compose, \
             contextlib.redirect_stdout(io.StringIO()):
            services.start_mysql()
        self.assertEqual(compose.call_args_list[0].args, ('up', '-d', 'mysql'))
        query = compose.call_args_list[2].args[-1]
        self.assertIn('information_schema.tables', query)
        self.assertNotIn('INSERT', query)
        self.assertNotIn('DROP', query)

    def test_live_ui_requires_ready_features_and_cleans_up_api(self):
        child = Mock()
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(services, 'ROOT', Path(folder)), \
                 patch.object(services, 'preflight', return_value=True), \
                 patch.object(services, 'launch', return_value=child) as launch, \
                 patch.object(services, 'wait_http', return_value={'service': 'merlion-express-api', 'features': {}}), \
                 patch.object(services, 'stop_process') as stop, \
                 contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                code = services.main(['--skip-mysql', '--frontend-mode', 'live'])
                self.assertEqual(code, 1)
                self.assertEqual(launch.call_count, 1)
                stop.assert_called_once_with(child)

    def test_child_exit_is_detected_without_waiting_for_a_port(self):
        child = Mock()
        child.poll.return_value = 1
        with self.assertRaisesRegex(RuntimeError, 'exited before'):
            services.wait_http(child, 'http://127.0.0.1:1')

    def test_cleanup_stops_only_owned_process(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            import os
            first = services.launch([sys.executable, '-c', 'import time; time.sleep(60)'], folder, os.environ.copy(), folder / 'first.log')
            second = services.launch([sys.executable, '-c', 'import time; time.sleep(60)'], folder, os.environ.copy(), folder / 'second.log')
            try:
                services.stop_process(first)
                self.assertIsNotNone(first.poll())
                self.assertIsNone(second.poll())
            finally:
                services.stop_process(first)
                services.stop_process(second)

    def test_node_engine_and_port_validation(self):
        for version in ('v20.19.0', 'v22.12.0', 'v24.0.0'):
            self.assertTrue(services.node_supported(version))
        for version in ('v20.18.0', 'v21.7.0', 'v22.11.0', 'not-a-version'):
            self.assertFalse(services.node_supported(version))
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            services.arguments(['--api-port', '5173', '--frontend-port', '5173'])


class MysqlGreetingTests(unittest.TestCase):
    def test_mysql_greeting_identifies_a_server_without_client_tools(self):
        payload = b'\x0a8.0.42\x00synthetic'
        packet = len(payload).to_bytes(3, 'little') + b'\x00' + payload
        class Connection:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def recv(self, count):
                nonlocal packet
                chunk, packet = packet[:count], packet[count:]
                return chunk
        with patch.object(services.socket, 'create_connection', return_value=Connection()):
            self.assertTrue(services.local_mysql_running())

    def test_a_non_mysql_tcp_service_is_not_a_database(self):
        connection = Mock()
        connection.__enter__ = Mock(return_value=connection)
        connection.__exit__ = Mock(return_value=False)
        connection.recv.return_value = b'HTTP'
        with patch.object(services.socket, 'create_connection', return_value=connection):
            self.assertFalse(services.local_mysql_running())


if __name__ == '__main__':
    unittest.main()
