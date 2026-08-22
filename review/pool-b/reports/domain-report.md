# DOMAIN Phase 1 Analysis — Pool B: Apply Coupon

## Endpoint and source identity

| Item | Value |
| --- | --- |
| Selected endpoint | `POST /api/apply-coupon` |
| Base URL | `http://localhost:3000` |
| API specification | `reference/api_specification.md`, section 5.1, lines 151–163; SHA-256 `488CBCB790099BA9CBB34C7C80BA04C6AEC9E9EBB598F031FFA575737547B139` |
| System requirements | `reference/system_requirements.md`, FR-09 lines 110–135, FR-17 lines 213–216, SEC-02 line 279; version 2.0 dated 2026-05-14; SHA-256 `7859599624A8F94E7B28859F5E3EDBEE71F275E1A71043E3EFCAB10D5EE14CDD` |
| Shared normalized context | `review/pool-b/shared-api-context.md` (read-only) |
| Analysis phase | Phase 1 only; no test cases generated |

The API specification documents a JSON request example but no formal request schema. FR-09 defines five conjunctive coupon-qualification conditions and the discount formulas. In this report, **qualifying** and **nonqualifying** mean that a value and its associated setup do or do not satisfy those explicit conditions. They do not assert a particular HTTP status, error body, validation order, coercion rule, or other undocumented observable behavior.

## Valid baseline

Request:

```http
Authorization: Bearer <valid JWT for the test user>
Content-Type: application/json
```

```json
{
  "code": "SAVE10",
  "total_amount": 500000,
  "user_id": 1
}
```

Setup:

- `SAVE10` has the documented fixture properties: type `percent`, discount value 10%, minimum order amount 300000, expiry date 2099-12-31, and maximum one use per user (FR-09 lines 128–132).
- The coupon exists, has `is_active = 1`, and the current date is before 2099-12-31 (FR-09 C1–C2, lines 116–117).
- The authenticated test user has used `SAVE10` zero times, which is less than its `max_uses_per_user` of 1 (FR-09 C5, line 120 and fixture line 132).
- The bearer token is a valid JWT (FR-09 C4, line 119; SEC-02 line 279).
- For setup only, the JWT identifies the test user represented by `user_id: 1`. The sources do not specify this identity-binding rule.

Expected formula oracle for this qualifying baseline: `discount_amount = 500000 × 10 / 100 = 50000` and `final_amount = 500000 - 50000 = 450000` (FR-09 lines 124 and 126). One-factor-at-a-time analysis keeps all other request values and setup conditions at this baseline unless a documented relation requires coordinated changes.

The exact `Content-Type` MIME value is not stated by the source; `application/json` above is a transport assumption consistent with the documented “Body (JSON)” representation, not an asserted contract requirement.

## Complete parameter inventory

### Transport locations

| Location | Inventory | Exact basis |
| --- | --- | --- |
| Path | No path parameters declared | The fixed path is `/api/apply-coupon` at API specification line 154 |
| Query | No query parameters declared | No query input appears in API specification section 5.1, lines 153–163 |
| Header | `Authorization` carrying a valid JWT is required for coupon application; the normalized transport convention is `Bearer <token>` | FR-09 C4 line 119; SEC-02 line 279; shared context authentication model |
| Cookie | No cookie parameters declared | No cookie input appears in API specification section 5.1 or FR-09 |
| Body container | A JSON object is the documented representation | API specification lines 156–162 |
| Nested body fields | None declared | The example contains only three top-level members: `code`, `total_amount`, and `user_id` |

The sources do not define malformed-body handling, an exact request MIME string, duplicate-member behavior, member order, additional-property behavior, or coercion.

### Header and body inputs

