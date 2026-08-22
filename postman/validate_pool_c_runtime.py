"""Validate Pool C fixtures, traceability, collection wiring, schema, and Newman compatibility."""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import hmac
import json
import sqlite3
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import jsonschema

from pool_c_fixtures import (
    COLLECTION_PATH, CSV_PATH, SECRET_KEY, fixture_summary, inspect_case, reset_case,
    restore, reviewed_ids, runtime_variables, snapshot, validate_schema,
)


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "postman" / "postman-v2.1.0-schema.json"
GMT7 = timezone(timedelta(hours=7))
FLOW_COUNTS = {"API-080": 2, "API-081": 2, "API-082": 2, "API-083": 2, "API-084": 4, "API-085": 2}


def create_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            total_amount INTEGER,
            status TEXT DEFAULT 'pending',
            shipping_address TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
    )


def seed_snapshot_sentinel(connection: sqlite3.Connection) -> None:
    connection.execute(
        "INSERT INTO orders VALUES (42,9,88,'pending','Original order','2020-01-01 00:00:00')"
    )
    connection.commit()


def decode_part(value: str) -> dict[str, Any]:
    return json.loads(base64.urlsafe_b64decode(value + "=" * (-len(value) % 4)))


def valid_signature(token: str, secret: str) -> bool:
    parts = token.split(".")
    if len(parts) != 3:
        return False
    actual = base64.urlsafe_b64decode(parts[2] + "=" * (-len(parts[2]) % 4))
    expected = hmac.new(secret.encode(), f"{parts[0]}.{parts[1]}".encode(), hashlib.sha256).digest()
    return hmac.compare_digest(actual, expected)


def validate_jwts() -> None:
    variables = runtime_variables()
    admin = variables["adminToken"]
    non_admin = variables["nonAdminToken"]
    if not valid_signature(admin, SECRET_KEY) or decode_part(admin.split(".")[1])["role"] != "admin":
        raise RuntimeError("adminToken is not a valid deterministic Admin JWT")
    if not valid_signature(non_admin, SECRET_KEY) or decode_part(non_admin.split(".")[1])["role"] == "admin":
        raise RuntimeError("nonAdminToken is not a valid deterministic non-Admin JWT")
    if variables["malformedToken"].count(".") == 2:
        raise RuntimeError("malformedToken must remain malformed")
    if valid_signature(variables["forgedToken"], SECRET_KEY):
        raise RuntimeError("forgedToken unexpectedly verifies with the SUT secret")
    expired = decode_part(variables["expiredToken"].split(".")[1])
    if not valid_signature(variables["expiredToken"], SECRET_KEY) or expired["exp"] >= 2:
        raise RuntimeError("expiredToken does not have signed-expired semantics")
    inactive = decode_part(variables["otherInvalidToken"].split(".")[1])
    if not valid_signature(variables["otherInvalidToken"], SECRET_KEY) or inactive["nbf"] <= 1:
        raise RuntimeError("otherInvalidToken is not the signed not-yet-valid fixture")


def validate_temp_database() -> None:
    with tempfile.TemporaryDirectory(prefix="pool-c-runtime-") as temp_dir:
        database_path = Path(temp_dir) / "database.sqlite"
        connection = sqlite3.connect(database_path)
        try:
            create_schema(connection)
            seed_snapshot_sentinel(connection)
            saved = snapshot(connection)
            for test_id in reviewed_ids():
                values = reset_case(connection, test_id)
                state = inspect_case(connection, test_id)
                if state["targetStatus"] != values["initialStatus"]:
                    raise RuntimeError(f"{test_id}: reset/inspect initial-state mismatch")
                if len(state["orders"]) != 2:
                    raise RuntimeError(f"{test_id}: fixture is not isolated to two orders")
            restore(connection, saved)
            if snapshot(connection) != saved:
                raise RuntimeError("snapshot restoration did not reproduce the original orders table")
        finally:
            connection.close()


def request_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for item in items:
        if "request" in item:
            result.append(item)
        else:
            result.extend(request_items(item.get("item", [])))
    return result


