---
name: security-test-generator
description: Analyze specification-defined SEC-01–SEC-07 requirements for one API endpoint, pause for human review, then generate traceable SECURITY test candidates. Use independently or as the security specialist under api-test-generator.
---

# Security Test Generator

Focus only on security tests supported by requirements applicable to one selected endpoint. Design candidates; do not attack or execute against a live service.

## Inputs and ownership

Require `api_contract`, normalized `test_model`, and extracted `security_requirements` (`SEC-01` through `SEC-07`), inline or through a shared-context path, plus `security_report_path`. In generation also accept `candidate_output_path`. If invoked independently with a specification and endpoint, extract them once. Record missing SEC IDs as absent; never substitute a generic checklist.

In an orchestrated run, read but never edit shared context. Write only the security report during analysis and the security candidate fragment during generation. Never write the combined final suite.

## Select one phase

- **Analysis:** use unless an approved report exists and the user asks for tests.
- **Generation:** require `Review Status: APPROVED`, or explicit user approval of that exact report version.

Do not perform both phases in one invocation. The author cannot self-approve. If an approved report exists during analysis, leave it unchanged and return `READY_FOR_GENERATION`.

## Phase 1 — analyze and report

1. Identify authentication, authorization-relevant identifiers or roles, sensitive inputs/outputs, untrusted input surfaces, transport/header requirements, and documented abuse or rate constraints.
2. Evaluate each available requirement from `SEC-01` through `SEC-07`. Preserve ID, exact text or faithful meaning, applicability, evidence, and assumptions. Do not invent missing requirements.
3. Derive positive and negative scenarios only from applicable requirements and endpoint characteristics. Keep example payloads inert; do not send them.
4. Give scenarios IDs such as `SS-001` and map them to SEC IDs and exact bases.
5. Write the report with endpoint/source, characteristics, an `SEC-01`–`SEC-07` applicability matrix including absent entries, a scenario table (ID, precondition, stimulus, expected security behavior, requirement IDs, basis, assumptions), gaps, and a review block containing `Review Status: PENDING`, `Reviewer`, `Review Notes`, and `Reviewed Version`.
6. Return the report path and `AWAITING_HUMAN_REVIEW`, then stop. Do not generate tests.

## Phase 2 — generate from the reviewed model

1. Read the contract and approved report.
2. Generate distinct cases covering every reviewed applicable SEC requirement and scenario, including valid-control cases when reviewed.
3. Use provisional IDs such as `SECURITY-P001`; an orchestrator may replace them.
4. Cite scenario IDs, SEC IDs, and exact bases. Record assumptions for unspecified status, message, redaction, timing, or side effects.
5. Verify requirement/scenario coverage and report uncovered applicable items.
6. Write a JSON array to `candidate_output_path` when supplied; otherwise return candidates directly.

## Candidate schema

Every candidate has exactly `Test ID`, `Endpoint`, `Category` (`SECURITY`), `Test Objective`, `Preconditions`, `Request Input`, `Expected Result`, `Specification Basis`, and `Assumptions / Notes`.

Do not claim compliance with unsupplied standards. Do not execute tests, probe services, or use live credentials without separate authorization.
