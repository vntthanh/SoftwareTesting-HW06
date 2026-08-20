---
name: domain-test-generator
description: Analyze equivalence partitions and boundary values for every input of one API endpoint, pause for human review, then generate traceable DOMAIN test candidates. Use independently or as the domain specialist under api-test-generator.
---

# Domain Test Generator

Focus only on Domain Testing for every input of one selected endpoint. Keep analysis and candidate generation separated by human review.

## Inputs and ownership

Require `api_contract` and normalized `test_model`, inline or through a shared-context path, plus `domain_report_path`. The report path may be a standalone domain report or, during generation, a reviewed combined Phase-1 report; in the combined form read only the `DOMAIN` section. In generation also accept `candidate_output_path`. For supplemental generation, also accept existing domain candidates and a category-specific uncovered partition/boundary or additional-count request. If invoked independently with a specification and endpoint, extract the same contract and model once; stop if the endpoint is absent or ambiguous.

In an orchestrated run, read but never edit shared context. During Phase 1 write only the unique report path supplied by the parent, including when it is a temporary merge input. During generation, treat a combined reviewed report as read-only and write only the domain candidate fragment. Never write the combined report or final suite.

## Select one phase

- **Analysis:** use unless an approved report exists and the user asks for tests.
- **Generation:** require `Review Status: APPROVED`, or explicit user approval of that exact report version.

Do not perform both phases in one invocation. The author cannot self-approve. If an approved report exists during analysis, leave it unchanged and return `READY_FOR_GENERATION`.

## Phase 1 — analyze and report

1. Inventory every path, query, header, cookie, and body input, including nested fields. Record location, requiredness, type, format, allowed values, nullability, default, and explicit constraints.
2. Derive supported valid and invalid equivalence partitions. Consider omission, null, empty, malformed, in-set/out-of-set, and type classes only when meaningful.
3. Derive boundaries from explicit numeric, length, count, date/time, or other ordered limits, using boundary, just-inside, and just-outside values where representable. Never infer limits from examples or common practice.
4. Define a valid baseline so cases can vary one partition or boundary at a time unless a reviewed interaction requires multiple changes.
5. Give partitions and boundaries IDs such as `DP-001` and `DB-001`, exact bases, and assumptions.
6. Write the report with endpoint/source, baseline, complete parameter inventory, partition table, boundary table, documented cross-parameter constraints, gaps, ambiguities, and a review block containing `Review Status: PENDING`, `Reviewer`, `Review Notes`, and `Reviewed Version`.
7. Return the report path and `AWAITING_HUMAN_REVIEW`, then stop. Do not generate tests.

## Phase 2 — generate from the reviewed model

1. Read the contract and approved standalone report or approved `DOMAIN` section of a combined report.
2. Generate cases covering every reviewed partition and boundary for every parameter. Prefer one-factor-at-a-time against the reviewed baseline; combine only for reviewed cross-parameter rules.
3. Use provisional IDs such as `DOMAIN-P001`; an orchestrator may replace them.
4. Cite reviewed partition/boundary IDs and exact specification bases. State assumptions for unspecified invalid responses.
5. For a supplemental request, inspect the existing domain candidates and generate only supported, semantically distinct cases for the requested reviewed partitions, boundaries, or additional count. Do not reproduce existing candidates or go beyond the approved domain model.
6. Verify parameter, partition, and boundary coverage; report unrepresentable reviewed items.
7. Write a JSON array to `candidate_output_path` when supplied; otherwise return candidates directly.

## Candidate schema

Every candidate has exactly `Test ID`, `Endpoint`, `Category` (`DOMAIN`), `Test Objective`, `Preconditions`, `Request Input`, `Expected Result`, `Specification Basis`, and `Assumptions / Notes`.

Do not treat examples as constraints or fabricate behavior. Do not execute tests.
