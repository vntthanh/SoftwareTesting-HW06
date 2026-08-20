# State Transition Analysis — Pool A

- **Category:** STATE
- **State Applicability:** APPLICABLE
- **Selected endpoint:** `POST /api/reset-password`
- **Phase:** 1 — applicability and analysis only
- **Report version:** `STATE-PHASE1-v1`

## Source identity

- API specification: `reference/api_specification.md`, SHA-256 `488CBCB790099BA9CBB34C7C80BA04C6AEC9E9EBB598F031FFA575737547B139`.
- System requirements: `reference/system_requirements.md`, version 2.0 dated 2026-05-14, SHA-256 `7859599624A8F94E7B28859F5E3EDBEE71F275E1A71043E3EFCAB10D5EE14CDD`.
- Selected operation: API specification lines 44–52.
- Related requirements: FR-01 at system requirements lines 30–36; FR-03 at lines 46–60; SEC-07 at line 284.
- Shared normalized context: `review/pool-a/shared-api-context.md`.

## Applicability evidence

State-transition testing applies because the authoritative requirements define an OTP lifecycle and state-dependent reset behavior:

1. FR-03 lines 48–51 defines a prior workflow step that generates a random six-digit OTP for a registered email. This issuance is a precondition established outside the selected endpoint.
2. FR-03 line 60 binds the OTP to the email that requested it and expressly says it cannot be used for another email.
3. SEC-07 line 284 requires the reset-password OTP to have an expiry and to be invalidated after use.
4. FR-03 lines 55–60 defines the reset step using the OTP and a conforming new password; the selected endpoint and its three documented request fields appear at API specification lines 44–52.

These rules make the result depend on whether the OTP is usable, expired, already used, and presented with its bound email. The state names below are normalized analysis labels; they are not source terminology.

## State definitions

| State ID | Normalized state | Definition | Exact basis | Constraints / caveats |
| --- | --- | --- | --- | --- |
| `ST-01` | OTP usable for bound email | An OTP has been generated for a registered email, is still within its unspecified validity period, and has not been used. It is usable only with the email that requested it. | FR-03 lines 48–51 and 60; SEC-07 line 284 | Issuance occurs in workflow step 1, outside the selected endpoint. The sources do not define the lifetime, issuance response semantics, or how multiple OTPs interact. |
| `ST-02` | OTP expired | The OTP's required validity period has elapsed, so it no longer satisfies the time-validity guard. | SEC-07 line 284 | The expiry duration, clock source, boundary instant, and any grace period are not specified. |
| `ST-03` | OTP invalidated after use | The OTP has been used and, as required, is invalidated for later use. | SEC-07 line 284 | The sources do not define the exact commit point at which a reset attempt counts as “used,” nor the response to a replay. |

The account's password replacement is an intended effect of the reset operation (API specification lines 44–52 and FR-03 lines 55–60), but the sources do not define enough persistence or transaction semantics to introduce separate credential-state IDs without invention.

## Guards and state variables

| Guard ID | Guard | Satisfied condition | Failure significance | Exact basis |
| --- | --- | --- | --- | --- |
| `GD-01` | Email binding | Request `email` is the email for which the submitted OTP was generated. | The OTP cannot be used for a different email. | FR-03 line 60 |
| `GD-02` | Time validity | OTP is within its validity period. | An expired OTP cannot be treated as valid for reset. | SEC-07 line 284 |
| `GD-03` | One-time validity | OTP has not already been used and invalidated. | An invalidated OTP cannot be treated as reusable. | SEC-07 line 284 |
| `GD-04` | New-password strength | `newPassword` has at least 8 characters and includes at least one uppercase letter, one lowercase letter, one digit, and one of `@`, `$`, `!`, `%`, `*`, `?`, `&`. | A nonconforming new password does not meet the reset requirement. | FR-03 line 58 incorporating FR-01 line 34 |
| `GD-05` | Workflow password confirmation | The new-password and confirmation values match. | The system must reject a mismatch in the two-step workflow. | FR-03 lines 57–59 |

`GD-05` is authoritative at workflow/UI level, but it is not directly expressible through the documented selected-endpoint request: the API example contains only `email`, `resetToken`, and `newPassword` (API specification lines 46–52). No confirmation field or mapping may be invented.

## Transition and guard table

