# Shared API Context — Pool B

## Source identity

- API specification: `reference/api_specification.md`, section 5.1, lines 151–163; SHA-256 `488CBCB790099BA9CBB34C7C80BA04C6AEC9E9EBB598F031FFA575737547B139`.
- System requirements: `reference/system_requirements.md`, FR-09, lines 110–135; FR-17, lines 213–216; security requirements, lines 274–284; version 2.0, updated 2026-05-14; SHA-256 `7859599624A8F94E7B28859F5E3EDBEE71F275E1A71043E3EFCAB10D5EE14CDD`.
- These two documents are authoritative. Facts below identify their exact section or line basis. Examples are not promoted to constraints.

## Selected operation

| Item | Value | Exact basis |
| --- | --- | --- |
| Method and path | `POST /api/apply-coupon` | API specification §5.1, line 154 |
| Summary | Calculate the total after applying a discount and return JSON containing `discount_amount` and `final_amount`. | API specification §5.1, line 155 |
| Operation ID | Not documented. | API specification §5.1, lines 153–163 |
| Base URL | `http://localhost:3000` | API specification introduction |
| Functional requirement | FR-09, coupon application during Checkout | System requirements FR-09, lines 110–126 |

The method/path lookup is unique in the supplied API specification.

## Input inventory

### Header

| Name | Requiredness | Type/format | Allowed values / constraints | Basis |
| --- | --- | --- | --- | --- |
| `Authorization` | Required for coupon application | Bearer authentication header carrying a JWT | JWT must be valid. No token syntax, claims, expiry handling, or error response is specified beyond validity. | FR-09 C4, line 119; SEC-02, line 279 |

### JSON body

Request media type is documented as JSON. No alternate request media type is documented (API specification §5.1, lines 156–162).

| Field | Location | Requiredness | Documented representation | Format / allowed values / nullability / default / explicit constraints | Basis |
| --- | --- | --- | --- | --- | --- |
| `code` | Body | Not explicitly stated | JSON string in the documented body (`"SAVE10"`) | Coupon must exist and have `is_active = 1` to qualify. No length, casing, whitespace, pattern, nullability, or default is specified. | API specification §5.1, lines 156–162; FR-09 C1, line 116 |
| `total_amount` | Body | Not explicitly stated | JSON number in the documented body (`500000`) | Must be greater than or equal to the coupon's `min_order_amount` to qualify. No general minimum, maximum, integer/decimal rule, precision, nullability, or default is specified. | API specification §5.1, lines 156–162; FR-09 C3, line 118 |
| `user_id` | Body | Not explicitly stated | JSON number in the documented body (`1`) | Per-user prior usage must be less than `max_uses_per_user`. No relationship between this body value and the authenticated JWT identity, numeric range, integer rule, nullability, or default is specified. | API specification §5.1, lines 156–162; FR-09 C5, line 120 |

There are no documented path parameters, query parameters, cookie parameters, or other request headers for this operation.

### Related stored coupon attributes (not request fields)

| Attribute | Documented rule | Basis |
| --- | --- | --- |
| `is_active` | Must equal `1` for the coupon to qualify. | FR-09 C1, line 116 |
| `expired_at` | The current date must be before `expired_at`. Equality is not valid. | FR-09 C2, line 117 |
| `min_order_amount` | Coupon qualifies when total is `>= min_order_amount`; coupon creation constrains it to `>= 0`. | FR-09 C3, line 118; FR-17, line 216 |
| `max_uses_per_user` | Prior uses by the user must be `< max_uses_per_user`; coupon creation constrains it to `>= 1`. | FR-09 C5, line 120; FR-17, line 216 |
| `type` | Coupon creation allows `percent` or `fixed`. | FR-17, line 216 |
| `discount_value` | Coupon creation requires a positive value. | FR-17, line 216 |

### Documented sample coupon fixtures

| Code | Type | Value | Minimum order | Expiry | Uses/user | Basis |
| --- | --- | ---: | ---: | --- | ---: | --- |
| `SAVE10` | `percent` | 10% | 300000 | 2099-12-31 | 1 | FR-09, lines 128–132 |
| `BIGBUY` | `fixed` | 50000 | 500000 | 2099-12-31 | 1 | FR-09, lines 128–133 |
| `VIP100` | `fixed` | 100000 | 300000 | 2099-12-31 | 2 | FR-09, lines 128–134 |
| `EXPIRED` | `percent` | 20% | 100000 | 2020-01-01 | 1 | FR-09, lines 128–135 |

