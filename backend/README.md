# Backend — Merlion Express

[Mac, Windows and WSL API setup](api_service/backend_API_setup.md) · [Existing ingestion tools](unstructured/README.md)

The API implements complaint submission, follow-up/candidate selection, SQLite session recovery and `GET /api/health`, with interactive documentation at `/docs`. Live order lookup still requires B's structured provider; ordinary order requests return a safe `503` until it is connected. Missing order references can be clarified and prohibited requests refused without that provider. Weekly reporting, automated resolution assessment and semantic retrieval remain pending. The frontend defaults to its existing synthetic demo mode.

See the [complaint/session implementation handoff](../docs/03-Handoffs/John_2026-11-17-complaint-session-api.md) for provider integration, contract decisions and verified checks. No synthetic provider is enabled by default.

## Environment setup

Run from the project root, `team2_merlion_express/`. Use separate virtual environments/checkouts for macOS, WSL and native Windows; do not share a `.venv` between operating systems.

### macOS / WSL — Bash or zsh

Create `.venv` only if it is missing, then activate it and install/repair API packages:

```bash
python3.13 -m venv .venv
source .venv/bin/activate
.venv/bin/python -m pip install -r backend/api_service/requirements.txt
.venv/bin/python -m pip check
.venv/bin/python -m pip --version
```

Use an installed Python 3.11+ if 3.13 is unavailable. On macOS, your installed 3.13 interpreter can also be invoked as `/Library/Frameworks/Python.framework/Versions/3.13/bin/python3.13`; in WSL use Linux Python and install its matching venv package if needed.

If the project moved and the environment has stale paths, stop project services and recreate it first:

```bash
if command -v deactivate >/dev/null 2>&1; then deactivate; fi
mv .venv "/tmp/merlion-venv-backup-$(date +%Y%m%d-%H%M%S)"
python3.13 -m venv .venv
source .venv/bin/activate
.venv/bin/python -m pip install -r backend/api_service/requirements.txt
.venv/bin/python -m pip check
.venv/bin/python -m pip --version
```

### Windows — PowerShell

Create `.venv` only if it is missing, then install/repair packages using its interpreter. Activation is optional for these commands:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\api_service\requirements.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pip --version
```

Select your installed Python 3.11+ with `py` if 3.13 is unavailable. Optional activation: `.\.venv\Scripts\Activate.ps1`; if execution policy blocks it, the interpreter commands above still work without activation.

To recreate an environment after moving the project, stop project services first:

```powershell
if (Get-Command deactivate -ErrorAction SilentlyContinue) { deactivate }
$venvBackup = Join-Path $env:TEMP ("merlion-venv-backup-" + (Get-Date -Format "yyyyMMdd-HHmmss"))
Move-Item -LiteralPath .venv -Destination $venvBackup
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\api_service\requirements.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pip --version
```

Keep the backup until the new environment works. These steps leave the project's `.env` file unchanged; see the [full setup guide](api_service/backend_API_setup.md) for frontend/database prerequisites and troubleshooting.

## Start services

| Terminal | Check prerequisites, then start services |
|---|---|
| macOS / WSL Bash | `bash scripts/start.sh` |
| Windows PowerShell | `.\scripts\start.ps1` |

The launcher checks Python/dependencies, Node/Vite, ports and MySQL availability. It reuses responding local MySQL without requiring Docker, or checks Docker/Compose and starts MySQL when needed, then starts the API and frontend and waits for HTTP readiness. Keep the terminal open. Ctrl+C stops the launched app processes and leaves the selected MySQL server running.

Startup never installs dependencies, imports/overwrites SQL, runs paid extraction or kills unrelated processes. Checks always run before any service starts. Logs go to ignored `output/startup/`.

Use `--mysql-mode local` to require local MySQL, `--mysql-mode docker` to force Docker, or `--skip-mysql` to manage the database separately. Use `--no-frontend` for backend-only startup, `--api-port 8001` / `--frontend-port 5174` for port conflicts, or `--reload` for API development. `--frontend-mode live` requires triage, weekly and session capabilities together; it remains blocked while weekly reporting and structured lookup are unavailable. Direct API development is available independently.

Dependencies: [runtime](api_service/requirements.txt), [development/testing](api_service/requirements-dev.txt). Scripts resolve the checkout from their own location and use its `.venv`; activation is optional for the launchers.

## Simple structure for API catalog implementation

Use three functional groups. Keep request handling and application logic together in `api_service/`; separate folders for routes, schemas, repositories and core helpers are unnecessary at this scale.

```text
backend/
├── README.md
├── api_service/
│   ├── app.py                    # FastAPI complaint/session/health routes
│   ├── models.py                 # Validated request and response contracts
│   ├── service.py                # Structured-provider boundary and bounded calls
│   ├── store.py                  # SQLite sessions and concurrent-write checks
│   ├── evidence.py               # Cached POD/policy adapters and source checks
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── backend_API_setup.md
│   └── tests/
├── rag_service/                   # Planned: index.py, retrieve.py, answer.py
└── unstructured/                  # Existing ingestion/extraction tools
    ├── emails.py
    ├── evals.py
    ├── extract_images.py
    ├── ingest.py
    ├── llm.py
    ├── masking.py
    ├── paths.py
    ├── pod.py
    ├── policy.py
    ├── ratecard.py
    ├── README.md
    ├── search.py
    ├── sqlref.py
    ├── tests
    │   ├── fixtures.py
    │   ├── test_emails.py
    │   ├── test_images.py
    │   ├── test_llm_and_cache.py
    │   ├── test_masking.py
    │   ├── test_policy_and_ingest.py
    │   └── test_search_and_evals.py    
    └── xlsx.py
```

`api_service/` is the single HTTP application; `rag_service/` will contain imported Python modules, not another web server. Use underscores because these folders are Python packages. Create `rag_service/` when its implementation starts; retain `unstructured/` and its current contracts.

| Group | API catalog responsibility |
|---|---|
| `api_service/` | All six HTTP endpoints; request/response models, order/SQL/GPS tools, full rate/policy checks, weekly reports, guards and SQLite sessions. Add focused files such as `models.py`, `data.py`, `weekly.py`, `sessions.py` or `guardrails.py` when implemented. |
| `rag_service/` — planned | Masked chunk/index construction, exact/keyword/vector retrieval orchestration, grounded answer generation and citation assembly (TOOL-11/13). Reuse the existing evidence tools. |
| `unstructured/` — existing | Email/guide parsing, cached image extraction and file-backed email/policy/POD/base-rate tools (TOOL-01–04). |

Offline SQL/case/GPS preparation can start in a separate `api_service/prepare.py` command module; HTTP requests must not run ingestion or cleaning. MySQL DDL stays in `database/`, runtime data stays under ignored `data/` and `output/`, and shared startup stays in [`scripts/`](../scripts/README.md).

The entry point is `uvicorn backend.api_service.app:app`. The three complaint/session routes and health exist; weekly routes and `rag_service/` remain planned. SQLite defaults to ignored `output/api/sessions.sqlite3`; `CAPSTONE_SESSION_DB` overrides the path. Recovery reads saved state without model/tool calls. See the [API catalog](../docs/02-Design/api-catalog_v0.9.1.md) for contracts.

After installing the development dependencies, run `python -m unittest discover -s backend/api_service/tests -v` and `python -m evals.complaint_api_starter`. The starter explicitly injects synthetic data; production startup never uses it. No API request runs ingestion or paid extraction.
