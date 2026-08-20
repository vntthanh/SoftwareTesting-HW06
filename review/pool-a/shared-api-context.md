# Shared API Context — Pool A

## Source identity

- API specification: `reference/api_specification.md`, SHA-256 `488CBCB790099BA9CBB34C7C80BA04C6AEC9E9EBB598F031FFA575737547B139`.
- System requirements: `reference/system_requirements.md`, version 2.0 dated 2026-05-14, SHA-256 `7859599624A8F94E7B28859F5E3EDBEE71F275E1A71043E3EFCAB10D5EE14CDD`.
- Selected operation: API specification lines 44–52, `POST /api/reset-password`.
- Related authoritative requirements: FR-01 at system requirements lines 30–36; FR-03 at lines 46–60; SEC-01–SEC-07 at lines 274–284.
- Base URL: `http://localhost:3000` (API specification introductory metadata).

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
| `email` | JSON body | JSON string in example | API schema requiredness is not stated; FR-03 requires the user to enter the email in step 1 and binds the OTP to that email | Not specified | None specified | The OTP is valid only for the email that requested it; it cannot be used for another email | API specification lines 46–52; FR-03 lines 48–60 |
| `resetToken` | JSON body | JSON string in example | API schema requiredness is not stated; FR-03 step 2 requires the user to enter the OTP | Not specified | None specified | The generated OTP has exactly 6 decimal digits; SEC-07 additionally says minimum 6 digits, expiry, and invalidation after use | API specification lines 46–52; FR-03 lines 48–60; SEC-07 line 284 |
| `newPassword` | JSON body | JSON string in example | API schema requiredness is not stated; FR-03 step 2 requires a new password | Not specified | None specified | Minimum 8 characters and at least one uppercase letter, one lowercase letter, one digit, and one special character from `@`, `$`, `!`, `%`, `*`, `?`, `&` | API specification lines 46–52; FR-03 line 58 incorporates FR-01; FR-01 line 34 |

No path, query, header, or cookie inputs are declared for this operation. No nested body fields, defaults, enumerations, maximum lengths, or explicit nullability rules are documented.

### Related confirmation-password requirement

FR-03 lines 57–59 requires the user to enter a confirmation of the new password and requires both password entries to match. The selected API example has no confirmation-password field. Therefore, confirmation is an authoritative workflow/UI requirement, but the documents do not specify whether or how it is submitted to `POST /api/reset-password`; it must not be invented as an API request field.

### Request media type and schema

- Documented representation: JSON body (API specification line 46).
- Exact HTTP `Content-Type` value: not specified.
- Formal schema, additional-property behavior, property order, coercion, and malformed-body handling: not specified.

## Response inventory

No success response, error response, HTTP status, response media type, response header, response body schema, required property, error structure, or message is documented for `POST /api/reset-password` in API specification lines 44–52 or in FR-03. Do not borrow the documented `200 OK` response for the different `POST /api/forgot-password` operation at API specification line 42.

## Authentication and authorization

- The selected operation has no endpoint-specific JWT, role, or other authorization declaration in API specification lines 44–52.
- The API specification's JWT note at line 59 applies to the subsequent Users APIs and does not state that it applies to this reset endpoint.
- SEC-02 says security-sensitive APIs must require a valid JWT, but neither source identifies whether this public reset-password operation is included in that class. Do not assert a JWT requirement without human interpretation.
- No role or ownership rule is declared for this endpoint beyond OTP-to-email binding in FR-03.

## SEC-01–SEC-07 extraction

