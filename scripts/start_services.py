"""Cross-platform preflight and supervised local startup; no installation or ingestion."""
from __future__ import annotations

import sys

# Prerequisite checks should not create project bytecode/cache files.
sys.dont_write_bytecode = True

import argparse
from datetime import datetime
import importlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import socket
import subprocess
import time
from urllib.error import URLError
from urllib.request import ProxyHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
EVIDENCE = ("emails.jsonl", "policy_chunks.jsonl", "pod_records.jsonl", "rate_cards.jsonl")
HTTP = build_opener(ProxyHandler({}))  # Loopback probes must never use an external proxy.


def mark(ok: bool, message: str) -> None:
    print(f"[{'✅' if ok else ' '}] {message}", flush=True)


def note(message: str) -> None:
    print(f"[⚠️ ] {message}", flush=True)


def port_number(value: str) -> int:
    number = int(value)
    if not 1024 <= number <= 65535:
        raise argparse.ArgumentTypeError("Use a port between 1024 and 65535.")
    return number


def arguments(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mysql-mode", choices=("auto", "local", "docker"), default="auto",
                        help="Reuse a running local MySQL by default; otherwise use Docker.")
    parser.add_argument("--skip-mysql", action="store_true", help="Leave database management to the operator.")
    parser.add_argument("--no-frontend", action="store_true", help="Check prerequisites, then start only API and optional MySQL.")
    parser.add_argument("--frontend-mode", choices=("demo", "live"), default="demo")
    parser.add_argument("--api-port", type=port_number, default=8000)
    parser.add_argument("--frontend-port", type=port_number, default=5173)
    parser.add_argument("--reload", action="store_true", help="Enable Uvicorn development reload.")
    args = parser.parse_args(argv)
    if not args.no_frontend and args.api_port == args.frontend_port:
        parser.error("API and frontend ports must be different.")
    return args


def command(argv, timeout=15):
    return subprocess.run(argv, cwd=ROOT, text=True, capture_output=True, timeout=timeout, check=False)


def compose(*args, timeout=30):
    return command(["docker", "compose", "--project-directory", str(ROOT), "-f", str(ROOT / "docker-compose.yml"), *args], timeout=timeout)


def port_free(port: int) -> bool:
    try:
        with socket.socket() as sock:
            # POSIX servers leave TIME_WAIT sockets after shutdown; permit immediate restart.
            # Do not use SO_REUSEADDR on Windows, where it can mask an active listener.
            if os.name != "nt":
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("127.0.0.1", port))
        return True
    except OSError:
        return False


def node_supported(version: str) -> bool:
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)(?:[-+].*)?", version.strip())
    if not match:
        return False
    major, minor, _ = map(int, match.groups())
    return major == 20 and minor >= 19 or major == 22 and minor >= 12 or major > 22


def local_mysql_running() -> bool:
    """Identify MySQL's initial greeting without credentials, client tools or SQL writes."""
    def read_exact(sock, size):
        data = b""
        while len(data) < size:
            part = sock.recv(size - len(data))
            if not part:
                raise OSError("Incomplete greeting")
            data += part
        return data

    try:
        with socket.create_connection(("127.0.0.1", 3306), timeout=1) as sock:
            header = read_exact(sock, 4)
            length = int.from_bytes(header[:3], "little")
            if header[3] != 0 or not 8 <= length <= 16384:
                return False
            payload = read_exact(sock, min(length, 256))
            version = payload[1:].split(b"\0", 1)[0]
            return payload[0] in (9, 10) and re.match(rb"\d+\.\d+", version) is not None
    except OSError:
        return False