| Input | Location | Requiredness | Documented type / format | Allowed values and explicit constraints | Nullability | Default | Exact basis |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `Authorization` | Header | Required for coupon application | Bearer authentication header carrying a JWT in the normalized context; token syntax and claims are not specified | JWT must be valid | Not applicable as a JSON concept; empty-header handling is unspecified | None specified | FR-09 C4 line 119; SEC-02 line 279 |
| `code` | JSON body, top-level | Not explicitly stated by an API schema | Shown as JSON string (`"SAVE10"`) | The resolved coupon must exist and have `is_active = 1`; the coupon must also meet its expiry condition. Coupon creation requires a unique `code`, but no length, pattern, casing, whitespace, or nonempty rule is stated | Not specified | None specified | API specification lines 156–162; FR-09 C1–C2 lines 116–117; FR-17 line 216 |
| `total_amount` | JSON body, top-level | Not explicitly stated by an API schema | Shown as JSON number (`500000`) | Must be greater than or equal to the resolved coupon's `min_order_amount`. No general minimum, maximum, integer-only, decimal precision, or currency-unit rule is specified | Not specified | None specified | API specification lines 156–162; FR-09 C3 line 118 |
| `user_id` | JSON body, top-level | Not explicitly stated by an API schema | Shown as JSON number (`1`) | The selected user's prior-use count for the coupon must be less than `max_uses_per_user`. No range, integer-only rule, existence rule, or JWT/body identity-binding rule is specified | Not specified | None specified | API specification lines 156–162; FR-09 C5 line 120 |

### Related stored coupon attributes and state-dependent preconditions

These are not additional request fields, but they determine which semantic domain a request value occupies.

| Attribute / state | Explicit domain rule | Exact basis |
| --- | --- | --- |
| Coupon existence and `is_active` | The code must exist in the database and the coupon must have `is_active = 1` | FR-09 C1 line 116 |
| `expired_at` | Current date must be strictly before `expired_at` | FR-09 C2 line 117 |
| `min_order_amount` | `total_amount >= min_order_amount`; coupon creation requires `min_order_amount >= 0` | FR-09 C3 line 118; FR-17 line 216 |
| Prior uses and `max_uses_per_user` | Prior uses by this user must be `< max_uses_per_user`; coupon creation requires `max_uses_per_user >= 1` | FR-09 C5 line 120; FR-17 line 216 |
| `type` | Coupon creation allows `percent` or `fixed` | FR-17 line 216 |
| `discount_value` | Coupon creation requires a positive value | FR-17 line 216 |

The active/inactive flag, expiry relation, and per-user usage count are retained in DOMAIN because they define input-dependent eligibility classes and ordered business boundaries for this calculation. They are state-dependent preconditions, not endpoint-driven transitions: API specification line 155 documents calculation of a discounted total, and neither authoritative source documents that this endpoint mutates a coupon or usage record, increments or consumes a use, reserves a coupon, or reaches a destination state. Accordingly, endpoint-driven STATE transition testing is `NOT_APPLICABLE`; DP-008–DP-014, DP-029–DP-031, DB-004, and DB-005–DB-007 remain the authoritative DOMAIN coverage for these conditions.

## Equivalence partitions

Classification legend:

- **Qualifying**: satisfies the cited explicit rule, assuming all other baseline conditions hold.
- **Nonqualifying**: contradicts at least one cited FR-09 qualification condition. The source does not specify the response.
- **Unspecified**: the authoritative sources do not say whether the API accepts, rejects, coerces, or otherwise handles the class.
- **Documented representation only**: shown by the API example but not established by a formal schema.

### Body container and transport

| ID | Input / subject | Partition | Classification | Exact specification basis | Assumptions / limits |
| --- | --- | --- | --- | --- | --- |
| DP-001 | Body container | JSON object containing `code`, `total_amount`, and `user_id` in their documented representations | Documented representation only | API specification lines 156–162 | It becomes qualifying only when all DP-008, DP-019, DP-029, and DP-005 conditions and relevant state guards hold |
| DP-002 | Body container | Well-formed JSON whose top-level value is not an object | Unspecified | API specification lines 156–162 show an object but provide no schema or rejection rule | Includes arrays, strings, numbers, booleans, and JSON `null` |
| DP-003 | Body container | Malformed JSON, empty payload, or non-JSON payload | Unspecified | No malformed-body or alternate-media handling rule is stated | No parser response may be inferred |
| DP-004 | Body container | Documented members plus one or more additional members | Unspecified | No additional-property rule is documented | Do not assume either ignore or reject behavior |
| DP-005 | `Authorization` | Bearer header carries a valid JWT | Qualifying for C4 | FR-09 C4 line 119; SEC-02 line 279 | Other four FR-09 conditions must also hold |
| DP-006 | `Authorization` | Header omitted or empty, so no valid JWT is supplied | Nonqualifying for C4 | FR-09 C4 line 119 | Exact status, body, challenge header, and evaluation order are unspecified |
| DP-007 | `Authorization` | Header is present but does not carry a valid JWT, including malformed, invalid, or expired token material | Nonqualifying for C4 | FR-09 C4 requires a valid JWT; SEC-02 line 279 | Token grammar, claims, signature algorithms, expiry treatment, and distinction among failure modes are not specified |

