"""Seed deterministic Pool A users and OTPs directly into the initialized SUT SQLite DB."""

import argparse
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from pool_a_fixtures import all_accounts, fixture_email


REQUIRED_USER_COLUMNS = {
    "id", "name", "email", "password", "role", "login_attempts",
    "locked_until", "reset_token", "shipping_address", "phone",
}


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


def validate_schema(connection: sqlite3.Connection) -> None:
    columns = connection.execute("PRAGMA table_info(users)").fetchall()
    if not columns:
        raise RuntimeError("users table is missing; start/init the SUT before running this fixture")
    names = {row[1] for row in columns}
    missing = sorted(REQUIRED_USER_COLUMNS - names)
    if missing:
        raise RuntimeError(f"SUT users schema is missing expected columns: {missing}")
    reset_token = next(row for row in columns if row[1] == "reset_token")
    if str(reset_token[2]).upper() != "TEXT":
        raise RuntimeError(f"users.reset_token must be TEXT, found {reset_token[2]!r}")


def seed(database_path: Path) -> int:
    accounts = all_accounts()
    connection = sqlite3.connect(database_path, timeout=10)
    try:
        validate_schema(connection)
        connection.execute("BEGIN IMMEDIATE")
        connection.execute("DELETE FROM users WHERE email LIKE 'poola-api-%@example.test'")
        connection.executemany(
            """INSERT INTO users
               (name, email, password, role, login_attempts, locked_until, reset_token, shipping_address, phone)
               VALUES (?, ?, ?, 'user', 0, NULL, ?, NULL, NULL)""",
            [
                (f"Pool A {account.test_id} {account.label}", account.email, "FixtureOld1!", account.reset_token)
                for account in accounts
            ],
        )
        # API-032 is deliberately absent; this also cleans up prior manual runs.
        connection.execute("DELETE FROM users WHERE email = ?", (fixture_email("API-032"),))
        connection.commit()

        seeded = connection.execute(
            """SELECT email, reset_token, typeof(reset_token)
               FROM users WHERE email LIKE 'poola-api-%@example.test' ORDER BY email"""
        ).fetchall()
        if len(seeded) != len(accounts):
            raise RuntimeError(f"Expected {len(accounts)} fixture accounts, found {len(seeded)}")
        expected = {account.email: account.reset_token for account in accounts}
        for email, token, storage_type in seeded:
            if token != expected[email] or storage_type != "text":
                raise RuntimeError(f"Fixture verification failed for {email}: token={token!r}, typeof={storage_type!r}")
        return len(seeded)
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sut-dir", type=Path, required=True, help="Path to the eShop SUT repository")
    parser.add_argument("--base-url", default="http://127.0.0.1:3000", help="Running initialized SUT URL")
    args = parser.parse_args()
    database_path = args.sut_dir.resolve() / "backend" / "database.sqlite"
    if not database_path.is_file():
        raise RuntimeError(f"SUT SQLite database does not exist: {database_path}")
    require_running_sut(args.base_url)
    count = seed(database_path)
    print(f"SEEDED: {count} deterministic Pool A accounts in {database_path}")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"FIXTURE ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
