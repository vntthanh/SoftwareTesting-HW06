# Contract Analysis Report — Pool C

## Endpoint and source identity

- Endpoint: `PUT /api/admin/orders/:id/status`
- Scope: CONTRACT analysis only; no test cases are generated in this phase.
- API specification: `reference/api_specification.md`, SHA-256 `488CBCB790099BA9CBB34C7C80BA04C6AEC9E9EBB598F031FFA575737547B139`.
- System requirements: `reference/system_requirements.md`, version 2.0 dated 2026-05-14, SHA-256 `7859599624A8F94E7B28859F5E3EDBEE71F275E1A71043E3EFCAB10D5EE14CDD`.
- Normalized input: `review/pool-c/shared-api-context.md`.
- Exact operation basis: API specification section 6.2, lines 179–182; related requirements FR-10, system requirements lines 141–162; FR-12, lines 174–179; FR-18, lines 218–222.
- Base URL: `http://localhost:3000` (API specification line 5).

## Request inventory

| Element | Location / representation | Requiredness | Type / format | Values and structural constraints | Nullability / default | Exact basis |
| --- | --- | --- | --- | --- | --- | --- |
| Method | HTTP method | Required by the selected operation | `PUT` | Exactly the documented method for this operation | Not applicable | API specification line 181 |
| Path | Request target | Required by the selected operation | `/api/admin/orders/:id/status` | Contains one `id` placeholder | Not applicable | API specification line 181 |
| `id` | Path parameter | Structurally required to instantiate the documented route; formal parameter requiredness is not stated | Type and format not specified | Identifies the target order; syntax, numeric/string representation, range, canonicalization, and existence behavior are unspecified | Nullability and default not specified | API specification line 181; FR-18 lines 218–221 |
| `Authorization` | Header | Required for every Admin API | `Bearer <token>`; detailed JWT syntax is not specified | JWT must be valid and carry `role = 'admin'` | Nullability and default not specified | API specification line 173; FR-12 lines 174–179; SEC-02 and SEC-03, system requirements lines 279–280 |
| Request body | JSON representation | A JSON body example is documented; formal body requiredness is not stated | JSON object in the example | Example shape is `{"status":"confirmed"}`; no formal JSON Schema or additional-property rule is supplied | Nullability and default not specified | API specification line 182 |
| `status` | JSON body property | Present in the documented example; formal schema requiredness is not stated | JSON string in the example | Vocabulary: `pending`, `confirmed`, `shipping`, `delivered`, `canceled`; an actual change must obey FR-10 | Nullability and default not specified | API specification line 182; FR-10 lines 141–162; FR-18 line 221 |

No query parameters, cookie inputs, nested body fields, or other headers are documented. No coercion, string-length, whitespace, case-normalization, duplicate-property, or extra-property rule is specified.

## Request media types

- The specification labels the request body as JSON and provides a JSON object example (API specification line 182).
- It does not state an exact `Content-Type` value, whether `Content-Type` is required, which JSON-compatible media types are accepted, or the behavior for unsupported or missing media types.
- `Content-Type: application/json` is permissible as a setup representation assumption, but strict media-type acceptance or rejection is not part of the documented contract.
- No `Accept` requirement or response content-negotiation behavior is documented.

## Response inventory

The selected operation has no documented response status, media type, required header, body schema, property, type, format, enumeration, nullability rule, or error structure in API specification lines 179–182.

| Outcome | Documented status | Media type / headers | Schema / required properties | Exact basis |
| --- | --- | --- | --- | --- |
| Valid status change | Not specified | Not specified | Not specified | No response contract appears in API specification lines 179–182 |
| Invalid state transition | Not specified | Not specified | Must return an error with an appropriate message; structure and wording are not specified | FR-10 line 162 |
| Missing/invalid JWT | Not specified | Not specified | Not specified | Authentication behavior is required by API specification line 173, FR-12 lines 174–179, and SEC-02, but no response contract is defined |
| Authenticated non-admin token | Not specified | Not specified | Not specified | Admin-role verification is required by FR-12 lines 174–179 and SEC-03, but no response contract is defined |
| Invalid or nonexistent `id` | Not specified | Not specified | Not specified | No identifier domain or failure response is supplied |
| Structurally invalid body or unsupported `status` value | Not specified | Not specified | Not specified | The example and state vocabulary define the documented representation and values, but no validation response contract is supplied |

