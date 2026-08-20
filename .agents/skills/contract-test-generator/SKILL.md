---
name: contract-test-generator
description: Analyze one API endpoint's request and response contract, pause for human review, then generate traceable CONTRACT test candidates from the approved report. Use independently or as the contract specialist under api-test-generator.
---

# Contract Test Generator

Focus only on contract tests for one selected endpoint. Support two separate invocations: analysis before human review and test generation after approval.

## Inputs and ownership

Require `api_contract` and normalized `test_model`, inline or through a shared-context path, plus `contract_report_path`. The report path may be a standalone contract report or, during generation, a reviewed combined Phase-1 report; in the combined form read only the `CONTRACT` section. In generation also accept `candidate_output_path`. For supplemental generation, also accept existing contract candidates and a category-specific uncovered-rule or additional-count request. If invoked independently with a specification and endpoint, extract the same contract and model once; stop if the endpoint is absent or ambiguous.

In an orchestrated run, read but never edit shared context. During Phase 1 write only the unique report path supplied by the parent, including when it is a temporary merge input. During generation, treat a combined reviewed report as read-only and write only the contract candidate fragment. Never write the combined report or final suite.

## Select one phase

- **Analysis:** use unless an approved report exists and the user asks for tests.
- **Generation:** require `Review Status: APPROVED`, or explicit user approval of that exact report version.

Do not perform both phases in one invocation. The author cannot self-approve. If an approved report exists during analysis, leave it unchanged and return `READY_FOR_GENERATION`.

## Phase 1 — analyze and report

1. Analyze request method, path, parameters, headers, cookies, media types, body schemas, nested fields, requiredness, types, formats, enumerations, nullability, defaults, and explicit structural constraints.
2. Analyze every documented response status, media type, required header, schema shape, required property, type, format, enumeration, nullability, and error structure.
3. Identify positive and negative contract rules without guessing unspecified validation. Give each a stable ID such as `CR-001` and an exact specification basis.
4. Write the report with endpoint/source identity, request inventory, response inventory by status/media type, a rule table (ID, target, valid/invalid condition, expected contract behavior, basis, assumptions), gaps, ambiguities, and a review block containing `Review Status: PENDING`, `Reviewer`, `Review Notes`, and `Reviewed Version`.
5. Return the report path and `AWAITING_HUMAN_REVIEW`, then stop. Do not generate tests.

## Phase 2 — generate from the reviewed model

1. Read the contract and approved standalone report or approved `CONTRACT` section of a combined report. Treat reviewed model changes as test-design authority while the specification remains authority for API behavior.
2. Generate distinct positive and negative cases covering every approved rule and relevant request/response contract.
3. Use provisional IDs such as `CONTRACT-P001`; an orchestrator may replace them.
4. Map every case to approved rule IDs and exact specification bases. Put unspecified behavior in `Assumptions / Notes`.
5. For a supplemental request, inspect the existing contract candidates and generate only supported, semantically distinct cases for the requested reviewed rules or additional count. Do not reproduce existing candidates or go beyond the approved contract model.
6. Verify every approved rule is covered or explicitly reported unresolved.
7. Write a JSON array to `candidate_output_path` when supplied; otherwise return candidates directly.

## Candidate schema

Every candidate has exactly `Test ID`, `Endpoint`, `Category` (`CONTRACT`), `Test Objective`, `Preconditions`, `Request Input`, `Expected Result`, `Specification Basis`, and `Assumptions / Notes`.

Keep mutations precise. Do not invent status codes, fields, coercion, rejection precedence, or error messages. Do not execute tests.
