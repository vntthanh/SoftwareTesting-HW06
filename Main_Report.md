# HW06-AI — API Testing Main Report

## 1. Student and Assignment Information

| Field | Value |
| --- | --- |
| Student ID | 23127261 |
| Student name | Vương Ngũ Tín Thành |
| Class | 23KTPM2 |
| Assignment | HW06-AI — API Testing |
| System under test | EShop |
| SUT repository | <https://github.com/ttbhanh/eshop-sut> |
| Submission repository | <https://github.com/vntthanh/SoftwareTesting-HW06> |
| Report date | 2026-08-18 |
| Last updated | 2026-08-22 |

## 2. Selected APIs

| Pool | Feature | Selected API | Main Testing Focus |
| --- | --- | --- | --- |
| A | FR-03 – Forgot Password / Password Reset | `POST /api/reset-password` | Input validation, reset-token behavior, password rules, security |
| B | FR-09 – Discount Coupons | `POST /api/apply-coupon` | Coupon eligibility, amount boundaries, user constraints, calculation |
| C | FR-18 – Admin Order Management | `PUT /api/admin/orders/:id/status` | Authorization, order-state transitions, invalid transitions |

## 3. Agent Skills

### 3.1. Agent Skills Overall

| Component | Type | Responsibility |
| --- | --- | --- |
| **API Test Generator** | Coordinator | Coordinates the complete API test-generation process and combines results |
| **Domain Test Generator** | Specialized generator | Performs equivalence partitioning and Boundary Value Analysis |
| **State Transition Test Generator** | Specialized generator | Models states and valid/invalid transitions when applicable |
| **Security Test Generator** | Specialized generator | Derives security tests from applicable SEC-01–SEC-07 requirements |
| **Contract Test Generator** | Specialized generator | Validates request and response contracts/schema |
| **AI Audit** | Reused supporting skill | Records AI interactions and file modifications into the AI Audit Report |

The first five components form the **AI-driven API Test Generator architecture** designed for HW06.

The **AI Audit** skill (reused from homework `HW05-AI`) operates alongside this architecture. It records the AI-assisted workflow so that the generation, review, correction, and implementation activities remain auditable.

### 3.2. Skills Design

The design artifacts for the **API Test Generator** and its four specialized generators are stored in the `skills-design/` folder. Each generator has its own subfolder containing its design specification and corresponding diagram.

The **AI Audit** skill is not included in this folder because it is a reusable skill carried over from HW05.

## Pool A: Forgot Password

### A.1. Introduction

Pool A covers **FR-03 – Forgot Password / Password Reset**. This report selects `POST /api/reset-password`, which resets a user's password using an email address, reset token, and new password.

### A.2. Contractual Testing Analysis

The selected endpoint is documented as `POST /api/reset-password` with a JSON body containing three top-level fields:

| Field | Documented representation | Reviewed constraint |
| --- | --- | --- |
| `email` | JSON string | Required for account identification and OTP-to-email binding |
| `resetToken` | JSON string | Required; represents the six-digit OTP generated during step 1 |
| `newPassword` | JSON string | Required; must satisfy the FR-01 password-strength rules incorporated by FR-03 |

The reviewed contract model contains rules `CR-001`–`CR-012`. It covers the method and path, JSON-object representation, documented member set, string representations, OTP/email binding, password strength, OTP expiry, one-time use, the combined valid request, and the absence of a documented response schema.

The API specification does not define response statuses or bodies for this endpoint. The reviewed test model therefore labels `Content-Type: application/json`, `200 OK` for a normal successful reset, and `400 Bad Request` for invalid request data as external HTTP testing assumptions. It does not invent response messages, response fields, validation precedence, or parser behavior beyond the reviewed assumptions.

FR-03 requires a confirmation-password value at workflow/UI level, but the endpoint body does not document such a field. Consequently, `CR-008` remains unresolved for direct API testing: no `confirmPassword`-style property was invented. The complete analysis is stored in [`review/pool-a/reports/contract-report.md`](review/pool-a/reports/contract-report.md).

### A.3. Domain Testing Analysis

Domain analysis uses the documented example as a value baseline and adds the required workflow state: a registered email, a six-digit OTP issued for that same email, an unexpired and unused OTP, and a conforming new password. Tests vary one input factor at a time where possible.

The reviewed model defines 26 equivalence partitions (`DP-001`–`DP-026`) across the JSON container and the three body fields. Important partitions include:

- valid and malformed/non-object JSON containers;
- missing, `null`, and wrong-type values for all three required fields;
- registered, unregistered, malformed, empty, and OTP-mismatched email values;
- OTP values below, at, and above six digits; non-decimal, wrong-type, omitted, and unissued values;
- passwords that meet all rules or separately omit uppercase, lowercase, digit, allowed special character, or minimum length.

Six boundary models (`DB-001`–`DB-006`) cover OTP length, password length, and the minimum counts of uppercase, lowercase, digit, and allowed-special characters. No unsupported maximum lengths, email boundaries, or concrete OTP lifetime were inferred.

Additional JSON properties remain exploratory because the specification defines no accept/reject oracle (`API-030`). Conversely, `Aa1!bbbb#` is valid (`API-059`) because it satisfies every explicit password rule through `A`, lowercase letters, `1`, and the allowed `!`; no requirement prohibits the additional `#`. The complete analysis is stored in [`review/pool-a/reports/domain-report.md`](review/pool-a/reports/domain-report.md).

### A.4. State Transition Testing Analysis

State-transition testing is applicable because FR-03 and SEC-07 define an OTP lifecycle. The reviewed model contains three normalized states:

| State | Meaning |
| --- | --- |
| `ST-01` | OTP is usable, unexpired, unused, and bound to the requesting email |
| `ST-02` | OTP has passed the real SUT expiry point and is no longer usable |
| `ST-03` | OTP was used successfully and invalidated |

Five transitions/guard failures (`TR-001`–`TR-005`) cover successful reset and OTP invalidation, cross-email OTP use, expired OTP use, replay after successful use, and weak-password rejection. The reviewed `TR-005` decision preserves the usable OTP and leaves the old password unchanged when password validation fails.

Expiry tests do not assume a lifetime, clock, boundary, or grace period. They execute only when the real SUT expiry point can be configured or objectively observed; otherwise, the case is recorded as `BLOCKED / NOT EXECUTABLE`, not as a product failure. The complete analysis is stored in [`review/pool-a/reports/state-report.md`](review/pool-a/reports/state-report.md).

### A.5. Security Testing Analysis

All supplied requirements `SEC-01`–`SEC-07` were evaluated for this endpoint:

