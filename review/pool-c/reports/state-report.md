# State Transition Analysis Report — Pool C

## Scope and source identity

- **Category:** STATE
- **Selected endpoint:** `PUT /api/admin/orders/:id/status`
- **API specification:** `reference/api_specification.md`, section 6.2, lines 179–182, SHA-256 `488CBCB790099BA9CBB34C7C80BA04C6AEC9E9EBB598F031FFA575737547B139`
- **System requirements:** `reference/system_requirements.md`, version 2.0 dated 2026-05-14, SHA-256 `7859599624A8F94E7B28859F5E3EDBEE71F275E1A71043E3EFCAB10D5EE14CDD`
- **Shared normalized context:** `review/pool-c/shared-api-context.md`
- **Report version:** `STATE-PHASE1-v2`

## Applicability determination

**State Applicability: APPLICABLE**

The selected endpoint changes an order's lifecycle status. FR-10 defines five states, expressly diagrams five valid transitions, declares `delivered` and `canceled` final, and requires an error with an appropriate message for every invalid transition (system requirements lines 141–162). FR-18 requires Admin status changes to follow FR-10 (lines 218–221). Therefore the result varies according to the order's prior state and requested destination, and a meaningful state-transition model applies.

Authentication and Admin-role checks are preconditions to exercising this state model, not order lifecycle states. Setup through order creation or other operations is also treated as a precondition because only one endpoint was selected.

## State definitions

| State ID | State | Definition / role in this model | Exact basis |
| --- | --- | --- | --- |
| ST-01 | `pending` | Initial lifecycle state represented in the FR-10 diagram; may advance to `confirmed` or be canceled by User or Admin. | FR-10 lines 141–155 |
| ST-02 | `confirmed` | Intermediate state after Admin confirmation; may advance to `shipping` or be canceled by User or Admin. | FR-10 lines 146–155 |
| ST-03 | `shipping` | Intermediate fulfillment state after Admin ships; may advance only to `delivered`. The authoritative FR-10 diagram omits cancellation from this state, and FR-18 requires Admin changes to follow FR-10. | FR-10 lines 146–161; FR-18 line 221; human review dated 2026-08-22 |
| ST-04 | `delivered` | Final state; cannot transition to any other state. | FR-10 lines 146–149 and 158–160 |
| ST-05 | `canceled` | Final state; cannot transition to any other state. | FR-10 lines 150–160 |

## Expressly supported valid-transition model

For every row, setup must provide an existing order in the named source state and a valid JWT whose role is `admin`. The trigger is a request to the selected endpoint with that order's fixture ID and the destination in the JSON `status` property. Concrete IDs and tokens are fixtures, not specification constants.

| Transition ID | Classification | Trigger / request | Source | Guard | Destination | Observable semantic result | Exact basis |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TR-001 | Valid | `status: "confirmed"` | ST-01 `pending` | Authenticated Admin; existing order is `pending` | ST-02 `confirmed` | Status change is accepted and the order reaches `confirmed`; exact HTTP response is unspecified. | FR-10 lines 146–149; FR-18 line 221 |
| TR-002 | Valid | `status: "shipping"` | ST-02 `confirmed` | Authenticated Admin; existing order is `confirmed` | ST-03 `shipping` | Status change is accepted and the order reaches `shipping`; exact HTTP response is unspecified. | FR-10 lines 146–149; FR-18 line 221 |
| TR-003 | Valid | `status: "delivered"` | ST-03 `shipping` | Authenticated Admin; existing order is `shipping` | ST-04 `delivered` | Status change is accepted and the order reaches `delivered`; exact HTTP response is unspecified. | FR-10 lines 146–149; FR-18 line 221 |
| TR-004 | Valid | `status: "canceled"` | ST-01 `pending` | Authenticated Admin; existing order is `pending` | ST-05 `canceled` | Status change is accepted and the order reaches `canceled`; exact HTTP response is unspecified. | FR-10 lines 150–155; FR-18 line 221 |
| TR-005 | Valid | `status: "canceled"` | ST-02 `confirmed` | Authenticated Admin; existing order is `confirmed` | ST-05 `canceled` | Status change is accepted and the order reaches `canceled`; exact HTTP response is unspecified. | FR-10 lines 150–155; FR-18 line 221 |

