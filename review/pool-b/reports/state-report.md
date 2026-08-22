# State Applicability Record — Pool B

- **Category:** STATE
- **State Applicability:** NOT_APPLICABLE
- **Selected endpoint:** `POST /api/apply-coupon`
- **Functional requirement:** FR-09
- **Phase:** 1 — applicability analysis only
- **Report version:** `STATE-PHASE1-v2`
- **Review Required:** NO

## Source identity

- API specification: `reference/api_specification.md`, section 5.1, lines 151–163; SHA-256 `488CBCB790099BA9CBB34C7C80BA04C6AEC9E9EBB598F031FFA575737547B139`.
- System requirements: `reference/system_requirements.md`, version 2.0 dated 2026-05-14; FR-09, lines 110–135; FR-17, lines 213–216; SHA-256 `7859599624A8F94E7B28859F5E3EDBEE71F275E1A71043E3EFCAB10D5EE14CDD`.
- Shared normalized context: `review/pool-b/shared-api-context.md`.

## Applicability basis

FR-09 C1, C2, and C5 define state-dependent eligibility preconditions: the coupon must exist and be active, the current date must be before its expiry, and the user's prior usage must be below the per-user limit. However, API specification section 5.1, line 155 documents this endpoint only as calculating the total after applying a discount. Neither authoritative source documents an endpoint-driven state change, destination state, lifecycle sequence, coupon consumption, usage-count increment, reservation, or idempotency rule for `POST /api/apply-coupon`.

Accordingly, no supported endpoint-driven transition model exists for STATE testing. Active/inactive status, expiry, and usage-limit conditions remain covered as DOMAIN partitions and boundaries.

No STATE test candidates were generated.
