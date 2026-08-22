# DOMAIN Phase 1 Analysis — Pool C Admin Order Management

## Scope and source identity

- Endpoint: `PUT /api/admin/orders/:id/status`
- API specification: `reference/api_specification.md`, section 6.2, lines 179–182, SHA-256 `488CBCB790099BA9CBB34C7C80BA04C6AEC9E9EBB598F031FFA575737547B139`
- System requirements: `reference/system_requirements.md`, version 2.0 dated 2026-05-14, SHA-256 `7859599624A8F94E7B28859F5E3EDBEE71F275E1A71043E3EFCAB10D5EE14CDD`
- Related requirements: FR-10 (lines 141–162), FR-12 (lines 174–179), FR-18 (lines 218–222), and SEC-02/SEC-03 (lines 279–280)
- Shared normalized context: `review/pool-c/shared-api-context.md`
- Analysis version: `DOMAIN-P1-v2`

This report analyzes equivalence partitions and explicit boundaries for the documented request inputs only. It does not define test cases or invent response status codes, schemas, or messages.

## Incorporated human-review decision

The Pool C Phase 1 human review dated 2026-08-22 establishes that FR-10's diagram is the authoritative, exhaustive state machine for non-self transitions. Accordingly, the following omitted non-self transitions are classified `INVALID`: PR-001 `pending` → `shipping`, PR-002 `pending` → `delivered`, PR-003 `confirmed` → `pending`, PR-004 `confirmed` → `delivered`, PR-005 `shipping` → `pending`, PR-006 `shipping` → `confirmed`, and PR-007 `shipping` → `canceled`. FR-10 line 161 does not authorize PR-007, and FR-18 requires Admin status changes to follow FR-10. Same-state updates remain `UNSPECIFIED`. This decision revises transition classifications only and does not approve Phase 2 generation.

## Valid baseline

```http
PUT /api/admin/orders/<existing-pending-order-id>/status
Authorization: Bearer <valid-admin-JWT>
Content-Type: application/json

{"status":"confirmed"}
```

Baseline setup and assumptions:

- `<existing-pending-order-id>` is a fixture that identifies an existing order currently in `pending`; neither its concrete value nor its representation is a specification constant.
- `<valid-admin-JWT>` is a valid JWT whose claims include `role = 'admin'`.
- `confirmed` is an allowed status and `pending` → `confirmed` is an expressly supported FR-10 transition.
- `Content-Type: application/json` is used because the API specification labels the request body as JSON. The exact header requirement and rejection behavior are unspecified.
- No exact success status, media type, headers, or response body can be asserted from the supplied sources.

## Complete parameter inventory

| Input | Location | Requiredness | Type / format | Allowed values and explicit constraints | Nullability | Default | Exact basis |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `id` | Path placeholder | Structurally present in the documented route; formal schema requiredness is not stated | Not specified | Must identify the order targeted by the update; syntax, numeric/string representation, range, canonical form, and existence behavior are unspecified | Not specified | Not specified | API specification line 181; FR-18 lines 218–221 |
| `Authorization` | Header | Required | `Bearer <token>`; token is a JWT, but detailed JWT serialization/claim schema is not specified | JWT must be valid and contain `role = 'admin'` | Not specified | Not specified | API specification line 173; FR-12 lines 174–179; SEC-02/SEC-03 lines 279–280 |
| `status` | JSON body property | A JSON-body example contains it, but formal property requiredness is not stated | JSON string in the example; no formal schema or format is provided | `pending`, `confirmed`, `shipping`, `delivered`, `canceled`; the requested change must also obey FR-10 | Not specified | Not specified | API specification line 182; FR-10 lines 141–162; FR-18 line 221 |

Inventory completeness notes:

- No query or cookie inputs are documented.
- No nested body fields are documented.
- The JSON body is the containing representation for `status`. Its object requirement, empty-body behavior, malformed-JSON behavior, non-object behavior, duplicate-property behavior, additional-property behavior, and coercion rules are not formally specified.
- `Content-Type` is not inventoried as a documented contract input because no exact header name/value rule is stated. `application/json` remains a representation assumption for the baseline.