## Response inventory

| Response aspect | Documented contract | Exact basis |
| --- | --- | --- |
| Status codes | None documented, for success or failure. | API specification §5.1, lines 153–163 |
| Media type | JSON is explicitly stated for the returned structure; no concrete MIME string or alternate media type is documented. | API specification §5.1, line 155 |
| Body fields | JSON contains `discount_amount` and `final_amount`. Requiredness, JSON types, formats, nullability, additional properties, and error schemas are not explicitly documented. | API specification §5.1, line 155 |
| Response headers | None documented. | API specification §5.1, lines 153–163 |
| Percent calculation | `discount_amount = total × discount_value / 100`. | FR-09, line 124 |
| Fixed calculation | `discount_amount = discount_value`. | FR-09, line 125 |
| Final amount | `final_amount = total - discount_amount`. | FR-09, line 126 |

## Authentication and authorization

- Coupon application requires a valid JWT because FR-09 C4 states that the user must have one (FR-09, line 119).
- SEC-02 independently requires a valid JWT for security-sensitive APIs (line 279); FR-09 makes applicability explicit for this endpoint.
- No admin role is required or documented. SEC-03 concerns Admin APIs, while this endpoint is not under `/api/admin/*` and is a Checkout user operation (FR-09, lines 110–112).
- No authorization rule defines whether the client-supplied `user_id` must equal the JWT subject. This is an ambiguity, not a stated requirement.

## Security requirements SEC-01–SEC-07

| ID | Requirement | Endpoint applicability evidence |
| --- | --- | --- |
| SEC-01 | Passwords must not be stored in plaintext. | Present at line 278; no password input, output, or storage behavior is involved in this operation, so no direct applicability is documented. |
| SEC-02 | Security-sensitive APIs must require a valid JWT. | Present at line 279 and directly applicable through FR-09 C4, line 119. |
| SEC-03 | Admin APIs must verify `role = 'admin'` in the token. | Present at line 280; this is not documented as an Admin API, so no direct applicability is established. |
| SEC-04 | User-entered data displayed in the UI must be escaped and not rendered with direct `innerHTML`. | Present at line 281; `code` is user-controlled, but this API's response/UI reflection behavior is not documented. Applicability to an API-only assertion is not established by the sources. |
| SEC-05 | Database queries must use parameterized queries rather than string concatenation. | Present at line 282. `code` and `user_id` plausibly participate in database lookup, but the implementation/data-flow is not specified; the security specialist must distinguish the global requirement from black-box observability assumptions. |
| SEC-06 | Profile update APIs must not permit client changes to `role`. | Present at line 283; this endpoint is not a profile update operation, so not applicable. |
| SEC-07 | Password-reset OTP must have at least six digits, expire, and become invalid after use. | Present at line 284; this endpoint has no OTP behavior, so not applicable. |

No SEC identifier from SEC-01 through SEC-07 is absent from the supplied requirements.

## Documented functional and contract rules

1. The operation is `POST /api/apply-coupon` (API specification §5.1, line 154).
2. The documented body is JSON and contains `code`, `total_amount`, and `user_id` in the example structure (API specification §5.1, lines 156–162). The source does not explicitly declare these fields required.
3. Coupon application requires all five FR-09 conditions simultaneously: active existing code, unexpired date, threshold met inclusively, valid JWT, and remaining per-user usage (FR-09, lines 112–120).
4. A percent coupon uses the percent formula; a fixed coupon uses the fixed formula; final amount subtracts the discount (FR-09, lines 122–126).
5. The response is JSON containing `discount_amount` and `final_amount` (API specification §5.1, line 155).
6. No status codes, error structures, exact messages, rejection precedence, rounding rules, maximum discount cap, or side-effect rules are documented.

## State-dependent preconditions and related operations

- Eligibility depends on stored coupon conditions: existence/active flag and expiry (FR-09 C1–C2, lines 116–117).
- Eligibility depends on a user-specific prior-use condition: prior uses must be strictly less than `max_uses_per_user` (FR-09 C5, line 120).
- The endpoint description says it calculates a discounted total (API specification §5.1, line 155). Neither authoritative source states that calling this endpoint increments the usage count, reserves a coupon, consumes a use, or changes any state.
- Therefore, these are state-dependent preconditions but do not form a documented endpoint-driven state transition model for `POST /api/apply-coupon`. Keep active/inactive, expiry, and usage-limit coverage under DOMAIN rather than STATE.
- Coupon setup can be treated as a precondition using documented admin coupon management (`POST /api/admin/coupons` in API specification §6.4 and FR-17), but this Pool B scope selects only `POST /api/apply-coupon`.
- FR-09 places coupon entry at Checkout (lines 110–112), but no sequencing or coupling with `POST /api/checkout` is specified.

