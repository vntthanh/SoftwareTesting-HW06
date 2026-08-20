# Pool A — Phase 1 Security Analysis

## Report identity

- **Selected endpoint:** `POST /api/reset-password`
- **Scope:** Phase 1 security analysis only; no test cases were generated and no API was probed.
- **Report version:** `POOL-A-SECURITY-PHASE1-v1`
- **API specification:** `reference/api_specification.md`, SHA-256 `488CBCB790099BA9CBB34C7C80BA04C6AEC9E9EBB598F031FFA575737547B139`; selected operation at lines 44–52.
- **System requirements:** `reference/system_requirements.md`, version 2.0 dated 2026-05-14, SHA-256 `7859599624A8F94E7B28859F5E3EDBEE71F275E1A71043E3EFCAB10D5EE14CDD`; FR-01 at lines 30–36, FR-03 at lines 46–60, and SEC-01–SEC-07 at lines 278–284.
- **Shared normalized context:** `review/pool-a/shared-api-context.md` (read-only input).
- **Authoritative-source rule:** The API specification and system requirements are treated as authoritative. Where they do not define behavior, this report records a gap rather than inferring a contract.

## Endpoint and security characteristics

| Characteristic | Analysis | Exact basis / limitation |
| --- | --- | --- |
| Operation and request surface | The operation is `POST /api/reset-password`. Its documented JSON example contains `email`, `resetToken`, and `newPassword`; all three are untrusted client-controlled inputs at the API boundary. | API specification lines 44–52. Formal requiredness, nullability, types beyond the example, maximum lengths, extra-property handling, and malformed-body behavior are not specified. |
| Authentication | No endpoint-specific JWT, bearer-token, cookie, or other authentication declaration is supplied. | API specification lines 44–52. The JWT note at line 59 applies to the subsequent Users APIs and must not be transferred to this operation. SEC-02 is evaluated separately below. |
| Authorization-relevant identifier | `email` selects the reset subject, and the OTP may authorize reset only for the email that requested it. | FR-03 lines 48 and 57–60. No user ID, ownership field, or role is documented for this request. |
| Roles | No role is documented for the operation. It is not an Admin API and is not under `/api/admin/*`. | API specification lines 44–52; FR-12 defines Admin scope elsewhere. |
| Sensitive inputs | `newPassword` is a new credential. `resetToken` is an OTP knowledge factor. `email` is an account identifier and participates in OTP binding. | API specification lines 46–52; FR-03 lines 48–60; SEC-01 and SEC-07. |
| Sensitive outputs | No response body, status, header, token, or error contract is documented for this operation. | API specification lines 44–52 and FR-03. The `POST /api/forgot-password` response at API specification line 42 belongs to a different operation and is not inherited. |
| Password policy | The new password must be at least 8 characters and contain at least one uppercase letter, one lowercase letter, one digit, and one of `@`, `$`, `!`, `%`, `*`, `?`, `&`. | FR-03 line 58 incorporates FR-01 line 34. This is a functional input constraint; SEC-01 separately governs storage. |
| OTP characteristics | The reset OTP is a random 6-decimal-digit value, is bound to the requesting email, expires, and is invalidated after use. | FR-03 lines 48–50 and 60; SEC-07 line 284. The expiry duration and randomness mechanism are not specified. |
| Persistence and database | The system overview names SQLite, and reset logically concerns stored account credentials and OTP state. SEC-01 governs any password persistence, and SEC-05 governs any database query that the implementation executes. | System requirements section 1; SEC-01 and SEC-05. The selected API contract does not expose the storage representation, query structure, or persistence timing. |
| UI rendering | The endpoint receives user-controlled data, but no response reflection or UI rendering path is defined for this operation. | SEC-04 is a UI display rule. Neither selected-operation source defines rendered output for these values. |
| Transport and headers | The supplied base URL is `http://localhost:3000`; the body is labeled JSON. No exact `Content-Type`, TLS requirement, security response header, or endpoint-specific authorization header is stated. | API specification introductory metadata and lines 46–52. This report does not add an HTTPS or header requirement. |
| Abuse controls | Expiry and one-time invalidation are the only documented replay/abuse controls for this endpoint's OTP. | SEC-07 line 284. Attempt limits, throttling, reset-request rate limits, lockouts, brute-force handling, and monitoring are not specified. |
| Observability | The intended operation is password reset, but the sources define no exact success/error status, response body, message, redaction rule, timing rule, or audit/log behavior. | API specification lines 44–52; FR-03. Expected security behavior below is therefore stated without invented HTTP details. |