Consequently, no exact HTTP code, response body, error field, message wording, response header, or response media type may be asserted from the supplied sources.

## Contract rules

| ID | Target | Valid condition | Invalid condition | Expected contract behavior | Exact specification basis | Assumptions / review notes |
| --- | --- | --- | --- | --- | --- | --- |
| CR-001 | Method and route | Request uses `PUT /api/admin/orders/<id>/status` | A different method or path is used | The selected operation is addressed only through the documented method and route; behavior of other methods/routes is unspecified | API specification line 181 | `<id>` is a fixture substitution for `:id`; do not invent alternate-method status codes |
| CR-002 | Path `id` presence | The route contains a concrete value in the `:id` segment identifying the target order | The `:id` segment is absent, empty, malformed, out of range, or does not identify an existing order | Only structural presence in the route and its purpose as the target identifier are documented; validation and failure behavior are unresolved | API specification line 181; FR-18 lines 218–221 | The source does not define an ID type, grammar, range, nullability, canonicalization, or not-found response |
| CR-003 | `Authorization` scheme | Header is supplied in the documented `Bearer <token>` representation | Header is absent or does not use the documented Bearer representation | Access requires the documented Authorization header; exact rejection status/body is unspecified | API specification line 173 | Detailed bearer-token grammar and rejection precedence are not supplied |
| CR-004 | JWT validity | Bearer token is a valid JWT | JWT is invalid | The Admin API must not authorize the request with an invalid JWT; exact error response is unspecified | FR-12 lines 174–179; SEC-02 line 279 | JWT signature, expiry, issuer, audience, and claim-validation details are not individually specified |
| CR-005 | Admin role | Valid JWT contains `role = 'admin'` | Token is present/valid but does not carry the required Admin role | The request must not be authorized merely because a token is present; exact error response is unspecified | FR-12 lines 174–179; SEC-03 line 280 | No role hierarchy, case normalization, or alternative admin claim is documented |
| CR-006 | Body representation | Body is represented as a JSON object consistent with the documented example | Body is malformed JSON, a non-object JSON value, absent, or sent with an unsupported/missing media type | The specification supports the JSON-object representation but does not define rejection behavior for the invalid variants | API specification line 182 | Formal body requiredness and exact `Content-Type` acceptance are unresolved; do not assert a status code |
| CR-007 | `status` member representation | JSON object contains `status` as a JSON string, consistent with the example | `status` is absent, `null`, or a non-string JSON value | A string-valued `status` is the only documented representation; formal requiredness, nullability, coercion, and invalid-shape behavior are unresolved | API specification line 182 | This rule records the documented shape, not an invented JSON Schema requirement |
| CR-008 | `status` vocabulary | `status` is one of `pending`, `confirmed`, `shipping`, `delivered`, `canceled` | `status` is outside that documented vocabulary | Only the five documented lifecycle values are supported by the contract; exact rejection status/body is unspecified | API specification line 182; FR-10 lines 141–155 | Case folding, trimming, aliases, and unknown-value handling are not specified |
| CR-009 | Transition constraint | Requested status change is one of the five non-self edges shown in FR-10's authoritative, exhaustive diagram | Requested non-self status change is omitted from the FR-10 diagram, including PR-001 through PR-007 | A valid transition may update the status; every invalid transition must return an error with an appropriate message | FR-10 lines 146–162; FR-18 line 221; human-review authority overlay in `review/pool-c/shared-api-context.md` | FR-10 line 161 does not authorize `shipping` → `canceled`; FR-18 requires Admin changes to follow FR-10. Same-state updates remain unspecified. Success/error codes and payloads are unspecified |
| CR-010 | Final-state guard | No further change is attempted after `delivered` or `canceled` | A request attempts to move an order from `delivered` or `canceled` to any other state | The attempted transition must be treated as invalid and return an error with an appropriate message | FR-10 lines 158–162; FR-18 line 221 | Exact response contract remains unspecified |
| CR-011 | Extra or duplicate body members | Request stays within the documented example shape | Body contains additional properties or duplicate `status` properties | Acceptance or rejection is unspecified and must not be asserted without review authority | API specification line 182 | There is no `additionalProperties` or duplicate-key rule |
| CR-012 | Successful response | Authorized request identifies an order and requests a supported, permitted transition | Any otherwise successful scenario | A status update is the intended semantic result, but no observable HTTP response contract is documented | API specification lines 179–182; FR-18 lines 218–221 | Status code, response media type, headers, and body must remain unresolved |
| CR-013 | Error response shape | An invalid transition produces an error with an appropriate message | Exact status, schema, fields, media type, or wording is assumed | Assert only the documented semantic error/message requirement; do not assert an invented wire format | FR-10 line 162 | “Appropriate” is not objectively defined; review should supply an oracle if exact verification is required |

