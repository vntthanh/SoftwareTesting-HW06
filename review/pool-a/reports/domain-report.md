# DOMAIN Phase 1 Analysis — Pool A: Reset Password

## Endpoint and source identity

| Item | Value |
| --- | --- |
| Selected endpoint | `POST /api/reset-password` |
| Base URL | `http://localhost:3000` |
| API specification | `reference/api_specification.md`, SHA-256 `488CBCB790099BA9CBB34C7C80BA04C6AEC9E9EBB598F031FFA575737547B139` |
| System requirements | `reference/system_requirements.md`, version 2.0 dated 2026-05-14, SHA-256 `7859599624A8F94E7B28859F5E3EDBEE71F275E1A71043E3EFCAB10D5EE14CDD` |
| Shared normalized context | `review/pool-a/shared-api-context.md` (read-only) |
| Endpoint basis | API specification lines 44–52 |
| Related requirement basis | FR-01, system requirements lines 30–36; FR-03, lines 46–60; SEC-07, line 284 |
| Analysis phase | Phase 1 only; no test cases generated |

The API specification documents a JSON body example but no formal request schema and no response contract for this operation. In this report, **valid** and **invalid** describe whether a value satisfies an explicit source rule or the documented reset workflow. They do not assert a particular HTTP status, response body, validation order, or implementation behavior.

## Valid baseline

Documented request example:

```json
{
  "email": "test@domain.com",
  "resetToken": "123456",
  "newPassword": "NewPassword123!"
}
```

Source basis: API specification lines 46–52.

For this example to be a genuinely valid workflow baseline, all of the following setup conditions must hold:

- `email` is a registered email address (FR-03 line 50).
- `resetToken` is the 6-decimal-digit OTP generated for that same email (FR-03 lines 50–51 and 60).
- The OTP is unexpired and has not previously been used (SEC-07 line 284).
- `newPassword` contains at least eight characters, including at least one uppercase letter, one lowercase letter, one digit, and one character from `@`, `$`, `!`, `%`, `*`, `?`, `&` (FR-03 line 58 incorporating FR-01 line 34).
- The workflow's confirmation-password value equals `newPassword` (FR-03 lines 57–59). The sources do not specify a confirmation field in this endpoint's API body, so this is a setup condition only and is not added to the request.

The literal API example does not establish registration, OTP issuance, binding, expiry, or prior-use state. Accordingly, it is a value baseline only until those preconditions are established. One-factor-at-a-time domain analysis keeps every other input and all state preconditions at this valid baseline unless a reviewed interaction explicitly requires multiple changes.

## Complete parameter inventory

### Transport locations

| Location | Inventory | Exact basis |
| --- | --- | --- |
| Path | No path parameters declared | The path is the fixed `/api/reset-password` at API specification line 45 |
| Query | No query parameters declared | No query input appears in API specification lines 44–52 |
| Header | No endpoint-specific headers declared | No header input appears in API specification lines 44–52; the JWT note at line 59 applies to the subsequent Users APIs |
| Cookie | No cookie parameters declared | No cookie input appears in API specification lines 44–52 |
| Body container | A JSON object is shown as the documented representation | API specification lines 46–52 |
| Nested body fields | None declared | The example at API specification lines 47–53 contains only three top-level members |

The exact HTTP `Content-Type`, malformed-body handling, member order, duplicate-member behavior, property coercion, and additional-property behavior are not specified.

### Body fields

| Input | Location | Documented type / format | Requiredness | Nullability | Default | Allowed values and explicit constraints | Exact basis |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `email` | JSON body, top-level | Shown as a JSON string; endpoint-specific email syntax is not specified | API schema requiredness is not stated. FR-03 requires a registered email in step 1 and binds the OTP to that email | Not specified | None specified | For a valid reset workflow, it is the registered email that requested the OTP. The OTP cannot be used with a different email | API specification lines 46–52; FR-03 lines 50 and 60 |
| `resetToken` | JSON body, top-level | Shown as a JSON string; represents a decimal OTP | API schema requiredness is not stated. FR-03 step 2 requires entry of the OTP | Not specified | None specified | The generated OTP is exactly 6 random decimal digits, is bound to its requesting email, expires, and is invalidated after use. SEC-07 independently sets a minimum entropy statement of 6 digits | API specification lines 46–52; FR-03 lines 51, 57, and 60; SEC-07 line 284 |
| `newPassword` | JSON body, top-level | Shown as a JSON string; no Unicode or whitespace policy is specified | API schema requiredness is not stated. FR-03 step 2 requires a new password | Not specified | None specified | At least 8 characters; at least 1 uppercase letter, 1 lowercase letter, 1 digit, and 1 special character from `@`, `$`, `!`, `%`, `*`, `?`, `&` | API specification lines 46–52; FR-03 lines 57–58; FR-01 line 34 |