| Requirement | Applicability and treatment |
| --- | --- |
| `SEC-01` | Applicable: the reset password must not be stored in plaintext. Verification is explicitly white-box/storage-level because Postman alone cannot prove persistence behavior. |
| `SEC-02` | Not applicable under the reviewed recovery model: the OTP is the recovery credential and no JWT is required for this unauthenticated endpoint. |
| `SEC-03` | Not applicable: this is not an Admin API. |
| `SEC-04` | No direct API scenario: the sources define no response-reflection or UI-rendering sink for the submitted values. |
| `SEC-05` | Conditionally applicable: inert SQL/query metacharacters must not bypass reset controls, affect another account, reveal database information, or cause unexpected failure. Full parameterization proof may require implementation inspection. |
| `SEC-06` | Not applicable: this is not a profile-update API and has no documented `role` input. |
| `SEC-07` | Directly applicable: the OTP is six digits, email-bound, expiring, and invalidated after successful use. |

The security model contains nine scenarios (`SS-001`–`SS-009`). In addition to SEC-01, SEC-05, and SEC-07 coverage, the reviewed model includes two external best-practice scenarios: automated-guessing resistance and account-enumeration resistance. The guessing test runs only when an authoritative configured abuse-control limit is known and never invents a threshold. The enumeration test compares the same `400` status, semantic JSON body (or exact non-JSON body), content type, redirect behavior, password/token/account-metadata side effects, and treats timing as informational unless an approved tolerance exists.

The complete analysis is stored in [`review/pool-a/reports/security-report.md`](review/pool-a/reports/security-report.md).

### A.6. AI-Generated Test Cases

The final reviewed test cases for this pool are stored in: [`test-cases/a-forgot-password.csv`](test-cases/a-forgot-password.csv)

The test cases were derived from the reviewed analyses in Sections A.2–A.5.

| Testing Type | Number of Test Cases |
| --- | ---: |
| Contractual Testing | 26 |
| Domain Testing | 36 |
| State Transition Testing | 5 |
| Security Testing | 9 |
| **Total** | **76** |

The suite uses stable IDs `API-001`–`API-082` and exactly nine traceability fields per record. Every case targets `POST /api/reset-password`. The 76 specialist-generated cases retain their provisional specialist IDs in `Assumptions / Notes`; `API-077`–`API-082` are the six human-authored additions documented in Section A.7. Validation found no missing fields, duplicate IDs, endpoint/category mismatches, or unexpected logical cases. Coverage includes `CR-001`–`CR-007`, `CR-009`–`CR-012`, `DP-001`–`DP-026`, `DB-001`–`DB-006`, `TR-001`–`TR-005`, and `SS-001`–`SS-009`; `CR-008` is explicitly unresolved because confirmation-password transport is not documented.

Eight specialist-generated cases were revised after review: `API-025`, `API-030`, `API-059`, `API-065`, `API-068`, `API-072`, `API-075`, and `API-076`. These revisions clarified exploratory behavior, valid additional password characters, observable/configurable expiry preconditions, white-box storage verification, configured rate limits, and account-enumeration comparison rules. Six human-authored cases were then added as `API-077`–`API-082`. Revalidation preserved all 82 IDs and coverage.

Pool A execution fixtures are seeded only after the SUT starts, because the SUT recreates its SQLite schema on startup. The idempotent fixture script opens `backend/database.sqlite` directly (without importing SUT `database.js`), creates dedicated deterministic accounts and exact TEXT OTPs, and never calls `/api/forgot-password`. Expiry cases `API-025`, `API-065`, and `API-072` remain blocked because the actual SUT has no expiry state/check; `API-075` remains blocked because it has no rate limiter or authoritative threshold; and `API-077` remains manual because sequential Postman/Newman cannot establish its concurrency barrier.

### A.7. Human Cases

| ID | Category | Test case | Expected result | Notes |
| --- | --- | --- | --- | --- |
| **API-077** | STATE | Send **two concurrent** reset requests with the same email/OTP but different valid new passwords. | Exactly **one succeeds**; the other is rejected. The OTP must authorize only one reset. | Previous AI tested sequential replay but explicitly did not test concurrency. |
| **API-078** | CONTRACT | Send otherwise valid JSON text using `Content-Type: text/plain`. Then retry normally with the same OTP using `application/json`. | The first response is any `4xx` client-error status and does not consume the OTP; statuses outside `400`–`499` are not accepted. `415 Unsupported Media Type` is the human/external HTTP expectation, but any safe `4xx` rejection, including `400 Bad Request`, is acceptable when the OTP remains intact. The second request succeeds. | The specification documents a JSON body but no response status for this endpoint; both the accepted `4xx` class and preferred `415` are human/external HTTP expectations, not specification requirements. |
| **API-079** | CONTRACT | Send `Content-Type: application/json` with an **empty HTTP body**. Then retry with a valid request using the same OTP. | Empty request returns `400`, not `5xx`; OTP remains usable and the valid retry succeeds. | Previous tests omit individual fields but do not exercise the completely missing body before destructuring. |
| **API-080** | DOMAIN | With a valid email/OTP, send `newPassword` as an object: `{"value":"Aa1!aaaa"}`. Then retry with a valid string using the same OTP. | First request returns `400`, not `5xx`, and does not consume the OTP. Second request succeeds. | Previous AI used a number as its representative non-string value. |
| **API-081** | SECURITY | Account A: reset using a valid OTP and a password containing SQL syntax while still meeting password rules, e.g. `Aa1!';DROP TABLE users;--`. Then use a valid OTP for Account B in another reset request. | A's password is treated only as data; its reset succeeds normally. B's reset also succeeds, proving the injected password did not damage the users data path. | Existing SQL-injection testing attacks `email` only. The `newPassword` field could also be attacked. |
| **API-082** | SECURITY | Send a valid reset request with an invalid/garbage `Authorization: Bearer ...` header. | Reset still succeeds with `200`; an invalid JWT must not affect this public recovery endpoint. | JWT is not applicable but we should test the case where a bad JWT header is actually present. |

The AI missed these cases mainly because the initial generation focused on test cases that could be derived directly from the API specification. Concurrency and server-side persistence require deeper execution and state reasoning, so cases such as simultaneous OTP reuse were not identified.

Alternative JSON input representations were also under-sampled because the domain analysis focused on representative equivalence partitions rather than different structural representations of the same input. In addition, the initial security analysis used representative SQL injection cases but did not systematically apply them to every client-controlled field.

These gaps show that specification-based AI generation can provide wide coverage, but human review is necessary to identify execution-dependent, state-dependent, and less obvious security cases.

### A.8. Newman Execution Analysis

#### Run summary

