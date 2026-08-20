# Shared API Context — Pool A

## Source identity

- API specification: `reference/api_specification.md`, SHA-256 `488CBCB790099BA9CBB34C7C80BA04C6AEC9E9EBB598F031FFA575737547B139`.
- System requirements: `reference/system_requirements.md`, version 2.0 dated 2026-05-14, SHA-256 `7859599624A8F94E7B28859F5E3EDBEE71F275E1A71043E3EFCAB10D5EE14CDD`.
- Selected operation: API specification lines 44–52, `POST /api/reset-password`.
- Related authoritative requirements: FR-01 at system requirements lines 30–36; FR-03 at lines 46–60; SEC-01–SEC-07 at lines 274–284.
- Base URL: `http://localhost:3000` (API specification introductory metadata).

## Phase 2 reviewed authority overlay

The user explicitly approved the exact Phase 1 report files currently on disk on 2026-08-20 and directed Phase 2 to continue. This explicit approval is the review gate even though the report templates still contain stale `PENDING` markers.

| Reviewed report | Approved SHA-256 |
| --- | --- |
| `reports/contract-report.md` | `DF8A9603E9125CBB7E50C1579A8FC039F921EC52AD047FDEDA7B2195DD40DA4A` |
| `reports/domain-report.md` | `AAECA27F28ED86824746400554D5A15515C41F5DCCF88CED3626AD67FD31EB27` |
| `reports/state-report.md` | `59F8DAC3A97C89F3BE7CF5E286457FDAEE7ADDB54C5E1530C92B59A67878CD99` |
| `reports/security-report.md` | `824D889B0CC9FB8EA986485FF4F49CFD76B449FBE21652E232F87071A367906A` |

For Phase 2, specification facts remain authoritative for SUT behavior and the approved Phase 1 edits are test-design authority. Reviewed external assumptions must be labeled as such in candidate `Specification Basis` and `Assumptions / Notes`.

When an older narrative sentence conflicts with a manually revised structured rule, partition, transition, applicability, or scenario row, the structured row controls. This resolves two internal stale-text conflicts without reopening Phase 1:

1. STATE `TR-005` controls: weak-password rejection leaves the OTP in `ST-01` and does not change the password, as a reviewed external workflow assumption. The older summary/gap statement that token consumption is unspecified is superseded for this transition.
2. The SECURITY SEC-02 matrix controls: JWT is `NOT APPLICABLE` to this unauthenticated recovery endpoint, as a reviewed external password-reset assumption. Older coverage/gap text calling JWT applicability unresolved is superseded.

## Selected operation

| Property | Documented value | Exact basis |
| --- | --- | --- |
| Method | `POST` | API specification line 45 |
| Path | `/api/reset-password` | API specification line 45 |
| Summary | Đặt lại mật khẩu (Reset password) | API specification heading at line 44 |
| Operation ID | Not specified | No operation ID appears in API specification lines 44–52 |

## Request contract

The API specification labels the body as JSON and provides this example (lines 46–52):

```json
{
  "email": "test@domain.com",
  "resetToken": "123456",
  "newPassword": "NewPassword123!"
}
```

### Input inventory

| Input | Location | Documented representation | Requiredness | Nullability | Default | Allowed values / explicit constraints | Exact basis |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `email` | JSON body | JSON string in example | Reviewed as required because it identifies the account and enforces OTP binding; formal schema requiredness is not stated | Reviewed invalid when omitted, `null`, or non-string; source nullability is not stated | None specified | The OTP is valid only for the email that requested it; it cannot be used for another email. Malformed/empty email is reviewed invalid without an overly restrictive regex. | API specification lines 46–52; FR-03 lines 48–60; approved CONTRACT gaps 1–2 and DOMAIN DP-008–DP-010 |
| `resetToken` | JSON body | JSON string in example | Reviewed as required for step 2; formal schema requiredness is not stated | Reviewed invalid when omitted, `null`, or non-string, with no coercion; source nullability is not stated | None specified | The generated OTP has exactly 6 decimal digits; SEC-07 additionally says minimum 6 digits, expiry, and invalidation after use | API specification lines 46–52; FR-03 lines 48–60; SEC-07 line 284; approved DOMAIN DP-015–DP-016 |
| `newPassword` | JSON body | JSON string in example | Reviewed as required for step 2; formal schema requiredness is not stated | Reviewed invalid when omitted, `null`, or non-string, with no coercion; source nullability is not stated | None specified | Minimum 8 characters and at least one uppercase letter, one lowercase letter, one digit, and one special character from `@`, `$`, `!`, `%`, `*`, `?`, `&` | API specification lines 46–52; FR-03 line 58 incorporates FR-01; FR-01 line 34; approved DOMAIN DP-025–DP-026 |

No path, query, header, or cookie inputs are declared for this operation. No nested body fields, defaults, enumerations, maximum lengths, or explicit nullability rules are documented.

