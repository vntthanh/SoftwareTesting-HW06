"""Apply and verify one deterministic Pool B runtime state in the initialized SUT DB."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from pool_b_fixtures import reset_case, reviewed_ids, runtime_variables, validate_schema


def require_running_sut(url: str, attempts: int = 20) -> None:
    last_error = None
    for _ in range(attempts):
        try:
            with urllib.request.urlopen(url, timeout=1):
                return
        except urllib.error.HTTPError:
            return
        except (urllib.error.URLError, TimeoutError) as error:
            last_error = error
            time.sleep(0.25)
    raise RuntimeError(f"SUT is not reachable at {url}; start it before seeding ({last_error})")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sut-dir", type=Path, required=True, help="Path to the eShop SUT repository")
    parser.add_argument("--test-id", choices=reviewed_ids(), default="API-001")
    parser.add_argument("--base-url", default="http://127.0.0.1:3000")
    parser.add_argument(
        "--print-runtime-variables",
        action="store_true",
        help="Print the deterministic non-production JWT variable map as JSON",
    )
    args = parser.parse_args()
    database_path = args.sut_dir.resolve() / "backend" / "database.sqlite"
    if not database_path.is_file():
        raise RuntimeError(f"SUT SQLite database does not exist: {database_path}")
    require_running_sut(args.base_url)
    connection = sqlite3.connect(database_path, timeout=10)
    try:
        validate_schema(connection)
        reset_case(connection, args.test_id)
    finally:
        connection.close()
    print(f"READY: deterministic Pool B state for {args.test_id} in {database_path}")
    if args.print_runtime_variables:
        print(json.dumps(runtime_variables(), indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"FIXTURE ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