def preflight(args) -> bool:
    checks = []

    def check(ok, message):
        checks.append(ok)
        mark(ok, message)

    check(sys.version_info >= (3, 11), "Python 3.11+ (3.13 recommended)")
    check(sys.prefix != sys.base_prefix, "Project virtual environment selected")
    packages_ready = True
    python_command = r".\.venv\Scripts\python.exe" if os.name == "nt" else ".venv/bin/python"
    repair_command = f"{python_command} -m pip install -r backend/api_service/requirements.txt"
    for module in ("fastapi", "pydantic", "uvicorn"):
        try:
            importlib.import_module(module)
        except ImportError:
            packages_ready = False
            check(False, f"{module}: missing from the selected virtual environment")
        except Exception as exc:
            packages_ready = False
            check(False, f"{module}: import failed ({type(exc).__name__})")
        else:
            check(True, f"{module}: importable")
    if packages_ready:
        try:
            consistent = command([sys.executable, "-m", "pip", "check"]).returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            consistent = False
        check(consistent, "Installed Python dependency versions are consistent (pip check)")
        packages_ready = consistent
    if not packages_ready:
        note(f"From the project root, install/repair API packages: {repair_command}")
    try:
        from backend.api_service.app import app  # Validates the actual entry point, not just its file.
        check(callable(app), "backend.api_service.app:app entry point loads")
    except Exception as exc:
        # Do not print raw exceptions/configuration that could contain credentials.
        check(False, f"backend.api_service.app:app cannot load ({type(exc).__name__})")
    check(port_free(args.api_port), f"API port {args.api_port} available")
    if not args.skip_mysql:
        if args.mysql_mode != "docker" and local_mysql_running():
            args._mysql_backend = "local"
            check(True, "Existing MySQL responding on 127.0.0.1:3306; Docker not required")
            note("Reusing the existing server without restarting it. Authentication/schema checks remain in the database setup guide.")
        elif args.mysql_mode == "local":
            check(False, "Local MySQL not responding on 127.0.0.1:3306")
            note("Start your local MySQL service, then rerun startup. Docker is not required in local mode.")
        elif args.mysql_mode == "auto" and not port_free(3306):
            check(False, "Port 3306 is occupied but did not return a MySQL greeting")
            note("Check the existing database/service on port 3306; Docker will not be started over an unidentified listener.")
        else:
            args._mysql_backend = "docker"
            note("No reusable local MySQL selected; using Docker Compose.")
            installed = shutil.which("docker") is not None
            check(installed, "Docker CLI available on PATH")
            if not installed:
                note("Install Docker Desktop or enable its Docker CLI on PATH, then reopen this terminal. For WSL, enable Docker Desktop integration for the distribution.")
            if installed:
                try:
                    daemon_ready = command(["docker", "info"]).returncode == 0
                    check(daemon_ready, "Docker Desktop/daemon running")
                    if not daemon_ready:
                        note("Start Docker Desktop and wait for the engine; verify with docker info. For WSL, enable distribution integration.")
                    compose_ready = command(["docker", "compose", "version"]).returncode == 0
                    check(compose_ready, "Docker Compose v2 available")
                    if not compose_ready:
                        note("Enable/install Docker Compose v2; verify with docker compose version.")
                except (OSError, subprocess.TimeoutExpired):
                    check(False, "Docker checks failed or timed out; start Docker Desktop")
    if not args.no_frontend:
        node = shutil.which("node")
        check(node is not None, "Node.js available on PATH")
        if node is None:
            note("Install a compatible Node.js release or load your Node version manager into this terminal; verify with node --version.")
        if node:
            try:
                result = command([node, "--version"])
                supported = result.returncode == 0 and node_supported(result.stdout)
                check(supported, "Node compatible with Vite (20.19+ / 22.12+)")
                if not supported:
                    note("Select Node 20.19+ on the 20.x line, or 22.12+; reload the terminal after changing Node versions.")
            except (OSError, subprocess.TimeoutExpired):
                check(False, "Node version check failed")
        frontend_ready = (FRONTEND / "node_modules/vite/bin/vite.js").is_file()
        check(frontend_ready, "Frontend dependencies installed")
        if not frontend_ready:
            note("From the project root, run npm --prefix frontend ci (npm.cmd --prefix frontend ci in PowerShell).")
        check(port_free(args.frontend_port), f"Frontend port {args.frontend_port} available")
    if (ROOT / ".env").is_file():
        mark(True, "Project .env present (values never printed; provider validity not probed)")
    else:
        note("No project .env; health and synthetic UI work without a model key.")
    missing = [name for name in EVIDENCE if not (ROOT / "output/unstructured" / name).is_file()]
    if missing:
        note("Evidence preparation incomplete: " + ", ".join(missing) + ". No extraction will run automatically.")
    if not args.no_frontend and args.frontend_mode == "demo":
        note("Frontend will display synthetic in-browser demo data.")
    return all(checks)


def start_mysql() -> None:
    print("Starting/reusing MySQL; source data will not be imported or overwritten.", flush=True)
    result = compose("up", "-d", "mysql", timeout=180)
    if result.returncode:
        raise RuntimeError("MySQL could not start. Check Docker, port 3306 and docker compose logs mysql.")
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        result = compose("exec", "-T", "mysql", "sh", "-c",
                         'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysqladmin -h127.0.0.1 -uroot ping --silent')
        if result.returncode == 0:
            mark(True, "MySQL responding")
            query = ("SELECT COUNT(*) FROM information_schema.tables "
                     "WHERE table_schema='merlion_express' AND table_name IN ('drivers','orders','deliveries')")
            # Password is expanded inside the container, never read into the launcher/logs.
            result = compose("exec", "-T", "mysql", "sh", "-c",
                             'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql -h127.0.0.1 -uroot -N -B -e "$1"', "sh", query)
            if result.returncode != 0:
                raise RuntimeError("MySQL schema check failed; inspect the database before continuing.")
            if result.stdout.strip() == "3":
                mark(True, "Three source tables exist (row counts and application migrations are separate checks)")
            else:
                note("Source tables are not seeded. Follow database/createdb_seed_sql_data.md before live integration.")
            return
        time.sleep(2)
    raise RuntimeError("MySQL readiness timed out after 90 seconds.")