### `code`

| ID | Input / subject | Partition | Classification | Exact specification basis | Assumptions / limits |
| --- | --- | --- | --- | --- | --- |
| DP-008 | `code` | Resolves to an existing active, unexpired `percent` coupon | Qualifying for C1–C2 | FR-09 C1–C2 lines 116–117; percent formula line 124; `SAVE10` fixture line 132 | Threshold, JWT, and usage conditions must also hold |
| DP-009 | `code` | Resolves to an existing active, unexpired `fixed` coupon | Qualifying for C1–C2 | FR-09 C1–C2 lines 116–117; fixed formula line 125; `BIGBUY` and `VIP100` fixtures lines 133–134 | Threshold, JWT, and usage conditions must also hold |
| DP-010 | `code` | Does not resolve to a coupon in the database | Nonqualifying for C1 | FR-09 C1 line 116 | Lookup comparison and rejection response are unspecified |
| DP-011 | `code` | Resolves to an existing coupon with `is_active != 1` | Nonqualifying for C1 | FR-09 C1 line 116 | Requires an arranged inactive fixture; no such sample fixture is supplied |
| DP-012 | `code` | Resolves to an active coupon whose current date is before `expired_at` | Qualifying for C2 | FR-09 C2 line 117 | This isolates the expiry state while keeping C1 true |
| DP-013 | `code` | Resolves to an active coupon whose current date equals `expired_at` | Nonqualifying for C2 | FR-09 C2 requires current date to be before `expired_at` | Timezone and timestamp granularity are unspecified |
| DP-014 | `code` | Resolves to an active coupon whose current date is after `expired_at` | Nonqualifying for C2 | FR-09 C2 line 117; `EXPIRED` fixture line 135 | Other conditions may be held valid to isolate expiry |
| DP-015 | `code` | Empty string, whitespace-only string, or an unusual/arbitrary string | Unspecified | No nonempty, whitespace, pattern, or allowed-character rule is documented | Such a value is nonqualifying only if setup establishes that it does not resolve to an active coupon |
| DP-016 | `code` | Casing or surrounding whitespace differs from a stored code | Unspecified | No normalization or comparison rule is documented | Do not assume case sensitivity or trimming |
| DP-017 | `code` | Member omitted or JSON `null` | Unspecified | API schema requiredness and nullability are not stated | The semantic coupon-existence rule does not define request validation behavior |
| DP-018 | `code` | Non-string JSON value | Unspecified | The example shows a string but no formal type rule or coercion rule is stated | Includes numbers, booleans, objects, and arrays |

### `total_amount`

| ID | Input / subject | Partition | Classification | Exact specification basis | Assumptions / limits |
| --- | --- | --- | --- | --- | --- |
| DP-019 | `total_amount` | JSON number greater than the selected coupon's `min_order_amount` | Qualifying for C3 | FR-09 C3 line 118 | No integer or decimal restriction is added |
| DP-020 | `total_amount` | JSON number exactly equal to the selected coupon's `min_order_amount` | Qualifying for C3 | FR-09 C3 explicitly uses `>=`, line 118 | Inclusive threshold |
| DP-021 | `total_amount` | JSON number below the selected coupon's `min_order_amount` | Nonqualifying for C3 | FR-09 C3 line 118 | There is no general apply-request minimum separate from the selected coupon threshold |
| DP-022 | `total_amount` | Zero | Conditional: qualifying when selected coupon minimum is 0; otherwise nonqualifying for C3 | FR-09 C3 line 118; FR-17 permits `min_order_amount = 0`, line 216 | No documented sample coupon has a zero minimum; an arranged coupon is needed |
| DP-023 | `total_amount` | Negative JSON number | Nonqualifying for every validly created coupon because coupon minimum is at least 0 | FR-09 C3 line 118 together with FR-17 `min_order_amount >= 0`, line 216 | This conclusion relies on the stored coupon satisfying FR-17; no separate request validation rule is inferred |
| DP-024 | `total_amount` | Positive decimal or very large finite JSON number while remaining on a known side of the coupon threshold | C3 classification follows only the threshold comparison; representation handling otherwise unspecified | FR-09 C3 line 118; API example line 160 | No precision, integer-only, maximum, rounding, or overflow rule is documented |
| DP-025 | `total_amount` | Numeric-looking JSON string | Unspecified | The example uses a JSON number, but no formal type or coercion rule is stated | Do not treat `"500000"` as equivalent to `500000` without review |
| DP-026 | `total_amount` | Member omitted or JSON `null` | Unspecified | API schema requiredness, nullability, and default are not stated | No error response may be inferred |
| DP-027 | `total_amount` | Boolean, object, or array | Unspecified | The example uses a number but no formal type rule is stated | No coercion behavior may be inferred |
| DP-028 | `total_amount` / body | `NaN`, positive infinity, or negative infinity token | Malformed JSON / unspecified API behavior | JSON request representation at API specification lines 156–162 | These are not JSON numbers; covered operationally by malformed-body DP-003 |