## SEC-01–SEC-07 applicability matrix

All seven SEC IDs are present in the authoritative requirements; none is absent.

| ID | Authoritative requirement (faithful English rendering) | Applicability to `POST /api/reset-password` | Evidence and exact basis | Phase 1 treatment |
| --- | --- | --- | --- | --- |
| SEC-01 | Passwords must **not** be stored in plaintext. | **APPLICABLE — implementation-facing.** A successful reset replaces a password, so any resulting persistence must satisfy the supplied password-storage rule. | SEC-01 line 278; the selected operation is “Đặt lại mật khẩu” at API specification lines 44–52; FR-03 lines 55–59 requires entry of a new password. | Scenario `SS-001`. The rule is not verifiable from the undocumented API response alone; authorized storage inspection or implementation instrumentation would be required. No hashing algorithm or format is specified. |
| SEC-02 | Security-sensitive APIs must require a valid JWT token. | **NOT APPLICABLE.** `POST /api/reset-password` is part of the unauthenticated account-recovery workflow. Requiring an existing JWT would prevent a user who cannot authenticate from recovering the account. The OTP is the recovery credential for this workflow. | FR-03 lines 46–60; API specification lines 44–52 contain no JWT requirement; external password-reset best practice | No JWT is required for this selected reset operation. |
| SEC-03 | Admin APIs must verify `role = 'admin'` in the token, not merely the token's presence. | **NOT APPLICABLE.** The selected endpoint is not documented as an Admin API and is not under `/api/admin/*`. | SEC-03 line 280; API specification lines 44–52; FR-12's Admin API scope. | No scenario derived. |
| SEC-04 | User input displayed in the UI must be correctly escaped; `innerHTML` must not be used directly. | **UNSUPPORTED FOR DIRECT ENDPOINT APPLICATION / AMBIGUOUS IF A UI LATER DISPLAYS A VALUE.** The endpoint has user-controlled inputs, but the sources define neither response reflection nor a UI rendering sink for them. | SEC-04 line 281; API specification lines 44–52 provide no response; FR-03 supplies workflow UI facts but does not say these submitted values are rendered. | No endpoint scenario derived. A UI-specific scenario would require a documented display sink and is outside the selected API contract as supplied. |
| SEC-05 | Database queries must use parameterized queries, not direct string concatenation. | **APPLICABLE CONDITIONALLY — implementation-facing.** Every database query executed by this operation is governed by SEC-05. The sources indicate an SQLite-backed system and a stateful email/OTP/password workflow, but do not specify the actual query set. | SEC-05 line 282; system requirements section 1 names SQLite; FR-03 lines 48–60 defines registered-email lookup, OTP/email binding, and reset state. | Scenario `SS-002`, phrased conditionally and requiring implementation/runtime query inspection. No SQL text, table, column, or API error behavior is assumed. |
| SEC-06 | Profile-update APIs must not allow a client to change `role`. | **NOT APPLICABLE.** This is a password-reset endpoint, not a profile-update API, and its documented body has no `role` field. | SEC-06 line 283; API specification lines 44–52. | No scenario derived. |
| SEC-07 | Reset-password OTP must have sufficient entropy (at least 6 digits), expire, and be invalidated after use. | **APPLICABLE — direct workflow rule.** This requirement explicitly addresses reset-password OTP. FR-03 further specifies a random OTP of exactly 6 decimal digits and binding to the requesting email. | SEC-07 line 284; FR-03 lines 48–50 and 57–60. | Scenarios `SS-003`–`SS-007`. Randomness is an issuance property of step 1 and cannot be isolated through the selected consumption endpoint; that observability limit is retained. |

## Security scenarios for applicable requirements

These are Phase 1 scenarios, not executable test cases. They intentionally omit exact HTTP statuses, response schemas, messages, and timing assertions because none is specified.

