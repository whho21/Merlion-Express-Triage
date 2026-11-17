"""Live smoke check for the TOOL-05 MySQL provider (read-only).

Run from the repo root after importing the instructor dump:

    python -m scripts.check_sql_provider                 # probes a sample order
    CAPSTONE_DB_PASSWORD=... python -m scripts.check_sql_provider 12345

Prints connection health, table counts and one provider resolve round trip.
Never prints customer names, phones or addresses.
"""
import sys

from backend.api_service.sql_provider import MySqlProvider, SqlProviderError, _config


def main(argv=None):
    number = None
    if argv:
        number = int(argv[0])
    try:
        provider = MySqlProvider()
        if number is None:
            connection = provider._connection_factory()
            cursor = connection.cursor()
            cursor.execute('SELECT order_id FROM orders ORDER BY order_id LIMIT 1')
            row = cursor.fetchone()
            cursor.close()
            connection.close()
            number = int(row[0])
        result = provider.resolve(f'order V1-{number}')
    except (SqlProviderError, ValueError, IndexError) as exc:
        print(f'FAIL: {exc}')
        print('Check the dump is imported (database/createdb_seed_sql_data.md) and credentials:')
        print({k: v for k, v in _config().items() if k != 'password'})
        return 1
    print(f"status={result['status']} source_version={result['source_version']} "
          f"received_date={result['received_date']} candidates={len(result['candidates'])}")
    for candidate in result['candidates']:
        print(f"  {candidate['system_version']}:{candidate['order_id']} "
              f"created={candidate['created']} status={candidate['status']}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
