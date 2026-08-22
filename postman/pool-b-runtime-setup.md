# Pool B Runtime Setup

## Purpose

Pool B keeps the 74 reviewed requests unchanged while supplying deterministic database and JWT preconditions at runtime. The setup follows Pool A's direct-SQLite approach, with an additional per-request reset because several Pool B cases require conflicting usage counts for the same coupon and user.

## Controlled fixtures

The runtime owns the complete `coupons` and `coupon_usage` contents during a wrapped run. It preserves unrelated users, ensures users 1 and 2 exist, and makes users 0 and 999999999 absent. The wrapper snapshots the original coupon tables and controlled user rows before execution and restores them in a `finally` block.

| Coupon | Type | Value | Minimum | Active | Expiry | Max uses |
|---|---|---:|---:|---:|---|---:|
| SAVE10 | percent | 10 | 300000 | 1 | 2099-12-31 | 1 |
| BIGBUY | fixed | 50000 | 500000 | 1 | 2099-12-31 | 1 |
| VIP100 | fixed | 100000 | 300000 | 1 | 2099-12-31 | 2 |
| EXPIRED | percent | 20 | 100000 | 1 | 2020-01-01 | 1 |
| INACTIVE_TEST | percent | 10 | 300000 | 0 | 2099-12-31 | 1 |
| EXPIRES_TODAY_TEST | percent | 10 | 300000 | 1 | current fixture date | 1 |
| ZERO_MIN_TEST | percent | 10 | 0 | 1 | 2099-12-31 | 1 |
| EXPIRY_BOUNDARY_TEST | percent | 10 | 300000 | 1 | tomorrow for API-052; yesterday for API-053 | 1 |
| GENERIC_LIMIT_TEST | fixed | 50000 | 300000 | 1 | 2099-12-31 | 3 |
| PERCENT1 | percent | 1 | 0 | 1 | 2099-12-31 | 1 |
| PERCENT100 | percent | 100 | 0 | 1 | 2099-12-31 | 1 |

Nonzero prior-use overrides are reset immediately before their requests:

| Test IDs | Coupon / user | Prior uses |
|---|---|---:|
| API-040 | SAVE10 / 1 | 1 |
| API-041 | SAVE10 / 1 | 2 |
| API-054 | GENERIC_LIMIT_TEST / 1 | 2 |
| API-055 | GENERIC_LIMIT_TEST / 1 | 3 |
| API-056 | GENERIC_LIMIT_TEST / 1 | 4 |
| API-057 | VIP100 / 1 | 1 |
| API-058 | VIP100 / 1 | 2 |
| API-059 | VIP100 / 1 | 3 |
| API-072 | SAVE10 / authenticated user 1 | 1 |

Every other case begins with zero coupon-usage rows. The reset also guarantees that nonexistent, unusual, empty, and injection-like coupon codes do not resolve because only the controlled manifest is present.

## JWT variants

The wrapper supplies deterministic, non-production values for:

- `authToken`: valid HS256 token for user 1, signed with the SUT's configured test secret.
- `limitReachedAuthToken`: valid signed token for user 1, labeled for API-072.
- `invalidToken`: deliberately malformed `not-a-jwt` value.
- `invalidSignatureToken`: well-formed token signed with a different secret.
- `expiredToken`: correctly signed token with `exp=1`.

These values establish the reviewed inputs; whether `/api/apply-coupon` enforces them is a test outcome, not fixture behavior.

## Validate without running the real SUT

From `D:\GitHub\SoftwareTesting-HW06`:

```powershell
C:\Users\xing0\AppData\Local\Python\bin\python.exe postman\validate_pool_b_runtime.py --sut-dir D:\GitHub\eshop-sut
C:\Users\xing0\AppData\Local\Python\bin\python.exe postman\validate_pool_b_targeted_newman.py
C:\Users\xing0\AppData\Local\Python\bin\python.exe .agents\skills\postman-test-generator\scripts\validate_postman_collection.py postman\pool-b-discount-coupons.postman_collection.json postman\postman-v2.1.0-schema.json
```

The first command tests all 74 reset states and restoration against a temporary SQLite database, and opens the existing SUT database read-only for schema validation. The second runs only seven representative collection requests against local fixture/SUT mocks. It is not the full Newman suite and does not contact the real SUT.

## Inspect one case after the SUT is started

Like Pool A, start the SUT before writing fixtures because `database.js` drops and recreates its tables on startup. To apply one state for manual inspection:

```powershell
Set-Location D:\GitHub\eshop-sut\backend
node server.js
# In a second PowerShell:
Set-Location D:\GitHub\SoftwareTesting-HW06
C:\Users\xing0\AppData\Local\Python\bin\python.exe postman\seed_pool_b_fixtures.py --sut-dir D:\GitHub\eshop-sut --test-id API-040 --print-runtime-variables
```

The one-case seeder intentionally leaves that case's controlled state in the test database. Use the wrapped runner for suite execution and automatic restoration.

## Full Newman command for later

Do not invoke the collection with plain `newman run`: the collection intentionally skips a request when the authenticated local fixture controller is absent. When full execution is authorized, start the SUT and use:

```powershell
Set-Location D:\GitHub\SoftwareTesting-HW06
C:\Users\xing0\AppData\Local\Python\bin\python.exe postman\run_pool_b_with_fixtures.py --sut-dir D:\GitHub\eshop-sut --newman-command npx.cmd newman
```

The wrapper performs this sequence:

1. Confirms the real SUT is reachable and its initialized SQLite schema is compatible.
2. Snapshots `coupons`, `coupon_usage`, SQLite sequences, and controlled user rows.
3. Starts an authenticated fixture controller bound to a random localhost port.
4. Supplies controller values and all JWT variants to Newman as runtime variables.
5. Resets and verifies the exact case state before each reviewed request.
6. Requires exactly one reset for each of the 74 reviewed IDs after a successful run.
7. Restores the pre-run database snapshot even if Newman fails or is interrupted normally.

The wrapper does not hide SUT failures: it only establishes reviewed preconditions and returns Newman's exit code.