## Explicit positive and negative rule coverage

- Positive contract conditions are represented by the valid-condition column of CR-001 through CR-010 and CR-012.
- Negative contract conditions are represented by the invalid-condition column of CR-001 through CR-011 and CR-013.
- CR-002, CR-006, CR-007, and CR-011 deliberately stop at documenting uncertainty: the sources do not authorize guessed validation outcomes.
- CR-009 and CR-010 record only contract-level state constraints. Full transition-path analysis is outside this report's CONTRACT scope.

## Human-review decision applied

The human review treats FR-10's diagram as the authoritative, exhaustive state machine for non-self transitions. Accordingly, the following previously proposed or ambiguous paths are classified `INVALID` for this contract model:

| Path rule | Source | Destination | Reviewed classification |
| --- | --- | --- | --- |
| PR-001 | `pending` | `shipping` | `INVALID` |
| PR-002 | `pending` | `delivered` | `INVALID` |
| PR-003 | `confirmed` | `pending` | `INVALID` |
| PR-004 | `confirmed` | `delivered` | `INVALID` |
| PR-005 | `shipping` | `pending` | `INVALID` |
| PR-006 | `shipping` | `confirmed` | `INVALID` |
| PR-007 | `shipping` | `canceled` | `INVALID` |

FR-10 line 161 does not authorize PR-007: FR-18 requires Admin status changes to follow FR-10, and the authoritative diagram omits that edge. Same-state requests (`pending` → `pending`, `confirmed` → `confirmed`, `shipping` → `shipping`, `delivered` → `delivered`, and `canceled` → `canceled`) remain `UNSPECIFIED`. This review decision does not approve Phase 2 generation.

## Gaps and ambiguities requiring review

1. The `id` type, syntax, range, canonicalization, nullability, existence behavior, and invalid/not-found response are unspecified.
2. Formal request-body and `status` requiredness are unspecified. So are nullability, wrong-type handling, malformed/non-object JSON behavior, coercion, trimming, case normalization, duplicate keys, and extra properties.
3. The exact request `Content-Type`, whether it is mandatory, supported alternatives, `Accept` behavior, and media-type rejection behavior are unspecified.
4. No success status, error status, response media type, response header, response body schema, or exact error structure is documented.
5. FR-10 line 162 requires an “appropriate message” for invalid transitions but supplies no structure, field name, language, wording, or deterministic oracle.
6. Same-state updates, idempotency, concurrency/version conflicts, atomicity, and validation/authentication/authorization precedence are unspecified.
7. JWT validity details beyond requiring a valid JWT with `role = 'admin'` are unspecified.

## Review decisions requested

- Confirm whether CR-007 should be approved only as a documented representation or elevated into a strict required/non-null/string schema rule.
- Decide whether requests with missing/extra/duplicate fields, malformed or non-object JSON, and missing/unsupported `Content-Type` have any approved expected behavior.
- Supply an approved `id` domain and nonexistent-order oracle if such cases should be generated with exact expectations.
- Supply response status/body/media-type/header expectations only if an authoritative reviewed rule exists; otherwise generation must retain semantic-only or unresolved oracles.
- Define what makes an invalid-transition message “appropriate,” if it must be objectively asserted.

## Review block

- Review Status: PENDING
- Reviewer: Human reviewer (user), 2026-08-22
- Review Notes: FR-10's diagram is authoritative and exhaustive for non-self transitions. PR-001 through PR-007 are `INVALID`, including `shipping` → `canceled`; FR-10 line 161 does not authorize that edge, and FR-18 requires Admin changes to follow FR-10. Same-state updates remain `UNSPECIFIED`. All other Phase 1 contract analysis is preserved. Phase 2 is not approved and no tests were generated.
- Reviewed Version: `CONTRACT-PHASE1-v2`