| Metric | Normalized result |
| --- | --- |
| Collection | `Pool A - Reset Password Reviewed Tests` |
| Execution window | 2026-08-22 12:42:53.158 to 12:43:00.739 (GMT+7) |
| Duration | 7.581 seconds |
| Intended collection leaf requests | 88 |
| Total requests | 85 (Newman `run.stats`; 82 executed collection leaf requests plus 3 pre-request helper calls) |
| Logical test cases | 82 total: 77 with an observed execution and 5 explicitly blocked before request dispatch |
| Assertions | 82 total: 59 passed, 23 failed, 0 pending/skipped |
| Request errors | 0 |
| Pre-request script errors | 0 |
| Test script errors | 0 |
| Logical cases with failed automated assertions | 22 |
| Logical execution statuses | `PASS`: 55; `FAIL_ASSERTION`: 22; `FAIL_MANUAL`: 1; `BLOCKED_NOT_EXECUTED`: 4; `REQUEST_ERROR`: 0; `RUNTIME_ERROR`: 0; `NOT_EXECUTED`: 0 |
| Manual oracle requirements | 23 logical cases explicitly retain a manual, white-box, state/side-effect, concurrency, or data-driven check |

HTTP 4xx/5xx responses are classified only through their automated assertions; they are not treated as failures by status code alone. Failed assertions below are execution evidence, not defect diagnoses.

#### Logical test-case outcomes