`confirmationPassword` is not inventoried as an API input. FR-03 requires a confirmation value in the workflow, but neither source specifies its API field name or mapping for this endpoint.

## Equivalence partitions

Classification legend:

- **Valid**: satisfies the cited explicit domain/workflow rule, assuming all baseline preconditions.
- **Invalid**: contradicts a cited explicit domain/workflow rule. The sources still do not define the endpoint's observable response.
- **Unspecified**: the sources do not define whether the API accepts, rejects, coerces, or otherwise handles the partition; it must not be converted into expected behavior without review.
- **Documented representation only**: present in the API example, but no formal schema or success response proves acceptance on its own.

| ID | Input / subject | Partition | Classification | Exact specification basis | Assumptions / limits |
| --- | --- | --- | --- | --- | --- |
| DP-001 | Body container | JSON object containing `email`, `resetToken`, and `newPassword` in the documented representations | Documented representation only | API specification lines 46–52 | Becomes a valid workflow request only when DP-005, DP-011, and DP-018 and all state/setup constraints hold |
| DP-002 | Body container | Well-formed JSON whose top-level value is not an object | Unspecified | API specification lines 46–52 show an object but state no schema or rejection rule | No invalid status or body may be inferred |
| DP-003 | Body container | Malformed JSON or a non-JSON payload | Unspecified | No malformed-body rule or exact media type is stated in API specification lines 44–52 | No parser behavior may be inferred |
| DP-004 | Body container | Documented members plus one or more additional members | Unspecified | No additional-property rule appears in API specification lines 44–52 | Do not assume either ignore or reject behavior |
| DP-005 | `email` | Registered email that requested the supplied usable OTP | Valid | FR-03 lines 50–51 and 60 | Requires issuance, binding, unexpired, and unused setup; email syntax validation at this endpoint is not inferred |
| DP-006 | `email` × `resetToken` | Email differs from the email that requested the supplied OTP | Invalid | FR-03 line 60: OTP is valid only for the requesting email and cannot be used for another email | Relational partition; exact comparison normalization and response are unspecified |
| DP-007 | `email` | Email is not registered | No source-supported valid workflow; endpoint behavior unspecified | FR-03 line 50 requires the user to enter a registered email in step 1 | The reset endpoint's response to such a value is not stated; no usable OTP setup can be established from the sources |
| DP-008 | `email` | Syntactically malformed or empty JSON string | Invalid | FR-03 requires a registered email; reviewed external input-validation practice requires syntactically valid structured input | Do not use an overly restrictive RFC email regex |
| DP-009 | `email` | Member omitted | Invalid | `email` is necessary to identify the account and enforce OTP-to-email binding | Reviewed external API-validation assumption |
| DP-010 | `email` | JSON `null` or a non-string JSON value | Invalid | The documented representation is a JSON string and the workflow requires an email value | Reviewed external API-validation assumption; do not coerce values |
| DP-011 | `resetToken` | Exactly 6 decimal digits and the token is the usable OTP issued for the baseline email | Valid | FR-03 lines 51, 57, and 60; SEC-07 line 284 | “Usable” means unexpired and unused; it does not establish any HTTP outcome |
| DP-012 | `resetToken` | Decimal string with fewer than 6 digits, including the empty string | Invalid OTP representation | FR-03 line 51 specifies the generated OTP as 6 digits; SEC-07 line 284 specifies minimum 6 digits | Treating `resetToken` as the step-1 generated OTP is supported by the two-step workflow and endpoint example |
| DP-013 | `resetToken` | Decimal string with more than 6 digits | Invalid representation for the generated OTP | FR-03 line 51 specifies the generated OTP as exactly 6 digits | SEC-07 alone says minimum 6, but FR-03 defines the generated workflow token as 6 digits. This classification does not claim an API length validator |
| DP-014 | `resetToken` | Six-character string containing one or more non-decimal characters | Invalid OTP representation | FR-03 line 51 specifies 6 digits | The source does not define whitespace trimming, Unicode digit handling, or coercion |
| DP-015 | `resetToken` | Member omitted | Invalid | FR-03 step 2 requires the OTP to perform the reset | Reviewed external API-validation assumption |
| DP-016 | `resetToken` | JSON `null` or a non-string JSON value | Invalid | The documented representation is a string containing the OTP | Reviewed external API-validation assumption; numeric `123456` is not treated as equivalent to string `"123456"` |
| DP-017 | `resetToken` | Exactly 6 decimal digits but not the OTP issued for the baseline email | Invalid workflow token | FR-03 lines 51 and 60 | This includes a different issued value or a value with no matching issuance; exact verification and response are unspecified |
| DP-018 | `newPassword` | Length at least 8 and contains at least 1 uppercase letter, 1 lowercase letter, 1 digit, and 1 allowed special character | Valid | FR-03 line 58 incorporates FR-01 line 34 | All clauses are conjunctive; no maximum length is stated |
| DP-019 | `newPassword` | String length 0 through 7 | Invalid | FR-01 line 34 via FR-03 line 58 | Character-count semantics are not defined; empty is included here rather than duplicated |
| DP-020 | `newPassword` | Length at least 8, but contains 0 uppercase letters | Invalid | FR-01 line 34 via FR-03 line 58 | Hold all other password clauses valid to isolate this partition |
| DP-021 | `newPassword` | Length at least 8, but contains 0 lowercase letters | Invalid | FR-01 line 34 via FR-03 line 58 | Hold all other password clauses valid to isolate this partition |
| DP-022 | `newPassword` | Length at least 8, but contains 0 digits | Invalid | FR-01 line 34 via FR-03 line 58 | Hold all other password clauses valid to isolate this partition |
| DP-023 | `newPassword` | Length at least 8, but contains 0 characters from `@`, `$`, `!`, `%`, `*`, `?`, `&` | Invalid | FR-01 line 34 via FR-03 line 58 | A non-listed punctuation character does not satisfy this clause; the source does not say that other characters are prohibited when an allowed special is also present |
| DP-024 | `newPassword` | Meets all explicit clauses and also contains characters outside the named special-character set | Unspecified beyond the clauses being met | FR-01 line 34 requires at least one listed special but does not define a complete character alphabet | Do not infer that other characters are forbidden or permitted by a separate rule |
| DP-025 | `newPassword` | Member omitted | Invalid | FR-03 step 2 requires a new password | Reviewed external API-validation assumption |
| DP-026 | `newPassword` | JSON `null` or a non-string JSON value | Invalid | The documented representation is a string and password rules apply to that string value | Reviewed external API-validation assumption; no coercion is allowed |

