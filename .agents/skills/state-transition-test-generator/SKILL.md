---
name: state-transition-test-generator
description: Determine whether one API endpoint has specified stateful behavior, model its transitions for human review, then generate traceable STATE test candidates. Use independently or as the state specialist under api-test-generator.
---

# State Transition Test Generator

Focus only on State Transition Testing for one selected endpoint and first determine whether the specification provides a meaningful state model.

## Inputs and ownership

Require `api_contract` and normalized `test_model`, inline or through a shared-context path, plus `state_report_path`. The report path may be a standalone state report or, during generation, a reviewed combined Phase-1 report; in the combined form read only the `STATE` section. In generation also accept `candidate_output_path` and the parent-preserved `state_applicability` record. For supplemental generation, also accept existing state candidates and a category-specific uncovered-transition or additional-count request. If invoked independently with a specification and endpoint, extract the same contract and model once; stop if the endpoint is absent or ambiguous.

In an orchestrated run, read but never edit shared context. During Phase 1 write only the unique report path supplied by the parent, including when it is a temporary merge input. During generation, treat a combined reviewed report as read-only and write only the state candidate fragment. Never write the combined report or final suite.

## Select one phase

- **Applicability/analysis:** use unless an approved applicable-state report exists and the user asks for tests.
- **Generation:** require `Review Status: APPROVED`, or explicit user approval of that exact report version, except that a preserved `state_applicability` record with `status: NOT_APPLICABLE` follows the empty-output path below and requires no approval.

Do not perform analysis and generation in one invocation. The author cannot self-approve. If an approved report exists during analysis, leave it unchanged and return `READY_FOR_GENERATION`.

## Phase 1 — determine applicability, analyze, and report

1. Identify documented lifecycle states, prior-state preconditions, state-changing effects, guards, idempotency rules, sequence rules, or results varying by resource, account, or session state.
2. If no supported state behavior applies, do not invent states or create a review report merely to force coverage. Return `{"status":"NOT_APPLICABLE","tests":[],"basis":"<exact evidence or absence finding>"}`. When the parent supplied a Phase-1 output path, also write a minimal mergeable applicability record containing `Category: STATE`, `State Applicability: NOT_APPLICABLE`, the selected endpoint, source identity, exact basis, and `Review Required: NO`; this is a status record, not a report awaiting approval.
3. If applicable, identify states with IDs such as `ST-01`.
4. Identify valid and supported invalid transitions: trigger/request, source, guard, destination, observable result, and exact basis. Give transition IDs such as `TR-001`.
5. Build a transition table. Treat setup through other operations as a precondition unless the user selected a multi-endpoint flow.
6. Write the report with endpoint/source, applicability evidence, state definitions, transition/guard table, supported invalid-transition model, gaps, ambiguities, and a review block containing `Review Status: PENDING`, `Reviewer`, `Review Notes`, and `Reviewed Version`.
7. Return the report path and `AWAITING_HUMAN_REVIEW`, then stop. Do not generate tests.

## Phase 2 — generate from the reviewed model

1. If the parent passes a `state_applicability` record with `status: NOT_APPLICABLE` and its exact Phase-1 basis, verify it matches the shared context and the `State Applicability: NOT_APPLICABLE` marker and basis in the standalone or combined `STATE` status section. Write an empty JSON array `[]` to `candidate_output_path` when supplied, return the same status and basis, and stop. Do not require an approved state report and do not generate placeholder cases.
2. Otherwise read the contract and approved standalone report or approved `STATE` section of a combined report.
3. Generate cases for every reviewed valid and invalid transition. Make initial state and setup explicit in `Preconditions`.
4. Use provisional IDs such as `STATE-P001`; an orchestrator may replace them.
5. Cite transition IDs and exact bases. Do not infer destination, side effect, status, or idempotency guarantee.
6. For a supplemental request, inspect the existing state candidates and generate only supported, semantically distinct cases for the requested reviewed transitions or additional count. Do not reproduce existing candidates or go beyond the approved state model.
7. Verify transition coverage and report transitions not exercisable through the endpoint.
8. Write a JSON array to `candidate_output_path` when supplied; otherwise return candidates directly.

## Candidate schema

Every candidate has exactly `Test ID`, `Endpoint`, `Category` (`STATE`), `Test Objective`, `Preconditions`, `Request Input`, `Expected Result`, `Specification Basis`, and `Assumptions / Notes`.

For a non-applicable orchestrated generation pass, preserve the Phase-1 status into Phase 2 and materialize the empty candidate fragment as required above. Do not create placeholder cases or execute tests.
