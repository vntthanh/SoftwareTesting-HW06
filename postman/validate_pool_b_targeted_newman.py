import json
import re
import sqlite3
import subprocess
import sys
import tempfile
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "postman"))

from pool_b_fixtures import COLLECTION_PATH, restore, runtime_variables, snapshot, verify_case
from run_pool_b_with_fixtures import FixtureHandler, FixtureServer
from validate_pool_b_runtime import GMT7, create_schema, seed_snapshot_sentinel


VALIDATION_PATH = ROOT / "postman" / "pool-b-runtime-validation.json"


class SutMock(ThreadingHTTPServer):
    body = {}
    captured = []


class SutHandler(BaseHTTPRequestHandler):
    server: SutMock

    def do_GET(self):
        self.respond()

    def do_POST(self):
        self.rfile.read(int(self.headers.get("Content-Length", "0")))
        self.respond()

    def respond(self):
        self.server.captured.append(dict(self.headers))
        encoded = json.dumps(self.server.body).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, *_):
        return


def response_for(item):
    script = "\n".join(line for event in item.get("event", []) for line in event["script"]["exec"])
    discount = re.search(r"data\.discount_amount\)\.to\.eql\(([-\d.]+)\)", script)
    final = re.search(r"data\.final_amount\)\.to\.eql\(([-\d.]+)\)", script)
    return ({"discount_amount": float(discount.group(1)), "final_amount": float(final.group(1))}
            if discount and final else {})


def main():
    collection = json.loads(COLLECTION_PATH.read_text(encoding="utf-8"))
    items = {item["name"][:7]: item for folder in collection["item"] for item in folder["item"]}
    selected = [
        "API-001", "API-040", "API-041", "API-052", "API-053",
        "API-063", "API-068", "API-069", "API-072",
    ]
    with tempfile.TemporaryDirectory(prefix="pool-b-newman-") as temp_dir:
        database_path = Path(temp_dir) / "database.sqlite"
        connection = sqlite3.connect(database_path)
        create_schema(connection)
        seed_snapshot_sentinel(connection)
        saved = snapshot(connection)
        connection.close()

        control_key = "targeted-validation-key"
        fixture = FixtureServer(("127.0.0.1", 0), FixtureHandler)
        fixture.database_path = database_path
        fixture.control_key = control_key
        fixture.reset_ids = []
        fixture_thread = threading.Thread(target=fixture.serve_forever, daemon=True)
        fixture_thread.start()

        sut = SutMock(("127.0.0.1", 0), SutHandler)
        sut_thread = threading.Thread(target=sut.serve_forever, daemon=True)
        sut_thread.start()
        try:
            variables = {
                "baseUrl": f"http://127.0.0.1:{sut.server_address[1]}",
                "studentId": "23127261",
                "fixtureControlUrl": f"http://127.0.0.1:{fixture.server_address[1]}",
                "fixtureControlKey": control_key,
                **runtime_variables(),
            }
            for test_id in selected:
                item = items[test_id]
                sut.body = response_for(item)
                sut.captured = []
                command = ["npx.cmd", "newman", "run", str(COLLECTION_PATH), "--folder", item["name"], "--reporters", "cli", "--silent"]
                for key, value in variables.items():
                    command += ["--env-var", f"{key}={value}"]
                result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
                if result.returncode:
                    raise RuntimeError(f"Targeted Newman {test_id} failed:\n{result.stdout}\n{result.stderr}")
                if fixture.reset_ids[-1:] != [test_id] or len(sut.captured) != 1:
                    raise RuntimeError(f"{test_id}: fixture reset or SUT request was not observed exactly once")
                if sut.captured[0].get("X-Student-Id") != "23127261":
                    raise RuntimeError(f"{test_id}: X-Student-Id was not delivered")
                connection = sqlite3.connect(database_path)
                try:
                    verify_case(connection, test_id)
                finally:
                    connection.close()
            if fixture.reset_ids != selected:
                raise RuntimeError(f"Unexpected targeted reset sequence: {fixture.reset_ids}")
        finally:
            fixture.shutdown(); fixture.server_close(); fixture_thread.join(timeout=5)
            sut.shutdown(); sut.server_close(); sut_thread.join(timeout=5)
        connection = sqlite3.connect(database_path)
        try:
            restore(connection, saved)
            if snapshot(connection) != saved:
                raise RuntimeError("Targeted Newman validation did not restore the original state")
        finally:
            connection.close()
    version = subprocess.run(
        ["npx.cmd", "newman", "--version"], cwd=ROOT, capture_output=True,
        text=True, encoding="utf-8", errors="replace", timeout=30,
    ).stdout.strip()
    validation = json.loads(VALIDATION_PATH.read_text(encoding="utf-8"))
    validation["targetedNewmanCompatibility"] = {
        "status": "PASS",
        "validatedAt": datetime.now(GMT7).strftime("%Y-%m-%d %H:%M:%S GMT+7"),
        "newmanVersion": version,
        "selectedTestIds": selected,
        "requestsExecutedAgainstLocalMock": len(selected),
        "realSutStartedOrContacted": False,
        "fullNewmanSuiteExecuted": False,
    }
    VALIDATION_PATH.write_text(json.dumps(validation, indent=2) + "\n", encoding="utf-8")
    print("TARGETED NEWMAN PASS: 9 representative requests; fixture reset hook, conflicting counts, dates, JWT variants, robustness assertions, student header, and restoration verified")


if __name__ == "__main__":
    main()