### Related confirmation-password requirement

FR-03 lines 57–59 requires the user to enter a confirmation of the new password and requires both password entries to match. The selected API example has no confirmation-password field. Therefore, confirmation is an authoritative workflow/UI requirement, but the documents do not specify whether or how it is submitted to `POST /api/reset-password`; it must not be invented as an API request field.

### Request media type and schema

- Documented representation: JSON body (API specification line 46).
- Phase 2 request `Content-Type`: `application/json`, adopted as a reviewed external standard-HTTP assumption; it is not an explicit SUT requirement.
- Formal schema, additional-property behavior, property order, coercion, and malformed-body handling: not specified.

## Response inventory

No success response, error response, HTTP status, response media type, response header, response body schema, required property, error structure, or message is documented for `POST /api/reset-password` in API specification lines 44–52 or in FR-03. Do not borrow the documented `200 OK` response for the different `POST /api/forgot-password` operation at API specification line 42.

Reviewed Phase 2 HTTP oracles: expect `200 OK` for a normal successful reset and `400 Bad Request` for invalid request data. These are approved external HTTP assumptions from the CONTRACT report, not source-defined response facts. Response bodies, headers, media types, and error messages remain unspecified.

## Authentication and authorization

- The selected operation has no endpoint-specific JWT, role, or other authorization declaration in API specification lines 44–52.
- The API specification's JWT note at line 59 applies to the subsequent Users APIs and does not state that it applies to this reset endpoint.
- Approved Phase 2 interpretation: SEC-02 is not applicable to this unauthenticated account-recovery operation; the OTP is the recovery credential. This is a reviewed external password-reset assumption because the sources do not explicitly classify the endpoint.
- No role or ownership rule is declared for this endpoint beyond OTP-to-email binding in FR-03.

## SEC-01–SEC-07 extraction

| ID | Faithful requirement | Endpoint applicability evidence available in sources |
| --- | --- | --- |
| SEC-01 | Passwords must not be stored in plaintext. | Potentially applicable to storage of the new password after reset; the selected operation concerns replacing a password. Exact storage mechanism and observable response are not specified. |
| SEC-02 | Security-sensitive APIs must require a valid JWT. | Reviewed as `NOT APPLICABLE`: this is an unauthenticated recovery endpoint and the OTP is the recovery credential. Source documents do not explicitly make this classification; the approved SECURITY matrix uses external password-reset practice. |
| SEC-03 | Admin APIs must verify `role = 'admin'` in the token. | Not applicable on its face: selected path is not under `/api/admin/*` and no admin role is stated. |
| SEC-04 | User input displayed in the UI must be escaped; do not use `innerHTML` directly. | UI-level requirement is present. The selected API has user-controlled inputs, but no response reflection or UI rendering behavior is documented. Direct endpoint applicability is unsupported/ambiguous. |
| SEC-05 | Database queries must use parameterized queries, not direct string concatenation. | Applicable conditionally. Approved black-box scenario uses inert SQL/query metacharacters and requires no validation bypass, cross-account modification, database-information exposure, or unexpected server failure; implementation inspection may additionally verify parameterization. |
| SEC-06 | Profile-update APIs must not allow changing client-supplied `role`. | Not applicable on its face: this is not a profile-update API and has no documented `role` input. |
| SEC-07 | Reset-password OTP must have enough entropy (minimum 6 digits), expire, and be invalidated after use. | Directly applicable to this reset-password workflow; FR-03 also specifies a random 6-digit OTP and email binding. |

All seven SEC IDs are present in the supplied requirements; none is absent. Exact text is at system requirements lines 278–284.

## Documented state behavior

- Workflow: step 1 requests an OTP for a registered email; step 2 submits the OTP, new password, and confirmation (FR-03 lines 46–60).
- Binding guard: the OTP is valid only for the email that requested it and cannot be used for another email (FR-03 line 60).
- Time guard: the OTP has an expiry (SEC-07 line 284); duration is not specified.
- Consumption effect: the OTP is invalidated after use (SEC-07 line 284).
- Reviewed weak-password guard effect: for `TR-005`, rejection preserves `ST-01` and leaves the password unchanged; this is an external workflow assumption.
- Credential effect: the operation is identified as reset password and step 2 supplies a new password; precise persistence timing, transactional semantics, and responses are not specified.
- Related operation: `POST /api/forgot-password` creates a reset token and documents a `200 OK` example, but its response contract must not be transferred to the selected operation (API specification lines 33–42).

## Normalized test model

### Parameter inventory

Body inputs are `email`, `resetToken`, and `newPassword`. No other API parameters are explicitly specified. The workflow also has a confirmation-password value whose API mapping is unspecified.

### Valid baseline request

The API example is the only supplied request example:

```json
{
  "email": "test@domain.com",
  "resetToken": "123456",
  "newPassword": "NewPassword123!"
}
```