| Test ID | Execution Status | Request / Flow Step | HTTP Status | Assertion Result | Failure / Error Message | Manual Oracle Required | Execution Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| API-001 | `PASS` | Verify the documented method, path, JSON-object member representations, and reviewed successful-reset response oracle with a fully valid reset request. | 200 OK | PASS — API-001 - reviewed status is 200 | N/A | NO | Matched by immutable item ID; one execution observed. |
| API-002 | `PASS` | Verify that malformed JSON is treated as invalid request data under the reviewed validation model. | 400 Bad Request | PASS — API-002 - reviewed status is 400 | N/A | NO | Matched by immutable item ID; one execution observed. |
| API-003 | `PASS` | Verify that a syntactically valid non-object JSON body is treated as invalid request data. | 400 Bad Request | PASS — API-003 - reviewed status is 400 | N/A | NO | Matched by immutable item ID; one execution observed. |
| API-004 | `PASS` | Verify that omission of reviewed-required member email is rejected. | 400 Bad Request | PASS — API-004 - reviewed status is 400 | N/A | NO | Matched by immutable item ID; one execution observed. |
| API-005 | `PASS` | Verify that null is rejected for reviewed-required string member email. | 400 Bad Request | PASS — API-005 - reviewed status is 400 | N/A | NO | Matched by immutable item ID; one execution observed. |
| API-006 | `PASS` | Verify that a non-string JSON value is rejected for email without coercion. | 400 Bad Request | PASS — API-006 - reviewed status is 400 | N/A | NO | Matched by immutable item ID; one execution observed. |
| API-007 | `PASS` | Verify that omission of reviewed-required member resetToken is rejected. | 400 Bad Request | PASS — API-007 - reviewed status is 400 | N/A | NO | Matched by immutable item ID; one execution observed. |
| API-008 | `PASS` | Verify that null is rejected for reviewed-required string member resetToken. | 400 Bad Request | PASS — API-008 - reviewed status is 400 | N/A | NO | Matched by immutable item ID; one execution observed. |
| API-009 | `FAIL_ASSERTION` | Verify that a valid issued resetToken value is rejected when represented as a JSON number rather than a string. | 200 OK | FAIL — API-009 - reviewed status is 400 | expected response to have status code 400 but got 200 | NO | Matched by immutable item ID; one execution observed. |
| API-010 | `PASS` | Verify rejection of a five-digit token that does not meet the reviewed exact six-decimal-digit workflow shape. | 400 Bad Request | PASS — API-010 - reviewed status is 400 | N/A | NO | Matched by immutable item ID; one execution observed. |
| API-011 | `PASS` | Verify rejection of a seven-digit token under the reviewed exact six-decimal-digit reset workflow rule. | 400 Bad Request | PASS — API-011 - reviewed status is 400 | N/A | NO | Matched by immutable item ID; one execution observed. |
| API-012 | `PASS` | Verify rejection of a six-character token containing a non-decimal character. | 400 Bad Request | PASS — API-012 - reviewed status is 400 | N/A | NO | Matched by immutable item ID; one execution observed. |
| API-013 | `PASS` | Verify that an issued six-digit OTP beginning with zero remains valid through the documented string representation. | 200 OK | PASS — API-013 - reviewed status is 200 | N/A | NO | Matched by immutable item ID; one execution observed. |
| API-014 | `PASS` | Verify rejection of a well-shaped six-digit token that was not issued for the submitted reset workflow. | 400 Bad Request | PASS — API-014 - reviewed status is 400 | N/A | NO | Matched by immutable item ID; one execution observed. |
| API-015 | `PASS` | Verify that a valid OTP issued for one email cannot be paired with a different email. | 400 Bad Request | PASS — API-015 - reviewed status is 400 | N/A | NO | Matched by immutable item ID; one execution observed. |
| API-016 | `FAIL_ASSERTION` | Verify that omission of reviewed-required member newPassword is rejected. | 200 OK | FAIL — API-016 - reviewed status is 400 | expected response to have status code 400 but got 200 | NO | Matched by immutable item ID; one execution observed. |
| API-017 | `FAIL_ASSERTION` | Verify that null is rejected for reviewed-required string member newPassword. | 200 OK | FAIL — API-017 - reviewed status is 400 | expected response to have status code 400 but got 200 | NO | Matched by immutable item ID; one execution observed. |
| API-018 | `FAIL_ASSERTION` | Verify that a non-string JSON value is rejected for newPassword without coercion. | 200 OK | FAIL — API-018 - reviewed status is 400 | expected response to have status code 400 but got 200 | NO | Matched by immutable item ID; one execution observed. |
| API-019 | `PASS` | Verify acceptance of a password at the documented minimum length that contains every required character class. | 200 OK | PASS — API-019 - reviewed status is 200 | N/A | NO | Matched by immutable item ID; one execution observed. |
| API-020 | `FAIL_ASSERTION` | Verify rejection of a seven-character password even when all required character classes are present. | 200 OK | FAIL — API-020 - reviewed status is 400 | expected response to have status code 400 but got 200 | NO | Matched by immutable item ID; one execution observed. |
| API-021 | `FAIL_ASSERTION` | Verify rejection of an otherwise conforming password that lacks an uppercase letter. | 200 OK | FAIL — API-021 - reviewed status is 400 | expected response to have status code 400 but got 200 | NO | Matched by immutable item ID; one execution observed. |
| API-022 | `FAIL_ASSERTION` | Verify rejection of an otherwise conforming password that lacks a lowercase letter. | 200 OK | FAIL — API-022 - reviewed status is 400 | expected response to have status code 400 but got 200 | NO | Matched by immutable item ID; one execution observed. |
| API-023 | `FAIL_ASSERTION` | Verify rejection of an otherwise conforming password that lacks a digit. | 200 OK | FAIL — API-023 - reviewed status is 400 | expected response to have status code 400 but got 200 | NO | Matched by immutable item ID; one execution observed. |
| API-024 | `FAIL_ASSERTION` | Verify rejection of a password whose only punctuation is outside the allowed special-character set. | 200 OK | FAIL — API-024 - reviewed status is 400 | expected response to have status code 400 but got 200 | NO | Matched by immutable item ID; one execution observed. |
| API-025 | `BLOCKED_NOT_EXECUTED` | Verify that an expired OTP cannot satisfy the reset request contract. | N/A | N/A — not executed | N/A | YES — A real OTP expiry point must be configured or objectively observed; the SUT has no expiry state/check. | Explicit pre-request skip: SUT has no OTP expiry state or check. No SUT verdict was produced. |
| API-026 | `PASS` | Setup: pre-request first-use reset (`pm.sendRequest`, expected HTTP 200)<br>Verify that an OTP already used in a successful reset cannot satisfy a second reset request. | Setup: unavailable in detailed execution rows<br>400 Bad Request | Setup: no Newman assertion<br>PASS — API-026 - reviewed status is 400 | N/A | NO | The pre-request helper call is included in Newman’s request total but has no separate response record. Two identical main-execution rows (same cursor, request, response, and assertion) were correlated as one observed main step. |
| API-078 | `FAIL_ASSERTION` | Step 1: Verify that otherwise valid JSON text sent as text/plain receives a 4xx client-error response and is rejected without consuming the OTP. [Step 1 - text/plain]<br>Step 2: Verify that otherwise valid JSON text sent as text/plain receives a 4xx client-error response and is rejected without consuming the OTP. [Step 2 - JSON retry] | Step 1: 500 Internal Server Error<br>Step 2: 200 OK | Step 1: FAIL — API-078 - text/plain response is 4xx<br>Step 2: PASS — API-078 - reviewed status is 200 | Step 1: expected 500 to be within 400..499 | YES — Metadata retains manual review of the external HTTP expectation and OTP-state evidence after the text/plain attempt. | Matched all 2 ordered collection steps by immutable item ID. |
| API-079 | `PASS` | Step 1: Verify that an empty application/json request body is rejected safely without consuming the OTP. [Step 1 - empty body]<br>Step 2: Verify that an empty application/json request body is rejected safely without consuming the OTP. [Step 2 - valid retry] | Step 1: 400 Bad Request<br>Step 2: 200 OK | Step 1: PASS — API-079 - reviewed status is 400<br>Step 2: PASS — API-079 - reviewed status is 200 | N/A | NO | Matched all 2 ordered collection steps by immutable item ID. |
| API-027 | `PASS` | Verify the documented JSON object shape with a registered email, its usable six-digit OTP, and a conforming password. | 200 OK | PASS — API-027 - reviewed status is 200 | N/A | NO | Matched by immutable item ID; one execution observed. |
| API-028 | `PASS` | Verify rejection of a well-formed JSON request whose top-level value is an array rather than an object. | 400 Bad Request | PASS — API-028 - reviewed status is 400 | N/A | NO | Matched by immutable item ID; one execution observed. |
| API-029 | `PASS` | Verify rejection of a malformed JSON request body. | 400 Bad Request | PASS — API-029 - reviewed status is 400 | N/A | NO | Matched by immutable item ID; one execution observed. |
| API-030 | `PASS` | EXPLORATORY/CHARACTERIZATION: Record how the endpoint handles an additional JSON member while all documented members remain valid. | 200 OK | NO_AUTOMATED_ASSERTIONS | N/A | YES — Exploratory characterization has no specified automated status oracle; manually review the recorded behavior. | Matched by immutable item ID. The HTTP exchange completed, but PASS denotes execution only because no automated behavior oracle ran. |
| API-031 | `PASS` | Verify that an OTP cannot be used with a different registered email. | 400 Bad Request | PASS — API-031 - reviewed status is 400 | N/A | NO | Matched by immutable item ID; one execution observed. |
| API-032 | `PASS` | Verify handling of a syntactically ordinary email address that is not registered. | 400 Bad Request | PASS — API-032 - reviewed status is 400 | N/A | NO | Matched by immutable item ID; one execution observed. |
| API-033 | `PASS` | Verify rejection of a clearly malformed email string without imposing a restrictive email regex. | 400 Bad Request | PASS — API-033 - reviewed status is 400 | N/A | NO | Matched by immutable item ID; one execution observed. |
| API-034 | `PASS` | Verify rejection of an empty email string. | 400 Bad Request | PASS — API-034 - reviewed status is 400 | N/A | NO | Matched by immutable item ID; one execution observed. |
| API-035 | `PASS` | Verify rejection when the required email member is omitted. | 400 Bad Request | PASS — API-035 - reviewed status is 400 | N/A | NO | Matched by immutable item ID; one execution observed. |
| API-036 | `PASS` | Verify rejection when email is JSON null. | 400 Bad Request | PASS — API-036 - reviewed status is 400 | N/A | NO | Matched by immutable item ID; one execution observed. |
| API-037 | `PASS` | Verify rejection when email has a non-string JSON type. | 400 Bad Request | PASS — API-037 - reviewed status is 400 | N/A | NO | Matched by immutable item ID; one execution observed. |
| API-038 | `PASS` | Verify rejection of an empty resetToken string. | 400 Bad Request | PASS — API-038 - reviewed status is 400 | N/A | NO | Matched by immutable item ID; one execution observed. |
| API-039 | `PASS` | Verify the just-below OTP length boundary with five decimal digits. | 400 Bad Request | PASS — API-039 - reviewed status is 400 | N/A | NO | Matched by immutable item ID; one execution observed. |
| API-040 | `PASS` | Verify the just-above exact OTP length boundary with seven decimal digits. | 400 Bad Request | PASS — API-040 - reviewed status is 400 | N/A | NO | Matched by immutable item ID; one execution observed. |
| API-041 | `PASS` | Verify rejection of a six-character resetToken containing a non-decimal character. | 400 Bad Request | PASS — API-041 - reviewed status is 400 | N/A | NO | Matched by immutable item ID; one execution observed. |
| API-042 | `PASS` | Verify rejection when the required resetToken member is omitted. | 400 Bad Request | PASS — API-042 - reviewed status is 400 | N/A | NO | Matched by immutable item ID; one execution observed. |
| API-043 | `PASS` | Verify rejection when resetToken is JSON null. | 400 Bad Request | PASS — API-043 - reviewed status is 400 | N/A | NO | Matched by immutable item ID; one execution observed. |
| API-044 | `FAIL_ASSERTION` | Verify rejection when a valid issued resetToken value is represented as a JSON number rather than a string. | 200 OK | FAIL — API-044 - reviewed status is 400 | expected response to have status code 400 but got 200 | NO | Matched by immutable item ID; one execution observed. |
| API-045 | `PASS` | Verify rejection of a well-formed six-digit token that was not issued for the baseline email. | 400 Bad Request | PASS — API-045 - reviewed status is 400 | N/A | NO | Matched by immutable item ID; one execution observed. |
| API-046 | `FAIL_ASSERTION` | Verify rejection of an empty newPassword string. | 200 OK | FAIL — API-046 - reviewed status is 400 | expected response to have status code 400 but got 200 | YES — Verify that the password is unchanged and the OTP remains usable after rejection. | Matched by immutable item ID; one execution observed. |
| API-047 | `FAIL_ASSERTION` | Verify the just-below password length boundary with a seven-character password that otherwise contains all required classes. | 200 OK | FAIL — API-047 - reviewed status is 400 | expected response to have status code 400 but got 200 | YES — Verify that the password is unchanged and the OTP remains usable after rejection. | Matched by immutable item ID; one execution observed. |
| API-048 | `PASS` | Verify the eight-character password boundary with exactly one uppercase, one digit, and one allowed special character. | 200 OK | PASS — API-048 - reviewed status is 200 | N/A | NO | Matched by immutable item ID; one execution observed. |
| API-049 | `PASS` | Verify the just-above password length boundary with nine characters while all composition rules remain satisfied. | 200 OK | PASS — API-049 - reviewed status is 200 | N/A | NO | Matched by immutable item ID; one execution observed. |
| API-050 | `FAIL_ASSERTION` | Verify the just-below uppercase-count boundary with zero uppercase letters while all other password clauses remain satisfied. | 200 OK | FAIL — API-050 - reviewed status is 400 | expected response to have status code 400 but got 200 | YES — Verify that the password is unchanged and the OTP remains usable after rejection. | Matched by immutable item ID; one execution observed. |
| API-051 | `PASS` | Verify the just-above uppercase-count boundary with two uppercase letters while all password clauses remain satisfied. | 200 OK | PASS — API-051 - reviewed status is 200 | N/A | NO | Matched by immutable item ID; one execution observed. |
| API-052 | `FAIL_ASSERTION` | Verify the just-below lowercase-count boundary with zero lowercase letters while all other password clauses remain satisfied. | 200 OK | FAIL — API-052 - reviewed status is 400 | expected response to have status code 400 but got 200 | YES — Verify that the password is unchanged and the OTP remains usable after rejection. | Matched by immutable item ID; one execution observed. |
| API-053 | `PASS` | Verify the lowercase-count boundary with exactly one lowercase letter while all password clauses remain satisfied. | 200 OK | PASS — API-053 - reviewed status is 200 | N/A | NO | Matched by immutable item ID; one execution observed. |
| API-054 | `PASS` | Verify the just-above lowercase-count boundary with exactly two lowercase letters while all password clauses remain satisfied. | 200 OK | PASS — API-054 - reviewed status is 200 | N/A | NO | Matched by immutable item ID; one execution observed. |
| API-055 | `FAIL_ASSERTION` | Verify the just-below digit-count boundary with zero digits while all other password clauses remain satisfied. | 200 OK | FAIL — API-055 - reviewed status is 400 | expected response to have status code 400 but got 200 | YES — Verify that the password is unchanged and the OTP remains usable after rejection. | Matched by immutable item ID; one execution observed. |
| API-056 | `PASS` | Verify the just-above digit-count boundary with exactly two digits while all password clauses remain satisfied. | 200 OK | PASS — API-056 - reviewed status is 200 | N/A | NO | Matched by immutable item ID; one execution observed. |
| API-057 | `FAIL_ASSERTION` | Verify the just-below allowed-special-count boundary with zero listed special characters while all other password clauses remain satisfied. | 200 OK | FAIL — API-057 - reviewed status is 400 | expected response to have status code 400 but got 200 | YES — Verify that the password is unchanged and the OTP remains usable after rejection. | Matched by immutable item ID; one execution observed. |
| API-058 | `PASS` | Verify the just-above allowed-special-count boundary with exactly two listed special characters while all password clauses remain satisfied. | 200 OK | PASS — API-058 - reviewed status is 200 | N/A | NO | Matched by immutable item ID; one execution observed. |
| API-059 | `PASS` | Verify successful reset with a valid password that satisfies every explicit strength clause and also contains an additional non-listed punctuation character. | 200 OK | PASS — API-059 - reviewed status is 200 | N/A | NO | Matched by immutable item ID; one execution observed. |
| API-060 | `FAIL_ASSERTION` | Verify rejection when the required newPassword member is omitted. | 200 OK | FAIL — API-060 - reviewed status is 400 | expected response to have status code 400 but got 200 | NO | Matched by immutable item ID; one execution observed. |
| API-061 | `FAIL_ASSERTION` | Verify rejection when newPassword is JSON null. | 200 OK | FAIL — API-061 - reviewed status is 400 | expected response to have status code 400 but got 200 | NO | Matched by immutable item ID; one execution observed. |
| API-062 | `FAIL_ASSERTION` | Verify rejection when newPassword has a non-string JSON type. | 200 OK | FAIL — API-062 - reviewed status is 400 | expected response to have status code 400 but got 200 | NO | Matched by immutable item ID; one execution observed. |
| API-080 | `FAIL_ASSERTION` | Step 1: Verify that an object-valued newPassword is rejected without consuming the OTP. [Step 1 - object password]<br>Step 2: Verify that an object-valued newPassword is rejected without consuming the OTP. [Step 2 - string retry] | Step 1: 200 OK<br>Step 2: 400 Bad Request | Step 1: FAIL — API-080 - reviewed status is 400<br>Step 2: FAIL — API-080 - reviewed status is 200 | Step 1: expected response to have status code 400 but got 200<br>Step 2: expected response to have status code 200 but got 400 | NO | Matched all 2 ordered collection steps by immutable item ID. |
| API-063 | `PASS` | Verify reviewed transition TR-001: a usable OTP for its bound email completes the intended reset and becomes invalidated after use (ST-01 to ST-03). | 200 OK | PASS — API-063 - reviewed status is 200 | N/A | YES — Verify the password change and transition of the used OTP to the invalidated state. | Matched by immutable item ID; one execution observed. |
| API-064 | `PASS` | Verify reviewed invalid transition TR-002: an ST-01 OTP bound to email A cannot be used with a different email B. | 400 Bad Request | PASS — API-064 - reviewed status is 400 | N/A | NO | Matched by immutable item ID; one execution observed. |
| API-065 | `BLOCKED_NOT_EXECUTED` | Verify reviewed invalid transition TR-003: an expired OTP in ST-02 cannot perform a valid password reset. | N/A | N/A — not executed | N/A | YES — A real OTP expiry point must be configured or objectively observed; the SUT has no expiry state/check. | Explicit pre-request skip: SUT has no OTP expiry state or check. No SUT verdict was produced. |
| API-066 | `PASS` | Setup: pre-request first-use reset (`pm.sendRequest`, expected HTTP 200)<br>Verify reviewed invalid transition TR-004: replaying an OTP after it reached ST-03 cannot perform another reset. | Setup: unavailable in detailed execution rows<br>400 Bad Request | Setup: no Newman assertion<br>PASS — API-066 - reviewed status is 400 | N/A | NO | The pre-request helper call is included in Newman’s request total but has no separate response record. Two identical main-execution rows (same cursor, request, response, and assertion) were correlated as one observed main step. |
| API-067 | `FAIL_ASSERTION` | Verify reviewed guard-failing transition TR-005: rejecting a weak new password preserves the usable OTP in ST-01 and leaves the account's old password unchanged. | 200 OK | FAIL — API-067 - reviewed status is 400 | expected response to have status code 400 but got 200 | YES — Verify that the old password and usable OTP state are preserved after the rejected weak password. | Matched by immutable item ID; one execution observed. |
| API-077 | `PASS` | Two synchronized reset requests using the same email/OTP but different valid passwords. | One request: 200 OK<br>Other request: 400 Bad Request | MANUAL PASS | N/A | NO — completed with a separate concurrency harness. | **Manual verification.** A synchronized concurrent harness was used because sequential Newman cannot establish a concurrency barrier. Exactly one reset succeeded, the other was rejected, and the OTP was consumed once. |
| API-068 | `FAIL` | WHITE-BOX/STORAGE VERIFICATION: Verify that a successfully reset password is not persisted as plaintext. | 200 OK | MANUAL FAIL | The submitted reset password was stored in plaintext. | NO — completed by direct database inspection. | **Manual verification.** The HTTP reset request succeeded, but direct database inspection confirmed that the new password was persisted in plaintext. |
| API-069 | `PASS` | Verify that inert SQL/query metacharacters in a client-controlled field do not bypass reset controls, affect another account, expose database information, or cause unexpected server failure. | 400 Bad Request | PASS — API-069 - reviewed status is 400 | N/A | YES — Check protected-account/storage side effects, information exposure, and parameterized query handling. | Matched by immutable item ID; one execution observed. |
| API-070 | `PASS` | Verify the valid security control: a random exactly 6-decimal-digit, unexpired, unused OTP authorizes reset only for the email to which it is bound and is consumed on successful use. | 200 OK | PASS — API-070 - reviewed status is 200 | N/A | YES — Verify the intended password change and one-time OTP consumption. | Matched by immutable item ID; one execution observed. |
| API-071 | `PASS` | Verify that an OTP issued for one email cannot authorize a reset for another email. | 400 Bad Request | PASS — API-071 - reviewed status is 400 | N/A | YES — Verify that neither account password changed. | Matched by immutable item ID; one execution observed. |
| API-072 | `BLOCKED_NOT_EXECUTED` | Verify that an expired reset OTP cannot authorize a password reset. | N/A | N/A — not executed | N/A | YES — A real OTP expiry point must be configured or objectively observed; the SUT has no expiry state/check. | Explicit pre-request skip: SUT has no OTP expiry state or check. No SUT verdict was produced. |
| API-073 | `PASS` | Setup: pre-request first-use reset (`pm.sendRequest`, expected HTTP 200)<br>Verify one-time use by rejecting replay of an OTP after it has successfully reset the bound account's password. | Setup: unavailable in detailed execution rows<br>400 Bad Request | Setup: no Newman assertion<br>PASS — API-073 - reviewed status is 400 | N/A | YES — Verify that replay did not replace the password established by the first successful reset. | The pre-request helper call is included in Newman’s request total but has no separate response record. Two identical main-execution rows (same cursor, request, response, and assertion) were correlated as one observed main step. |
| API-074 | `PASS` | Verify that a resetToken shorter than the specified six decimal digits cannot authorize reset. | 400 Bad Request | PASS — API-074 - reviewed status is 400 | N/A | YES — Verify that the account password remains unchanged. | Matched by immutable item ID; one execution observed. |
| API-075 | `BLOCKED_NOT_EXECUTED` | Verify resistance to automated guessing of six-digit reset OTPs through rate limiting or equivalent abuse protection. | N/A | N/A — not executed | N/A | YES — A configured abuse-control threshold and manual/data-driven execution are required; neither is available. | Explicit pre-request skip: SUT has no rate limiter or authoritative threshold. No SUT verdict was produced. |
| API-076 | `PASS` | Step 1: Verify that reset failure behavior does not materially disclose whether the submitted account exists. [Request A - registered email]<br>Step 2: Verify that reset failure behavior does not materially disclose whether the submitted account exists. [Request B - non-existing email] | Step 1: 400 Bad Request<br>Step 2: 400 Bad Request | Step 1: PASS — API-076 - reviewed status is 400<br>Step 2: PASS — API-076 - reviewed status is 400<br>Step 2: PASS — API-076 - comparable failure representation | N/A | YES — Check password/token/account-metadata side effects; timing remains informational without an approved tolerance. | Matched all 2 ordered collection steps by immutable item ID. |
| API-081 | `PASS` | Step 1: Verify that SQL syntax in a rule-conforming new password is treated as data and does not damage another account's reset path. [Step 1 - Account A injection string]<br>Step 2: Verify that SQL syntax in a rule-conforming new password is treated as data and does not damage another account's reset path. [Step 2 - Account B integrity check] | Step 1: 200 OK<br>Step 2: 200 OK | Step 1: PASS — API-081 - reviewed status is 200<br>Step 2: PASS — API-081 - reviewed status is 200 | N/A | YES — Authorized implementation or database inspection is still needed to prove parameterized storage. | Matched all 2 ordered collection steps by immutable item ID. |
| API-082 | `PASS` | Verify that an invalid bearer token does not interfere with the public password-recovery endpoint. | 200 OK | PASS — API-082 - reviewed status is 200 | N/A | NO | Matched by immutable item ID; one execution observed. |

