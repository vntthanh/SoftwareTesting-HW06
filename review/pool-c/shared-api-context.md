# Shared API Context — Pool C

## Source identity

- API specification: `reference/api_specification.md`, SHA-256 `488CBCB790099BA9CBB34C7C80BA04C6AEC9E9EBB598F031FFA575737547B139`.
- System requirements: `reference/system_requirements.md`, version 2.0 dated 2026-05-14, SHA-256 `7859599624A8F94E7B28859F5E3EDBEE71F275E1A71043E3EFCAB10D5EE14CDD`.
- Selected operation: API specification section 6.2, lines 179–182, `PUT /api/admin/orders/:id/status`.
- Related authoritative requirements: FR-10 at system requirements lines 141–162; FR-12 at lines 174–179; FR-18 at lines 218–222; SEC-01–SEC-07 at lines 274–284.
- Base URL: `http://localhost:3000` (API specification line 5).

## Human-review authority overlay

The user reviewed this exact Pool C Phase 1 model on 2026-08-22 and supplied the following test-design decisions. These decisions resolve prior ambiguities without changing the quoted source text:

1. FR-10's diagram is the authoritative, exhaustive state machine for non-self transitions.
2. The omitted non-self transitions `pending` → `shipping`, `pending` → `delivered`, `confirmed` → `pending`, `confirmed` → `delivered`, `shipping` → `pending`, `shipping` → `confirmed`, and `shipping` → `canceled` are `INVALID`.
3. FR-10 line 161 does not authorize `shipping` → `canceled`; FR-18 requires every Admin status change to follow FR-10.
4. Same-state updates remain `UNSPECIFIED`; the closed-world decision does not classify them.
5. All other Phase 1 analysis remains unchanged, and this review does not approve Phase 2 generation.

## Phase 2 approval authority

On 2026-08-22, the user explicitly approved the exact current Pool C Phase 1 reports and authorized Phase 2 generation for `PUT /api/admin/orders/:id/status`, targeting at least 35 cases while preserving CR/DP/TR/SS traceability and leaving unspecified behavior unresolved. This explicit approval is the review gate even though the report templates retain `PENDING` markers.

| Approved report | Approved SHA-256 |
| --- | --- |
| `reports/contract-report.md` (`CONTRACT-PHASE1-v2`) | `4143CBF16AF1B80114002EA14B2DC8568BFE5CBC3F94C2136E7736DB3F3BF86B` |
| `reports/domain-report.md` (`DOMAIN-P1-v2`) | `4E534D3D3D79915C9BECB185BA649D3D3BF532A67D0BA3D71D4C0F0B01217734` |
| `reports/state-report.md` (`STATE-PHASE1-v2`) | `DA86BDAE5A9EFA23AB1F60EB25798918929C6EF33845063AA7B71E3C4471DCF8` |
| `reports/security-report.md` (unchanged Phase 1 report) | `FE0B7C67580B95E23602F236D8444F81A756B24FBD6FD888C9113581E19A2D2E` |

Specification facts remain authoritative for SUT behavior; the approved Phase 1 reports and human-review overlay are test-design authority. No generator may invent HTTP status codes, response schemas, exact messages, ID domains, same-state behavior, or other unresolved behavior.

## Selected operation

| Property | Documented value | Exact basis |
| --- | --- | --- |
| Method | `PUT` | API specification line 181 |
| Path | `/api/admin/orders/:id/status` | API specification line 181 |
| Summary | Update an order's status in the system-wide Admin Order Management API | API specification headings at lines 171 and 179, operation at line 181 |
| Operation ID | Not specified | No operation ID appears in API specification lines 179–182 |

## Request contract

### Input inventory

