# Security Analysis Report — Pool B

## Endpoint and sources

- Endpoint: `POST /api/apply-coupon`
- Functional scope: FR-09, coupon application during Checkout.
- Authoritative API source: `reference/api_specification.md`, §5.1, lines 151–163; SHA-256 `488CBCB790099BA9CBB34C7C80BA04C6AEC9E9EBB598F031FFA575737547B139`.
- Authoritative requirements source: `reference/system_requirements.md`, FR-09, lines 110–135, and SEC-01–SEC-07, lines 274–284; version 2.0, updated 2026-05-14; SHA-256 `7859599624A8F94E7B28859F5E3EDBEE71F275E1A71043E3EFCAB10D5EE14CDD`.
- Normalized context: `review/pool-b/shared-api-context.md` (read-only).
- Analysis scope: specification-supported security behavior only. No service was probed and no live credentials or attack traffic were used.

## Security characteristics

### Authentication

FR-09 C4 requires the user to have a valid JWT. SEC-02 independently requires security-sensitive APIs to require a valid JWT. The normalized context identifies `Authorization: Bearer <token>` as the system-wide transport convention, while noting that the endpoint subsection itself does not define token syntax, claims, expiration handling, or a concrete authentication error response.

### Authorization-relevant identifiers and roles

- The JSON body includes client-supplied `user_id`, and FR-09 C5 evaluates coupon use per user.
- No authoritative rule binds body `user_id` to the authenticated JWT subject. A matching JWT identity and body value is therefore valid baseline setup, not a required authorization oracle.
- This operation is a Checkout user operation, not an Admin API. No admin role requirement applies, and SEC-03 does not provide a basis for requiring `role = 'admin'` here.

### Sensitive inputs and outputs

- The bearer JWT is security-sensitive credential material. It must not be exposed in test artifacts, logs, or responses; however, token redaction behavior is not specified as an endpoint response requirement.
- `user_id` is authorization-relevant and may identify a user, but the sources do not classify it or either response amount as confidential data.
- The documented response contains `discount_amount` and `final_amount`; it does not document token, password, role, OTP, or other credential fields.

### Untrusted input surfaces

- Header: `Authorization` bearer value.
- JSON body: `code`, `total_amount`, and `user_id`.
- FR-09 C1 requires locating `code` in the database, and C5 requires evaluating user-specific use state. These rules establish database interaction, but not the implementation's query construction.

### Transport, headers, and abuse constraints

- JWT authentication is required. The shared context records the `Authorization: Bearer <token>` convention, but the endpoint section does not restate it.
- No HTTPS/TLS requirement, CORS policy, CSRF rule, security response header, rate limit, lockout, replay prevention, request-size limit, or other abuse constraint is documented for this endpoint.

## SEC-01–SEC-07 applicability matrix

All SEC IDs from SEC-01 through SEC-07 are present in the authoritative requirements.

| ID | Requirement (faithful meaning) | Applicability | Evidence and exact basis | Analysis consequence / assumptions |
| --- | --- | --- | --- | --- |
| SEC-01 | Passwords must not be stored in plaintext. | Not applicable | System requirements line 278. This operation has no password input, output, or documented password-storage behavior. | No endpoint scenario is derived. |
| SEC-02 | Security-sensitive APIs must require a valid JWT. | Applicable | System requirements line 279; FR-09 C4, line 119, explicitly requires a valid JWT for coupon application. | Derive valid-control and invalid/missing-JWT scenarios. Exact status, error schema/message, and token validation mechanism are unspecified. |
| SEC-03 | Admin APIs must verify `role = 'admin'` in the token. | Not applicable | System requirements line 280. FR-09 describes a Checkout user operation, and the path is not under `/api/admin/*`. | Do not require an admin role and do not derive admin-role scenarios. |
| SEC-04 | User-entered data displayed in the UI must be escaped and must not be rendered using direct `innerHTML`. | Not directly applicable to this API operation | System requirements line 281. `code` is user-controlled, but neither authoritative source documents UI rendering or response reflection for this endpoint. | No API-only XSS oracle is supported. Any UI rendering test belongs to a documented consuming UI flow, which is absent here. |
| SEC-05 | Database queries must use parameterized queries rather than direct string concatenation. | Applicable at the implementation/query layer | System requirements line 282; FR-09 C1, line 116, requires coupon existence lookup in the database, and C5, line 120, requires a per-user usage lookup. | Derive inert metacharacter-input scenarios asserting that input is handled as data and cannot alter query semantics. Black-box behavior can reveal a violation but cannot by itself prove parameterized-query use; implementation review/instrumentation is needed for conclusive compliance. Exact rejection response is unspecified. |
| SEC-06 | Profile update APIs must not allow the client to change `role`. | Not applicable | System requirements line 283. This is not a profile update API and has no documented `role` input. | No endpoint scenario is derived. |
| SEC-07 | Password-reset OTPs must have at least six digits, expire, and become invalid after use. | Not applicable | System requirements line 284. This operation has no password-reset or OTP behavior. | No endpoint scenario is derived. |