For a genuinely valid state baseline, the email must be registered, the OTP must have been generated for that same email, must be unexpired and unused, and any UI/workflow confirmation must equal `newPassword`. The example alone does not prove those preconditions.

### Response inventory

No response contract is documented. Reviewed external Phase 2 oracles add `200 OK` for normal success and `400 Bad Request` for invalid request data; no body, header, media type, or message is assumed.

### Contract rules supported by sources

1. Method and path are `POST /api/reset-password`.
2. The documented request representation is a JSON object example containing `email`, `resetToken`, and `newPassword`.
3. The reset token represents the 6-digit OTP generated in step 1 and is bound to the requesting email.
4. The new password follows the incorporated FR-01 strength rule.
5. Workflow confirmation must match the new password, but the API field/mapping is unspecified.
6. OTP expiry and one-time invalidation are required.
7. The sources define no exact invalid status, error body, validation order, success status, or success body; only the explicitly reviewed external HTTP assumptions in rules 8–9 may supply those oracles.
8. Approved external validation assumptions make all three body fields required; omission, `null`, wrong JSON types, malformed JSON, and non-object JSON are invalid. Extra and duplicate properties remain unspecified.
9. Approved external HTTP assumptions use `application/json`, `200 OK` for normal success, and `400 Bad Request` for invalid request data.

### State cues

OTP lifecycle (`issued`/usable, expired, consumed) and email binding are explicitly supported. Names for states are normalized analysis labels, not vocabulary stated verbatim in the sources. Approved `TR-005` further preserves the usable OTP and unchanged password after weak-password rejection as an external assumption.

### Security characteristics

Sensitive new credential input; OTP knowledge factor; OTP entropy, binding, expiry, and one-time use; credential storage and database access. Approved SECURITY scenarios cover non-plaintext storage (`SS-001`), SQL-injection resistance (`SS-002`), OTP controls (`SS-003`–`SS-007`), automated-guessing resistance with reviewed `429` expectation but no invented threshold (`SS-008`), and account-enumeration resistance (`SS-009`). JWT is reviewed not applicable. Rate limiting and enumeration resistance are external security-practice additions rather than explicit SEC requirements.

## Specification facts vs. gaps and assumptions

### Facts

- Facts are limited to the items above with exact source references.
- Both supplied documents are authoritative; neither supplies a response contract for this operation.

### Gaps / ambiguities (must not be converted into behavior)

- Formal schema requiredness/nullability remains absent, but approved external validation assumptions make the three documented fields required and omission/null/wrong type invalid. Extra and duplicate property behavior remains unspecified.
- How confirmation password maps to the selected API request.
- Exact email syntax validation at this endpoint. FR-01 defines email format for registration; FR-03 only states registered email and binding.
- OTP expiry duration, generation alphabet beyond decimal digits, retry limits, attempt limits, rate limits, and replay response.
- Whether reset success automatically logs in, revokes sessions/tokens, sends notification, or returns any token.
- All success/error statuses, response bodies, messages, media types, and headers.
- The source does not classify JWT applicability; the approved external interpretation is that JWT is not required.
- Password maximum length, Unicode policy, whitespace policy, reuse/history rules, and case normalization.
- Email case normalization and existence-disclosure behavior.
- Behavior for malformed JSON, wrong JSON types, nulls, omissions, duplicates, or additional fields.

### Working assumptions permitted only as test setup labels

- Analysts may label an OTP as unexpired/unused or expired/used only when the real SUT expiry point is configurable or objectively observable. If it is not, expiry candidates are `BLOCKED / NOT EXECUTABLE`; never assume, simulate, estimate, or invent a duration, boundary, clock, or grace period.
- Analysts may refer to successful password replacement as the intended effect of a reset-password operation, while noting that the exact persistence and observable response are unspecified.
- Use `application/json`, `200 OK` for normal success, and `400 Bad Request` for invalid request data as reviewed external HTTP assumptions.
- For `TR-005`, treat weak-password rejection as leaving the OTP usable and password unchanged.
- Treat `Aa1!bbbb#` as valid: it meets the minimum length and includes uppercase, lowercase, digit, and the allowed `!`; no requirement prohibits the additional `#`.
- Treat extra JSON properties as exploratory only because no acceptance/rejection behavior is specified.
- `SS-001` requires authorized white-box/storage inspection; Postman or an API response alone cannot prove whether the password is stored in plaintext.
- For `SS-008`, execute only with an authoritative configured abuse-control limit and use that exact trigger. If none is known, mark the case blocked; never invent a threshold. Use `429 Too Many Requests` only when configured rate limiting is the control that triggers.
- For `SS-009`, require the same `400` status, semantic equality of JSON bodies after removing only predeclared nondeterministic fields (or exact equality for non-JSON bodies), the same content type and redirect behavior, no password/token/account-metadata side effects, and informational-only timing unless an approved tolerance exists.