### `user_id` and user-specific usage

| ID | Input / subject | Partition | Classification | Exact specification basis | Assumptions / limits |
| --- | --- | --- | --- | --- | --- |
| DP-029 | `user_id` plus stored usage | Identifies a user whose prior-use count for the selected coupon is below `max_uses_per_user` | Qualifying for C5 | FR-09 C5 line 120 | The source does not define how the body identifier is authenticated |
| DP-030 | `user_id` plus stored usage | Identifies a user whose prior-use count equals `max_uses_per_user` | Nonqualifying for C5 | FR-09 C5 uses strict `<`, line 120 | Exact response and whether attempts are counted are unspecified |
| DP-031 | `user_id` plus stored usage | Identifies a user whose prior-use count is greater than `max_uses_per_user` | Nonqualifying for C5 | FR-09 C5 line 120 | Such state may indicate inconsistent data, but it remains outside the qualifying partition |
| DP-032 | `user_id` × JWT identity | Body identifier denotes the same user represented by the valid JWT | Baseline setup; contractual classification unspecified | FR-09 C4–C5 lines 119–120 mention valid JWT and per-user usage but state no binding rule | Do not promote the assumed match into a requirement |
| DP-033 | `user_id` × JWT identity | Body identifier denotes a different user from the valid JWT | Unspecified | No ownership or identity-binding rule is documented | Security implications require review; no expected accept/reject outcome is source-supported |
| DP-034 | `user_id` | Numeric value for a nonexistent user | Unspecified | No user-existence rule for this endpoint is documented | Usage lookup behavior is unknown |
| DP-035 | `user_id` | Zero, negative, fractional, or very large finite JSON number | Unspecified | No range, integer-only, or maximum rule is documented | Do not infer identifier conventions from the example value `1` |
| DP-036 | `user_id` | Member omitted or JSON `null` | Unspecified | API schema requiredness, nullability, and default are not stated | The C5 semantic relation does not define validation behavior |
| DP-037 | `user_id` | String, boolean, object, or array | Unspecified | The example uses a JSON number but no formal type or coercion rule is stated | Numeric-looking strings remain unspecified |

### Omission, null, empty, malformed, type, and set coverage check

| Concern | `Authorization` | `code` | `total_amount` | `user_id` | Body container |
| --- | --- | --- | --- | --- | --- |
| Omission | DP-006, nonqualifying C4 | DP-017, unspecified request behavior | DP-026, unspecified | DP-036, unspecified | Missing/empty payload in DP-003 |
| Null / empty | Empty header in DP-006 | DP-015 and DP-017 | DP-026 | DP-036 | JSON `null` in DP-002; empty payload in DP-003 |
| Malformed | DP-007 | Syntax/normalization unknown in DP-015–DP-016 | Non-JSON numeric tokens in DP-028 | No identifier format is stated | DP-003 |
| In-set / out-of-set | Valid versus invalid JWT in DP-005–DP-007 | Existing/active versus nonexistent/inactive/expired in DP-008–DP-014 | Threshold partitions DP-019–DP-023 | Usage partitions DP-029–DP-031 | Additional members DP-004 |
| JSON / transport type | Header transport, not JSON | DP-018 | DP-025–DP-028 | DP-035–DP-037 | DP-001–DP-003 |