## Security scenario model

All example values below are inert design inputs only. They were not sent to a service. For negative scenarios, “reject or otherwise deny coupon calculation” intentionally does not prescribe an HTTP status, error body, or message because none is documented.

| Scenario ID | Precondition | Stimulus | Expected security behavior | Requirement IDs | Exact basis | Assumptions |
| --- | --- | --- | --- | --- | --- | --- |
| SS-001 | `SAVE10` is active and unexpired; `total_amount` meets its minimum; the test user has remaining usage; a valid test JWT is available. | Send the documented baseline JSON with `Authorization: Bearer <valid test JWT>`. | Authentication permits the request to proceed to the FR-09 conditions; if all conditions qualify, the documented discount response may be calculated. | SEC-02; FR-09 C4 | SEC-02, system requirements line 279; FR-09 C4, line 119; API specification §5.1, lines 154–162. | The JWT is valid under the SUT's configured issuer/signing rules. Its test identity is represented by body `user_id: 1` only as setup, not as a specified binding rule. |
| SS-002 | Same qualifying coupon and user state as SS-001. | Omit the `Authorization` header. | The operation must not apply the coupon or return a successful discounted calculation because the required valid JWT is absent. | SEC-02; FR-09 C4 | SEC-02, line 279; FR-09 C4, line 119. | Status, body, message, and challenge headers are unspecified. |
| SS-003 | Same qualifying coupon and user state as SS-001. | Supply an `Authorization` value that is not a valid bearer JWT, such as an inert malformed token placeholder. | The operation must not apply the coupon or return a successful discounted calculation because the JWT is invalid. | SEC-02; FR-09 C4 | SEC-02, line 279; FR-09 C4, line 119. | Exact bearer grammar and malformed-token classification are unspecified. Status, body, and message are unspecified. |
| SS-004 | Same qualifying coupon and user state as SS-001; create a test JWT whose signature is invalid for the SUT. | Send the baseline request with the invalid-signature test JWT. | The operation must not apply the coupon or return a successful discounted calculation; a token without a valid signature is not a valid JWT credential. | SEC-02; FR-09 C4 | SEC-02, line 279; FR-09 C4, line 119. | JWT signing algorithm, issuer, audience, claim rules, and exact response are unspecified. The invalid-signature setup must be established without using live credentials. |
| SS-005 | Same qualifying coupon and user state as SS-001; create a test JWT that is expired according to the SUT's accepted time claim semantics. | Send the baseline request with the expired test JWT. | The operation must not apply the coupon or return a successful discounted calculation because an expired JWT is not valid. | SEC-02; FR-09 C4 | SEC-02, line 279; FR-09 C4, line 119. | The sources do not define required claims, clock skew, timezone, or expiry validation details; the test environment must establish that the SUT recognizes the token as expired. Exact response is unspecified. |
| SS-006 | A valid test JWT is present; the coupon lookup database contains only controlled test data; the user has no coupon matching the supplied literal. | Send `code` as an inert SQL-like literal such as `' OR '1'='1` in otherwise baseline JSON. | The `code` value must be handled as data, must not change query structure or match an unrelated coupon, and must not expose database contents or query diagnostics. The request may be rejected or treated as a nonexistent coupon. | SEC-05; FR-09 C1 | SEC-05, system requirements line 282; FR-09 C1, line 116. | HTTP status, message, error schema, and diagnostic-redaction wording are unspecified. A black-box pass does not conclusively prove parameterized-query use. |
| SS-007 | A valid test JWT is present; the database and usage records are isolated test fixtures. | Send `code` as an inert statement-delimiter/comment-like literal such as `SAVE10'; SELECT 1; --` in otherwise baseline JSON. | The entire value must remain data; it must not execute an additional statement, alter coupon or usage state, expose database contents, or return query diagnostics. It may only be handled according to normal literal coupon-code semantics. | SEC-05; FR-09 C1, C5 | SEC-05, line 282; FR-09 C1 and C5, lines 116 and 120. | The database engine and driver are unspecified. No state mutation is documented for this endpoint; fixture inspection may detect an unexpected injection side effect, but source/code review is required to prove parameterization. Exact response is unspecified. |
| SS-008 | A valid test JWT is present; coupon and per-user usage records are isolated controlled fixtures; no user is identified by the supplied literal. | Send client-controlled body `user_id` as a controlled inert SQL/metacharacter string such as `1' OR '1'='1` in otherwise baseline JSON. | The complete `user_id` value must remain data and must not alter query semantics, broaden or bypass the per-user usage scope, select another user's usage record, or change database state. No HTTP status, error schema, or message is prescribed. | SEC-05; FR-09 C5 | SEC-05, system requirements line 282; FR-09 C5, line 120. | The documented example represents `user_id` as a JSON number, but type validation and coercion are unspecified; the string is an inert security-analysis input, not a claimed valid domain value. A black-box pass cannot conclusively prove parameterized-query use. Identity binding to the JWT is separately unspecified. |

