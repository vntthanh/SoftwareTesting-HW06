---
name: api-test-generator
description: Generate a reviewed, traceable candidate API test suite for one endpoint by coordinating contract, domain, state-transition, and security specialists. Use for full multi-dimension API test design; use a specialized generator directly when only one dimension is needed.
---

# API Test Generator

Generate candidate tests for one selected API endpoint from an API specification. Prepare the endpoint context once, delegate the four test dimensions with Codex's native subagent tools, preserve the human-review gate, and make the parent agent the sole owner of aggregation and final output.

## Inputs

Require an API specification document and a selected endpoint, including method and path when the path is overloaded. Accept `target_count` (default `35`), `work_directory`, and `final_output_path` (default `candidate-api-tests.csv` in the work directory).

Do not guess when multiple operations could match. If the selected contract is not found, stop with the exact lookup failure.

## Output contract

Every final record has exactly:

1. `Test ID`
2. `Endpoint`
3. `Category` (`DOMAIN`, `STATE`, `SECURITY`, or `CONTRACT`)
4. `Test Objective`
5. `Preconditions`
6. `Request Input`
7. `Expected Result`
8. `Specification Basis`
9. `Assumptions / Notes`

Use CSV for `.csv`, a JSON array for `.json`, or a Markdown table for `.md`. Keep structured cell values unambiguous. The default CSV can later be reviewed and converted by `$postman-test-generator`.

## Parent-owned work layout

Use distinct paths so parallel agents never write the same file:

```text
<work_directory>/
|-- shared-api-context.md
|-- orchestration-status.md
|-- reports/
|   |-- contract-report.md
|   |-- domain-report.md
|   |-- state-report.md
|   `-- security-report.md
|-- candidates/
|   |-- contract-tests.json
|   |-- domain-tests.json
|   |-- state-tests.json
|   `-- security-tests.json
`-- candidate-api-tests.csv
```

The parent owns the shared context, status file, and final output. Each specialist owns only its named report and candidate fragment. Never give a specialist the final output path.

## Prepare shared context once

Before spawning any subagent, extract the selected operation and write `shared-api-context.md`. Reuse that exact file for all specialists and both phases; do not ask four agents to re-extract the specification.

Include:

- Source identity and stable section, operation, or line references.
- Selected method, path, summary, and operation ID.
- All path, query, header, cookie, and body inputs, including nested fields, with requiredness, type, format, allowed values, nullability, defaults, and explicit constraints.
- Request media types and schemas.
- Every documented response status, media type, header, and schema.
- Authentication and authorization declarations.
- Requirements `SEC-01` through `SEC-07` found in the specification, with exact identifiers and applicability evidence. Mark missing requirements as absent; do not invent them.
- Documented state behavior, lifecycle terms, preconditions, effects, and related operations.
- A normalized model: parameter inventory, valid baseline request, response inventory, contract rules, state cues, and security characteristics.
- Ambiguities and assumptions separated from specification facts.

Every specification fact needs an exact basis. Never turn an inference into a stated requirement.

## Choose the current phase

The workflow is split by human review:

- Use **Phase 1 — analysis** while any applicable report is missing or lacks explicit approval.
- Use **Phase 2 — generation** only when contract, domain, security, and applicable state reports contain `Review Status: APPROVED`, or the user explicitly approves those exact report versions.
- Treat `STATE: NOT_APPLICABLE` as an empty state result needing no report approval. Preserve its evidence in the parent-owned status file.
- In a mixed state, run Phase 1 for all four. A specialist with an approved report returns it unchanged; the others produce or revise reports.

Never cross the review gate merely because the generated reports look correct. A report author is not the human reviewer.

## Native four-agent orchestration

Use Codex's native `spawn_agent` and `wait_agent` capabilities. Do not build a script, queue, polling framework, or custom coordinator.

For the selected phase:

1. Spawn exactly four subagents without waiting between spawns so they run concurrently. Tell one each to use `$contract-test-generator`, `$domain-test-generator`, `$state-transition-test-generator`, and `$security-test-generator`.
2. Give every subagent the phase, the same absolute shared-context path, its own absolute report path, and, in Phase 2, its own candidate JSON path. State that it must not edit shared context, status, another specialist's files, or final output.
3. Wait for all four agents to finish using native waiting with long bounded waits. Do not serialize work by waiting after each spawn.
4. If any agent fails, blocks, or violates its boundary, do not aggregate. Report the dimension and preserve successful results for a scoped retry.

After Phase 1, inspect all results, update the status file, list reports requiring human review, and stop. Do not generate tests or final output.

After Phase 2, require a candidate JSON array from every applicable agent and either an array or justified empty state result. Then aggregate.

## Aggregate and validate

Only the parent:

1. Combines the four candidate arrays.
2. Rejects records missing a required field, targeting the wrong endpoint, or using a category outside the specialist's assignment.
3. Removes semantic duplicates when preconditions, stimulus, and expected behavior are materially the same. Preserve distinct specification bases and specialist rule IDs on the retained case.
4. Attaches or repairs `Specification Basis` only from the shared contract or approved report. Put unspecified behavior in `Assumptions / Notes`.
5. Checks required coverage:
   - Contract: request and every documented response contract, required fields, types, allowed values, and structural rules.
   - Domain: every input parameter, reviewed partition, and applicable reviewed boundary.
   - State: reviewed valid and invalid transitions when applicable.
   - Security: every reviewed applicable requirement among `SEC-01`–`SEC-07`.
6. Treats `target_count` as a suite-size target, not permission to invent behavior. Add or retain distinct cases from reviewed models. If count and coverage conflict, preserve coverage and report the shortfall or excess.
7. Assigns final stable sequential IDs such as `API-001` only after de-duplication. Preserve provisional specialist IDs in notes when useful.
8. Validates ID uniqueness, allowed categories, endpoint consistency, non-empty objectives and expected results, exact specification bases, explicit assumptions, and final count.
9. Writes final output only after validation succeeds and summarizes per-category counts, duplicates, gaps, assumptions, and review provenance.

Do not execute generated tests or mutate an API unless separately requested and authorized.