def start_database(args) -> None:
    if getattr(args, "_mysql_backend", "docker") == "local":
        if not local_mysql_running():
            raise RuntimeError("Existing MySQL stopped responding after preflight; restart it and retry.")
        mark(True, "Existing MySQL ready; no Docker commands were run")
    else:
        start_mysql()


def launch(argv, cwd: Path, env, log_path: Path):
    options = {"start_new_session": True} if os.name != "nt" else {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    with log_path.open("w", encoding="utf-8") as log:
        return subprocess.Popen(argv, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT, **options)


def stop_process(process) -> None:
    if os.name == "nt" and process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True, check=False, timeout=10)
    else:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        if os.name != "nt":
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        else:
            process.kill()
        process.wait(timeout=5)


def wait_http(process, url: str, *, json_result=False, timeout=30):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("A service exited before becoming ready; inspect its startup log.")
        try:
            with HTTP.open(Request(url), timeout=1) as response:
                if response.status == 200:
                    return json.load(response) if json_result else None
        except (URLError, OSError, ValueError):
            pass
        time.sleep(0.25)
    raise RuntimeError(f"Readiness timed out for {url}; inspect its startup log.")


def main(argv=None) -> int:
    args = arguments(argv)
    if not preflight(args):
        print("Preflight failed. Follow backend/api_service/backend_API_setup.md; nothing was started.", flush=True)
        return 1
    mark(True, "Preflight passed; starting services")
    children = []
    log_dir = ROOT / "output/startup" / (datetime.now().strftime("%Y%m%d-%H%M%S") + f"-{os.getpid()}")
    try:
        if not args.skip_mysql:
            start_database(args)
        log_dir.mkdir(parents=True, exist_ok=False, mode=0o700)
        print(f"Service logs: {log_dir}", flush=True)
        env = dict(os.environ, PYTHONUNBUFFERED="1", CAPSTONE_FRONTEND_PORT=str(args.frontend_port))
        api_args = [sys.executable, "-m", "uvicorn", "backend.api_service.app:app", "--host", "127.0.0.1", "--port", str(args.api_port)]
        if args.reload:
            api_args.extend(["--reload", "--reload-dir", str(ROOT / "backend")])
        api = launch(api_args, ROOT, env, log_dir / "api.log")
        children.append(api)
        health = wait_http(api, f"http://127.0.0.1:{args.api_port}/api/health", json_result=True)
        if health.get("service") != "merlion-express-api":
            raise RuntimeError("API health returned an unexpected service identity.")
        mark(True, f"API process responding: http://127.0.0.1:{args.api_port}/docs")
        if not all(health.get("features", {}).get(k) for k in ("triage", "weekly", "sessions")):
            note("API bootstrap only: complaint, weekly and session capabilities are not all ready.")
            if not args.no_frontend and args.frontend_mode == "live":
                raise RuntimeError("Live UI startup blocked: implement triage, weekly and sessions before selecting live mode.")
        if not args.no_frontend:
            env.update(VITE_USE_MOCK="true" if args.frontend_mode == "demo" else "false",
                       VITE_API_BASE_URL=f"http://127.0.0.1:{args.api_port}")
            vite = launch([shutil.which("node"), str(FRONTEND / "node_modules/vite/bin/vite.js"),
                           "--host", "127.0.0.1", "--port", str(args.frontend_port), "--strictPort"],
                          FRONTEND, env, log_dir / "frontend.log")
            children.append(vite)
            wait_http(vite, f"http://127.0.0.1:{args.frontend_port}")
            mark(True, f"Frontend responding: http://127.0.0.1:{args.frontend_port} ({args.frontend_mode} data)")
        print("Services running. Keep this terminal open; Ctrl+C stops this launcher's API/frontend.", flush=True)
        while True:
            for child in children:
                if child.poll() is not None:
                    raise RuntimeError("A supervised service exited; stopping the other app processes. Inspect the logs.")
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nStopping app processes...", flush=True)
        return 0
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f"[ ] {exc}", file=sys.stderr, flush=True)
        return 1
    finally:
        for child in reversed(children):
            try:
                stop_process(child)
            except (OSError, subprocess.TimeoutExpired):
                note("Could not fully stop one owned process; inspect this launch's logs/processes.")
        if not args.skip_mysql:
            if getattr(args, "_mysql_backend", "docker") == "local":
                note("Existing MySQL is left running; manage it with your local database tools.")
            else:
                note("Docker MySQL is not stopped by this launcher. To stop it if running: docker compose stop mysql")


if __name__ == "__main__":
    # Script path execution must import backend.api_service.app from the checkout, regardless of cwd.
    sys.path.insert(0, str(ROOT))

    def request_stop(signum, frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, request_stop)
    if hasattr(signal, "SIGBREAK"):
        signal.signal(signal.SIGBREAK, request_stop)
    raise SystemExit(main())