| Transition ID | Classification | Source | Trigger / request | Guard or event | Destination | Required observable result | Exact basis |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `TR-001` | Valid state-changing transition | `ST-01` | `POST /api/reset-password` with the documented `email`, `resetToken`, and `newPassword`; workflow confirmation is a setup condition because its API mapping is unspecified | `GD-01`, `GD-02`, `GD-03`, and `GD-04` satisfied; `GD-05` satisfied at workflow level | `ST-03` for the OTP; intended password-reset effect for the account | The password-reset operation uses the eligible OTP, and the OTP is invalidated after use. No HTTP status, body, message, header, exact persistence point, or transaction order is specified. | API specification lines 44–52; FR-03 lines 55–60; SEC-07 line 284 |
| `TR-002` | Supported invalid transition attempt | `ST-01`, where the OTP is bound to email A | Submit that OTP with a different email B | `GD-01` fails | Not specified. The sources do not say whether the failed cross-email attempt consumes or otherwise changes the OTP for email A. | The OTP must not be usable to reset email B. Exact HTTP response and the state/effect for email A are unspecified. | FR-03 line 60 |
| `TR-003` | Supported invalid transition attempt | `ST-02` | Submit the expired OTP to the selected endpoint | `GD-02` fails | The OTP remains non-usable due to expiry (`ST-02` as its validity classification); any endpoint-driven mutation is unspecified. | The expired OTP must not be treated as a valid reset OTP. Exact HTTP response, password effect, and other side effects are unspecified. | SEC-07 line 284 |
| `TR-004` | Supported invalid transition attempt / replay | `ST-03` | Submit an OTP again after it has already been used and invalidated | `GD-03` fails | The OTP remains invalidated (`ST-03`); no reactivation behavior is documented. Any additional endpoint side effects are unspecified. | The invalidated OTP must not be reusable for another reset. Exact HTTP response and other effects are unspecified. | SEC-07 line 284 |
| `TR-005` | Guard-failing transition attempt | `ST-01` | Submit an otherwise state-eligible OTP with a `newPassword` that violates the incorporated FR-01 strength rule | `GD-04` fails | `ST-01` — the OTP remains usable | The reset is rejected and the password is not changed. As a reviewed external workflow assumption, an unsuccessful password validation does not consume a valid OTP. | FR-03 line 58; FR-01 line 34; external password-reset workflow assumption |

### Setup and out-of-scope lifecycle changes

- Establishing `ST-01` requires workflow step 1, which generates an OTP for a registered email (FR-03 lines 48–51). Under the selected single-endpoint scope, this is a precondition, not a tested transition through `POST /api/reset-password`.
- Elapsing the unspecified validity period establishes `ST-02` (SEC-07 line 284). The sources provide no duration or boundary value.
- `TR-001` is the documented selected-endpoint path that supports the `ST-01` → `ST-03` OTP transition. Exact sequencing between password replacement and OTP invalidation is not documented.

## Supported invalid-transition model

- Wrong-email use is supported as invalid by the explicit binding prohibition in FR-03 line 60 (`TR-002`). The model does not assert that this attempt consumes or preserves the OTP.
- Expired-token use is supported as invalid by the required expiry in SEC-07 (`TR-003`). No specific expiry duration or error contract is asserted.
- Reuse after a successful use is supported as invalid by the required invalidation-after-use rule in SEC-07 (`TR-004`). No replay status or error body is asserted.
- A weak new password is a documented guard failure (`TR-005`), but token consumption on this validation failure is unspecified.
- A confirmation mismatch is supported as invalid for the overall workflow by FR-03 lines 57–59, but it is not modeled as an endpoint transition because the selected API has no documented confirmation field or mapping.
- Unknown, malformed, omitted, null, wrong-type, or additional request values are not assigned state transitions because their handling is not specified.

## Gaps and ambiguities requiring review

1. No success or error HTTP status, response body, message, media type, or header is specified for the selected endpoint.
2. OTP expiry duration, boundary instant, clock source, and grace period are unspecified.
3. The exact point at which an OTP counts as “used” is unspecified: receipt, successful OTP validation, successful password validation, or committed password replacement could differ.
4. Atomicity and ordering between password replacement and OTP invalidation are unspecified, including behavior under partial failure.
5. OTP state after a wrong-email attempt or weak-password attempt is unspecified.
6. The workflow requires confirmation to match, but the endpoint's request example has no confirmation field and no mapping is documented.
7. No rule states whether issuing a newer OTP supersedes older OTPs, whether multiple live OTPs may exist, or whether OTPs are unique across accounts.
8. Retry limits, attempt counters, lockout, throttling, and resend behavior are unspecified.
9. Email normalization/case handling is unspecified and must not be folded into the binding guard.
10. Behavior for arbitrary/unissued tokens is not expressly documented; it must not be given an invented state, status, or message.
11. Session/token revocation, automatic login, notifications, password-history rules, and old-password behavior after reset are unspecified.
12. The sources do not state whether JWT authentication applies to this public-looking reset operation.

## Review block

- **Review Status:** PENDING
- **Reviewer:**
- **Review Notes:**
- **Reviewed Version:**

No test candidates were generated in Phase 1.
