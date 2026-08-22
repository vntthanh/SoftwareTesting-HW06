"""Deterministic Pool C order, state-oracle, and JWT fixtures."""

from __future__ import annotations

import base64
import csv
import hashlib
import hmac
import json
import sqlite3
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "test-cases" / "c-order-management.csv"
COLLECTION_PATH = ROOT / "postman" / "pool-c-order-management.postman_collection.json"
SECRET_KEY = "super_secret_key_that_should_not_be_here"
TARGET_BASE = 300000
UNRELATED_BASE = 400000
REQUIRED_ORDER_COLUMNS = {
    "id", "user_id", "total_amount", "status", "shipping_address", "created_at"
}


def reviewed_ids() -> list[str]:
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    ids = [row["Test ID"] for row in rows]
    expected = [f"API-{number:03d}" for number in range(1, 86)]
    if ids != expected:
        raise RuntimeError("Pool C CSV must retain exactly API-001 through API-085 in order")
    return ids


def case_number(test_id: str) -> int:
    if test_id not in reviewed_ids():
        raise RuntimeError(f"Unknown reviewed Pool C Test ID: {test_id}")
    return int(test_id.removeprefix("API-"))


def initial_status(test_id: str) -> str:
    number = case_number(test_id)
    if number in {19, 36, 52, 67, 68, 69, 83}:
        return "shipping"
    if number in {20, 25, 55, 56, 57, 58}:
        return "delivered"
    if number in {21, 59, 60, 61, 62}:
        return "canceled"
    if number in {22, 35, 38, 51, 54, 65, 66}:
        return "confirmed"
    return "pending"


def fixture_values(test_id: str) -> dict[str, Any]:
    number = case_number(test_id)
    return {
        "testId": test_id,
        "orderId": TARGET_BASE + number,
        "unrelatedOrderId": UNRELATED_BASE + number,
        "nonexistentOrderId": 900000 + number,
        "initialStatus": initial_status(test_id),
        "unrelatedInitialStatus": "confirmed",
    }


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def make_jwt(payload: dict[str, Any], secret: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    signing_input = ".".join(
        _b64url(json.dumps(part, separators=(",", ":"), sort_keys=True).encode("utf-8"))
        for part in (header, payload)
    )
    signature = hmac.new(secret.encode(), signing_input.encode("ascii"), hashlib.sha256).digest()
    return f"{signing_input}.{_b64url(signature)}"


def runtime_variables() -> dict[str, str]:
    future = 4102444800
    return {
        "adminToken": make_jwt(
            {"exp": future, "fixture": "pool-c-admin", "id": 1, "role": "admin"}, SECRET_KEY
        ),
        "nonAdminToken": make_jwt(
            {"exp": future, "fixture": "pool-c-non-admin", "id": 2, "role": "user"}, SECRET_KEY
        ),
        "malformedToken": "not-a-jwt",
        "forgedToken": make_jwt(
            {"exp": future, "fixture": "pool-c-forged", "id": 1, "role": "admin"},
            "pool-c-intentionally-wrong-secret",
        ),
        "expiredToken": make_jwt(
            {"exp": 1, "fixture": "pool-c-expired", "id": 1, "role": "admin"}, SECRET_KEY
        ),
        "otherInvalidToken": make_jwt(
            {"exp": future, "nbf": future, "fixture": "pool-c-not-yet-valid", "id": 1, "role": "admin"},
            SECRET_KEY,
        ),
    }


def validate_schema(connection: sqlite3.Connection) -> None:
    columns = connection.execute("PRAGMA table_info(orders)").fetchall()
    if not columns:
        raise RuntimeError("SUT table is missing: orders")
    actual = {row[1] for row in columns}
    missing = sorted(REQUIRED_ORDER_COLUMNS - actual)
    if missing:
        raise RuntimeError(f"SUT orders schema is missing expected columns: {missing}")


def snapshot(connection: sqlite3.Connection) -> dict[str, Any]:
    validate_schema(connection)
    columns = [row[1] for row in connection.execute("PRAGMA table_info(orders)")]
    return {
        "columns": columns,
        "orders": [list(row) for row in connection.execute("SELECT * FROM orders ORDER BY id")],
        "sequence": connection.execute(
            "SELECT seq FROM sqlite_sequence WHERE name = 'orders'"
        ).fetchone(),
    }


def restore(connection: sqlite3.Connection, saved: dict[str, Any]) -> None:
    columns = saved["columns"]
    marks = ",".join("?" for _ in columns)
    connection.execute("BEGIN IMMEDIATE")
    try:
        connection.execute("DELETE FROM orders")
        if saved["orders"]:
            connection.executemany(
                f"INSERT INTO orders ({','.join(columns)}) VALUES ({marks})", saved["orders"]
            )
        connection.execute("DELETE FROM sqlite_sequence WHERE name = 'orders'")
        if saved["sequence"] is not None:
            connection.execute(
                "INSERT INTO sqlite_sequence(name,seq) VALUES ('orders',?)", (saved["sequence"][0],)
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise


def reset_case(connection: sqlite3.Connection, test_id: str) -> dict[str, Any]:
    values = fixture_values(test_id)
    connection.execute("BEGIN IMMEDIATE")
    try:
        validate_schema(connection)
        connection.execute("DELETE FROM orders")
        connection.executemany(
            """INSERT INTO orders
               (id,user_id,total_amount,status,shipping_address,created_at)
               VALUES (?,?,?,?,?,?)""",
            [
                (
                    values["orderId"], 2, 123456, values["initialStatus"],
                    f"Pool C target {test_id}", "2026-08-22 00:00:00",
                ),
                (
                    values["unrelatedOrderId"], 2, 654321, values["unrelatedInitialStatus"],
                    f"Pool C unrelated {test_id}", "2026-08-22 00:00:01",
                ),
            ],
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    verify_case(connection, test_id)
    return values


def inspect_case(connection: sqlite3.Connection, test_id: str) -> dict[str, Any]:
    values = fixture_values(test_id)
    rows = connection.execute(
        "SELECT id,status FROM orders ORDER BY id"
    ).fetchall()
    return {
        **values,
        "targetStatus": next((status for order_id, status in rows if order_id == values["orderId"]), None),
        "unrelatedStatus": next(
            (status for order_id, status in rows if order_id == values["unrelatedOrderId"]), None
        ),
        "orders": [{"id": order_id, "status": status} for order_id, status in rows],
    }


def verify_case(connection: sqlite3.Connection, test_id: str) -> None:
    state = inspect_case(connection, test_id)
    expected_ids = {state["orderId"], state["unrelatedOrderId"]}
    actual_ids = {row["id"] for row in state["orders"]}
    if actual_ids != expected_ids:
        raise RuntimeError(f"{test_id}: isolated order fixture mismatch: {actual_ids!r}")
    if state["targetStatus"] != state["initialStatus"]:
        raise RuntimeError(f"{test_id}: target order state mismatch")
    if state["unrelatedStatus"] != state["unrelatedInitialStatus"]:
        raise RuntimeError(f"{test_id}: unrelated order state mismatch")


def fixture_summary() -> dict[str, Any]:
    return {
        "reviewedTestIds": len(reviewed_ids()),
        "targetIdRange": [TARGET_BASE + 1, TARGET_BASE + 85],
        "unrelatedIdRange": [UNRELATED_BASE + 1, UNRELATED_BASE + 85],
        "initialStates": {test_id: initial_status(test_id) for test_id in reviewed_ids()},
        "jwtVariables": sorted(runtime_variables()),
    }