## Equivalence partitions

The expected-result column deliberately uses “specified,” “unsupported,” or “unresolved” rather than assigning undocumented HTTP status codes or response bodies.

| ID | Input / aspect | Partition | Representative value or condition | Classification and semantic oracle | Exact basis / rationale |
| --- | --- | --- | --- | --- | --- |
| DP-001 | `id` | Identifies an existing order in a source state compatible with the requested destination | Existing `pending` order ID with `status = confirmed` | Supported valid baseline; the status update is permitted when authentication is valid | API specification line 181; FR-10 lines 146–149; FR-18 lines 218–221 |
| DP-002 | `id` | Identifies an existing order, but its current state makes the requested transition invalid | Existing `delivered` order ID with a different allowed destination | Semantically invalid; must return an error with an appropriate message, but exact response details are unspecified | FR-10 lines 158–162 |
| DP-003 | `id` | Does not identify an existing order | A syntactically routable but nonexistent fixture ID | Behavior unresolved; existence-error semantics and response contract are not specified | The endpoint targets an order, but neither API specification line 181 nor FR-18 defines nonexistent-order behavior |
| DP-004 | `id` | Empty or omitted path segment | Request path lacking a value after `/orders/` | Usually a different route rather than a value delivered to this operation; operation-level behavior is unresolved and must not be asserted as `id` validation | Route shape in API specification line 181; no routing behavior is specified |
| DP-005 | `id` | Alternate lexical/type classes | Non-numeric text, signed text, decimal text, whitespace/encoded whitespace, or other lexical forms | Classification unresolved because the specification defines no `id` type or syntax; retain as a gap rather than declaring invalid | API specification line 181 supplies only `:id` |
| DP-006 | `id` | Null literal lexical value | Path segment `null` | Classification unresolved; a path cannot carry JSON null, and the string `null` has no specified identifier semantics | No `id` type, syntax, or nullability is specified |
| DP-007 | `Authorization` | Valid JWT with Admin role | `Bearer <valid-admin-JWT>` with `role = 'admin'` | Supported valid authentication/authorization partition | API specification line 173; FR-12 lines 174–179; SEC-02/SEC-03 lines 279–280 |
| DP-008 | `Authorization` | Header omitted | No `Authorization` header | Invalid for this Admin endpoint; access must not be granted. Exact response status/body is unspecified | API specification line 173; FR-12 lines 177–179; SEC-02 lines 279 |
| DP-009 | `Authorization` | Header present but empty or without a token | Empty value or `Bearer` with no token | Does not provide the required valid JWT; access must not be granted. Exact response details are unspecified | Same basis as DP-008 |
| DP-010 | `Authorization` | Wrong authentication scheme or malformed Bearer/JWT representation | `Basic ...`, malformed token segments, or otherwise non-valid JWT | Does not satisfy valid Bearer JWT requirement; access must not be granted. Exact parsing and response details are unspecified | API specification line 173; FR-12 lines 177–179; SEC-02 line 279 |
| DP-011 | `Authorization` | Bearer JWT is not valid | Expired, invalid-signature, or otherwise invalid JWT fixture | Invalid; access must not be granted. The sources do not define validation precedence, token defect taxonomy, or exact response | FR-12 lines 177–179; SEC-02 line 279 |
| DP-012 | `Authorization` | Valid JWT without Admin role | Valid non-Admin JWT, or valid JWT lacking `role = 'admin'` | Unauthorized for Admin API; access must not be granted. Exact response details are unspecified | FR-12 lines 174–179; SEC-03 line 280 |
| DP-013 | `status` | Allowed vocabulary: `confirmed` | `"confirmed"` | In-set value; validity of the update depends on source state. Valid from `pending` | FR-10 lines 141–149; API specification line 182 |
| DP-014 | `status` | Allowed vocabulary: `shipping` | `"shipping"` | In-set value; validity depends on source state. Valid from `confirmed` | FR-10 lines 141–149 |
| DP-015 | `status` | Allowed vocabulary: `delivered` | `"delivered"` | In-set value; validity depends on source state. Valid from `shipping` | FR-10 lines 141–149 |
| DP-016 | `status` | Allowed vocabulary: `canceled` | `"canceled"` | In-set value; valid from `pending` and `confirmed`. `shipping` → `canceled` (PR-007) is invalid under the reviewed authoritative, exhaustive FR-10 diagram; FR-10 line 161 does not authorize it, and FR-18 requires Admin changes to follow FR-10 | FR-10 lines 150–162; FR-18 line 221; Pool C Phase 1 human-review decision dated 2026-08-22 |
| DP-017 | `status` | Allowed vocabulary: `pending` | `"pending"` | In-set value. Non-self transitions into `pending` are invalid because the reviewed authoritative, exhaustive FR-10 diagram omits them (PR-003 and PR-005); same-state `pending` → `pending` remains unspecified | FR-10 lines 141–162; FR-18 line 221; Pool C Phase 1 human-review decision dated 2026-08-22 |
| DP-018 | `status` | String outside documented vocabulary | `"unknown"` | Unsupported destination under the documented five-state model; should not cause a valid state update. Exact error response is unspecified | FR-10 lines 141–155; API specification line 182 |
| DP-019 | `status` | Empty string | `""` | Outside the documented vocabulary; should not cause a valid state update. Exact error response is unspecified | Same basis as DP-018 |
| DP-020 | `status` | Case or whitespace variants of a documented value | `"Confirmed"`, `" confirmed "` | Classification unresolved because case normalization and whitespace trimming are not specified; they are not exact members of the documented lowercase vocabulary | No normalization rule appears in the supplied sources |
| DP-021 | `status` | JSON null | `{"status":null}` | Behavior unresolved because nullability and formal schema are unspecified; null is not one of the documented string values | API specification line 182 gives only a string example; no nullability rule exists |
| DP-022 | `status` | Non-string JSON type | `{"status":1}`, `{"status":true}`, `{"status":[]}`, or `{"status":{}}` | Behavior unresolved because no formal type/coercion rule is specified; such values do not exactly match the documented string vocabulary | API specification line 182; absence of formal JSON schema |
| DP-023 | `status` | Property omitted | `{}` | Behavior unresolved because formal requiredness and default behavior are unspecified | API specification line 182 provides an example, not a required-property declaration |
| DP-024 | JSON body | Empty or absent body | No body bytes | Behavior unresolved because body requiredness and empty-body response are unspecified | API specification line 182 labels a JSON body but supplies no formal schema |
| DP-025 | JSON body | Malformed JSON | Truncated or syntactically invalid JSON | Behavior unresolved at the response-contract level; malformed JSON cannot represent the documented request example | No malformed-body handling is specified |
| DP-026 | JSON body | Valid JSON but non-object top-level value | `null`, `[]`, `"confirmed"`, or `1` | Behavior unresolved because an object schema is implied only by example, not formally required | API specification line 182 |
| DP-027 | JSON body | Object includes `status` plus additional properties | `{"status":"confirmed","extra":"x"}` | Acceptance/rejection unresolved because no additional-property rule is specified | No formal JSON schema or extra-property rule exists |
| DP-028 | JSON body | Duplicate `status` property | `{"status":"confirmed","status":"shipping"}` | Parsing and effective-value behavior unresolved; no duplicate-property rule is specified | No duplicate-property rule exists |

