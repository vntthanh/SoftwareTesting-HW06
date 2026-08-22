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
| Last updated | 2026-08-21 |

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

### A.7. Human cases

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

## Pool B: Discount Coupons

### B.1. Introduction

Pool B covers **FR-09 – Discount Coupons**. This report selects `POST /api/apply-coupon`, which applies a coupon to an order amount and returns the calculated `discount_amount` and `final_amount`.

### B.2. Contractual Testing Analysis

### B.3. Domain Testing Analysis

### B.4. State Transition Testing Analysis

### B.5. Security Testing Analysis

### B.6. AI-Generated Test Cases

The final reviewed test cases for this pool are stored in: [`test-cases/b-discount-coupons.csv`](test-cases/b-discount-coupons.csv)

The test cases were derived from the reviewed analyses in Sections A.2–A.5.

| Testing Type | Number of Test Cases |
| --- | ---: |
| Contractual Testing | |
| Domain Testing | |
| State Transition Testing | |
| Security Testing | |
| **Total** | |

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
