# Backend API setup — macOS, Windows and WSL

Run setup from **`team2_merlion_express/`**, the folder containing `backend/`, `frontend/` and `docker-compose.yml`. Each teammate creates a local `.venv`; do not commit/copy it between computers or share one environment between native Windows and WSL.

## 1. What this starts

| Service | Local address | Current behaviour |
|---|---|---|
| MySQL | `127.0.0.1:3306` | Reuse an existing local server; otherwise start the MySQL 8 Compose service with its durable volume. First Docker startup may download the image. |
| Python API | `http://127.0.0.1:8000` | Complaint submission, follow-up/candidate selection, SQLite recovery, `/api/health`, `/docs` and `/openapi.json`. B's live structured provider remains pending. |
| React/Vite | `http://127.0.0.1:5173` | Existing complaint, weekly and explainer screens, using synthetic mock data by default. |

`/api/health` reports `status: degraded`: sessions are implemented, while triage remains unavailable until B's structured provider is connected. Weekly reporting and semantic retrieval remain unavailable. Ordinary order submissions return `503 DEPENDENCY_UNAVAILABLE` with the default provider; no records are fabricated. SQLite persists sanitised workflow state under ignored `output/api/sessions.sqlite3` (override with `CAPSTONE_SESSION_DB`). Requests without an order reference can clarify, and prohibited requests can refuse, without a database/model call.

## 2. Install prerequisites once

- Python **3.11 or newer**; Python 3.13 is the recommended common interpreter for this project. The existing standard-library ingestion modules also work independently on their documented Python versions.
- Node.js compatible with Vite: **20.19+ on the 20.x line, or 22.12+**. Prefer a supported newer release. Node and npm must be available in the terminal running the scripts.
- Either an existing local MySQL server on `127.0.0.1:3306`, or Docker Desktop with Compose v2. Docker is not required when local MySQL responds. For the Docker fallback in WSL, enable distribution integration.
- Source package for real-data work, obtained privately. It is not required to inspect the synthetic frontend or bootstrap health endpoint.

Use separate native-Windows and WSL checkouts/environments. In WSL install Linux Python/Node and run the Bash launcher; native Windows uses Windows Python/Node and the PowerShell launcher.

## 3. macOS — Terminal / zsh / Bash

Create the environment **only if it does not already exist**:

```bash
python3 --version
python3 -m venv .venv
```

Check that `python3` is 3.11+ before creating it; select your installed `python3.13` explicitly if necessary. Reuse the project's existing compatible `.venv`.

```bash
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r backend/api_service/requirements.txt
python -m pip check
```

Install frontend dependencies once:

```bash
cd frontend
npm ci
cd ..
```

The repository includes a package lock; use `npm ci` for its recorded frontend dependency versions. Do not install Python packages globally or use `sudo pip`.

## 4. Windows — PowerShell

Create a Windows environment **only if it does not already exist**, using an installed 3.11+ interpreter:

```powershell
py -3.13 --version
py -3.13 -m venv .venv
```

The launcher invokes the environment's interpreter directly, so activation is not required:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r backend\api_service\requirements.txt
.\.venv\Scripts\python.exe -m pip check
Push-Location frontend
npm.cmd ci
Pop-Location
```

If 3.13 is not installed, select your installed compatible version with the Python launcher. If `py` is unavailable but `python --version` is compatible, use `python -m venv .venv`.

If PowerShell blocks the local startup script, use a process-only policy for this terminal, subject to your organisation's policy:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\start.ps1
```

Alternatively run the same launcher directly without changing execution policy:

```powershell
.\.venv\Scripts\python.exe scripts\start_services.py
```

Optional activation for other work: `.\.venv\Scripts\Activate.ps1`.

## 5. Windows — WSL Bash

Use your WSL checkout and Linux tools, not `.venv/Scripts/python.exe` from native Windows. After installing Linux Python 3.11+ and Node/npm:

```bash
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r backend/api_service/requirements.txt
python -m pip check
cd frontend
npm ci
cd ..
# Only when using the Docker fallback:
docker info
docker compose version
```

If environment creation reports that `venv`/`ensurepip` is missing, install the matching Python venv package for your Linux distribution, then retry. When using the Docker fallback, Docker Desktop → Settings → Resources → WSL Integration must include the distribution. Do not mix Windows Node binaries with Linux `node_modules`.