| Input | Location | Documented representation | Requiredness | Type / format | Allowed values / explicit constraints | Nullability / default | Exact basis |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `id` | Path placeholder | `:id` | Structurally present in the documented route; formal schema requiredness is not stated | Not specified | Must identify the order targeted by the operation; numeric/string form, range, syntax, and existence behavior are unspecified | Nullability and default not specified | API specification line 181; FR-18 lines 218–221 |
| `Authorization` | Header | `Bearer <token>` | Required | Bearer JWT; detailed JWT format is not specified | Token must be valid and contain `role = 'admin'` | Nullability and default not specified | API specification line 173; FR-12 lines 174–179; SEC-02 and SEC-03 at lines 279–280 |
| `status` | JSON body property | JSON string in example | A body example contains it, but formal schema requiredness is not stated | JSON string in example; no formal format | `pending`, `confirmed`, `shipping`, `delivered`, `canceled`; actual update must obey FR-10's state machine | Nullability and default not specified | API specification line 182; FR-10 lines 141–162; FR-18 line 221 |

No query or cookie inputs and no nested body fields are documented. No formal schema, extra-property rule, duplicate-property rule, coercion rule, length rule, case-normalization rule, or default is specified.

### Request media type and body schema

- The specification labels the body as JSON and gives `{"status": "confirmed"}` (API specification line 182).
- An exact `Content-Type` header value and media-type rejection behavior are not documented.
- Formal JSON Schema requiredness, nullability, and additional-property behavior are not documented.

## Response inventory

No success or error HTTP status, response media type, response header, body schema, required property, error structure, or exact message is documented for this operation in API specification lines 179–182. FR-10 line 162 states only that every invalid transition must return an error with an appropriate message; it does not define the status, structure, or wording. Do not invent response details.

## Authentication and authorization

- Every API in section 6 requires `Authorization: Bearer <token>` and an Admin account (API specification line 173).
- Every `/api/admin/*` API requires a valid JWT and `role = 'admin'` in that token (FR-12 lines 174–179).
- SEC-02 requires valid JWTs for security-sensitive APIs; SEC-03 specifically requires Admin APIs to verify the admin role, not merely token presence (system requirements lines 279–280).
- No ownership restriction applies to a specific user's orders: FR-18 says Admin can view all users' orders and update statuses under FR-10 (lines 218–221).

## SEC-01–SEC-07 extraction

All seven requirement IDs are present in `reference/system_requirements.md` lines 278–284; none is absent.

| ID | Faithful requirement | Endpoint applicability evidence |
| --- | --- | --- |
| SEC-01 | Passwords must not be stored as plaintext. | Not applicable on its face: this endpoint has no password input or documented password storage effect. |
| SEC-02 | Security-sensitive APIs must require a valid JWT. | Directly applicable through the Admin API authentication declarations at API specification line 173 and FR-12 lines 177–179. |
| SEC-03 | Admin APIs must check `role = 'admin'` in the token, not only token presence. | Directly applicable because the selected path is `/api/admin/*`; FR-12 independently requires the admin role. |
| SEC-04 | User-entered data displayed in the UI must be escaped; do not use direct `innerHTML`. | No direct API response-reflection or UI rendering behavior is specified for `id` or `status`. FR-18's safe-display rule concerns shipping addresses, which this endpoint does not accept. Endpoint-level applicability is unsupported. |
| SEC-05 | Database queries must be parameterized, not directly concatenated. | Potentially applicable to database lookup/update using the untrusted path `id` and body `status`; the implementation mechanism is not observable from the specified response contract. |
| SEC-06 | Profile-update APIs must not permit client changes to `role`. | Not applicable: this is an order-status update, not a profile update, and `role` is not a documented body field. |
| SEC-07 | Reset-password OTP must have sufficient entropy, expire, and be invalidated after use. | Not applicable: this endpoint does not handle OTP or password reset. |

## Documented state behavior

FR-10 defines five order states: `pending`, `confirmed`, `shipping`, `delivered`, and `canceled` (lines 141–155). Under the human-review authority overlay, its diagram is the authoritative, exhaustive state machine for non-self transitions and supports:

| Transition | Actor / trigger | Exact basis |
| --- | --- | --- |
| `pending` → `confirmed` | Admin confirms | FR-10 lines 146–149 |
| `confirmed` → `shipping` | Admin ships | FR-10 lines 146–149 |
| `shipping` → `delivered` | Admin completes | FR-10 lines 146–149 |
| `pending` → `canceled` | User or Admin cancels | FR-10 lines 150–155 |
| `confirmed` → `canceled` | User or Admin cancels | FR-10 lines 150–155 |