## Explicitly supported invalid-transition model

FR-10 expressly says `delivered` and `canceled` cannot transition to any other state. These rows exclude same-state requests because “any other state” does not resolve same-state idempotency. The only specified response oracle is rejection with an error and an appropriate message; status code, response schema, wording, and post-error persistence/atomicity are unspecified.

| Transition ID | Classification | Trigger / request | Source | Guard | Destination | Observable semantic result | Exact basis |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TR-006 | Invalid | `status: "pending"` | ST-04 `delivered` | Existing order is in final state `delivered` | None; requested transition is rejected | Error with an appropriate message; exact response details are unspecified. | FR-10 lines 158–162 |
| TR-007 | Invalid | `status: "confirmed"` | ST-04 `delivered` | Existing order is in final state `delivered` | None; requested transition is rejected | Error with an appropriate message; exact response details are unspecified. | FR-10 lines 158–162 |
| TR-008 | Invalid | `status: "shipping"` | ST-04 `delivered` | Existing order is in final state `delivered` | None; requested transition is rejected | Error with an appropriate message; exact response details are unspecified. | FR-10 lines 158–162 |
| TR-009 | Invalid | `status: "canceled"` | ST-04 `delivered` | Existing order is in final state `delivered` | None; requested transition is rejected | Error with an appropriate message; exact response details are unspecified. | FR-10 lines 158–162 |
| TR-010 | Invalid | `status: "pending"` | ST-05 `canceled` | Existing order is in final state `canceled` | None; requested transition is rejected | Error with an appropriate message; exact response details are unspecified. | FR-10 lines 158–162 |
| TR-011 | Invalid | `status: "confirmed"` | ST-05 `canceled` | Existing order is in final state `canceled` | None; requested transition is rejected | Error with an appropriate message; exact response details are unspecified. | FR-10 lines 158–162 |
| TR-012 | Invalid | `status: "shipping"` | ST-05 `canceled` | Existing order is in final state `canceled` | None; requested transition is rejected | Error with an appropriate message; exact response details are unspecified. | FR-10 lines 158–162 |
| TR-013 | Invalid | `status: "delivered"` | ST-05 `canceled` | Existing order is in final state `canceled` | None; requested transition is rejected | Error with an appropriate message; exact response details are unspecified. | FR-10 lines 158–162 |

## Human-reviewed omitted non-self transitions

The human review dated 2026-08-22 establishes that the FR-10 diagram is the authoritative, exhaustive state machine for non-self transitions. Accordingly, every omitted non-self edge below is **INVALID**. Stable IDs PR-001 through PR-007 are preserved for traceability. FR-10 line 161 does not authorize `shipping` → `canceled`; FR-18 requires Admin status changes to follow FR-10. As with TR-006 through TR-013, the only specified oracle is rejection with an error and an appropriate message; exact response details are unspecified.