def validate_collection() -> dict[str, Any]:
    collection = json.loads(COLLECTION_PATH.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.validators.validator_for(schema)(schema)
    errors = sorted(validator.iter_errors(collection), key=lambda error: list(error.path))
    if errors:
        rendered = [f"{'/'.join(map(str, error.path)) or '<root>'}: {error.message}" for error in errors]
        raise RuntimeError("Full Postman v2.1 schema validation failed:\n" + "\n".join(rendered))

    requests = request_items(collection["item"])
    ids = [item["name"][:7] for item in requests]
    counts = {test_id: ids.count(test_id) for test_id in reviewed_ids()}
    expected_counts = {test_id: FLOW_COUNTS.get(test_id, 1) for test_id in reviewed_ids()}
    if counts != expected_counts or len(requests) != 93:
        raise RuntimeError(f"Collection request mapping mismatch: {counts!r}")

    events = [event for event in collection.get("event", []) if event.get("listen") == "prerequest"]
    if len(events) != 1:
        raise RuntimeError("Collection must contain exactly one pre-request event")
    script = "\n".join(events[0]["script"]["exec"])
    for marker in (
        "X-Student-Id", "[Pool C execution evidence]", "fixtureControlUrl", "fixtureControlKey",
        "/reset/", "X-Fixture-Control-Key", "pm.execution.skipRequest()", "isContinuation",
        "orderId", "unrelatedOrderId", "nonexistentOrderId",
    ):
        if marker not in script:
            raise RuntimeError(f"Collection runtime hook is missing {marker!r}")

    variables = {item["key"]: item.get("value", "") for item in collection.get("variable", [])}
    required = set(runtime_variables()) | {
        "baseUrl", "studentId", "fixtureControlUrl", "fixtureControlKey", "orderId",
        "unrelatedOrderId", "nonexistentOrderId",
    }
    if not required.issubset(variables):
        raise RuntimeError(f"Collection variables missing: {sorted(required - set(variables))}")
    for key in set(runtime_variables()) | {"fixtureControlUrl", "fixtureControlKey"}:
        if variables[key]:
            raise RuntimeError(f"Runtime secret/controller variable must default blank: {key}")

    with CSV_PATH.open(encoding="utf-8-sig", newline="") as handle:
        source_rows = {row["Test ID"]: row for row in csv.DictReader(handle)}
    for test_id in reviewed_ids():
        matching = [item for item in requests if item["name"].startswith(test_id)]
        if not matching:
            raise RuntimeError(f"Missing collection mapping for {test_id}")
        source = source_rows[test_id]
        for item in matching:
            description = item["request"].get("description", "")
            if "Preconditions\n" not in description or "Reviewed Expected Result\n" not in description:
                raise RuntimeError(f"{item['name']}: source preconditions/expected result not preserved")
            for field in (
                "Test Objective", "Preconditions", "Request Input", "Expected Result",
                "Specification Basis", "Assumptions / Notes",
            ):
                if source[field] not in description:
                    raise RuntimeError(f"{item['name']}: reviewed {field} text changed or is missing")

    original_states = {
        **{f"API-{number:03d}": "delivered" for number in range(55, 59)},
        **{f"API-{number:03d}": "canceled" for number in range(59, 63)},
        **{f"API-{number:03d}": "pending" for number in range(63, 65)},
        **{f"API-{number:03d}": "confirmed" for number in range(65, 67)},
        **{f"API-{number:03d}": "shipping" for number in range(67, 70)},
    }
    for test_id, original_state in original_states.items():
        item = next(item for item in requests if item["name"].startswith(test_id))
        script_text = "\n".join(
            line
            for event in item.get("event", [])
            if event.get("listen") == "test"
            for line in event.get("script", {}).get("exec", [])
        )
        marker = f"target order state is {original_state}"
        if marker not in script_text or f"to.equal('{original_state}')" not in script_text:
            raise RuntimeError(f"{test_id}: missing fixture-backed unchanged-state assertion for {original_state}")

    allowed_script_markers = {
        "pm.sendRequest", "pm.test", "pm.expect", "pm.variables.replaceIn", "pm.request.headers",
        "pm.collectionVariables.set", "pm.execution.skipRequest", "console.log", "console.error",
    }
    all_scripts = script + "\n" + "\n".join(
        line
        for item in requests
        for event in item.get("event", [])
        for line in event.get("script", {}).get("exec", [])
    )
    for forbidden in ("pm.visualizer", "postman.setNextRequest", "require(", "eval("):
        if forbidden in all_scripts:
            raise RuntimeError(f"Newman compatibility check found forbidden marker: {forbidden}")
    if not all(marker in all_scripts for marker in allowed_script_markers):
        raise RuntimeError("Expected Newman-supported runtime primitives are missing")
    return {"requests": len(requests), "caseRequestCounts": counts}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sut-dir", type=Path, help="Optional SUT repository for read-only schema validation")
    parser.add_argument("--output", type=Path, default=Path("postman/pool-c-validation-results.json"))
    args = parser.parse_args()

    validate_jwts()
    validate_temp_database()
    collection_result = validate_collection()
    sut_schema = "NOT_REQUESTED"
    if args.sut_dir:
        database_path = args.sut_dir.resolve() / "backend" / "database.sqlite"
        connection = sqlite3.connect(f"file:{database_path}?mode=ro", uri=True)
        try:
            validate_schema(connection)
        finally:
            connection.close()
        sut_schema = "PASS_READ_ONLY"
    result = {
        "validatedAt": datetime.now(GMT7).strftime("%Y-%m-%d %H:%M:%S GMT+7"),
        "reviewedTestIds": 85,
        "postmanRequests": collection_result["requests"],
        "orderedFlows": FLOW_COUNTS,
        "fullPostmanV21Schema": "PASS",
        "fixtureManifest": "PASS",
        "allPerCaseResetsOnTemporaryDatabase": "PASS",
        "snapshotRestore": "PASS",
        "jwtVariants": "PASS",
        "collectionRuntimeHook": "PASS",
        "traceability": "PASS",
        "newmanCompatibilityStaticCheck": "PASS",
        "sutSchema": sut_schema,
        "realSutStartedOrContacted": False,
        "newmanExecuted": False,
        "summary": fixture_summary(),
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