- `delivered` and `canceled` are final states and cannot transition to any other state (FR-10 lines 158–160).
- Every invalid transition must return an error with an appropriate message (FR-10 line 162).
- FR-18 requires Admin status changes to follow FR-10 (line 221).
- The reviewed interpretation of FR-10 line 161 does not authorize `shipping` → `canceled`. Because the diagram omits that edge and FR-18 requires Admin changes to follow FR-10, `shipping` → `canceled` is invalid.
- Every other omitted non-self edge is invalid under the reviewed closed-world interpretation of the diagram.
- Same-state updates, idempotency, concurrency/version checks, rollback/atomicity details, and behavior for a nonexistent order are not specified.

## Normalized test model

### Parameter inventory

The documented inputs are path `id`, header `Authorization`, and JSON body property `status`. No other API inputs are specified.

### Valid baseline request

```http
PUT /api/admin/orders/<existing-pending-order-id>/status
Authorization: Bearer <valid-admin-JWT>
Content-Type: application/json

{"status":"confirmed"}
```

The existing order in `pending` state and valid Admin JWT are required setup conditions supported by FR-10 and FR-12. The concrete ID and token are fixture values, not specification constants. `Content-Type: application/json` is a representation assumption derived from the JSON-body label; the exact header requirement is unspecified.

### Response inventory

No exact response contract is supplied. The only explicit invalid-transition oracle is an error with an appropriate message (FR-10 line 162). Exact success/error statuses and bodies remain unspecified.

### Contract rules supported by sources

1. The method and path are `PUT /api/admin/orders/:id/status`.
2. The operation is under the Admin API and requires a valid Bearer JWT for an account/token with Admin role.
3. The request representation is a JSON object example containing `status`.
4. The documented status vocabulary is exactly `pending`, `confirmed`, `shipping`, `delivered`, and `canceled`.
5. Status changes must obey FR-10; the reviewed model treats its diagram as exhaustive for non-self transitions, and invalid transitions return an error with an appropriate message.
6. No response schema, exact status code, exact error wording, formal request schema, or ID domain is supplied.

### State cues

The endpoint mutates an order's lifecycle state. Source state, requested destination, actor authorization, final-state guards, and invalid-transition behavior determine the result. The five diagrammed transitions listed above are the only reviewed valid non-self transitions. All omitted non-self transitions, including `shipping` → `canceled`, are invalid. Same-state updates remain unspecified.

### Security characteristics

This is a privileged data-mutating Admin API with an untrusted path identifier and body value. JWT authentication, Admin role authorization, and parameterized database access are relevant. Password, profile-role mutation, OTP, UI escaping, rate limiting, and other generic controls must not be imported without specification support.

## Specification facts vs. gaps and assumptions

### Facts

- Facts are limited to items above carrying exact source references.
- Both supplied documents are authoritative; the system requirements supplement the compact endpoint listing with the order state machine and access-control rules.

### Gaps / ambiguities

- `id` type, syntax, range, canonicalization, existence behavior, and error response.
- Formal `status` requiredness, nullability, wrong-type behavior, whitespace/case normalization, and duplicate/extra fields.
- Exact `Content-Type` and `Accept` behavior; malformed and non-object JSON behavior.
- All success response details and all exact error status/body details.
- Same-state updates and idempotency, validation/authorization precedence, concurrency, and atomicity.
- JWT expiry/signature/claim details beyond validity and Admin role.

### Working assumptions permitted only as setup labels

- Concrete order IDs and JWTs may be fixture values while remaining clearly labeled as test setup, not specification constants.
- `application/json` may be used for the documented JSON representation, but strict rejection of other or missing media types cannot be asserted without review authority.
- For behavior whose HTTP status or body is unspecified, candidates must assert only the documented semantic outcome or clearly mark the response detail as unresolved/assumed.