| Scenario ID | Preconditions | Stimulus | Expected security behavior | Requirement IDs | Exact basis | Assumptions / observability limits |
| --- | --- | --- | --- | --- | --- | --- |
| SS-001 | A registered email has an issued OTP that is bound to that email, unexpired, and unused. The submitted new password satisfies FR-01. Authorized storage-level inspection or equivalent implementation instrumentation is available. | Submit the documented reset operation using that email, OTP, and a known new password, then inspect the resulting stored credential representation if the reset completes. | The new password is not stored in plaintext; the persisted representation must not be the submitted plaintext credential. | SEC-01 | SEC-01 line 278; API specification lines 44–52; FR-03 lines 55–59. | The sources do not specify a hashing/KDF algorithm, salt, encoded format, database field, commit timing, or API response. Equality-to-plaintext inspection supports the stated rule but does not establish compliance with an unstated algorithmic standard. |
| SS-002 | Use an isolated test environment and otherwise valid reset setup. | Submit SQL-like and query-metacharacter input through client-controlled fields such as `email` or `resetToken`. | The input must remain data: it must not bypass OTP/email validation, modify another account, expose database errors or sensitive database information, or cause an unexpected server failure. If implementation inspection is available, also verify that executed queries use parameterized values rather than string concatenation. | SEC-05 | SEC-05 line 282; API specification lines 46–52; external OWASP SQL-injection testing guidance | Black-box testing can detect injection effects but cannot by itself prove that every query is parameterized. |
| SS-003 | Step 1 has issued a random, exactly 6-decimal-digit OTP for a registered email. The OTP is bound to that same email, is unexpired, and has not been used. The new password satisfies FR-01. | Submit `POST /api/reset-password` with the same email, that OTP, and the conforming new password. | The OTP is eligible to authorize the reset for its bound email; on successful use, it becomes invalid for future use. | SEC-07 | SEC-07 line 284; FR-03 lines 48–50 and 57–60; API specification lines 44–52. | “Eligible” does not assert an undocumented status or response. The exact persistence sequence and how success is observed are unspecified. Random generation is a step-1 property used as a precondition here, not proven by this endpoint alone. |
| SS-004 | An OTP was issued for email A and is otherwise unexpired and unused. Email B is a different email. | Submit `POST /api/reset-password` using email B with email A's OTP and an otherwise conforming new password. | The OTP must not authorize a password reset for email B. | SEC-07 | FR-03 line 60 supplies the email-binding rule; SEC-07 line 284 identifies the reset OTP security requirement. | No exact rejection status, error body, message, attempt-count effect, or token-consumption effect is specified. |
| SS-005 | An OTP was issued for the same registered email but is expired. The new password otherwise satisfies FR-01. | Submit `POST /api/reset-password` with the expired OTP. | The expired OTP must not authorize a password reset. | SEC-07 | SEC-07 line 284 requires an expiry; selected request fields are at API specification lines 46–52. | Expiry duration and boundary semantics are unspecified, so setup may label the token expired without inventing a lifetime. No exact rejection response is asserted. |
| SS-006 | An OTP was successfully used once for its bound email. | Submit `POST /api/reset-password` again using the same OTP, with the same or another conforming new password. | The previously used OTP must not authorize a second reset. | SEC-07 | SEC-07 line 284 requires invalidation after use. | The first operation's exact success signal and the replay's exact response are unspecified. The setup may establish successful first use through an authorized observable effect. |
| SS-007 | No server-issued OTP corresponding to the submitted value exists; the submitted `resetToken` contains fewer than 6 decimal digits. Other workflow inputs are otherwise conforming. | Submit `POST /api/reset-password` with that undersized token value. | The value must not authorize a password reset because a valid reset OTP is specified as random and exactly 6 decimal digits, with SEC-07 setting a minimum of 6 digits. | SEC-07 | FR-03 lines 48–50; SEC-07 line 284 | No exact rejection response is asserted. |
| SS-008 | A registered account exists and the tester does not know its valid OTP. | Repeatedly submit different incorrect 6-digit OTP values. | The endpoint should resist automated OTP guessing through rate limiting or equivalent abuse protection; when rate limiting is triggered, use `429 Too Many Requests` as the reviewed external HTTP expectation. | SEC-07 / external security practice | SEC-07 requires an expiring reset OTP; external OWASP forgot-password guidance recommends protection against brute-force and excessive automated attempts. | Exact attempt threshold is unspecified and must not be invented. |
| SS-009 | Prepare requests involving both existing and non-existing accounts or otherwise invalid recovery identities where the workflow permits. | Compare recovery failure responses. | The responses should not reveal whether an account exists through materially different messages or behavior. | External security practice | OWASP forgot-password guidance | This is an added best-practice test, not an explicit SEC-01–SEC-07 requirement. |

