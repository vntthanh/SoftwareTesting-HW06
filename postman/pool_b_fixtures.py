"""Deterministic Pool B coupon, usage-state, user, and JWT fixtures."""

from __future__ import annotations

import base64
import csv
import hashlib
import hmac
import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "test-cases" / "b-discount-coupons.csv"
COLLECTION_PATH = ROOT / "postman" / "pool-b-discount-coupons.postman_collection.json"
SECRET_KEY = "super_secret_key_that_should_not_be_here"
CONTROLLED_USER_IDS = (0, 1, 2, 999999999)
REQUIRED_COLUMNS = {
    "coupons": {
        "id", "code", "type", "discount_value", "min_order_amount",
        "expired_at", "is_active", "max_uses_per_user",
    },
    "coupon_usage": {"id", "coupon_id", "user_id", "used_at"},
    "users": {
        "id", "name", "email", "password", "role", "login_attempts",
        "locked_until", "reset_token", "shipping_address", "phone",
    },
}


@dataclass(frozen=True)
class CouponFixture:
    id: int
    code: str
    type: str
    discount_value: int
    min_order_amount: int
    expired_at: str
    is_active: int
    max_uses_per_user: int


USAGE_COUNTS: dict[str, tuple[str, int, int]] = {
    "API-040": ("SAVE10", 1, 1),
    "API-041": ("SAVE10", 1, 2),
    "API-054": ("GENERIC_LIMIT_TEST", 1, 2),
    "API-055": ("GENERIC_LIMIT_TEST", 1, 3),
    "API-056": ("GENERIC_LIMIT_TEST", 1, 4),
    "API-057": ("VIP100", 1, 1),
    "API-058": ("VIP100", 1, 2),
    "API-059": ("VIP100", 1, 3),
    "API-072": ("SAVE10", 1, 1),
}


def reviewed_ids() -> list[str]:
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    ids = [row["Test ID"] for row in rows]
    expected = [f"API-{number:03d}" for number in range(1, 75)]
    if ids != expected:
        raise RuntimeError("Pool B CSV must retain exactly API-001 through API-074 in order")
    return ids


def coupon_manifest(today: date | None = None) -> tuple[CouponFixture, ...]:
    current = today or date.today()
    tomorrow = (current + timedelta(days=1)).isoformat()
    yesterday = (current - timedelta(days=1)).isoformat()
    return (
        CouponFixture(1001, "SAVE10", "percent", 10, 300000, "2099-12-31", 1, 1),
        CouponFixture(1002, "BIGBUY", "fixed", 50000, 500000, "2099-12-31", 1, 1),
        CouponFixture(1003, "VIP100", "fixed", 100000, 300000, "2099-12-31", 1, 2),
        CouponFixture(1004, "EXPIRED", "percent", 20, 100000, "2020-01-01", 1, 1),
        CouponFixture(1005, "INACTIVE_TEST", "percent", 10, 300000, "2099-12-31", 0, 1),
        CouponFixture(1006, "EXPIRES_TODAY_TEST", "percent", 10, 300000, current.isoformat(), 1, 1),
        CouponFixture(1007, "ZERO_MIN_TEST", "percent", 10, 0, "2099-12-31", 1, 1),
        CouponFixture(1008, "EXPIRY_BOUNDARY_TEST", "percent", 10, 300000, tomorrow, 1, 1),
        CouponFixture(1009, "GENERIC_LIMIT_TEST", "fixed", 50000, 300000, "2099-12-31", 1, 3),
        CouponFixture(1010, "PERCENT1", "percent", 1, 0, "2099-12-31", 1, 1),
        CouponFixture(1011, "PERCENT100", "percent", 100, 0, "2099-12-31", 1, 1),
    )


