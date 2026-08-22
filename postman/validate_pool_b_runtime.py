"""Validate the Pool B runtime manifest, reset/restore logic, JWTs, and collection wiring."""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import sqlite3
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from pool_b_fixtures import (
    COLLECTION_PATH,
    CSV_PATH,
    SECRET_KEY,
    USAGE_COUNTS,
    coupon_manifest,
    fixture_summary,
    reset_case,
    restore,
    reviewed_ids,
    runtime_variables,
    snapshot,
    validate_schema,
    verify_case,
)


GMT7 = timezone(timedelta(hours=7))


def create_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE coupons (
            id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE,
            type TEXT DEFAULT 'percent', discount_value INTEGER,
            min_order_amount INTEGER DEFAULT 0, expired_at DATETIME,
            is_active INTEGER DEFAULT 1, max_uses_per_user INTEGER DEFAULT 1
        );
        CREATE TABLE coupon_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT, coupon_id INTEGER,
            user_id INTEGER, used_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT,
            password TEXT, role TEXT DEFAULT 'user', login_attempts INTEGER DEFAULT 0,
            locked_until DATETIME, reset_token TEXT, shipping_address TEXT, phone TEXT
        );
        """
    )


def seed_snapshot_sentinel(connection: sqlite3.Connection) -> None:
    connection.execute(
        "INSERT INTO coupons VALUES (42,'ORIGINAL','fixed',7,8,'2030-01-01',1,9)"
    )
    connection.execute("INSERT INTO coupon_usage VALUES (43,42,999999999,'2020-01-01 00:00:00')")
    for user_id in (0, 1, 2, 999999999):
        connection.execute(
            "INSERT INTO users VALUES (?,?,?,?,?,0,NULL,NULL,NULL,NULL)",
            (user_id, f"Original {user_id}", f"original-{user_id}@example.test", "x", "user"),
        )
    connection.commit()


def decode_part(value: str) -> dict:
    padding = "=" * (-len(value) % 4)
    return json.loads(base64.urlsafe_b64decode(value + padding))


def valid_signature(token: str, secret: str) -> bool:
    parts = token.split(".")
    if len(parts) != 3:
        return False
    padding = "=" * (-len(parts[2]) % 4)
    actual = base64.urlsafe_b64decode(parts[2] + padding)
    expected = hmac.new(secret.encode(), f"{parts[0]}.{parts[1]}".encode(), hashlib.sha256).digest()
    return hmac.compare_digest(actual, expected)


def validate_jwts() -> None:
    variables = runtime_variables()
    valid = variables["authToken"]
    limit = variables["limitReachedAuthToken"]
    expired = variables["expiredToken"]
    invalid_signature = variables["invalidSignatureToken"]
    if not valid_signature(valid, SECRET_KEY) or decode_part(valid.split(".")[1])["id"] != 1:
        raise RuntimeError("authToken is not a valid deterministic user-1 JWT")
    if not valid_signature(limit, SECRET_KEY) or decode_part(limit.split(".")[1])["id"] != 1:
        raise RuntimeError("limitReachedAuthToken is not a valid deterministic user-1 JWT")
    if valid_signature(invalid_signature, SECRET_KEY):
        raise RuntimeError("invalidSignatureToken unexpectedly verifies with the SUT secret")
    if not valid_signature(expired, SECRET_KEY) or decode_part(expired.split(".")[1])["exp"] >= 2:
        raise RuntimeError("expiredToken does not have the required signed-expired semantics")
    if variables["invalidToken"].count(".") == 2:
        raise RuntimeError("invalidToken should be an intentionally malformed JWT")


def validate_temp_database() -> None:
    controlled_today = date(2026, 8, 22)
    with tempfile.TemporaryDirectory(prefix="pool-b-runtime-") as temp_dir:
        database_path = Path(temp_dir) / "database.sqlite"
        connection = sqlite3.connect(database_path)
        try:
            create_schema(connection)
            seed_snapshot_sentinel(connection)
            saved = snapshot(connection)
            for test_id in reviewed_ids():
                reset_case(connection, test_id, controlled_today)
                verify_case(connection, test_id, controlled_today)
            restore(connection, saved)
            after = snapshot(connection)
            if after != saved:
                raise RuntimeError("snapshot restoration did not reproduce the original database state")
        finally:
            connection.close()


def validate_collection() -> None:
    collection = json.loads(COLLECTION_PATH.read_text(encoding="utf-8"))
    requests = [item for folder in collection["item"] for item in folder["item"]]
    ids = [item["name"][:7] for item in requests]
    if len(ids) != 74 or len(set(ids)) != 74 or set(ids) != set(reviewed_ids()):
        raise RuntimeError("collection no longer contains each of the 74 reviewed IDs exactly once")
    events = [event for event in collection.get("event", []) if event.get("listen") == "prerequest"]
    if len(events) != 1:
        raise RuntimeError("collection must contain exactly one pre-request event")
    script = "\n".join(events[0]["script"]["exec"])
    for marker in (
        "X-Student-Id", "[Pool B execution evidence]", "fixtureControlUrl",
        "fixtureControlKey", "/reset/", "X-Fixture-Control-Key",
        "pm.execution.skipRequest()", "[Pool B fixture ready]",
    ):
        if marker not in script:
            raise RuntimeError(f"collection runtime hook is missing {marker!r}")
    variables = {item["key"]: item.get("value", "") for item in collection.get("variable", [])}
    required = set(runtime_variables()) | {"baseUrl", "studentId", "fixtureControlUrl", "fixtureControlKey"}
    if not required.issubset(variables):
        raise RuntimeError(f"collection variables missing: {sorted(required - set(variables))}")
    if variables["fixtureControlUrl"] or variables["fixtureControlKey"]:
        raise RuntimeError("fixture controller defaults must remain blank and be supplied by the runner")


def validate_review_mapping() -> None:
    text = CSV_PATH.read_text(encoding="utf-8-sig")
    for fixture in coupon_manifest(date(2026, 8, 22)):
        if fixture.code not in text:
            raise RuntimeError(f"fixture coupon is not traceable to reviewed CSV: {fixture.code}")
    if set(USAGE_COUNTS) != {
        "API-040", "API-041", "API-054", "API-055", "API-056",
        "API-057", "API-058", "API-059", "API-072",
    }:
        raise RuntimeError("usage override matrix changed unexpectedly")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sut-dir", type=Path, help="Optional SUT repository for read-only live-schema validation")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("postman/pool-b-runtime-validation.json"),
    )
    args = parser.parse_args()
    validate_review_mapping()
    validate_jwts()
    validate_temp_database()
    validate_collection()
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
        "reviewedTestIds": 74,
        "fixtureManifest": "PASS",
        "allPerCaseResetsOnTemporaryDatabase": "PASS",
        "snapshotRestore": "PASS",
        "jwtVariants": "PASS",
        "collectionRuntimeHook": "PASS",
        "sutSchema": sut_schema,
        "realSutStartedOrContacted": False,
        "fullNewmanSuiteExecuted": False,
        "summary": fixture_summary(),
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
