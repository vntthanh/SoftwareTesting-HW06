# CONTRACT Analysis Report — Pool B

## Endpoint and source identity

| Item | Value |
| --- | --- |
| Endpoint | `POST /api/apply-coupon` |
| Functional requirement | FR-09 — Mã Giảm Giá (Coupon) |
| API specification | `reference/api_specification.md`, §5.1, lines 151–163; SHA-256 `488CBCB790099BA9CBB34C7C80BA04C6AEC9E9EBB598F031FFA575737547B139` |
| System requirements | `reference/system_requirements.md`, FR-09 lines 110–135, FR-17 lines 213–216, and security requirements lines 274–284; version 2.0, updated 2026-05-14; SHA-256 `7859599624A8F94E7B28859F5E3EDBEE71F275E1A71043E3EFCAB10D5EE14CDD` |
| Normalized context | `review/pool-b/shared-api-context.md` (read-only) |
| Analysis scope | Request and response contract only; no test cases generated |

The API specification and system requirements are authoritative. The documented JSON request is treated as an example representation, not as a complete formal schema. Sample coupons are fixtures, not universal domain constraints.

## Request inventory

### Operation and media type

| Aspect | Documented contract | Exact basis |
| --- | --- | --- |
| Method | `POST` | API specification §5.1, line 154 |
| Path | `/api/apply-coupon` | API specification §5.1, line 154 |
| Request body media | Body is identified as JSON | API specification §5.1, lines 156–162 |
| Concrete `Content-Type` value | Not documented | API specification §5.1, lines 153–163 |
| Alternate request media types | Not documented | API specification §5.1, lines 153–163 |

### Headers

| Name | Requiredness | Representation / constraints | Exact basis |
| --- | --- | --- | --- |
| `Authorization` | A valid JWT is required for coupon application. | System-wide transport convention is `Authorization: Bearer <token>`. Token syntax, claims, expiry handling, and failure response are not defined for this endpoint. | FR-09 C4, line 119; SEC-02, line 279; normalized shared context, “Authentication and authorization” |

No path parameters, query parameters, cookies, or other request headers are documented for this operation.

### JSON body

| Field | Documented representation | Requiredness | Format / enum / nullability / default / structural constraints | Exact basis |
| --- | --- | --- | --- | --- |
| `code` | JSON string in the example (`"SAVE10"`) | Not explicitly stated | No length, casing, whitespace, pattern, nullability, or default is stated. For coupon eligibility, the code must identify an existing active coupon. | API specification §5.1, lines 156–162; FR-09 C1, line 116 |
| `total_amount` | JSON number in the example (`500000`) | Not explicitly stated | No integer/decimal rule, general minimum/maximum, precision, nullability, or default is stated. Eligibility requires the value to be at least the coupon's `min_order_amount`. | API specification §5.1, lines 156–162; FR-09 C3, line 118 |
| `user_id` | JSON number in the example (`1`) | Not explicitly stated | No integer rule, range, nullability, default, or binding to the JWT identity is stated. The per-user prior-use condition depends on a user identity. | API specification §5.1, lines 156–162; FR-09 C5, line 120 |

The sources do not define an enclosing JSON Schema, additional-property behavior, array handling, duplicate-key behavior, coercion, or behavior for an absent/malformed body.

## Response inventory

### Status and media type

| Aspect | Documented contract | Exact basis |
| --- | --- | --- |
| Success status | Not documented | API specification §5.1, lines 153–163 |
| Failure statuses | Not documented | API specification §5.1, lines 153–163; FR-09, lines 112–126 |
| Success media type | Response is described as JSON; no concrete MIME string is stated | API specification §5.1, line 155 |
| Failure media types | Not documented | API specification §5.1, lines 153–163 |
| Response headers | None documented | API specification §5.1, lines 153–163 |

### Successful response body

| Property | Required presence | Type / format / nullability | Semantic value | Exact basis |
| --- | --- | --- | --- | --- |
| `discount_amount` | The successful JSON is stated to contain this property | Formal JSON type, number format, precision, and nullability are not explicitly stated | For `percent`, `total × discount_value / 100`; for `fixed`, `discount_value` | API specification §5.1, line 155; FR-09, lines 124–125 |
| `final_amount` | The successful JSON is stated to contain this property | Formal JSON type, number format, precision, and nullability are not explicitly stated | `total - discount_amount` | API specification §5.1, line 155; FR-09, line 126 |