## Normalized test model

### Valid baseline request

- Precondition: `SAVE10` has the documented fixture properties, is active, current date is before 2099-12-31, and the authenticated user has used it zero times.
- Header: `Authorization: Bearer <valid JWT for the test user>`.
- JSON body: `{"code":"SAVE10","total_amount":500000,"user_id":1}`.
- Formula oracle: `discount_amount = 50000` and `final_amount = 450000`.
- Assumption limited to setup: the JWT identifies the test user represented by `user_id: 1`; the sources do not define that mapping rule.

### Parameter model

- `code`: distinguish documented existing active fixtures, documented expired fixture, nonexistent code, inactive existing code where a fixture can be arranged, and malformed/type/null/empty/omitted variants only as contract/domain explorations whose exact rejection response remains unspecified.
- `total_amount`: explicit business boundary exists at each coupon's `min_order_amount`; test just below, exactly equal, and above using documented fixtures. Other numeric/type/null/omission classes may be analyzed, but no general lower/upper/precision limits are specified.
- `user_id`: user-specific usage state is material. The source provides no numeric boundaries or JWT/body identity binding rule.
- `Authorization`: valid JWT is required. Missing, malformed, invalid, or expired-token behavior/status/message is not specified, though these are supported invalid validity classes for review under C4/SEC-02.

### Response model

- On a qualifying application, verify JSON includes both documented fields and the formula results.
- For nonqualifying requests, verify only behavior approved during review; authoritative sources do not define status, body schema, message, or whether calculation fields are absent.

### State applicability

- `State Applicability: NOT_APPLICABLE` for endpoint-driven transition testing. The exact basis is that FR-09 C1, C2, and C5 define state-dependent eligibility preconditions, while API specification §5.1 line 155 documents only calculation and neither source documents a trigger-driven state change, destination state, lifecycle sequence, consumption, usage increment, reservation, or idempotency rule for this endpoint.
- Coupon active/inactive, unexpired/at-or-past-expiry, and per-user usage below/at/above the limit remain DOMAIN partitions and boundaries.

### Security characteristics

- Valid-JWT gate is explicit (FR-09 C4; SEC-02).
- User-controlled surfaces are `code`, `total_amount`, `user_id`, and the bearer-token header.
- `code` and client-controlled `user_id` may be database lookup inputs because FR-09 C1 requires coupon lookup and C5 requires per-user usage lookup. SEC-05 is the explicit database-query requirement. Controlled inert SQL/metacharacter inputs should cover both surfaces without inventing an HTTP status oracle; black-box behavior cannot conclusively prove parameterization.
- The body `user_id` alongside JWT identity creates an authorization ambiguity; no ownership/binding behavior may be stated as required unless approved explicitly as an assumption.

## Ambiguities and assumptions

### Specification gaps (facts)

- Requiredness, formal JSON schema, additional-properties behavior, nullability, coercion, and defaults are undocumented for all body fields.
- HTTP response statuses, error body schemas/messages, and response headers are undocumented.
- JWT transport is implied by SEC-02 and the system-wide convention `Authorization: Bearer <token>`, but FR-09 C4 itself names only a valid JWT; the endpoint subsection does not repeat the header.
- No rule binds `user_id` to the authenticated JWT identity.
- No rounding/precision/currency-unit rules or lower bound preventing a negative `final_amount` are documented.
- Exact expiry-time/timezone semantics are not documented beyond “current date must be before `expired_at`.”
- No rejection priority is documented when multiple conditions fail.
- No consumption or other side effect is documented for applying a coupon.

### Working assumptions for analysis only

- Use JSON lexical representations from the documented body as baseline types, while labeling type-validation expectations unspecified.
- Use the documented sample coupons as fixtures, not universal domain constraints.
- Treat a matching authenticated user/JWT and `user_id` as baseline setup only; do not claim the match is contractually required.
- Do not invent status codes, error messages, rounding behavior, or state mutations.
