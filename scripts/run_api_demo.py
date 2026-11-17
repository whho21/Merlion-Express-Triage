"""Local demo launcher: run the API with an injected provider.

Choose the provider explicitly; never run production through this module.

    python -m scripts.run_api_demo --provider sql        # live MySQL (TOOL-05)
    python -m scripts.run_api_demo --provider synthetic  # evals fixture (no DB)
    CAPSTONE_API_PORT=8001 CAPSTONE_SESSION_DB=/tmp/demo.sqlite3 python -m scripts.run_api_demo

If the SQL provider cannot connect, the launcher says so and falls back to the
synthetic fixture with a Demo Data warning; it never pretends to be live.
Production never imports this module (CS-07, complaint/session handoff).
"""
import argparse
import os

import uvicorn

from backend.api_service.app import create_app
from backend.api_service.sql_provider import MySqlProvider, SqlProviderError
from evals.complaint_api_fixture import SyntheticProvider


def build_app(provider_name):
    if provider_name == 'synthetic':
        print('[ ] Demo Data: synthetic provider injected (fixture orders).', flush=True)
        return create_app(provider=SyntheticProvider())
    provider = MySqlProvider()
    try:
        probe = provider.resolve('')
        print(f"[✅] Live SQL provider: source_version={probe['source_version']} "
              f"received_date={probe['received_date']}.", flush=True)
        return create_app(provider=provider)
    except SqlProviderError as exc:
        print(f"[⚠️ ] SQL provider unavailable ({exc}). Falling back to the "
              "synthetic fixture — label output as Demo Data.", flush=True)
        return create_app(provider=SyntheticProvider())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--provider', choices=('sql', 'synthetic'), default='sql')
    args = parser.parse_args()
    app = build_app(args.provider)
    uvicorn.run(app, host='127.0.0.1', port=int(os.environ.get('CAPSTONE_API_PORT', '8000')))


if __name__ == '__main__':
    main()