### Omission, null, empty, malformed, type, and set coverage check

| Concern | `email` | `resetToken` | `newPassword` | Body container |
| --- | --- | --- | --- | --- |
| Omission | DP-009 | DP-015 | DP-025 | Not applicable as a member; absent-body behavior is covered by the general malformed/missing-body gap below |
| Null | DP-010 | DP-016 | DP-026 | DP-002 if JSON `null`; behavior unspecified |
| Empty string | DP-008, behavior unspecified | DP-012, violates 6-digit representation | DP-019, violates minimum length | Empty payload is DP-003 / unspecified |
| Malformed | DP-008, endpoint syntax unspecified | DP-014 for non-digit representation | Requirement-class omissions are DP-020–DP-023; encoding/Unicode malformedness is unspecified | DP-003 |
| In-set / out-of-set | Binding relationship DP-005/DP-006; no endpoint email set is specified | Decimal digits DP-011 versus DP-014 | Allowed special set DP-018 versus DP-023 | Additional members DP-004 / unspecified |
| JSON type | DP-010 | DP-016 | DP-026 | DP-001–DP-003 |

## Boundary analysis

Only explicitly stated ordered limits are included. Values in a boundary row are conceptual representatives; they are not test cases and do not define HTTP expectations.

| ID | Input / measure | Explicit limit | Just outside / below | Boundary | Just inside / above | Classification and exact basis | Assumptions / limits |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DB-001 | `resetToken` decimal-digit count | Generated OTP has exactly 6 digits | 5 digits: invalid OTP representation | 6 digits: valid representation | 7 digits: invalid representation for the generated OTP | FR-03 line 51; SEC-07 line 284 also requires a minimum of 6 digits | FR-03 defines the actual generated token as 6 digits, so both neighboring lengths fall outside that workflow token domain; no API response is specified |
| DB-002 | `newPassword` character count | Minimum 8 characters | 7: invalid | 8: valid if all composition clauses hold | 9: valid if all composition clauses hold | FR-01 line 34 via FR-03 line 58 | The sources do not define whether length counts Unicode code points, UTF-16 units, grapheme clusters, or bytes |
| DB-003 | `newPassword` uppercase-letter count | At least 1 | 0: invalid | 1: valid if all other clauses hold | 2: valid if all other clauses hold | FR-01 line 34 via FR-03 line 58 | The source does not define the character repertoire or locale used to identify uppercase letters |
| DB-004 | `newPassword` lowercase-letter count | At least 1 | 0: invalid | 1: valid if all other clauses hold | 2: valid if all other clauses hold | FR-01 line 34 via FR-03 line 58 | The source does not define the character repertoire or locale used to identify lowercase letters |
| DB-005 | `newPassword` digit count | At least 1 | 0: invalid | 1: valid if all other clauses hold | 2: valid if all other clauses hold | FR-01 line 34 via FR-03 line 58 | The source does not define whether “digit” is ASCII decimal only or a broader Unicode class |
| DB-006 | `newPassword` allowed-special-character count | At least 1 from `@`, `$`, `!`, `%`, `*`, `?`, `&` | 0: invalid | 1: valid if all other clauses hold | 2: valid if all other clauses hold | FR-01 line 34 via FR-03 line 58 | Characters outside the listed set do not count toward this measure; the source does not prohibit additional non-listed characters |