## Boundary analysis

Only source-supported ordered limits are included. Boundary representatives are analysis values, not generated test cases, and do not define undocumented response details.

| ID | Input / measure | Explicit limit | Just outside / below | Boundary | Just inside / above | Classification and exact basis | Assumptions / limits |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DB-001 | `total_amount` for `SAVE10` or `VIP100` | `min_order_amount = 300000`; qualifying comparison is `>=` | `299999`: nonqualifying C3 | `300000`: qualifying C3 | `300001`: qualifying C3 | FR-09 C3 line 118; fixtures lines 132 and 134 | Uses currency increments of 1 because fixture values are whole numbers; no general currency-unit or decimal rule is documented |
| DB-002 | `total_amount` for `BIGBUY` | `min_order_amount = 500000`; qualifying comparison is `>=` | `499999`: nonqualifying C3 | `500000`: qualifying C3 | `500001`: qualifying C3 | FR-09 C3 line 118; fixture line 133 | Same representational limitation as DB-001 |
| DB-003 | `total_amount` for an arranged coupon with the minimum allowed creation value | `min_order_amount = 0`; qualifying comparison is `>=` | `-1`: nonqualifying C3 | `0`: qualifying C3 | `1`: qualifying C3 | FR-17 line 216 permits minimum 0; FR-09 C3 line 118 | Requires a valid arranged coupon; no general rejection rule for negative request amounts is inferred |
| DB-004 | Current date relative to selected coupon `expired_at` | Current date must be strictly before `expired_at` | One representable date before expiry: qualifying C2 | Current date equal to expiry: nonqualifying C2 | One representable date after expiry: nonqualifying C2 | FR-09 C2 line 117 | “Current date” suggests calendar-date comparison, but timezone, time-of-day, and clock-control details are unspecified |
| DB-005 | Prior-use count for a coupon with `max_uses_per_user = M` | Prior uses must be `< M` | `M - 1`: qualifying C5 | `M`: nonqualifying C5 | `M + 1`: nonqualifying C5 | FR-09 C5 line 120 | `M >= 1` by FR-17 line 216, so `M - 1` is representable as a nonnegative count |
| DB-006 | Prior-use count for `SAVE10` or `BIGBUY` | Fixture `max_uses_per_user = 1` | `0`: qualifying C5 | `1`: nonqualifying C5 | `2`: nonqualifying C5 | FR-09 C5 line 120; fixture lines 132–133 | DB-006 is an exact fixture instantiation of DB-005 |
| DB-007 | Prior-use count for `VIP100` | Fixture `max_uses_per_user = 2` | `1`: qualifying C5 | `2`: nonqualifying C5 | `3`: nonqualifying C5 | FR-09 C5 line 120; fixture line 134 | A count of 0 is also qualifying but is not adjacent to this boundary |

No source-supported length boundary exists for `code`; no numeric identifier boundary exists for `user_id`; and no ordered boundary exists for JWT syntax. There is no general maximum, integer-only constraint, or precision limit for `total_amount`. The positive `discount_value` and nonnegative `min_order_amount` creation constraints describe stored coupon setup, not direct inputs to this endpoint; only `min_order_amount` is instantiated above because it directly determines the request boundary.

## Documented cross-parameter and state constraints