def manifest_for(test_id: str, today: date | None = None) -> tuple[CouponFixture, ...]:
    fixtures = list(coupon_manifest(today))
    if test_id == "API-053":
        current = today or date.today()
        fixtures = [
            CouponFixture(**{**asdict(item), "expired_at": (current - timedelta(days=1)).isoformat()})
            if item.code == "EXPIRY_BOUNDARY_TEST" else item
            for item in fixtures
        ]
    return tuple(fixtures)


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def make_jwt(payload: dict[str, Any], secret: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    signing_input = ".".join(
        _b64url(json.dumps(part, separators=(",", ":"), sort_keys=True).encode("utf-8"))
        for part in (header, payload)
    )
    signature = hmac.new(secret.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256).digest()
    return f"{signing_input}.{_b64url(signature)}"


def runtime_variables() -> dict[str, str]:
    future = 4102444800  # 2100-01-01T00:00:00Z
    valid = make_jwt({"exp": future, "fixture": "pool-b-valid", "id": 1, "role": "user"}, SECRET_KEY)
    return {
        "authToken": valid,
        "invalidToken": "not-a-jwt",
        "invalidSignatureToken": make_jwt(
            {"exp": future, "fixture": "pool-b-invalid-signature", "id": 1, "role": "user"},
            "pool-b-intentionally-wrong-secret",
        ),
        "expiredToken": make_jwt(
            {"exp": 1, "fixture": "pool-b-expired", "id": 1, "role": "user"},
            SECRET_KEY,
        ),
        "limitReachedAuthToken": make_jwt(
            {"exp": future, "fixture": "pool-b-limit-reached", "id": 1, "role": "user"},
            SECRET_KEY,
        ),
    }


def validate_schema(connection: sqlite3.Connection) -> None:
    for table, required in REQUIRED_COLUMNS.items():
        columns = connection.execute(f"PRAGMA table_info({table})").fetchall()
        if not columns:
            raise RuntimeError(f"SUT table is missing: {table}")
        actual = {row[1] for row in columns}
        missing = sorted(required - actual)
        if missing:
            raise RuntimeError(f"SUT {table} schema is missing expected columns: {missing}")


def snapshot(connection: sqlite3.Connection) -> dict[str, Any]:
    validate_schema(connection)
    user_columns = [row[1] for row in connection.execute("PRAGMA table_info(users)")]
    placeholders = ",".join("?" for _ in CONTROLLED_USER_IDS)
    return {
        "coupons": [list(row) for row in connection.execute("SELECT * FROM coupons ORDER BY id")],
        "coupon_usage": [list(row) for row in connection.execute("SELECT * FROM coupon_usage ORDER BY id")],
        "controlled_users": [
            list(row) for row in connection.execute(
                f"SELECT * FROM users WHERE id IN ({placeholders}) ORDER BY id", CONTROLLED_USER_IDS
            )
        ],
        "user_columns": user_columns,
        "sequence": [
            list(row) for row in connection.execute(
                "SELECT name, seq FROM sqlite_sequence WHERE name IN ('coupons','coupon_usage','users') ORDER BY name"
            )
        ],
    }


def restore(connection: sqlite3.Connection, saved: dict[str, Any]) -> None:
    user_columns = saved["user_columns"]
    placeholders = ",".join("?" for _ in CONTROLLED_USER_IDS)
    connection.execute("BEGIN IMMEDIATE")
    try:
        connection.execute("DELETE FROM coupon_usage")
        connection.execute("DELETE FROM coupons")
        connection.executemany(
            "INSERT INTO coupons VALUES (?,?,?,?,?,?,?,?)", saved["coupons"]
        )
        connection.executemany(
            "INSERT INTO coupon_usage VALUES (?,?,?,?)", saved["coupon_usage"]
        )
        connection.execute(f"DELETE FROM users WHERE id IN ({placeholders})", CONTROLLED_USER_IDS)
        if saved["controlled_users"]:
            marks = ",".join("?" for _ in user_columns)
            connection.executemany(
                f"INSERT INTO users ({','.join(user_columns)}) VALUES ({marks})",
                saved["controlled_users"],
            )
        connection.execute("DELETE FROM sqlite_sequence WHERE name IN ('coupons','coupon_usage','users')")
        connection.executemany("INSERT INTO sqlite_sequence(name,seq) VALUES (?,?)", saved["sequence"])
        connection.commit()
    except Exception:
        connection.rollback()
        raise


def reset_case(connection: sqlite3.Connection, test_id: str, today: date | None = None) -> None:
    if test_id not in reviewed_ids():
        raise RuntimeError(f"Unknown reviewed Pool B Test ID: {test_id}")
    fixtures = manifest_for(test_id, today)
    connection.execute("BEGIN IMMEDIATE")
    try:
        validate_schema(connection)
        for user_id, name, email, role in (
            (1, "Pool B User 1", "poolb-user-1@example.test", "user"),
            (2, "Pool B User 2", "poolb-user-2@example.test", "user"),
        ):
            exists = connection.execute("SELECT 1 FROM users WHERE id = ?", (user_id,)).fetchone()
            if not exists:
                connection.execute(
                    """INSERT INTO users
                       (id,name,email,password,role,login_attempts,locked_until,reset_token,shipping_address,phone)
                       VALUES (?,?,?,?,?,0,NULL,NULL,NULL,NULL)""",
                    (user_id, name, email, "PoolBFixture1!", role),
                )
        connection.execute("DELETE FROM users WHERE id IN (0, 999999999)")
        connection.execute("DELETE FROM coupon_usage")
        connection.execute("DELETE FROM coupons")
        connection.executemany(
            """INSERT INTO coupons
               (id,code,type,discount_value,min_order_amount,expired_at,is_active,max_uses_per_user)
               VALUES (?,?,?,?,?,?,?,?)""",
            [tuple(asdict(item).values()) for item in fixtures],
        )
        usage = USAGE_COUNTS.get(test_id)
        if usage:
            code, user_id, count = usage
            coupon_id = next(item.id for item in fixtures if item.code == code)
            connection.executemany(
                "INSERT INTO coupon_usage (id,coupon_id,user_id,used_at) VALUES (?,?,?,?)",
                [(2000 + number, coupon_id, user_id, f"2000-01-{number:02d} 00:00:00") for number in range(1, count + 1)],
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    verify_case(connection, test_id, today)


def verify_case(connection: sqlite3.Connection, test_id: str, today: date | None = None) -> None:
    expected = {item.code: item for item in manifest_for(test_id, today)}
    rows = connection.execute(
        "SELECT id,code,type,discount_value,min_order_amount,expired_at,is_active,max_uses_per_user FROM coupons"
    ).fetchall()
    actual = {row[1]: row for row in rows}
    if set(actual) != set(expected):
        raise RuntimeError(f"{test_id}: controlled coupon set mismatch")
    for code, item in expected.items():
        if actual[code] != tuple(asdict(item).values()):
            raise RuntimeError(f"{test_id}: coupon fixture mismatch for {code}: {actual[code]!r}")
    expected_usage = USAGE_COUNTS.get(test_id)
    usage_rows = connection.execute(
        """SELECT coupons.code,coupon_usage.user_id,COUNT(*)
           FROM coupon_usage JOIN coupons ON coupons.id=coupon_usage.coupon_id
           GROUP BY coupons.code,coupon_usage.user_id"""
    ).fetchall()
    wanted = [] if not expected_usage else [expected_usage]
    if usage_rows != wanted:
        raise RuntimeError(f"{test_id}: usage fixture mismatch: expected {wanted!r}, found {usage_rows!r}")
    present = {row[0] for row in connection.execute("SELECT id FROM users WHERE id IN (0,1,2,999999999)")}
    if present != {1, 2}:
        raise RuntimeError(f"{test_id}: controlled user presence mismatch: {present}")


def fixture_summary() -> dict[str, Any]:
    return {
        "reviewedTestIds": len(reviewed_ids()),
        "couponFixtures": [asdict(item) for item in coupon_manifest(date(2026, 8, 22))],
        "usageOverrides": {
            key: {"coupon": value[0], "userId": value[1], "priorUses": value[2]}
            for key, value in USAGE_COUNTS.items()
        },
        "controlledUsers": {"present": [1, 2], "absent": [0, 999999999]},
        "jwtVariables": sorted(runtime_variables()),
    }