No source-supported numeric, length, count, date/time, or other ordered boundaries exist for `email`. No maximum length is stated for any input. OTP expiry is an explicit state/time guard, but no duration or timestamp boundary is specified, so no concrete time boundary can be derived.

## Cross-parameter and state constraints

| Constraint ID | Constraint | Exact specification basis | Domain-analysis treatment |
| --- | --- | --- | --- |
| DC-001 | `resetToken` is valid only with the `email` for which it was requested; it cannot be reused with another email | FR-03 line 60 | DP-005/DP-006. This interaction must vary email and token association together when evaluating the binding rule |
| DC-002 | The reset token is the OTP generated in step 1, which is 6 decimal digits | FR-03 lines 48–51 and 57 | DP-011–DP-014 and DB-001. This does not prove a particular API validation mechanism |
| DC-003 | OTP must be unexpired | SEC-07 line 284 | Keep unexpired in the valid baseline. Expired-versus-unexpired is a state guard, but no concrete lifetime boundary exists |
| DC-004 | OTP is invalidated after use | SEC-07 line 284 | Keep unused in the valid baseline. First-use/reuse sequencing is stateful and has no specified response |
| DC-005 | All password strength clauses apply conjunctively | FR-01 line 34 via FR-03 line 58 | For a one-factor partition or boundary, hold length and all non-targeted composition clauses valid |
| DC-006 | Workflow confirmation must match `newPassword` | FR-03 lines 57–59 | Keep matching as a workflow setup condition only. The API request mapping is unspecified, so no confirmation member is invented |

## Gaps and ambiguities requiring review

1. The request has no formal schema. Field requiredness, nullability, JSON type enforcement, coercion, property order, duplicate-member handling, extra-member behavior, and missing/malformed-body behavior are unspecified.
2. The specification calls the representation JSON but does not state an exact HTTP `Content-Type` or charset.
3. FR-03 requires a registered email and token-to-email binding, but it gives no endpoint-specific email syntax rule, case-normalization rule, whitespace rule, or existence-disclosure behavior. FR-01's email-format rule is scoped to registration and was not transferred.
4. The endpoint body does not contain a confirmation-password field even though FR-03 requires confirmation in the workflow. Its API name, location, and submission mechanism are unspecified.
5. FR-03 says the generated OTP is exactly 6 random digits. SEC-07 says the OTP must have a minimum of 6 digits. This report uses exactly 6 digits for the workflow token because the concrete generation requirement is more specific, while noting that neither source states an API length-validation algorithm.
6. OTP decimal alphabet details are absent: ASCII versus Unicode digits, leading-zero preservation, whitespace trimming, and JSON numeric coercion are unspecified. The string representation in the example is not treated as a formal type rule.
7. OTP expiry exists, but no duration or comparison semantics are stated. Attempt limits, retries, rate limits, and lockout behavior are also unspecified.
8. Password maximum length, Unicode policy, whitespace policy, normalization, reuse/history policy, and exact character-count semantics are unspecified.
9. The password rule names the special characters that satisfy its required special-character class, but it does not define a complete allowed alphabet or prohibit other characters.
10. JWT applicability is ambiguous and no endpoint-specific authentication input is declared. No Authorization header was added to the input model.
11. There is no success or error response contract: no HTTP status, response body, error message, media type, header, or validation order is documented. Every invalid partition therefore lacks a source-supported observable API result beyond failure to satisfy the domain/workflow rule.
12. The example values do not prove the stateful preconditions needed for a valid reset and are not used to infer undocumented constraints.

## Review block

- **Review Status:** PENDING
- **Reviewer:** _Unassigned_
- **Review Notes:** _Awaiting human review of partition classifications, the exact-six-digit interpretation, explicit boundaries, and all recorded gaps. No test generation is authorized._
- **Reviewed Version:** _Not assigned — Phase 1 draft based on the source hashes listed above_