Additional response properties are neither allowed nor forbidden explicitly. No response schema is documented for a nonqualifying coupon, invalid request, or authentication failure.

## Contract rules

| ID | Target | Valid condition | Invalid / negative condition | Expected contract behavior | Exact specification basis | Assumptions / limits |
| --- | --- | --- | --- | --- | --- | --- |
| CR-001 | Operation | Request uses `POST /api/apply-coupon`. | Another method or path does not match the documented operation. | The coupon-application contract applies to the documented method/path only. No status or error response for an unmatched method/path is specified. | API specification §5.1, line 154 | No rejection status such as 404 or 405 may be asserted from these sources. |
| CR-002 | Request body media/shape | The baseline request body is JSON and includes the documented members `code`, `total_amount`, and `user_id`. | Non-JSON media, malformed JSON, a non-object top level, omitted members, or extra members are outside the described example. | JSON is the only documented request representation. Acceptance/rejection and the exact response for each negative variant are unspecified. | API specification §5.1, lines 156–162 | The example does not establish a formal required-property or `additionalProperties` rule. |
| CR-003 | `code` representation | The documented baseline represents `code` as a JSON string. | Non-string, `null`, empty, whitespace-only, or omitted `code` is not specified by the request contract. | A string is the documented representation; validation behavior for negative structural variants is unspecified. Independently, a nonexisting or inactive code fails FR-09 C1 eligibility. | API specification §5.1, lines 156–162; FR-09 C1, line 116 | Do not infer casing, trimming, length, or pattern rules. |
| CR-004 | `total_amount` representation | The documented baseline represents `total_amount` as a JSON number. | Non-number, `null`, omitted, non-finite, or precision variants are not specified. | A number is the documented representation; structural validation behavior is unspecified. A value below the selected coupon's threshold fails FR-09 C3, while equality qualifies. | API specification §5.1, lines 156–162; FR-09 C3, line 118 | No general numeric range, integer-only rule, precision rule, or coercion rule is defined. |
| CR-005 | `user_id` representation | The documented baseline represents `user_id` as a JSON number and the user has remaining uses. | Non-number, `null`, omitted, or out-of-range variants are not specified; prior use at the limit fails FR-09 C5. | A number is the documented representation. Coupon qualification requires prior uses `< max_uses_per_user`; exact structural or business failure responses are unspecified. | API specification §5.1, lines 156–162; FR-09 C5, line 120 | The sources do not bind `user_id` to the JWT subject or define integer/range rules. |
| CR-006 | Authentication prerequisite | Request is associated with a valid JWT. | Missing or invalid JWT does not satisfy FR-09 C4. | Only requests meeting the valid-JWT condition qualify for coupon application. Status, headers, body, message, and precedence for failure are unspecified. | FR-09 C4, line 119; SEC-02, line 279 | Bearer-header transport follows the documented system convention; token validation details are absent. |
| CR-007 | Successful response structure | All five FR-09 conditions are met and a coupon calculation succeeds. | One or more FR-09 conditions fails. | On success, return JSON containing both `discount_amount` and `final_amount`. The failure response contract is unspecified. | API specification §5.1, line 155; FR-09, lines 112–120 | Formal property types, additional properties, nullability, and status code remain unspecified. |
| CR-008 | Percent calculation | Qualifying coupon has `type = percent`. | A returned `discount_amount` differs from `total × discount_value / 100`. | `discount_amount` equals `total × discount_value / 100`. | FR-09, line 124 | No rounding or precision rule is defined. Use values with an exact expected result unless review approves a precision oracle. |
| CR-009 | Fixed calculation | Qualifying coupon has `type = fixed`. | A returned `discount_amount` differs from `discount_value`. | `discount_amount` equals `discount_value`. | FR-09, line 125 | No cap at `total_amount` or lower-bound rule for `final_amount` is defined. |
| CR-010 | Final amount calculation | A qualifying percent or fixed coupon is applied. | A returned `final_amount` differs from `total - discount_amount`. | `final_amount` equals `total - discount_amount`. | FR-09, line 126 | No currency unit, rounding, or precision rule is defined. |
| CR-011 | Documented percent fixture oracle | With the documented `SAVE10` fixture arranged as active, `total_amount = 500000`, valid JWT, and zero prior uses, all eligibility conditions hold. | Returned success structure or values do not match the formulas. | JSON contains `discount_amount = 50000` and `final_amount = 450000`. | FR-09, lines 112–132; API specification §5.1, lines 155–162 | Setup assumes the authenticated test user is represented by `user_id = 1`; this is not a normative JWT/body binding rule. |
| CR-012 | Documented fixed fixture oracle | With the documented `BIGBUY` fixture arranged as active, `total_amount = 500000`, valid JWT, and zero prior uses, all eligibility conditions hold. | Returned success structure or values do not match the formulas. | JSON contains `discount_amount = 50000` and `final_amount = 450000`. | FR-09, lines 112–133; API specification §5.1, line 155 | Fixture activation and current unexpired status must be established as preconditions. |

