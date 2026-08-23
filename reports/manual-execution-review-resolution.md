# Final Manual and Execution-Only Review Resolution

## Scope and decision rule

This review resolves every case that `Main_Report.md` still marked as requiring a manual oracle or as execution-only in Pools A, B, and C. Newman execution status is preserved as historical evidence; the verdict below is the final review verdict.

- `PASS`: the specification/reviewed oracle and the captured execution evidence are sufficient.
- `FAIL`: captured evidence contradicts a specification requirement or an explicitly reviewed human/external oracle.
- `BLOCKED`: a required state, persistence, implementation, timing, or configuration oracle is not present in the available evidence.
- `exploratory`: the specification intentionally supplies no pass/fail oracle; the observed behavior is characterization evidence only.

No HTTP status was treated as a failure by itself, and no state or implementation result was inferred from an HTTP response.

## Pool A — Forgot Password

| Test ID | Final review verdict | Short reasoning |
| --- | --- | --- |
| API-025 | `BLOCKED` | No real OTP-expiry state or observable/configurable expiry point exists; the request was correctly skipped. |
| API-030 | `exploratory` | Extra-property behavior is unspecified; HTTP 200 records acceptance only. |
| API-046 | `FAIL` | Empty password was accepted with 200 although the reviewed weak-password oracle requires rejection. |
| API-047 | `FAIL` | Seven-character password was accepted with 200, contradicting FR-03's eight-character minimum. |
| API-050 | `FAIL` | Password with no uppercase letter was accepted with 200, contradicting FR-03. |
| API-052 | `FAIL` | Password with no lowercase letter was accepted with 200, contradicting FR-03. |
| API-055 | `FAIL` | Password with no digit was accepted with 200, contradicting FR-03. |
| API-057 | `FAIL` | Password with no listed special character was accepted with 200, contradicting FR-03. |
| API-063 | `BLOCKED` | HTTP 200 was observed, but no captured password-change or OTP-invalidation evidence completes the state oracle. |
| API-065 | `BLOCKED` | The required expired state cannot be established because the SUT exposes no expiry state/check. |
| API-067 | `FAIL` | Weak-password guard returned 200 instead of rejection; this already contradicts the case before unavailable preservation checks matter. |
| API-069 | `BLOCKED` | HTTP 400 proves rejection only; protected-account/storage effects and parameterized-query use were not captured. |
| API-070 | `BLOCKED` | HTTP 200 proves response success only; intended password replacement and one-time OTP consumption were not captured. |
| API-071 | `BLOCKED` | HTTP 400 proves cross-email rejection only; evidence that neither password changed is unavailable. |
| API-072 | `BLOCKED` | The required expired state cannot be established because the SUT exposes no expiry state/check. |
| API-073 | `BLOCKED` | Replay returned 400, but the helper response and retained-password state needed by the full oracle are unavailable. |
| API-074 | `BLOCKED` | The short token returned 400, but unchanged-password evidence was not captured. |
| API-075 | `BLOCKED` | No authoritative abuse-control threshold or rate limiter exists, so the designed guessing test cannot produce a verdict. |
| API-076 | `BLOCKED` | Failure representations matched, but password/token/account-metadata side effects were not captured and no timing tolerance exists. |
| API-078 | `FAIL` | The reviewed robustness oracle requires a safe 4xx; step 1 returned 500. Step 2's 200 confirms the OTP was not consumed. |
| API-081 | `BLOCKED` | Both resets succeeded and Account B remained usable, but no implementation/database evidence proves parameterized password storage. |

Pool A totals: **0 PASS, 8 FAIL, 12 BLOCKED, 1 exploratory**.

Already-completed manual cases `API-068` (FAIL by direct plaintext-storage inspection) and `API-077` (PASS by synchronized concurrency harness) remain unchanged and are not counted as remaining reviews.

## Pool B — Discount Coupons

