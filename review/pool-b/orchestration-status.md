# Pool B API Test Generation Status

- Endpoint: `POST /api/apply-coupon`
- Requirement: FR-09
- Shared context: `review/pool-b/shared-api-context.md`
- Final output requested: `test-cases/b-discount-coupons.csv`
- Target count: 35 (skill default)
- Current phase: Phase 2 — second human-review deduplication and re-aggregation complete
- Overall status: COMPLETE
- Review gate: Passed by the user's explicit instruction on 2026-08-22 to continue to Phase 2, approving the exact current CONTRACT v2, DOMAIN v2, and SECURITY v2 reports. STATE remains `NOT_APPLICABLE` and requires no approval.

| Category | Report | Review status | Worker result |
| --- | --- | --- | --- |
| CONTRACT | `review/pool-b/reports/contract-report.md` | PENDING | AWAITING_HUMAN_REVIEW; `contract-report-v2 — 2026-08-22`; CR-001–CR-012 preserved |
| DOMAIN | `review/pool-b/reports/domain-report.md` | PENDING | AWAITING_HUMAN_REVIEW; `POOL-B-DOMAIN-v2`; DP-001–DP-037 and DB-001–DB-007 preserved |
| STATE | `review/pool-b/reports/state-report.md` | Not required | `State Applicability: NOT_APPLICABLE`; `Review Required: NO`; `STATE-PHASE1-v2` |
| SECURITY | `review/pool-b/reports/security-report.md` | PENDING | AWAITING_HUMAN_REVIEW; `security-report-v2`; SS-001–SS-007 preserved and SS-008 added |

Review disposition: FR-09 C1, C2, and C5 are state-dependent eligibility preconditions, but `POST /api/apply-coupon` has no documented endpoint-driven state transition. Active/inactive, expiry, and usage-limit coverage is owned by DOMAIN. STATE is therefore `NOT_APPLICABLE` and needs no approval.

SECURITY now includes SEC-05 coverage for client-controlled `user_id` through controlled inert SQL/metacharacter scenario SS-008, without an HTTP status, error schema, or message oracle.

## Phase-2 result

- Final output: `test-cases/b-discount-coupons.csv`
- Final count: 67 distinct candidates (target count 35 met)
- Category counts: CONTRACT 15; DOMAIN 44; STATE 0; SECURITY 8
- Review provenance: explicit user authorization to continue to Phase 2 using CONTRACT `contract-report-v2 — 2026-08-22`, DOMAIN `POOL-B-DOMAIN-v2`, SECURITY `security-report-v2`, and STATE `STATE-PHASE1-v2` with `NOT_APPLICABLE` status.
- Coverage: CR-001–CR-012; DP-001–DP-037; DB-001–DB-007; SS-001–SS-008; applicable SEC-02 and SEC-05.
- State handling: `state-tests.json` is exactly `[]`; no placeholder STATE cases were generated.
- Human-review corrections: minimum-threshold BVA labels follow `total_amount >= min_order_amount` (just-below outside; boundary and just-above inside); the SAVE10/300001 oracle uses mathematical results `30000.1` and `270000.9` without asserting floating-point representation or rounding; BIGBUY, EXPIRED, and nonexistent-code preconditions explicitly isolate their intended conditions.
- Same-category deduplication: fourteen DOMAIN duplicates removed in total. The first pass removed six repeated baseline records into retained DOMAIN-001. The first review pass consolidated DOMAIN-053 into DOMAIN-001, DOMAIN-042 into DOMAIN-009, DOMAIN-039 into DOMAIN-020, and DOMAIN-045 into DOMAIN-022. The second review pass consolidated DOMAIN-038 into DOMAIN-021 (`DP-021` + `DB-001` just-below), DOMAIN-048 into DOMAIN-013 (`DP-013` + `DB-004` equal-to-expiry), DOMAIN-054 into DOMAIN-030 (`DP-030` + `DB-006` at-limit), and DOMAIN-055 into DOMAIN-031 (`DP-031` + `DB-006` above-limit). All associated DP/DB bases, boundary objectives, and provisional IDs remain attached to retained cases.
- Remaining semantic duplicate groups: 0.
- Validation: exact nine-column schema, 67 sequential unique IDs (`API-001`–`API-067`), endpoint consistency, allowed categories, non-empty required content, explicit assumptions, complete reviewed trace-ID coverage, corrected BVA labels, fixture-specific preconditions, absence of the floating-point artifact, and a second partition-versus-boundary semantic-overlap audit all passed.
- Preserved gaps/assumptions: undocumented HTTP statuses, failure schemas/messages, requiredness/type/coercion details, JWT/body identity binding, rounding/precision, and endpoint-driven mutation are not invented. SEC-05 black-box cases do not claim to prove implementation-level parameterization.
- Execution: candidates were designed only; no API tests were executed and no service state was mutated.