## Positive and negative contract coverage model

Supported positive checks are: route identity; a JSON body using the three documented representations; a valid-JWT request satisfying all five eligibility conditions; presence of both response properties; and exact percent, fixed, and final-amount calculations where rounding is not implicated.

Supported negative checks with a determinate semantic oracle are limited to formula mismatches and the fact that a missing/invalid JWT or failed C1–C5 condition does not qualify for application. The sources do **not** define the observable HTTP contract for those failures. Structural mutations such as missing fields, wrong JSON types, `null`, extra properties, malformed JSON, or alternate media types are valid contract explorations, but their acceptance/rejection, status, and error body cannot be asserted unless the reviewer approves an explicit assumption or supplies additional authority.

## Cross-category disposition

- Active/inactive coupon status, the before/at/after-expiry conditions, and per-user prior usage below/at/above `max_uses_per_user` are state-dependent eligibility inputs to this endpoint and remain DOMAIN partitions and boundaries.
- `State Applicability: NOT_APPLICABLE` for endpoint-driven transition testing. The endpoint is documented as calculating a discounted total, and neither authoritative source documents that this call changes coupon status, increments usage, consumes or reserves a coupon, or otherwise produces a destination state.
- Valid-JWT enforcement remains SECURITY/CONTRACT coverage. SEC-05 checks for the client-controlled `code` and `user_id` database lookup surfaces remain SECURITY coverage and must use controlled inert inputs without asserting an undocumented HTTP status.

## Gaps and ambiguities requiring review

1. Requiredness is not explicitly declared for `code`, `total_amount`, or `user_id`.
2. No formal request schema defines types, nullability, formats, defaults, coercion, duplicate-key handling, or additional properties.
3. The API section labels the body JSON but does not specify a concrete request `Content-Type` header value or behavior for unsupported media types.
4. No success or failure HTTP status codes are documented.
5. No error body shape, required error properties, exact message, error media type, or rejection precedence is documented.
6. The success response properties have semantic calculation rules, but no formal JSON types, number formats, precision, rounding, nullability, or additional-property rule.
7. No rule binds body `user_id` to the authenticated JWT identity.
8. JWT syntax, claims, expiration interpretation, challenge headers, and endpoint-specific authentication failure behavior are not documented.
9. Expiry uses “current date before `expired_at`,” but timezone and time-of-day semantics are absent.
10. No maximum-discount cap or rule preventing a negative `final_amount` is documented.
11. The endpoint is described as a calculation. No usage-count increment, reservation, coupon consumption, idempotency, or other response-affecting side effect is specified.

## Analysis assumptions

- Use the lexical JSON representations in the documented request as the valid baseline, without treating the example as a complete formal schema.
- Use documented sample coupons as controlled fixtures, while preserving their state (active/inactive and prior-use count) explicitly in test preconditions.
- For the baseline only, the valid JWT identifies the test user represented by `user_id: 1`; this does not create a general identity-binding requirement.
- Do not infer status codes, error payloads, error messages, property rejection, coercion, rounding, or state mutations.

## Human review

- **Review Status: APPROVED**
- **Reviewer:** Human review (2026-08-23)
- **Review Notes:** Approved after final cross-artifact review. Active/inactive, expiry, and usage-limit coverage belongs to DOMAIN; endpoint-driven STATE transition testing is not applicable; SEC-05 `user_id` coverage belongs to SECURITY. The contract inventory, rules, gaps, and assumptions remain consistent with the authoritative sources and the retained candidates.
- **Reviewed Version:** `contract-report-v2 — 2026-08-22`