## 6. Configure local data separately

For later model-backed work, copy the template to `.env` **only if `.env` is absent**, then edit it locally with the authorised team key. Do not overwrite an existing configured file or put credentials in `VITE_` variables.

```bash
# macOS / WSL
if [ ! -f .env ]; then cp .env.example .env; fi
```

```powershell
# PowerShell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

The bootstrap needs no model key and startup never prints/probes one. Future model-backed routes and the existing extraction modules use server-side configuration.

For real-data work follow [database creation/seeding](../../database/createdb_seed_sql_data.md) and [unstructured ingestion](../unstructured/README.md). SQL seeding is a separate deliberate step because re-importing the dump replaces source tables. Docker-managed startup checks whether the three source tables exist; an existing local server is probed without authentication, so verify its schema separately. Neither check certifies row counts, case migrations or evidence correctness.

When seeding from PowerShell, use the existing guide's **Command Prompt** import command or open CMD explicitly; do not paste Bash `< file.sql` redirection into PowerShell. Paid image extraction is also separate and is never invoked by startup.

### Database selection

Default `--mysql-mode auto` recognises a MySQL greeting on `127.0.0.1:3306` and reuses that server without Docker, credentials or MySQL command-line tools. This confirms server availability only; verify credentials, schema and row counts separately using the database setup guide. The server must be reachable from the environment running the launcher, including WSL when applicable.

If no local server is found and port 3306 is free, startup checks Docker/Compose and starts the existing MySQL service. An occupied port that does not respond as MySQL blocks startup instead of launching another database over it. `--mysql-mode local` requires the existing server and never falls back to Docker; `--mysql-mode docker` explicitly chooses Compose.

## 7. Check and start

```bash
# macOS / WSL
bash scripts/start.sh
```

```powershell
# Windows PowerShell
.\scripts\start.ps1
```

Example output:

```text
[x] Project virtual environment selected
[x] fastapi: importable
[x] pydantic: importable
[x] uvicorn: importable
[x] Docker Desktop/daemon running
[x] API port 8000 available
[!] Frontend will display synthetic in-browser demo data.
[x] MySQL responding
[x] API process responding: http://127.0.0.1:8000/docs
[!] API bootstrap only: complaint, weekly and session capabilities are not all ready.
[x] Frontend responding: http://127.0.0.1:5173 (demo data)
```

`[x]` means that check passed; `[ ]` means a blocking check failed; `[!]` is an explicit limitation or preparation task. Missing model configuration/evidence or unseeded source tables are limitations for the bootstrap/demo, not automatic triggers to install/import/extract data.

Every startup checks the selected virtual environment, FastAPI/Pydantic/Uvicorn imports, `pip check`, Node PATH/version, frontend dependencies, ports and local MySQL availability. Docker CLI/daemon/Compose checks run only for the Docker fallback or explicit Docker mode. Missing prerequisites print the corresponding setup action. The script stops before starting anything when preflight fails. It rejects occupied API/frontend ports instead of reusing an unknown process or letting Vite silently choose a new port. If startup later fails, it cleans up the API/frontend processes it created; any started MySQL service remains running with its volume preserved.

### Options — same arguments in all terminals

| Option | Behaviour |
|---|---|
| `--mysql-mode auto` | Default: reuse existing MySQL on port 3306; otherwise check/start Docker MySQL. |
| `--mysql-mode local` | Require a responding local MySQL server; Docker is never checked or started. |
| `--mysql-mode docker` | Explicitly use the configured Docker Compose MySQL service. |
| `--skip-mysql` | Skip Docker/database management, useful for bootstrap API/UI work or an operator-managed database. Does not imply that an external database was validated. |
| `--no-frontend` | Skip Node/Vite checks and frontend startup. |
| `--api-port 8001` | Change the API port and the frontend's launch-time API base URL. |
| `--frontend-port 5174` | Change the frontend port and the bootstrap's allowed browser origins. |
| `--reload` | Development-only Uvicorn auto-reload for backend Python files. |
| `--frontend-mode demo` | Default: force the existing synthetic mock UI; this is not the future per-feature demo/live behaviour. |
| `--frontend-mode live` | Configure real API calls only when health reports triage, weekly and sessions ready. The current bootstrap blocks this mode and cleans up its API process. |

Example, with a separately managed database:

```bash
bash scripts/start.sh --skip-mysql --api-port 8001 --frontend-port 5174 --reload
```

To run just the API manually from the project root:

```bash
# macOS / WSL
.venv/bin/python -m uvicorn backend.api_service.app:app --host 127.0.0.1 --port 8000
```

```powershell
# PowerShell
.\.venv\Scripts\python.exe -m uvicorn backend.api_service.app:app --host 127.0.0.1 --port 8000
```

## 8. Stop, logs and troubleshooting

Keep the startup terminal open; press **Ctrl+C** to stop its API/frontend. Logs are under `output/startup/<timestamp>-<pid>/api.log` and `frontend.log`, already ignored by Git. Do not publish logs containing client data once domain services are added.

MySQL deliberately remains available. Stop it without deleting data with `docker compose stop mysql`; the next startup reuses its volume. Do not use volume-deleting commands as a routine restart.

| Problem | Action |
|---|---|
| Missing Python modules | Use the checkout's `.venv` interpreter and install `backend/api_service/requirements.txt`; verify with `python -m pip check`. |
| Missing Node/Vite | Load your Node environment, verify `node --version`, then run `npm ci` inside `frontend/` in the same operating system. |
| Docker check fails | Docker is needed only when no local MySQL is detected or Docker mode was chosen. Start local MySQL and rerun, or start Docker Desktop/check WSL integration. |
| Port 3306 occupied | Auto mode reuses a responding MySQL server. If the greeting cannot be recognised, investigate that listener; startup does not kill it or start Docker over it. |
| API/frontend port occupied | Stop the known prior service yourself or choose the port options above. |
| API health works but triage returns 503 | Connect B's structured provider through `create_app`; the default provider explicitly reports unavailable. `/docs` exposes the implemented complaint/session routes. Weekly routes still return 404. |
| MySQL source-table warning | Follow the separate import guide and verify the counts. Case tables/views still require their planned migrations. |
| Missing evidence warning | Prepare/distribute the approved local outputs using the ingestion guide; health/mock startup does not create evidence. |
| Script blocked in PowerShell | Use the process-scoped setting above or invoke `start_services.py` directly with the environment's Python. |
| API process exits/readiness times out | Inspect the run's log files; a child failure shuts down the other launched app process. |

## 9. Development checks

The runtime requirements pin FastAPI 0.163.1, Pydantic 2.14.3 and Uvicorn 0.54.0, verified together in an isolated Python 3.13 environment on macOS. Transitive dependencies are resolved by pip; these files are not a complete platform lockfile.

Install the optional testing dependencies into the same environment:

```bash
python -m pip install -r backend/api_service/requirements-dev.txt
python -m unittest discover -s backend/api_service/tests -v
python -m unittest discover -s scripts/tests -v
python -m evals.complaint_api_starter
```

In PowerShell use `.\.venv\Scripts\python.exe` in place of `python` if the environment is not activated. Existing ingestion checks remain available separately: `python -m unittest discover -s backend/unstructured/tests -t .`.

The complaint/session increment implements HTTP-01–03 and health from the [API catalog](../../docs/02-Design/api-catalog_v0.9.1.md). Live structured lookup, full rate/policy assessment, answer-model orchestration and weekly reporting remain pending. Existing extraction behaviour is unchanged. See the [implementation handoff](../../docs/03-Handoffs/John_2026-11-17-complaint-session-api.md) for the provider contract, decisions and actual verification results.

Validation on macOS: focused API/launcher tests and isolated real Uvicorn/Vite startup, prerequisite checks, occupied-port rejection, Ctrl+C cleanup, live-mode blocking and development-reload cleanup passed. Native PowerShell/WSL execution and a real Docker/MySQL startup were not run here; database start/probe logic was checked with controlled test doubles.

References: [FastAPI server setup](https://fastapi.tiangolo.com/deployment/manually/), [Vite prerequisites](https://vite.dev/guide/), [Vite CLI/strict port](https://vite.dev/guide/cli.html).