| Test ID | Final review verdict | Short reasoning |
| --- | --- | --- |
| API-004 | `exploratory` | Alternate-method rejection status is unspecified; 404 is characterization only. |
| API-005 | `exploratory` | Malformed-JSON handling has no specified status/body oracle; 400 is characterization only. |
| API-006 | `exploratory` | Non-object top-level handling is unspecified; 400 is characterization only. |
| API-007 | `exploratory` | `code` requiredness/default behavior is unspecified; 400 is characterization only. |
| API-008 | `exploratory` | Non-string `code` coercion and status are unspecified; 404 is characterization only. |
| API-009 | `exploratory` | `total_amount` requiredness/default behavior is unspecified; 400 is characterization only. |
| API-010 | `exploratory` | Numeric-string coercion is unspecified; 200 records acceptance only. |
| API-011 | `exploratory` | Omitted `user_id` behavior and JWT/body identity rules are unspecified; 200 records acceptance only. |
| API-012 | `exploratory` | String `user_id` coercion is unspecified; 200 records acceptance only. |
| API-013 | `FAIL` | A request without JWT returned a successful discounted calculation, contradicting FR-09 C4. |
| API-014 | `FAIL` | A known-invalid JWT returned a successful discounted calculation, contradicting FR-09 C4. |
| API-015 | `exploratory` | Additional-property behavior is unspecified; 200 records acceptance only. |
| API-017 | `exploratory` | Array-body handling is unspecified; 400 is characterization only. |
| API-018 | `exploratory` | Malformed-JSON response details are unspecified; 400 is characterization only. |
| API-019 | `exploratory` | Extra-member handling is unspecified; 200 records acceptance only. |
| API-020 | `FAIL` | The no-JWT domain variant was applied successfully, contradicting FR-09 C4. |
| API-021 | `FAIL` | The invalid-JWT domain variant was applied successfully, contradicting FR-09 C4. |
| API-023 | `PASS` | Nonexistent coupon is nonqualifying under FR-09 C1 and no successful calculation was returned. |
| API-024 | `PASS` | Inactive coupon is nonqualifying under FR-09 C1 and no successful calculation was returned. |
| API-025 | `PASS` | At expiry equality, the coupon was not applied, matching FR-09 C2's strict-before rule. |
| API-026 | `PASS` | The expired coupon was not applied, matching FR-09 C2. |
| API-027 | `exploratory` | Arbitrary-code syntax/handling is unspecified; 404 is characterization only. |
| API-028 | `exploratory` | Case and whitespace normalization are unspecified; 404 is characterization only. |
| API-029 | `exploratory` | Null-code type/coercion handling is unspecified; 400 is characterization only. |
| API-030 | `exploratory` | Numeric-code type/coercion handling is unspecified; 404 is characterization only. |
| API-032 | `PASS` | Below-minimum total was not applied, matching FR-09 C3. |
| API-034 | `PASS` | Negative total was not applied, matching FR-09 C3. |
| API-035 | `FAIL` | Observed `-4500005` discount and `5000005.5` final amount contradict the documented 10% formulas. |
| API-036 | `exploratory` | Numeric-string `total_amount` coercion is unspecified; 200 records acceptance only. |
| API-037 | `exploratory` | Null-total handling is unspecified; 400 is characterization only. |
| API-038 | `exploratory` | Boolean-total handling is unspecified; 400 is characterization only. |
| API-039 | `exploratory` | Non-JSON numeric-token handling is unspecified; 400 is characterization only. |
| API-040 | `PASS` | Usage exactly at the limit was denied, matching FR-09 C5's strict-less-than condition. |
| API-041 | `PASS` | Usage above the limit was denied, matching FR-09 C5. |
| API-042 | `exploratory` | JWT-subject/body-user binding is unspecified; 200 records the SUT's body-driven behavior. |
| API-043 | `exploratory` | Nonexistent-body-user behavior is unspecified; 200 is characterization only. |
| API-044 | `exploratory` | Fractional `user_id` validation/coercion is unspecified; 200 is characterization only. |
| API-045 | `exploratory` | Null `user_id` validation/coercion is unspecified; 200 is characterization only. |
| API-046 | `exploratory` | String `user_id` validation/coercion is unspecified; 200 is characterization only. |
| API-047 | `FAIL` | Observed `-2700009` discount and `3000010` final amount contradict the documented formulas. |
| API-048 | `PASS` | Just-below BIGBUY minimum was denied, matching FR-09 C3. |
| API-050 | `PASS` | Just-below zero minimum was denied, matching FR-09 C3. |
| API-053 | `PASS` | One day after expiry, the coupon was denied, matching FR-09 C2. |
| API-055 | `PASS` | Usage exactly at the configured maximum was denied, matching FR-09 C5. |
| API-056 | `PASS` | Usage above the configured maximum was denied, matching FR-09 C5. |
| API-058 | `PASS` | Usage exactly at the configured maximum was denied, matching FR-09 C5. |
| API-059 | `PASS` | Usage above the configured maximum was denied, matching FR-09 C5. |
| API-065 | `BLOCKED` | The 404 response proves no successful calculation, but query structure, diagnostics, and persistent effects require absent inspection evidence. |
| API-066 | `BLOCKED` | The 404 response proves no successful calculation, but multi-statement prevention and persistent state require absent inspection evidence. |
| API-072 | `exploratory` | JWT/body identity scoping is not specified; the historical rejection assertion was withdrawn and 200 is characterization only. |