#### Coverage and reconciliation notes

- The embedded collection supplied the authoritative intended set: 88 leaf request items grouped into 82 stable Test IDs. All observed main requests matched collection items by immutable item ID; no ambiguous or unmatched execution remained.
- Four logical cases remain explicitly blocked before dispatch: `API-025`, `API-065`, and `API-072` because no observable/configurable OTP-expiry state is available, and `API-075` because no authoritative abuse-control threshold is available.
- `API-026`, `API-066`, and `API-073` each issue a first-use reset through pre-request `pm.sendRequest` before the collection replay request. These three helper calls reconcile Newman’s 85 request total with 82 executed collection leaf requests. The JSON repeats each main execution object twice with identical cursor/request/response/assertion identity; each duplicate pair was correlated once for logical-case and assertion analysis. Newman’s source assertion totals then reconcile exactly to 82 assertions: 59 passed and 23 failed.
- `API-030` completed with HTTP 200 but defined no automated assertion; its `PASS` status means execution completed without request/runtime error, while its exploratory manual oracle remains pending.
- `API-080` contains two failed assertions across its two ordered steps, so the run has 23 failed assertions but 22 distinct logical cases with failed assertions.
- Manual-oracle requirements are independent of automated status. Automated results do not satisfy the explicitly retained checks, including storage inspection, password/OTP state verification, side-effect review, configured abuse-control execution, and true concurrency.
- `API-077` was blocked only in sequential Newman execution, then separately verified with a synchronized concurrency harness and received a final `PASS`.
- `API-068` passed its automated HTTP assertion but failed the required manual storage oracle; its final reviewed result is `FAIL` because the reset password was confirmed to be stored in plaintext.