## Coverage summary

- Applicable explicit security requirements covered: SEC-02 and SEC-05.
- SEC-02 coverage: one authenticated control plus missing, malformed, invalid-signature, and expired JWT classes.
- SEC-05 coverage: coupon lookup with tautology-like and statement-delimiter-like values, plus client-controlled `user_id` in the per-user usage lookup with a controlled inert SQL/metacharacter value. Assertions are limited to data treatment, unchanged query semantics and usage scope, and absence of database-state alteration; no HTTP status oracle is invented.
- Requirements intentionally producing no endpoint scenario: SEC-01, SEC-03, SEC-04, SEC-06, and SEC-07, for the applicability reasons recorded above.

## Gaps and review decisions needed

1. **JWT/body identity binding:** No rule states that body `user_id` must equal the authenticated JWT subject. SS-008 covers `user_id` only as an SEC-05 database-query input; cross-user identity binding cannot be asserted as an authorization requirement without an approved additional assumption or an authoritative source update.
2. **JWT validation contract:** Required claims, issuer, audience, signing algorithms, expiry/clock-skew rules, revocation, and malformed-token handling are not specified. SS-004 and SS-005 use environment-established invalid tokens without inventing those details.
3. **Authentication failure contract:** No HTTP status, error schema, exact message, `WWW-Authenticate` header, or response precedence is specified.
4. **Parameterized-query verification:** SEC-05 states an implementation requirement. Black-box inert-input scenarios for both coupon `code` and client-controlled `user_id` may detect unsafe query behavior but cannot prove parameterization; conclusive verification requires source review, query instrumentation, or equivalent implementation evidence.
5. **Input schema:** Requiredness, types beyond the example representations, nullability, coercion, length, pattern, and additional-property behavior are unspecified. This report does not turn those gaps into security constraints.
6. **Output and diagnostic disclosure:** No error response or redaction rule is documented. SEC-05 supports expecting query inputs not to change semantics; it does not supply exact error-content assertions.
7. **UI/XSS boundary:** SEC-04 concerns UI rendering. The sources do not identify a UI sink or state that `code` is reflected, so an API-only XSS case would be speculative.
8. **Transport and abuse controls:** HTTPS, rate limiting, replay resistance, request-size limits, CORS, and CSRF behavior are not specified and therefore have no candidate basis in this model.
9. **State mutation:** The operation is documented as a calculation. No usage increment, reservation, coupon consumption, or other side effect is specified, so security scenarios must not assert such mutation.

## Human review

- Review Status: APPROVED
- Reviewer: Human review (2026-08-23)
- Review Notes: Approved after final cross-artifact review. SEC-02 and SEC-05 applicability, the limits of black-box parameterization evidence, and the absence of a specified JWT/body identity-binding rule are correctly preserved in the retained candidates and execution triage.
- Reviewed Version: `security-report-v2; endpoint-context API 488CBCB790099BA9CBB34C7C80BA04C6AEC9E9EBB598F031FFA575737547B139 / requirements 7859599624A8F94E7B28859F5E3EDBEE71F275E1A71043E3EFCAB10D5EE14CDD`

The exact report version above is approved for the retained Pool B suite.
