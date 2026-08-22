"""Deterministic Pool A fixture definitions shared by seeding and generation."""

from dataclasses import dataclass


EMAIL_DOMAIN = "example.test"
NO_DATABASE_FIXTURE_IDS = {"API-002", "API-003", "API-025", "API-028", "API-029", "API-065", "API-072", "API-075"}
INTENTIONALLY_ABSENT_IDS = {"API-032"}
BLOCKED_IDS = {"API-025", "API-065", "API-072", "API-075", "API-077"}
REPLAY_PASSWORDS = {
    "API-026": "FixtureConsumed1!",
    "API-066": "FixtureConsumed2!",
    "API-073": "FixtureConsumed3!",
}
CROSS_ACCOUNT_IDS = {"API-015", "API-031", "API-064", "API-071", "API-081"}


@dataclass(frozen=True)
class AccountFixture:
    test_id: str
    label: str
    email: str
    reset_token: str


def deterministic_otp(test_id: str, label: str = "primary") -> str:
    number = int(test_id.split("-")[1])
    if test_id == "API-013":
        return "012345"
    if test_id in {"API-009", "API-044"}:
        return "123456"
    offset = 100000 if label == "primary" else 200000
    return f"{offset + number:06d}"


def fixture_email(test_id: str, label: str = "primary") -> str:
    suffix = "" if label == "primary" else f"-{label}"
    return f"poola-{test_id.lower()}{suffix}@{EMAIL_DOMAIN}"


def accounts_for(test_id: str) -> list[AccountFixture]:
    if test_id in NO_DATABASE_FIXTURE_IDS or test_id in INTENTIONALLY_ABSENT_IDS:
        return []
    if test_id in CROSS_ACCOUNT_IDS:
        return [
            AccountFixture(test_id, "a", fixture_email(test_id, "a"), deterministic_otp(test_id, "primary")),
            AccountFixture(test_id, "b", fixture_email(test_id, "b"), deterministic_otp(test_id, "secondary")),
        ]
    return [AccountFixture(test_id, "primary", fixture_email(test_id), deterministic_otp(test_id))]


def all_accounts() -> list[AccountFixture]:
    return [account for number in range(1, 83) for account in accounts_for(f"API-{number:03d}")]


def primary_account(test_id: str) -> AccountFixture | None:
    accounts = accounts_for(test_id)
    return accounts[0] if accounts else None


def secondary_account(test_id: str) -> AccountFixture | None:
    accounts = accounts_for(test_id)
    return accounts[1] if len(accounts) > 1 else None
