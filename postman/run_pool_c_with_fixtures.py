"""Run Pool C once with isolated per-case SQLite resets and automatic restoration."""

from __future__ import annotations

import argparse
import hmac
import json
import secrets
import sqlite3
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from pool_c_fixtures import (
    COLLECTION_PATH, inspect_case, reset_case, restore, reviewed_ids,
    runtime_variables, snapshot, validate_schema,
)


ROOT = Path(__file__).resolve().parents[1]


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
    raise RuntimeError(f"SUT is not reachable at {url}; start it before running Pool C ({last_error})")


class FixtureServer(ThreadingHTTPServer):
    database_path: Path
    control_key: str
    reset_ids: list[str]


class FixtureHandler(BaseHTTPRequestHandler):
    server: FixtureServer

    def _authorized(self) -> bool:
        supplied = self.headers.get("X-Fixture-Control-Key", "")
        if hmac.compare_digest(supplied, self.server.control_key):
            return True
        self.send_error(403, "Invalid fixture-control key")
        return False

    def _test_id(self, prefix: str) -> str:
        return self.path[len(prefix):].split("?", 1)[0] if self.path.startswith(prefix) else ""

    def do_POST(self) -> None:
        if not self._authorized():
            return
        test_id = self._test_id("/reset/")
        if test_id not in reviewed_ids():
            self.send_error(404, "Unknown reviewed Test ID")
            return
        try:
            connection = sqlite3.connect(self.server.database_path, timeout=10)
            try:
                values = reset_case(connection, test_id)
            finally:
                connection.close()
            self.server.reset_ids.append(test_id)
            payload = json.dumps(values).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("X-Pool-C-Fixture", test_id)
            self.end_headers()
            self.wfile.write(payload)
        except Exception as error:
            self.send_error(500, str(error))

    def do_GET(self) -> None:
        if not self._authorized():
            return
        test_id = self._test_id("/state/")
        if test_id not in reviewed_ids():
            self.send_error(404, "Unknown reviewed Test ID")
            return
        try:
            connection = sqlite3.connect(self.server.database_path, timeout=10)
            try:
                state = inspect_case(connection, test_id)
            finally:
                connection.close()
            payload = json.dumps(state).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        except Exception as error:
            self.send_error(500, str(error))

    def log_message(self, *_: object) -> None:
        return


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sut-dir", type=Path, required=True, help="Path to the eShop SUT repository")
    parser.add_argument("--base-url", default="http://127.0.0.1:3000")
    parser.add_argument("--student-id", default="23127261")
    parser.add_argument("--newman-command", nargs="+", required=True, help="For example: npx.cmd newman")
    parser.add_argument("--collection", type=Path, default=COLLECTION_PATH)
    parser.add_argument("--newman-arg", action="append", default=[])
    args = parser.parse_args()

    database_path = args.sut_dir.resolve() / "backend" / "database.sqlite"
    collection_path = args.collection.resolve()
    if not database_path.is_file():
        raise RuntimeError(f"SUT SQLite database does not exist: {database_path}")
    if not collection_path.is_file():
        raise RuntimeError(f"Pool C collection does not exist: {collection_path}")
    require_running_sut(args.base_url)

    connection = sqlite3.connect(database_path, timeout=10)
    try:
        validate_schema(connection)
        saved = snapshot(connection)
    finally:
        connection.close()

    control_key = secrets.token_urlsafe(32)
    server = FixtureServer(("127.0.0.1", 0), FixtureHandler)
    server.database_path = database_path
    server.control_key = control_key
    server.reset_ids = []
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    variables = {
        "baseUrl": args.base_url,
        "studentId": args.student_id,
        "fixtureControlUrl": f"http://127.0.0.1:{server.server_address[1]}",
        "fixtureControlKey": control_key,
        **runtime_variables(),
    }
    command = [*args.newman_command, "run", str(collection_path)]
    for key, value in variables.items():
        command.extend(["--env-var", f"{key}={value}"])
    command.extend(args.newman_arg)

    result_code = 1
    try:
        completed = subprocess.run(command, cwd=ROOT, check=False)
        result_code = completed.returncode
        if result_code == 0 and server.reset_ids != reviewed_ids():
            raise RuntimeError(
                f"Newman completed but fixture reset order was not exact: {server.reset_ids!r}"
            )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        connection = sqlite3.connect(database_path, timeout=10)
        try:
            restore(connection, saved)
        finally:
            connection.close()
        print(f"RESTORED: pre-run orders and sequence in {database_path}")
    raise SystemExit(result_code)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"POOL C RUNNER ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