| Constraint ID | Constraint | Exact specification basis | Domain-analysis treatment |
| --- | --- | --- | --- |
| DC-001 | C1 through C5 are conjunctive: existence/active state, unexpired state, threshold, valid JWT, and remaining per-user usage must all hold | FR-09 lines 112–120 | Keep every non-target condition valid when isolating a partition or boundary; no rejection priority is inferred |
| DC-002 | `code` selects the stored coupon whose `is_active`, `expired_at`, `min_order_amount`, `max_uses_per_user`, `type`, and `discount_value` drive qualification and calculation | FR-09 lines 116–125; FR-17 line 216 | Code partitions require controlled fixture state; changing code can change several dependent values and is not always one-factor-at-a-time |
| DC-003 | `total_amount` is compared with the selected coupon's `min_order_amount` | FR-09 C3 line 118 | DP-019–DP-023 and DB-001–DB-003 vary total against a known fixture threshold |
| DC-004 | Prior usage is scoped to both the selected coupon and the user represented by `user_id` in the documented body model | FR-09 C5 line 120; API specification lines 158–162 | DP-029–DP-031 and DB-005–DB-007 require user/coupon-specific setup |
| DC-005 | A valid JWT is required, but the sources do not bind JWT identity to body `user_id` | FR-09 C4–C5 lines 119–120 | Matching identity is baseline setup only; DP-032–DP-033 preserve the ambiguity |
| DC-006 | `percent` coupon calculation uses `total × discount_value / 100`; `fixed` uses `discount_value`; both subtract the discount from total | FR-09 lines 122–126 | DP-008 and DP-009 preserve both supported formula classes; response fields are documented by API specification line 155 |
| DC-007 | Active/inactive, expiry, and per-user usage-limit conditions are state-dependent preconditions, but this operation is documented only as calculating a result; no endpoint-driven mutation or destination state is stated | API specification line 155; FR-09 C1–C2 and C5 lines 116–117 and 120; absence of a mutation rule in FR-09 | Retain these conditions under DOMAIN (DP-008–DP-014, DP-029–DP-031, DB-004–DB-007). Endpoint-driven STATE transition testing is `NOT_APPLICABLE`; do not assert consumption, usage increment, reservation, idempotency, or persistence from repeated calls |

## Gaps and ambiguities requiring review

1. There is no formal request schema. Body-field requiredness, nullability, type enforcement, defaults, coercion, duplicate-member handling, additional-member behavior, and malformed/missing-body behavior are unspecified.
2. The source labels the body JSON but does not state the exact HTTP `Content-Type` value, charset, or behavior for alternate media types.
3. `code` has no length, pattern, alphabet, nonempty, casing, trimming, or normalization rule. Even coupon creation only states uniqueness; it does not state that an empty code is forbidden.
4. `total_amount` has no general lower/upper bound, integer requirement, decimal precision, currency unit, rounding, finite-range, or overflow rule. Only its comparison with the selected coupon's minimum is explicit.
5. FR-17 constrains stored `min_order_amount >= 0`, but the source does not say whether this endpoint may assume all stored records are valid or how inconsistent legacy data should behave.
6. `user_id` has no requiredness, nullability, range, integer, user-existence, or normalization rule.
7. No rule binds client-supplied `user_id` to the authenticated JWT identity. Acceptance or rejection of a mismatched identity cannot be specified without an approved assumption.
8. JWT transport is represented as a bearer header in the normalized system convention, but the endpoint subsection does not repeat the header. Token grammar, required claims, expiry semantics, and distinctions among missing, malformed, invalid, and expired tokens are not documented.
9. Expiry uses “current date before `expired_at`” without timezone, time-of-day, storage type, or comparison-granularity rules. Equality is nevertheless nonqualifying because “before” is strict.
10. Prior-use count is compared strictly with `max_uses_per_user`, but the sources do not define how prior use is recorded, whether this calculation endpoint changes the count, or how concurrent attempts behave.
11. Coupon creation allows `percent` and `fixed` and requires a positive `discount_value`, but no maximum percent, maximum fixed discount, cap at `total_amount`, negative-final prevention, rounding, or numeric precision rule is stated.
12. The sample coupons are fixtures, not universal constraints. Their literal values do not establish general `code`, amount, expiry, or use-limit ranges.
13. No HTTP success or failure status, error schema/message, response type details, response headers, or rejection precedence is documented. For nonqualifying and unspecified partitions, only the violated qualification rule can be cited.
14. The response is stated to contain `discount_amount` and `final_amount`, but their JSON types, requiredness, nullability, additional properties, and exact numeric representation are unspecified.
15. No path, query, cookie, or additional endpoint-specific header inputs are documented.

## Review block

- **Review Status:** PENDING
- **Reviewer:** _Unassigned_
- **Review Notes:** _Revised per review to state explicitly that active/inactive, expiry, and per-user usage-limit conditions remain DOMAIN state-dependent preconditions, while endpoint-driven STATE transition testing is NOT_APPLICABLE because no mutation or destination state is documented. All previously approved DOMAIN partitions, boundaries, classifications, and gaps are preserved. Awaiting human approval of this exact revised version; no test generation is authorized._
- **Reviewed Version:** `POOL-B-DOMAIN-v2`