| ID | Faithful requirement | Endpoint applicability evidence available in sources |
| --- | --- | --- |
| SEC-01 | Passwords must not be stored in plaintext. | Potentially applicable to storage of the new password after reset; the selected operation concerns replacing a password. Exact storage mechanism and observable response are not specified. |
| SEC-02 | Security-sensitive APIs must require a valid JWT. | Requirement is present, but the sources do not classify this endpoint as JWT-protected and provide no endpoint auth declaration. Applicability is ambiguous. |
| SEC-03 | Admin APIs must verify `role = 'admin'` in the token. | Not applicable on its face: selected path is not under `/api/admin/*` and no admin role is stated. |
| SEC-04 | User input displayed in the UI must be escaped; do not use `innerHTML` directly. | UI-level requirement is present. The selected API has user-controlled inputs, but no response reflection or UI rendering behavior is documented. Direct endpoint applicability is unsupported/ambiguous. |
| SEC-05 | Database queries must use parameterized queries, not direct string concatenation. | Potentially applicable if the reset operation queries or updates the database by email/token; implementation and direct external observability are not specified. |
| SEC-06 | Profile-update APIs must not allow changing client-supplied `role`. | Not applicable on its face: this is not a profile-update API and has no documented `role` input. |
| SEC-07 | Reset-password OTP must have enough entropy (minimum 6 digits), expire, and be invalidated after use. | Directly applicable to this reset-password workflow; FR-03 also specifies a random 6-digit OTP and email binding. |

All seven SEC IDs are present in the supplied requirements; none is absent. Exact text is at system requirements lines 278–284.

## Documented state behavior

- Workflow: step 1 requests an OTP for a registered email; step 2 submits the OTP, new password, and confirmation (FR-03 lines 46–60).
- Binding guard: the OTP is valid only for the email that requested it and cannot be used for another email (FR-03 line 60).
- Time guard: the OTP has an expiry (SEC-07 line 284); duration is not specified.
- Consumption effect: the OTP is invalidated after use (SEC-07 line 284).
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

Empty: no response contract is documented for the selected operation.

### Contract rules supported by sources

1. Method and path are `POST /api/reset-password`.
2. The documented request representation is a JSON object example containing `email`, `resetToken`, and `newPassword`.
3. The reset token represents the 6-digit OTP generated in step 1 and is bound to the requesting email.
4. The new password follows the incorporated FR-01 strength rule.
5. Workflow confirmation must match the new password, but the API field/mapping is unspecified.
6. OTP expiry and one-time invalidation are required.
7. No exact invalid status, error body, validation order, success status, or success body may be asserted.

### State cues

OTP lifecycle (`issued`/usable, expired, consumed) and email binding are explicitly supported. Names for states are normalized analysis labels, not vocabulary stated verbatim in the sources.

### Security characteristics

Sensitive new credential input; OTP knowledge factor; OTP entropy, binding, expiry, and one-time use; possible credential storage and database access. JWT applicability, response redaction, logging, transport security, throttling, and error-enumeration behavior are not documented.

## Specification facts vs. gaps and assumptions

### Facts

- Facts are limited to the items above with exact source references.
- Both supplied documents are authoritative; neither supplies a response contract for this operation.

### Gaps / ambiguities (must not be converted into behavior)

- Whether API body properties are formally required, nullable, or reject extra fields.
- How confirmation password maps to the selected API request.
- Exact email syntax validation at this endpoint. FR-01 defines email format for registration; FR-03 only states registered email and binding.
- OTP expiry duration, generation alphabet beyond decimal digits, retry limits, attempt limits, rate limits, and replay response.
- Whether reset success automatically logs in, revokes sessions/tokens, sends notification, or returns any token.
- All success/error statuses, response bodies, messages, media types, and headers.
- Whether JWT authentication is required for this endpoint.
- Password maximum length, Unicode policy, whitespace policy, reuse/history rules, and case normalization.
- Email case normalization and existence-disclosure behavior.
- Behavior for malformed JSON, wrong JSON types, nulls, omissions, duplicates, or additional fields.

### Working assumptions permitted only as test setup labels

- Analysts may label an OTP as unexpired/unused or expired/used to model the explicit guards, but must not invent its lifetime or API response.
- Analysts may refer to successful password replacement as the intended effect of a reset-password operation, while noting that the exact persistence and observable response are unspecified.

