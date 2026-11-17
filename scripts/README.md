# Service scripts

Run commands from `team2_merlion_express/`. First follow the [backend setup guide](../backend/api_service/backend_API_setup.md) to install Python/frontend dependencies and prepare local MySQL or Docker.

| Script | Usage | Description |
|---|---|---|
| [start.sh](start.sh) | `scripts/start.sh` | macOS/WSL launcher using the project's `.venv`. Checks prerequisites, then reuses local MySQL or starts Docker MySQL, followed by the API and React/Vite. |
| [start.ps1](start.ps1) | `.\scripts\start.ps1` | Windows PowerShell launcher using `.venv\Scripts\python.exe`. Runs the same checks and services as the Bash launcher. |
| [start_services.py](start_services.py) | `python scripts/start_services.py` | Shared service checker/supervisor; use the project environment's Python. Reports `[x]` successes, `[ ]` failures and `[!]` limitations, waits for readiness and stops its API/frontend on Ctrl+C. |
| [tests/test_start_services.py](tests/test_start_services.py) | `python -m unittest discover -s scripts/tests -v` | Checks startup failure handling, mandatory preflight, database probes, live-mode gating and owned-process cleanup. Requires the [development dependencies](../backend/api_service/requirements-dev.txt). |

Every startup checks these prerequisites before starting services; failures show a setup command or corrective action.

| Check | When it fails |
|---|---|
| Virtual environment, FastAPI/Pydantic/Uvicorn imports, `pip check` | Install/repair packages using the project Python and `backend/api_service/requirements.txt`. |
| Existing MySQL on `127.0.0.1:3306` | Reuse a responding MySQL server without Docker or MySQL client tools; schema/authentication validation stays in the database setup guide. |
| Docker CLI, Docker Desktop/daemon and Compose v2 | Required only when no existing MySQL is detected, or Docker mode is selected. Start Docker Desktop and enable WSL integration when needed. |
| Node on PATH and Vite-compatible version | Load the Node version manager or select a supported Node version in this terminal. |
| Frontend Vite dependencies | Run `npm --prefix frontend ci`; use `npm.cmd` in PowerShell. |
| API/frontend ports | Stop the known conflicting service or choose the launcher port options. |

All launchers accept the same options:

| Option | Purpose |
|---|---|
| `--mysql-mode auto` | Default: use existing MySQL on port 3306; otherwise start Docker MySQL. |
| `--mysql-mode local` | Require an already-running local MySQL; never use Docker. |
| `--mysql-mode docker` | Explicitly use Docker Compose MySQL. |
| `--skip-mysql` | Leave database management to the operator. |
| `--no-frontend` | Check/start the API and optional MySQL only. |
| `--api-port 8001` | Change API port; default `8000`. |
| `--frontend-port 5174` | Change frontend port; default `5173`. |
| `--reload` | Enable API development reload. |
| `--frontend-mode demo` | Default: synthetic frontend data. |
| `--frontend-mode live` | Require implemented triage, weekly and session capabilities; currently blocked by the API bootstrap. |
| `--help` | Show all options. |

Keep the startup terminal open. Ctrl+C stops the launched API/frontend; Existing MySQL is never stopped; Docker MySQL and its volume also remain available. Logs are under ignored `output/startup/`; startup never installs packages, imports SQL, runs paid extraction or kills unrelated services.