## Boundary analysis

| Boundary ID | Input | Explicit ordered limit | Boundary values | Result |
| --- | --- | --- | --- | --- |
| — | `id` | None specified | None derivable | No numeric, length, range, or ordered identifier limit may be inferred |
| — | `Authorization` | None specified | None derivable | No token/header length, claim-count, age, or time boundary is documented |
| — | `status` | None specified | None derivable | The five status strings form an enumeration, not an ordered magnitude boundary |
| — | JSON body | None specified | None derivable | No body size, property count, or nesting boundary is documented |

There are therefore no supported `DB-*` items in this report. FR-10's lifecycle ordering is a state-transition model, not a boundary-value constraint; it must not be recast as numeric or ordinal boundary testing.

## Documented cross-parameter and setup constraints

1. `Authorization` must contain both a valid JWT and `role = 'admin'`; token presence alone is insufficient (FR-12; SEC-02; SEC-03).
2. The semantic result of a `status` value depends on the current state of the order identified by `id`. Under the reviewed authoritative, exhaustive FR-10 diagram, the supported non-self transitions are `pending` → `confirmed`, `confirmed` → `shipping`, `shipping` → `delivered`, `pending` → `canceled`, and `confirmed` → `canceled` (FR-10; FR-18 line 221).
3. `delivered` and `canceled` are final states and cannot transition to any other state (FR-10 lines 158–160).
4. Every invalid transition must return an error with an appropriate message, although status code, schema, and wording are not defined (FR-10 line 162).
5. In addition to the final-state prohibitions above, the seven omitted non-self transitions from non-final source states are invalid under the reviewed closed-world interpretation of FR-10's diagram: PR-001 `pending` → `shipping`, PR-002 `pending` → `delivered`, PR-003 `confirmed` → `pending`, PR-004 `confirmed` → `delivered`, PR-005 `shipping` → `pending`, PR-006 `shipping` → `confirmed`, and PR-007 `shipping` → `canceled`. FR-10 line 161 does not authorize PR-007; FR-18 requires Admin changes to follow FR-10.
6. Same-state updates remain unspecified and are not classified by the reviewed closed-world decision.
7. One-factor-at-a-time domain generation should use the valid baseline. Partitions involving transition validity require an explicitly prepared source-state fixture and must cite the reviewed state rule rather than assume it from the destination string alone.