## Coverage and non-scenario decisions

- Applicable SEC-01 is represented by `SS-001`.
- Conditionally applicable SEC-05 is represented by `SS-002`, with its implementation-access condition explicit.
- Directly applicable SEC-07 is represented by `SS-003`–`SS-007`, covering a valid control, email binding, expiry, one-time use, and the documented minimum/exact OTP length.
- No scenarios are derived for SEC-02 or SEC-04 because endpoint applicability/observability is not established. Human approval may resolve applicability, but Phase 1 does not guess.
- No scenarios are derived for SEC-03 or SEC-06 because their defined scopes do not cover the selected endpoint.
- SEC-07's “random” issuance property is not independently testable through `POST /api/reset-password`; `SS-003` treats it as a workflow precondition. Testing generation quality would require the related step-1 operation and a reviewed statistical/entropy oracle not supplied here.

## Gaps and ambiguities requiring review

1. **JWT classification:** The documents do not say whether `POST /api/reset-password` is one of the “security-sensitive APIs” governed by SEC-02. Requiring JWT could materially conflict with a public account-recovery flow, but the sources do not resolve that conflict.
2. **Response contract:** No success or error status, body, message, media type, or header is documented. No security scenario may assert an exact response or redaction behavior.
3. **Storage oracle:** SEC-01 applies, but the documents specify neither the storage mechanism nor an externally observable proof. No hash/KDF algorithm, work factor, salt, or credential-history rule is supplied.
4. **Database oracle:** SEC-05 governs executed queries, but SQL statements, schemas, parameter APIs, and observability hooks are unspecified. Black-box behavior alone cannot prove parameterization.
5. **OTP expiry:** An expiry is required, but its duration, clock source, boundary condition, and clock-skew treatment are unspecified.
6. **OTP entropy:** FR-03 says random exactly 6 decimal digits and SEC-07 says at least 6 digits, but the random generator, entropy threshold beyond digit count, uniqueness expectation, and statistical acceptance criteria are not specified.
7. **OTP failure effects:** The documents do not define whether wrong, cross-email, expired, or replayed OTP attempts consume the OTP, increment an attempt counter, or affect later attempts.
8. **Abuse resistance:** OTP attempt limits, endpoint throttling, request-reset rate limits, brute-force lockout, monitoring, and alerting are not specified.
9. **Account enumeration:** The documents do not define whether status, body, timing, or messaging must conceal email existence or OTP failure reasons.
10. **Transport and headers:** The supplied base URL is HTTP for localhost. No HTTPS requirement, exact `Content-Type`, cache-control rule, or other security header is defined for this endpoint.
11. **Secret exposure:** Logging, telemetry, exception handling, response redaction, and client-side retention rules for `newPassword` and `resetToken` are not specified.
12. **Session consequences:** The documents do not state whether a successful reset revokes existing JWTs/sessions, logs the user in, returns a token, or sends a notification.
13. **Confirmation password mapping:** FR-03 requires new-password confirmation and equality, but the selected API body does not define a confirmation field or API-side mapping.
14. **Other request behavior:** Requiredness, nullability, wrong-type handling, extra properties, duplicate keys, maximum lengths, Unicode/whitespace policies, and malformed JSON behavior are unspecified.
15. **UI escaping:** SEC-04 applies when user input is displayed, but no selected-endpoint value is documented as reflected or rendered. A UI target and sink must be identified before deriving a security scenario.

## Human review decisions requested

- Decide whether SEC-02 classifies this public reset endpoint as JWT-protected. If yes, specify how an unauthenticated forgot-password/reset-password flow obtains the required JWT; if no, record that interpretation explicitly.
- Confirm whether the conditional implementation-level treatment of SEC-05 is accepted for the selected operation and whether authorized query instrumentation/source review will be available.
- Confirm whether the cross-step limitation on SEC-07 entropy is acceptable, or whether OTP issuance must be analyzed under `POST /api/forgot-password` in a separate reviewed scope.
- Confirm whether implementation-level evidence is available for SEC-01; otherwise the requirement remains applicable but not provable by a black-box API response.

## Review block

```text
Review Status: PENDING
Reviewer:
Review Notes:
Reviewed Version: POOL-A-SECURITY-PHASE1-v1
```

Generation is blocked until a human reviewer approves this exact report version or the orchestrator's exact combined Phase 1 report version containing this SECURITY analysis.