## Pool B: Discount Coupons

### B.1. Introduction

Pool B covers **FR-09 – Discount Coupons**. This report selects `POST /api/apply-coupon`, which applies a coupon to an order amount and returns the calculated `discount_amount` and `final_amount`.

### B.2. Contractual Testing Analysis

The selected endpoint is documented as `POST /api/apply-coupon`. It uses a JSON body with three top-level fields and requires a valid JWT under FR-09 C4:

| Input | Documented representation | Reviewed constraint |
| --- | --- | --- |
| `Authorization` | `Bearer <token>` header | The JWT must be valid; token claims and authentication-failure responses are not specified |
| `code` | JSON string | The coupon must exist and have `is_active = 1` to satisfy FR-09 C1 |
| `total_amount` | JSON number | Must be greater than or equal to the selected coupon's `min_order_amount` |
| `user_id` | JSON number | The user's prior use count for the coupon must be below `max_uses_per_user` |

The reviewed contract model contains rules `CR-001`–`CR-012`. It covers the method and path, documented JSON representation, the three body members, valid-JWT prerequisite, successful response structure, percent and fixed discount calculations, final-amount calculation, and exact calculation oracles for the documented `SAVE10` and `BIGBUY` fixtures.

On a qualifying request, the response is documented as JSON containing `discount_amount` and `final_amount`. For a percent coupon, `discount_amount = total × discount_value / 100`; for a fixed coupon, `discount_amount = discount_value`; and `final_amount = total - discount_amount`.