## Gaps and ambiguities requiring review

- The `id` type, syntax, range, length, canonicalization, and nonexistent-order behavior are unspecified.
- Formal request-body and `status` requiredness, type, nullability, default, coercion, case normalization, whitespace trimming, additional properties, and duplicate properties are unspecified.
- Empty, malformed, and non-object JSON behavior is unspecified.
- Exact `Content-Type` requirements and behavior for missing or unsupported media types are unspecified.
- All success response details and all exact error status/body details are unspecified.
- Same-state updates remain unspecified. Non-self transitions back to `pending` and Admin cancellation from `shipping` are resolved as invalid by the Pool C Phase 1 human review.
- JWT validity details (including expiry, signature, and claim rules), authorization/validation precedence, and exact rejection responses are unspecified.
- No explicit numeric, length, count, date/time, or other ordered limits exist, so boundary-value cases cannot be supported without adding requirements.

## Assumptions and generation guardrails

- Concrete IDs, tokens, and source-state orders may be fixture values only; they are not domain constants.
- A future candidate may assert only documented semantic outcomes. It must not invent HTTP status codes, exact response bodies, or error wording.
- Items marked unresolved are review questions, not automatically valid or invalid partitions. This does not apply to PR-001 through PR-007, which the human review classifies as invalid; same-state updates remain unresolved/unspecified.
- Security-specific attack construction and full state-transition coverage remain the responsibility of their respective specialist analyses; this report records only domain-relevant equivalence classes and interactions.

## Human review block

- Review Status: PENDING
- Reviewer: Human review supplied by user on 2026-08-22
- Review Notes: FR-10's diagram is authoritative and exhaustive for non-self transitions. PR-001 through PR-007 are `INVALID`, including `shipping` → `canceled`; FR-10 line 161 does not authorize that transition, and FR-18 requires Admin changes to follow FR-10. Same-state updates remain `UNSPECIFIED`. All other analysis is preserved. Phase 2 is not approved.
- Reviewed Version: `DOMAIN-P1-v2`