Pool B totals: **15 PASS, 6 FAIL, 2 BLOCKED, 27 exploratory**.

## Pool C — Admin Order Management

| Test ID | Final review verdict | Short reasoning |
| --- | --- | --- |
| API-002 | `exploratory` | Alternate-method behavior is unspecified; 404 is characterization only. |
| API-003 | `exploratory` | Altered-route behavior is unspecified; 404 is characterization only. |
| API-004 | `exploratory` | Nonexistent-ID response is unspecified; 404 is characterization only. |
| API-009 | `exploratory` | Malformed-JSON response behavior is unspecified; 400 is characterization only. |
| API-010 | `exploratory` | Non-object-body behavior is unspecified; 400 is characterization only. |
| API-011 | `exploratory` | Omitted-body status is unspecified; the observed 500 is a robustness observation, not a specification verdict. |
| API-012 | `exploratory` | Omitted-status requiredness/default behavior is unspecified; 400 is characterization only. |
| API-013 | `exploratory` | Nullability is unspecified; 400 is characterization only. |
| API-014 | `exploratory` | Non-string type/coercion behavior is unspecified; 400 is characterization only. |
| API-016 | `exploratory` | Additional-property behavior is unspecified; 200 records acceptance only. |
| API-017 | `exploratory` | Duplicate-key resolution is unspecified; 200 records observed parser behavior only. |
| API-022 | `exploratory` | Same-state transition behavior is unspecified; 400 is characterization only. |
| API-023 | `exploratory` | Omitted-Content-Type behavior is unspecified; 200 records acceptance only. |
| API-026 | `exploratory` | Nonexistent-ID response is unspecified; 404 is characterization only. |
| API-027 | `exploratory` | Omitted-ID routing behavior is unspecified; 404 is characterization only. |
| API-028 | `exploratory` | Text-ID validation behavior is unspecified; 404 is characterization only. |
| API-029 | `exploratory` | Literal-`null` ID behavior is unspecified; 404 is characterization only. |
| API-041 | `exploratory` | Status case normalization is unspecified; 400 records rejection only. |
| API-042 | `exploratory` | Status nullability is unspecified; 400 records rejection only. |
| API-043 | `exploratory` | Status type/coercion is unspecified; 400 records rejection only. |
| API-044 | `exploratory` | Status requiredness/default behavior is unspecified; 400 records rejection only. |
| API-045 | `exploratory` | Absent-body behavior is unspecified; 400 is characterization only. |
| API-046 | `exploratory` | Malformed-JSON behavior is unspecified; 400 is characterization only. |
| API-047 | `exploratory` | Non-object-body behavior is unspecified; 400 is characterization only. |
| API-048 | `exploratory` | Additional-property behavior is unspecified; 200 records acceptance only. |
| API-049 | `exploratory` | Duplicate-key resolution is unspecified; 400 records observed parser behavior only. |
| API-080 | `FAIL` | The reviewed human robustness oracle requires a safe 4xx; text/plain produced 500 and an unhandled exception. State evidence shows no step-1 mutation and a successful JSON retry. |

Pool C totals: **0 PASS, 1 FAIL, 0 BLOCKED, 26 exploratory**.

## Consolidated result

All 98 remaining reviews now have an explicit final disposition: **15 PASS, 15 FAIL, 14 BLOCKED, and 54 exploratory**. `BLOCKED` is used only where the case's required evidence is absent; it is not an SUT failure. `exploratory` records observed behavior without turning an unspecified requirement into a conformance oracle.