The API specification does not provide a formal request or response schema. Field requiredness, nullability, coercion, additional-property handling, concrete MIME values, HTTP statuses, error bodies, response headers, rounding, and validation precedence are not documented. The reviewed model therefore treats malformed bodies, omitted members, wrong types, and similar mutations as bounded contract explorations without inventing rejection statuses or messages. It also does not infer that body `user_id` must match the JWT subject. The complete analysis is stored in [`review/pool-b/reports/contract-report.md`](review/pool-b/reports/contract-report.md).

### B.3. Domain Testing Analysis

Domain analysis uses a qualifying `SAVE10` request as its baseline: the coupon is arranged as active and unexpired, `total_amount` is `500000`, the selected user has zero prior uses, and a valid JWT is supplied. This produces the mathematical oracle `discount_amount = 50000` and `final_amount = 450000`. Tests vary one input or one controlled coupon/user condition at a time where possible.

The reviewed model defines 37 equivalence partitions (`DP-001`–`DP-037`) across the JSON container, JWT header, and three body fields. Important partitions include:

- JSON object, malformed/non-object body, and additional-member representations;
- valid, missing, malformed, invalid, and expired JWT values;
- existing active percent/fixed coupons, nonexistent or inactive coupons, and coupons before, at, or after expiry;
- totals below, equal to, and above the selected coupon's minimum, including zero, negative, decimal, very large, wrong-type, omitted, and `null` values;
- per-user use counts below, at, and above `max_uses_per_user`;
- matching or mismatched JWT/body identities, nonexistent users, unusual identifier values, wrong types, omission, and `null`.

Seven boundary models (`DB-001`–`DB-007`) cover:

| Boundary group | Reviewed points |
| --- | --- |
| `SAVE10` / `VIP100` minimum `300000` | `299999` outside; `300000` and `300001` inside |
| `BIGBUY` minimum `500000` | `499999` outside; `500000` and `500001` inside |
| Minimum allowed coupon threshold `0` | `-1` outside; `0` and `1` inside |
| Expiry date | before expiry qualifies; equality and after expiry do not qualify |
| Generic and fixture-specific usage limits | `M - 1` qualifies; `M` and `M + 1` do not qualify |

Coupon activity, expiry, and prior-use count are state-dependent eligibility preconditions, but they remain DOMAIN coverage because this endpoint documents calculation rather than a state change. The analysis does not infer integer-only amounts, currency precision, rounding, maximum discounts, a zero floor for `final_amount`, identifier ranges, case normalization, or undocumented error responses. The complete analysis is stored in [`review/pool-b/reports/domain-report.md`](review/pool-b/reports/domain-report.md).

### B.4. State Transition Testing Analysis

State-transition testing is **not applicable** to the selected endpoint. FR-09 C1, C2, and C5 make coupon eligibility depend on stored conditions—active/inactive status, expiry, and the user's prior-use count—but the API specification describes `POST /api/apply-coupon` only as calculating discounted amounts.

Neither authoritative source states that this call increments coupon usage, consumes or reserves a coupon, changes `is_active`, creates a destination state, follows a lifecycle sequence, or has an idempotency rule. A transition model would therefore invent behavior. Active/inactive, before/equal/after-expiry, and below/at/above-use-limit cases are covered under DOMAIN instead. The Phase-2 STATE candidate fragment is exactly `[]`. The applicability record is stored in [`review/pool-b/reports/state-report.md`](review/pool-b/reports/state-report.md).

### B.5. Security Testing Analysis

All supplied requirements `SEC-01`–`SEC-07` were evaluated for this endpoint:

| Requirement | Applicability and treatment |
| --- | --- |
| `SEC-01` | Not applicable: the endpoint has no password input, output, or storage behavior. |
| `SEC-02` | Applicable: FR-09 C4 explicitly requires a valid JWT. Coverage includes a valid control and missing, malformed, invalid-signature, and expired JWT classes. |
| `SEC-03` | Not applicable: this Checkout operation is not an Admin API. |
| `SEC-04` | No direct API scenario: no UI rendering or response-reflection sink is documented for coupon input. |
| `SEC-05` | Applicable at the query/implementation layer: controlled inert SQL/metacharacter values are applied to both `code` and client-controlled `user_id`. |
| `SEC-06` | Not applicable: this is not a profile-update API and has no documented `role` input. |
| `SEC-07` | Not applicable: the endpoint has no password-reset OTP behavior. |