| Proposed ID | Classification | Trigger / request | Source | Guard | Destination | Observable semantic result | Exact basis |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PR-001 | INVALID | `status: "shipping"` | ST-01 `pending` | Authenticated Admin; existing order is `pending`; edge is omitted from the exhaustive diagram | None; requested transition is rejected | Error with an appropriate message; exact response details are unspecified. | FR-10 lines 146–162; FR-18 line 221; human review dated 2026-08-22 |
| PR-002 | INVALID | `status: "delivered"` | ST-01 `pending` | Authenticated Admin; existing order is `pending`; edge is omitted from the exhaustive diagram | None; requested transition is rejected | Error with an appropriate message; exact response details are unspecified. | FR-10 lines 146–162; FR-18 line 221; human review dated 2026-08-22 |
| PR-003 | INVALID | `status: "pending"` | ST-02 `confirmed` | Authenticated Admin; existing order is `confirmed`; edge is omitted from the exhaustive diagram | None; requested transition is rejected | Error with an appropriate message; exact response details are unspecified. | FR-10 lines 146–162; FR-18 line 221; human review dated 2026-08-22 |
| PR-004 | INVALID | `status: "delivered"` | ST-02 `confirmed` | Authenticated Admin; existing order is `confirmed`; edge is omitted from the exhaustive diagram | None; requested transition is rejected | Error with an appropriate message; exact response details are unspecified. | FR-10 lines 146–162; FR-18 line 221; human review dated 2026-08-22 |
| PR-005 | INVALID | `status: "pending"` | ST-03 `shipping` | Authenticated Admin; existing order is `shipping`; edge is omitted from the exhaustive diagram | None; requested transition is rejected | Error with an appropriate message; exact response details are unspecified. | FR-10 lines 146–162; FR-18 line 221; human review dated 2026-08-22 |
| PR-006 | INVALID | `status: "confirmed"` | ST-03 `shipping` | Authenticated Admin; existing order is `shipping`; edge is omitted from the exhaustive diagram | None; requested transition is rejected | Error with an appropriate message; exact response details are unspecified. | FR-10 lines 146–162; FR-18 line 221; human review dated 2026-08-22 |
| PR-007 | INVALID | `status: "canceled"` | ST-03 `shipping` | Authenticated Admin; existing order is `shipping`; edge is omitted from the exhaustive diagram | None; requested transition is rejected | Error with an appropriate message; exact response details are unspecified. | FR-10 lines 146–162, with line 161 not authorizing this edge; FR-18 line 221; human review dated 2026-08-22 |

Requests where source and requested destination are the same (`pending→pending`, `confirmed→confirmed`, `shipping→shipping`, `delivered→delivered`, and `canceled→canceled`) are not classified. Same-state update and idempotency semantics are entirely unspecified.

## Guards and endpoint-level preconditions

- The endpoint requires `Authorization: Bearer <token>`, a valid JWT, and `role = 'admin'` (API specification line 173; FR-12 lines 174–179; SEC-02 and SEC-03 at lines 279–280).
- The order must already exist in the transition's source state. How to create or place it there is fixture setup outside the selected single-endpoint model.
- The body uses a JSON `status` property, and the documented vocabulary is `pending`, `confirmed`, `shipping`, `delivered`, and `canceled` (API specification line 182; FR-10 lines 141–162).
- Authentication failure, authorization failure, nonexistent-order behavior, invalid status vocabulary, and malformed input are contract/domain/security concerns unless the specification ties them to lifecycle state. They are not modeled as lifecycle transitions here.

## Gaps and ambiguities

1. Same-state requests remain unspecified: whether one succeeds idempotently, fails as an invalid transition, or is handled another way is not defined.
2. No success status code, response body, headers, or exact persistence-verification response is specified.
3. Invalid transitions require an error with an appropriate message, but the HTTP status, body schema, and wording are unspecified.
4. Behavior for a nonexistent order is unspecified and cannot be modeled as an order lifecycle state.
5. Concurrency/version guards, atomicity, rollback behavior, and simultaneous-update ordering are unspecified.
6. Validation-versus-authentication/authorization precedence is unspecified.

## Review block

- **Review Status:** PENDING
- **Reviewer:** User human review received 2026-08-22
- **Review Notes:** For `STATE-PHASE1-v1`, the reviewer established that the FR-10 diagram is authoritative and exhaustive for non-self transitions; classified PR-001 through PR-007 as INVALID, including `shipping` → `canceled`; determined FR-10 line 161 does not authorize that edge because FR-18 requires Admin changes to follow FR-10; kept every same-state update UNSPECIFIED; preserved all other analysis; and explicitly withheld Phase 2 generation approval. These decisions are incorporated in `STATE-PHASE1-v2`.
- **Reviewed Version:** `STATE-PHASE1-v1` (decision source); revised report `STATE-PHASE1-v2` remains PENDING for Phase 2 approval

### Reviewer decisions requested

1. Approve this exact `STATE-PHASE1-v2` report for Phase 2 generation when ready, or revise it further.
2. If desired in a later review, define same-state behavior and any response or persistence oracle beyond the documented semantic outcomes; until then those points retain the stated limitations.

No STATE test candidates have been generated. Generation must wait for approval of this exact report version.