The reviewed security model contains eight scenarios (`SS-001`–`SS-008`). `SS-001`–`SS-005` cover the valid JWT control and missing or invalid credential classes. `SS-006`–`SS-008` cover inert query-like values in coupon `code` and `user_id`; these values must remain data and must not alter query semantics, broaden the per-user usage scope, select another user's record, modify database state, or expose query diagnostics.

No HTTP status, error schema, or message is invented for the negative security scenarios. Black-box results may reveal unsafe behavior but cannot conclusively prove that parameterized queries are used; source review, query instrumentation, or equivalent implementation evidence is required for that claim. The sources also do not define JWT claims, issuer, audience, accepted algorithms, clock skew, or a binding between the JWT identity and body `user_id`. The complete analysis is stored in [`review/pool-b/reports/security-report.md`](review/pool-b/reports/security-report.md).

### B.6. AI-Generated Test Cases

The final reviewed test cases for this pool are stored in: [`test-cases/b-discount-coupons.csv`](test-cases/b-discount-coupons.csv)

The test cases were derived from the reviewed analyses in Sections B.2–B.5.

| Testing Type | Number of Test Cases |
| --- | ---: |
| Contractual Testing | 15 |
| Domain Testing | 44 |
| State Transition Testing | 0 |
| Security Testing | 8 |
| **Total** | **67** |

The suite uses sequential IDs `API-001`–`API-067` and exactly nine traceability fields per record. Every case targets `POST /api/apply-coupon`. Coverage includes `CR-001`–`CR-012`, `DP-001`–`DP-037`, `DB-001`–`DB-007`, and `SS-001`–`SS-008`; applicable security requirements are `SEC-02` and `SEC-05`. No placeholder STATE cases were generated.

Human review corrected inclusive minimum-threshold labels, the mathematical oracle for `SAVE10` with `total_amount = 300001`, and the fixture preconditions for `BIGBUY`, `EXPIRED`, and nonexistent coupon codes. Same-category semantic deduplication removed 14 redundant DOMAIN records while preserving every partition/boundary basis and provisional specialist ID on retained cases. The final merged coverage includes `DP-021 + DB-001` just-below, `DP-013 + DB-004` equal-to-expiry, and `DP-030/DP-031 + DB-006` at/above the usage limit.

Final validation confirmed sequential unique IDs, the exact nine-column schema, endpoint/category consistency, non-empty required content, complete reviewed traceability, and no remaining same-category semantic duplicate groups. Undocumented statuses, error representations, coercion, identity binding, rounding/precision, and endpoint-driven state mutation remain explicit gaps rather than invented behavior. These are candidate test cases only; the API tests have not yet been executed. Generation and validation details are recorded in [`review/pool-b/orchestration-status.md`](review/pool-b/orchestration-status.md).

### B.7. Human Cases

| ID | Category | Test case | Expected result | Notes |
| --- | --- | --- | --- | --- |
| **API-068** | CONTRACT | Send otherwise valid JSON text using `Content-Type: text/plain`. | The request does not produce a successful coupon calculation. It is handled safely without a `5xx` server error. | The specification documents a JSON request body but does not define behavior for unsupported content types. The safe rejection expectation is human-added. |
| **API-069** | CONTRACT | Send `Content-Type: application/json` with a completely **empty HTTP body**. | The request does not apply a coupon and does not return a successful calculation. It is handled safely without a `5xx` server error. | Previous AI cases tested missing fields and malformed JSON, but not a completely missing body. |
| **API-070** | DOMAIN | Send an empty coupon code `""` while all other request conditions are valid. | The coupon is not applied because the submitted code does not identify an existing active coupon. | The AI tested unusual, null, numeric, and modified coupon-code values, but did not use the empty string as a separate representative. |
| **API-071** | DOMAIN | Apply `VIP100` with `total_amount = 300000`, exactly equal to its documented minimum, with zero prior uses. | The coupon qualifies. `discount_amount = 100000` and `final_amount = 200000`. | The generated boundary cases covered SAVE10 and BIGBUY minimum amounts, but did not test the exact minimum of VIP100. |
| **API-072** | SECURITY | An authenticated user has already reached the SAVE10 usage limit. Send another request with the same valid JWT but body `user_id = 0`. | The coupon must not be applied. Changing the client-supplied `user_id` must not allow the authenticated user to bypass the per-user usage limit. | JWT-to-body-user binding is not explicitly defined by the specification. This is a human-added security expectation based on FR-09 C4 and C5. |
| **API-073** | DOMAIN | Arrange an active percent coupon with `discount_value = 1`, `min_order_amount = 0`, and remaining usage. Apply it to `total_amount = 500000`. | `discount_amount = 5000` and `final_amount = 495000`. | The AI tested the documented percentage coupon but did not test the lower positive percentage boundary allowed by the documented coupon rules. |
| **API-074** | DOMAIN | Arrange an active percent coupon with `discount_value = 100`, `min_order_amount = 0`, and remaining usage. Apply it to `total_amount = 500000`. | `discount_amount = 500000` and `final_amount = 0`. | No upper percentage limit is documented. This case checks the percentage formula at a full-discount value. |

The AI missed these cases mainly because the initial generation focused on representative partitions and boundaries that could be derived directly from the API specification. Some additional request representations, such as an unsupported content type and a completely empty body, were therefore not selected.

The generated domain tests also covered the main documented coupon fixtures and representative boundaries, but did not systematically test every documented coupon at its own threshold or additional valid percentage values such as 1% and 100%.

The security analysis tested JWT validity, SQL-like inputs, and per-user usage limits, but did not combine authentication identity with a manipulated `user_id` to check for usage-limit bypass. This gap requires a human security assumption because the exact JWT-to-body-user binding rule is not documented.

These gaps show that specification-based AI generation can provide broad coverage, but human review is still useful for finding robustness cases, additional boundary combinations, and security interactions between otherwise separate input conditions.

### B.8. Newman Execution Analysis

## Pool C: Admin Order Management

### C.1. Introduction

Pool C covers **FR-18 – Admin Order Management**. This report selects `PUT /api/admin/orders/:id/status`, which allows an Admin user to update an order to one of the supported states: `pending`, `confirmed`, `shipping`, `delivered`, or `canceled`.

### C.2. Contractual Testing Analysis

### C.3. Domain Testing Analysis

### C.4. State Transition Testing Analysis

### C.5. Security Testing Analysis

### C.6. AI-Generated Test Cases

The final reviewed test cases for this pool are stored in [`test-cases/c-order-management.csv`](test-cases/c-order-management.csv).

The test cases were derived from the reviewed analyses in Sections A.2–A.5.

| Testing Type | Number of Test Cases |
| --- | ---: |
| Contractual Testing | |
| Domain Testing | |
| State Transition Testing | |
| Security Testing | |
| **Total** | |

### C.7. Human Cases

### C.8. Newman Execution Analysis
