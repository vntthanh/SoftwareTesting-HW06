# AI Audit Report

- **Student ID:** 23127261
- **Student Name:** Vương Ngũ Tín Thành
- **Class:** 23KTPM2
- **Assignment ID:** HW06-AI

## Summary of AI Accuracy

**TODO: Fill in AI Accuracy when complete the exercise.**

| Metric | Count | Percentage |
| --- | ---: | ---: |
| VALID | | % |
| INVALID | | % |
| INCOMPLETE | | % |

The verdict of each artifact is identified as:

- `VALID` if it is corrected, accepted as-is.
- `INVALID` if it is wrong, rejected.
- `INCOMPLETE` if it is acceptable after edits.

## AI Interaction Log

### Artifact 1

- **User:** Vương Ngũ Tín Thành
- **Date and Time:** 2026-08-19 23:39:52 GMT+7
- **Model Used:** GPT-5.6 Sol
- **Skill Used:**
  - `skill-creator`
  - `ai-audit`
- **Prompt:**

````markdown
Use [$skill-creator](C:\\Users\\xing0\\.codex\\skills\\.system\\skill-creator\\SKILL.md) and [$ai-audit](D:\\GitHub\\SoftwareTesting-HW06\\.agents\\skills\\ai-audit\\SKILL.md)

Create postman-test-generator agent skills. I've already designed the skill in [postman-test-generator.md](D:/GitHub/SoftwareTesting-HW06/skills-design/postman-test-generator/postman-test-generator.md).
````

- **AI Output:**

````markdown
The design is narrow enough that the skill should **convert reviewed CSV cases, not invent tests**. I’m also keeping Newman compatibility as a hard output constraint and treating the conversion report as a traceability/validation artifact because your input contract includes `conversion_report_path`.

The skill draft is now aligned to your design: CSV is authoritative for test intent, the API spec only resolves implementation details, and the skill explicitly avoids adding a review/design phase. I’m validating the package now, then I’ll build the audit file from the completed interactions available to ai-audit.

Done

`postman-test-generator` passed `skill-creator`'s `quick_validate.py`. Its main boundaries are: reviewed CSV test cases are authoritative, it does not design new cases, it generates Postman Collection v2.1 + conversion report, preserves traceability, requires `X-Student-Id`, parameterizes runtime values, and targets Newman-compatible scripts.
````

- **File Modifications:**
  - `File: AI_Audit.md`
    - `Action:` created.
    - `Deleted:` None.
    - `Replaced With:` None.
    - `Appended:` Initialized the AI audit report and added audit artifact(s) for the completed AI interactions.
  - `File: .agents/skills/postman-test-generator/SKILL.md`
    - `Action:` created.
    - `Deleted:` None.
    - `Replaced With:` None.
    - `Appended:` Added the `postman-test-generator` skill definition, including its purpose, input requirements, workflow, Postman collection generation rules, validation requirements, and output expectations.
  - `File: .agents/skills/postman-test-generator/agents/openai.yaml`
    - `Action:` created.
    - `Deleted:` None.
    - `Replaced With:` None.
    - `Appended:` Added the OpenAI agent configuration for the `postman-test-generator` skill.
- **Verdict:** INCOMPLETE
- **Reasoning:**
  - Preconditions notes may be lost. The skill does not explicitly preserve them.
  - Collection validation is too weak. It only checks valid JSON and v2.1 declaration, not full Postman v2.1 schema validity.
- **Student Fixes:** Continue state these defects out and guide the agent to fix them.

### Artifact 2

- **User:** Vương Ngũ Tín Thành
- **Date and Time:** 2026-08-20 00:22:32 GMT+7
- **Model Used:** GPT-5.6 Sol
- **Skill Used:**
  - `skill-creator`
  - `ai-audit`
- **Prompt:**

````markdown
There are some defects in the implemented `postman-test-generator` skill.

- Preconditions notes may be lost. The skill does not explicitly preserve them. 
- Collection validation is too weak. It only checks valid JSON and v2.1 declaration, not full Postman v2.1 schema validity. 

Use [$skill-creator](C:\\Users\\xing0\\.codex\\skills\\.system\\skill-creator\\SKILL.md) to revise the skill.
````

- **AI Output:**

````markdown
I’ll revise the existing skill in place, specifically addressing both defects: preserve precondition notes explicitly through conversion/traceability, and validate the generated collection against the full Postman Collection v2.1 schema rather than only checking JSON/version metadata. Then I’ll rerun `$skill-creator` validation and package the revised skill.

The prior generated working directory is no longer present in the sandbox, but the original design package is still available. I’m reconstructing the skill from that authoritative design plus the same `$skill-creator` rules, carrying forward the prior decisions (reviewed CSV as authority, Newman compatibility, traceability, and no test-case invention) while patching only the two identified defects.

One important interaction between the two fixes: preconditions should **not** be preserved by adding arbitrary custom JSON fields, because that can itself break v2.1 schema validity. I’m preserving them in schema-supported request descriptions and in the conversion report, with exact source text retained for traceability.

Both corrections are now implemented in the skill instructions. I also added a deterministic schema-validation helper so future executions can’t accidentally “pass” a collection merely because it is JSON with a v2.1 declaration.

Revised with `$skill-creator`.

The two defects are fixed:

- **Preconditions are explicitly preserved**
  - Kept in a schema-supported request description under `Preconditions` / `Setup`.
  - Also copied to the conversion report for traceability.
  - If a precondition cannot be automated safely, it stays as a note and is flagged instead of being dropped.
  - Arbitrary custom Postman fields are prohibited because they can violate the collection schema.

- **Full Postman v2.1 schema validation**
  - Added `references/validation.md`.
  - Added `scripts/validate_postman_collection.py`.
  - Validation now requires the complete Postman Collection v2.1 JSON Schema; valid JSON plus `info.schema` is explicitly insufficient.
  - Schema errors include their JSON paths and cause a non-zero exit.
  - The collection is only finalized after full schema validation passes.
  - The skill uses Postman’s documented v2.1 schema location. ([github.com](https://github.com/postmanlabs/postman-api-sdk-ts/blob/main/documentation/models/ModifyCollectionSchemaInfo.md?utm_source=chatgpt.com))

I also tested the validator with both a passing collection and a deliberately schema-invalid collection; the invalid one was correctly rejected. `$skill-creator`'s `quick_validate.py` also reports **`Skill is valid!`**.
````

- **File Modifications:**
  - File: `.agents/skills/postman-test-generator/SKILL.md`.
    - `Action:` edited.
    - `Deleted:` Prior exact text is not available in the completed interaction output.
    - `Replaced With:` Revised skill instructions that explicitly preserve reviewed preconditions/setup notes in schema-supported request descriptions and the conversion report, prohibit arbitrary custom Postman properties for traceability, require full Postman Collection v2.1 JSON Schema validation before finalization, and retain Newman compatibility requirements.
    - `Appended:` None.
  - `File:` `.agents/skills/postman-test-generator/references/validation.md`.
    - `Action:` created.
    - `Deleted:` None.
    - `Replaced With:` None.
    - `Appended:` Full-schema validation procedure using the official Postman Collection Format v2.1.0 schema, validation gate requirements, deterministic helper invocation, and failure-repair guidance.
  - `File:` `.agents/skills/postman-test-generator/scripts/validate_postman_collection.py`.
    - `Action:` created.
    - `Deleted:` None.
    - `Replaced With:` None.
    - `Appended:` Deterministic validator that parses the collection and schema, checks the v2.1 schema declaration, validates the complete collection, reports JSON-path schema errors, and exits non-zero on failure.
- **Verdict:** VALID
- **Reasoning:** The agent successfully fixed all defects.
- **Student Fixes:** None

### Artifact 3

- **User:** Vương Ngũ Tín Thành
- **Date and Time:** 2026-08-20 11:16:56 GMT+7
- **Model Used:** GPT-5.6 Sol
- **Skill Used:**
  - `skill-creator`
  - `ai-audit`
- **Prompt:**

````markdown
Use [$skill-creator](C:\Users\xing0\\.codex\skills\\.system\skill-creator\SKILL.md) to implement the Agent Skills defined by [api-test-generator](skills-design/api-test-generator/)

Treat the design as the source of truth.

Create **5 composable skills**:

- `api-test-generator` — orchestrator
- `contract-test-generator`
- `domain-test-generator`
- `state-transition-test-generator`
- `security-test-generator`

The four specialized generators must be independent skills, not reference files.

For `api-test-generator`, use Codex multi-agent orchestration to:

1. Prepare the shared API/endpoint context once.
2. Spawn **4 subagents concurrently**, one for each specialized skill.
3. Wait for all four to finish.
4. Aggregate and validate their results into the final output.

Please note that for specialized generators currently are split into 2 phases, due to `HUMAN REVIEW` step.

Specialized skills must also work independently. Use `references/` only for supporting material.

Avoid concurrent writes to the final output; the orchestrator owns aggregation and final output.

Do not build a custom multi-agent framework if Codex's native subagent orchestration is sufficient.

Follow [$skill-creator](C:\Users\xing0\\.codex\skills\\.system\skill-creator\SKILL.md) conventions and validate all five skills after implementation.

At the end, log this artifact using [$ai-audit](D:\GitHub\SoftwareTesting-HW06\\.agents\skills\ai-audit\SKILL.md) and report the created skill tree and validation results.
````

- **AI Output:**

````markdown
Implemented and validated all five skills, with Artifact 3 logged in [AI_Audit.md](D:/GitHub/SoftwareTesting-HW06/AI_Audit.md).

Created skill tree:

```text
.agents/skills/
├── api-test-generator/
│   ├── SKILL.md
│   └── agents/openai.yaml
├── contract-test-generator/
│   ├── SKILL.md
│   └── agents/openai.yaml
├── domain-test-generator/
│   ├── SKILL.md
│   └── agents/openai.yaml
├── state-transition-test-generator/
│   ├── SKILL.md
│   └── agents/openai.yaml
└── security-test-generator/
    ├── SKILL.md
    └── agents/openai.yaml
```

Validation results:

- `quick_validate.py`: passed for all five skills with `Skill is valid!`.
- Semantic checks passed for shared-context-once preparation, exactly four concurrent specialist agents, waiting for all four, parent-only aggregation/final writes, and two-phase human-review gates.
- All five `agents/openai.yaml` files parse successfully.
- Each specialist is independently invocable and owns only its report/candidate fragment.
- No `references/` were created because no supporting material was needed.

Artifacts 3-3 successfully appended to `D:\GitHub\SoftwareTesting-HW06\AI_Audit.md`.
````

- **File Modifications:**
  - `File: .agents/skills/api-test-generator/SKILL.md`.
    - `Action:` created, then replaced scaffold content.
    - `Deleted:` Initial skill-creator TODO scaffold.
    - `Replaced With:` Orchestrator instructions for one-time shared context preparation, concurrent native four-agent execution, two review-separated phases, parent-owned aggregation, de-duplication, traceability, coverage validation, target-count handling, and final output ownership.
    - `Appended:` None.
  - `File: .agents/skills/api-test-generator/agents/openai.yaml`.
    - `Action:` created.
    - `Deleted:` None.
    - `Replaced With:` None.
    - `Appended:` UI metadata and default invocation prompt for `api-test-generator`.
  - `File: .agents/skills/contract-test-generator/SKILL.md`.
    - `Action:` created, then replaced scaffold content.
    - `Deleted:` Initial skill-creator TODO scaffold.
    - `Replaced With:` Independent two-phase contract-analysis, human-review, candidate-generation, traceability, and file-ownership instructions.
    - `Appended:` None.
  - `File: .agents/skills/contract-test-generator/agents/openai.yaml`.
    - `Action:` created.
    - `Deleted:` None.
    - `Replaced With:` None.
    - `Appended:` UI metadata and default invocation prompt for `contract-test-generator`.
  - `File: .agents/skills/domain-test-generator/SKILL.md`.
    - `Action:` created, then replaced scaffold content.
    - `Deleted:` Initial skill-creator TODO scaffold.
    - `Replaced With:` Independent equivalence-partition and boundary-analysis workflow with human review, candidate generation, traceability, and file boundaries.
    - `Appended:` None.
  - `File: .agents/skills/domain-test-generator/agents/openai.yaml`.
    - `Action:` created.
    - `Deleted:` None.
    - `Replaced With:` None.
    - `Appended:` UI metadata and default invocation prompt for `domain-test-generator`.
  - `File: .agents/skills/state-transition-test-generator/SKILL.md`.
    - `Action:` created, then replaced scaffold content.
    - `Deleted:` Initial skill-creator TODO scaffold.
    - `Replaced With:` Independent applicability check, state/transition modeling, human review, candidate generation, justified empty result, traceability, and file boundaries.
    - `Appended:` None.
  - `File: .agents/skills/state-transition-test-generator/agents/openai.yaml`.
    - `Action:` created.
    - `Deleted:` None.
    - `Replaced With:` None.
    - `Appended:` UI metadata and default invocation prompt for `state-transition-test-generator`.
  - `File: .agents/skills/security-test-generator/SKILL.md`.
    - `Action:` created, then replaced scaffold content.
    - `Deleted:` Initial skill-creator TODO scaffold.
    - `Replaced With:` Independent SEC-01–SEC-07 applicability/scenario analysis, human review, candidate generation, safety, traceability, and file boundaries.
    - `Appended:` None.
  - `File: .agents/skills/security-test-generator/agents/openai.yaml`.
    - `Action:` created.
    - `Deleted:` None.
    - `Replaced With:` None.
    - `Appended:` UI metadata and default invocation prompt for `security-test-generator`.
  - `File: AI_Audit.md`.
    - `Action:` appended.
    - `Deleted:` None.
    - `Replaced With:` None.
    - `Appended:` Artifact 3 containing the verbatim prompt, final AI output, file modifications, and review TODOs.
  - `File: .skill-implementation.patch` and `.skill-stage/*/SKILL.md`.
    - `Action:` temporary files created and deleted.
    - `Deleted:` Staged patch and five staged skill files after protected-directory installation.
    - `Replaced With:` None.
    - `Appended:` None.
  - `File: .validation-deps/**`.
    - `Action:` temporary validator dependencies created and deleted.
    - `Deleted:` Isolated PyYAML validation dependency directory after validation.
    - `Replaced With:` None.
    - `Appended:` None.
- **Verdict:** INCOMPLETE
- **Reasoning:**
  - Cross-category deduplication may remove required test coverage.
  - STATE: NOT_APPLICABLE is not passed correctly into Phase 2.
  - Completed subagents are not explicitly closed.
  - The parent skill may generate extra tests itself instead of delegating them.
  - If the user provides one Phase-1 report file, parallel agents may write to the same file.
    - For one report file, workers should write separate temporary reports first. The parent should merge temporary reports into the final Phase-1 report.
    - Temporary files should be deleted only after the merged report is successfully validated.
    - If merging fails, temporary files should be kept for recovery.
- **Student Fixes:** Continue guide the agent to resolve defects.

### Artifact 4

- **User:** Vương Ngũ Tín Thành
- **Date and Time:** 2026-08-20 11:52:36 GMT+7
- **Model Used:** GPT-5.6 Sol
- **Skill Used:**
  - `skill-creator`
  - `ai-audit`
- **Prompt:**

````markdown
Revise the generated skills to fix the following logic defects. Keep the existing design and structure unless a change is required for these fixes. 
- Prevent cross-category deduplication from removing required coverage. 
- Preserve and pass `STATE: NOT_APPLICABLE` correctly into Phase 2. 
- Explicitly close completed subagents after their results are collected. 
- Do not let `api-test-generator` generate extra test cases itself; delegate additional generation to the appropriate specialist skill. 
- When the user provides a single Phase-1 report file: 
  - have parallel workers write to separate temporary report files;
  - merge them into the requested report only after all required Phase-1 workers finish; 
  - validate the merged report; 
  - delete temporary files only after successful validation; 
  - keep temporary files if merging or validation fails. 

Do not redesign unrelated parts.
````

- **AI Output:**

````markdown
Revised all five skills without redesigning unrelated behavior.

Key fixes:

- De-duplication is now category-scoped and cannot remove distinct reviewed coverage.
- `STATE: NOT_APPLICABLE` is persisted, passed into Phase 2, and materialized as `[]`.
- Completed subagents are explicitly closed after result collection.
- Supplemental cases must be generated by the appropriate specialist, never by the orchestrator.
- A single Phase-1 report now uses four temporary worker reports, post-completion merging, merged-report validation, and success-only cleanup. Temporary files survive any merge, validation, or write failure.
- Specialists can read their section from a combined reviewed report and support delegated supplemental generation.

Modified:

- [api-test-generator/SKILL.md](D:/GitHub/SoftwareTesting-HW06/.agents/skills/api-test-generator/SKILL.md)
- [contract-test-generator/SKILL.md](D:/GitHub/SoftwareTesting-HW06/.agents/skills/contract-test-generator/SKILL.md)
- [domain-test-generator/SKILL.md](D:/GitHub/SoftwareTesting-HW06/.agents/skills/domain-test-generator/SKILL.md)
- [state-transition-test-generator/SKILL.md](D:/GitHub/SoftwareTesting-HW06/.agents/skills/state-transition-test-generator/SKILL.md)
- [security-test-generator/SKILL.md](D:/GitHub/SoftwareTesting-HW06/.agents/skills/security-test-generator/SKILL.md)

Validation passed:

- `quick_validate.py`: all five skills returned `Skill is valid!`
- All defect-specific semantic checks passed.
- `git diff --check` passed.
- UI metadata and unrelated files were unchanged.
````

- **File Modifications:**
  - `File: .agents/skills/api-test-generator/SKILL.md`.
    - `Action:` edited.
    - `Deleted:` Prior orchestration wording that allowed cross-category semantic de-duplication, could let the parent add cases from reviewed models, did not explicitly close completed subagents, and did not define safe single-report merging or a complete Phase-2 state-not-applicable handoff.
    - `Replaced With:` Category-scoped coverage-preserving de-duplication; explicit persisted `STATE: NOT_APPLICABLE` Phase-2 handoff; native subagent closure after result collection; specialist-only supplemental generation; parent prohibition on authoring test content; and four-temp-file merge, validation, success-only deletion, and failure preservation rules for a single Phase-1 report.
    - `Appended:` A dedicated `Single Phase-1 report path` section and an explicit parent-generation boundary.
  - `File: .agents/skills/contract-test-generator/SKILL.md`.
    - `Action:` edited.
    - `Deleted:` Input and Phase-2 wording limited to standalone reports and initial candidate generation.
    - `Replaced With:` Support for a read-only `CONTRACT` section in a combined report, unique temporary Phase-1 output ownership, and specialist-owned supplemental generation against existing candidates and approved rules.
    - `Appended:` None.
  - `File: .agents/skills/domain-test-generator/SKILL.md`.
    - `Action:` edited.
    - `Deleted:` Input and Phase-2 wording limited to standalone reports and initial candidate generation.
    - `Replaced With:` Support for a read-only `DOMAIN` section in a combined report, unique temporary Phase-1 output ownership, and specialist-owned supplemental generation against existing candidates and reviewed partitions or boundaries.
    - `Appended:` None.
  - `File: .agents/skills/state-transition-test-generator/SKILL.md`.
    - `Action:` edited.
    - `Deleted:` State-not-applicable handling that returned only a justified empty result without a defined persistent Phase-1 status artifact or Phase-2 candidate fragment.
    - `Replaced With:` A mergeable Phase-1 `STATE: NOT_APPLICABLE` status record, approval bypass for that preserved status, exact status/basis verification in Phase 2, required empty `[]` candidate output, combined-report support, and specialist-owned supplemental generation for applicable transitions.
    - `Appended:` None.
  - `File: .agents/skills/security-test-generator/SKILL.md`.
    - `Action:` edited.
    - `Deleted:` Input and Phase-2 wording limited to standalone reports and initial candidate generation.
    - `Replaced With:` Support for a read-only `SECURITY` section in a combined report, unique temporary Phase-1 output ownership, and specialist-owned supplemental generation against existing candidates and approved scenarios or requirements.
    - `Appended:` None.
  - `File: .skill-revision-stage/*/SKILL.md`.
    - `Action:` temporary files created and deleted.
    - `Deleted:` Five staged revised skill files after protected-directory installation.
    - `Replaced With:` None.
    - `Appended:` None.
  - `File: .validation-deps/**`.
    - `Action:` temporary validator dependencies created and deleted.
    - `Deleted:` Isolated PyYAML dependency directory after all validation runs passed.
    - `Replaced With:` None.
    - `Appended:` None.
- **Verdict:** INCOMPLETE
- **Reasoning:**
  - `NOT_APPLICABLE` uses inconsistent names and formats.
  - Existing approved sections may be lost when using one combined Phase-1 report.
  - The orchestrator still says to spawn exactly four agents.
- **Student Fixes:**
  - Use one clear `NOT_APPLICABLE` format:
    - Report: `State Applicability: NOT_APPLICABLE`
    - Internal record: `state_applicability.status: NOT_APPLICABLE`
    - For one combined report, copy each existing category section into its own temporary file before spawning workers.
    - Merge the temporary reports back into the combined report after Phase 1.
    - Replace “exactly four agents” with one primary agent per testing dimension. Allow extra helper, retry, or supplemental agents when needed.

### Artifact 5

- **User:** Vương Ngũ Tín Thành
- **Date and Time:** 2026-08-20 12:40:11 GMT+7
- **Model Used:** GPT-5.6 Sol (parent and inherited specialist agents)
- **Skill Used:**
  - `api-test-generator`
  - `contract-test-generator`
  - `domain-test-generator`
  - `state-transition-test-generator`
  - `security-test-generator`
  - `ai-audit`
- **Prompt:**

````markdown
Use [$api-test-generator](D:\GitHub\SoftwareTesting-HW06\\.agents\skills\api-test-generator\SKILL.md) for **Pool A — Forgot Password / Reset Password**.



Inputs:

- API specification: [api_specification.md](reference/api_specification.md)
- System requirements: [system_requirements.md](reference/system_requirements.md)
- Selected API: `POST /api/reset-password`

Write the Phase 1 analysis to: `review/pool-a/` (create files).

After Phase 1, stop for my review before generating test cases.

Treat the provided specification and system requirements as authoritative. Do not invent missing API behavior.
````

- **AI Output:**

````markdown
I’m using the `api-test-generator` skill because this request calls for its coordinated Phase 1 analysis and explicit human-review checkpoint. I’ll read its instructions and the relevant endpoint requirements first, then create only the review artifacts under `review/pool-a/`.

The skill requires four parallel specialist agents and a hard review gate. I’m now reading each specialist’s exact Phase 1 contract and extracting a single shared endpoint context so all analyses use the same authoritative facts.

The selected contract is sparse: it defines the JSON request example but no response contract or status codes. The requirements add password-strength, OTP binding, expiry, and one-time-use rules; I’ll preserve those as requirements while explicitly marking unmapped fields and unspecified API behavior as gaps.

The shared context is complete. I’m starting the four mandated Phase 1 specialists concurrently; each owns only its category report, and none is allowed to generate test cases or modify the shared/status files.

All four Phase 1 outputs are back; state analysis found the OTP lifecycle applicable. I’m validating each report for source identity, complete tables, pending review markers, unsupported claims, and confirming that no candidate test files were created.

Phase 1 is complete and stopped at the human-review gate. No test cases were generated.

Review artifacts:

- [Contract analysis](D:/GitHub/SoftwareTesting-HW06/review/pool-a/reports/contract-report.md)
- [Domain analysis](D:/GitHub/SoftwareTesting-HW06/review/pool-a/reports/domain-report.md)
- [State-transition analysis](D:/GitHub/SoftwareTesting-HW06/review/pool-a/reports/state-report.md) — applicable
- [Security analysis](D:/GitHub/SoftwareTesting-HW06/review/pool-a/reports/security-report.md)
- [Shared API context](D:/GitHub/SoftwareTesting-HW06/review/pool-a/shared-api-context.md)
- [Orchestration status and review focus](D:/GitHub/SoftwareTesting-HW06/review/pool-a/orchestration-status.md)

All four reports are marked `PENDING`. The analysis explicitly preserves unspecified behavior, particularly the absent response contract, confirmation-password API mapping, JWT applicability, and OTP interpretation.
````

- **File Modifications:**
  - `File:` `review/pool-a/shared-api-context.md`.
    - `Action:` created.
    - `Deleted:` None.
    - `Replaced With:` None.
    - `Appended:` Shared source identity and hashes; the normalized request, response, authentication, SEC-01–SEC-07, state, and test models for `POST /api/reset-password`; exact specification bases; and explicit gaps and assumptions.
  - `File:` `review/pool-a/orchestration-status.md`.
    - `Action:` created, then edited.
    - `Deleted:` Initial `IN_PROGRESS` status and the four pending-specialist placeholders.
    - `Replaced With:` `AWAITING_HUMAN_REVIEW` status, collected-report paths and hashes, state applicability, coordinator validation results, five human-review focus items, and a gate record confirming that no candidate tests or final suite exist.
    - `Appended:` None.
  - `File:` `review/pool-a/reports/contract-report.md`.
    - `Action:` created.
    - `Deleted:` None.
    - `Replaced With:` None.
    - `Appended:` Phase 1 CONTRACT analysis containing source identity, request and response inventories, `CR-001`–`CR-012`, gaps and ambiguities, and a `Review Status: PENDING` block.
  - `File:` `review/pool-a/reports/domain-report.md`.
    - `Action:` created.
    - `Deleted:` None.
    - `Replaced With:` None.
    - `Appended:` Phase 1 DOMAIN analysis containing the valid baseline, parameter inventory, `DP-001`–`DP-026`, `DB-001`–`DB-006`, cross-parameter constraints, gaps and ambiguities, and a pending review block.
  - `File:` `review/pool-a/reports/state-report.md`.
    - `Action:` created.
    - `Deleted:` None.
    - `Replaced With:` None.
    - `Appended:` Phase 1 STATE analysis marking applicability as `APPLICABLE`, defining `ST-01`–`ST-03`, guards `GD-01`–`GD-05`, transitions `TR-001`–`TR-005`, gaps and ambiguities, and a pending review block.
  - `File:` `review/pool-a/reports/security-report.md`.
    - `Action:` created.
    - `Deleted:` None.
    - `Replaced With:` None.
    - `Appended:` Phase 1 SECURITY analysis containing endpoint characteristics, the SEC-01–SEC-07 applicability matrix, `SS-001`–`SS-007`, coverage decisions, gaps, requested human decisions, and a `Review Status: PENDING` block.
- **Verdict:** INCOMPLETE
- **Reasoning:**
  - Required request fields were not clearly enforced.
  - `null`, wrong-type, malformed, and malformed-email inputs were left unclear.
  - JWT requirement for reset password was unresolved.
  - SQL injection black-box checks were missing.
  - OTP brute-force/rate-limit checks were missing.
  - Account-enumeration checks were missing.
- **Student Fixes:**
  - Treated `email`, `resetToken`, and `newPassword` as required.
  - Treated malformed, missing, `null`, and wrong-type inputs as invalid.
  - Added `Content-Type: application/json`.
  - Added reviewed HTTP expectations: `200`, `400`, `415`, and `429`.
  - Marked JWT as not required for this recovery endpoint.
  - Kept OTP usable after failed validation.
  - Consume OTP only after a successful reset.
  - Added SQL injection black-box testing.
  - Added OTP brute-force/rate-limit testing.
  - Added account-enumeration testing.

### Artifact 6

- **User:** Vương Ngũ Tín Thành
- **Date and Time:** 2026-08-20 17:27:46 GMT+7
- **Model Used:** GPT-5.6 Sol (parent and inherited specialist agents)
- **Skill Used:**
  - `api-test-generator`
  - `contract-test-generator`
  - `domain-test-generator`
  - `state-transition-test-generator`
  - `security-test-generator`
  - `ai-audit`
- **Prompt:**

````markdown
Continue Pool A from the completed Phase 1 review. I have manually revised and approved the Phase 1 reports.

Shared API Context and Orchestration Status are outdated. Refresh them from the reviewed Phase 1 reports before continuing.

Then proceed with Phase 2 using [$api-test-generator](D:\\GitHub\\SoftwareTesting-HW06\\.agents\\skills\\api-test-generator\\SKILL.md) and generate the Pool A test cases as previously configured. Do not redo Phase 1 unless required to resolve an inconsistency.
````

- **AI Output:**

````markdown
I’m resuming with `api-test-generator` at its Phase 2 gate. I’ll first validate the manually approved report versions, reconcile the stale shared context and orchestration status strictly from those reviewed reports, then run the four specialist generators without reopening Phase 1 unless the reports conflict.

The report files still contain stale `PENDING` markers, but your current instruction explicitly approves the exact reviewed files now on disk, which satisfies the Phase 2 gate. I’m treating those files—not the stale markers or prior hashes—as the reviewed authority and checking their revisions before refreshing the parent-owned context.

The approved edits are present—the report hashes changed. I found two stale narrative remnants inside the reports: the structured STATE table now says a weak-password failure preserves the OTP, while its older summary still says unspecified; the SECURITY matrix now makes JWT not applicable, while older gap text still calls it unresolved. I’ll reconcile these by treating the manually revised structured rule/scenario tables as the approved decisions and record that precedence in the refreshed shared context, without rerunning Phase 1.

The parent-owned context is now synchronized with the approved report hashes and decisions. I’m beginning Phase 2 generation; each specialist will read the refreshed context plus only its reviewed report, write a category-owned JSON fragment, and leave aggregation/final IDs to the parent.

Phase 2 produced 76 raw candidates: 26 CONTRACT, 36 DOMAIN, 5 STATE, and 9 SECURITY. I’m now performing the parent-only checks—schema/category/endpoint validation, within-category duplicate review, reviewed-rule coverage, and final stable ID assignment—before writing the CSV.

The parent validation found no true within-category duplicates. Three case-insensitive matches were intentional uppercase/lowercase boundary pairs with different payloads and distinct reviewed coverage, so they are retained. Coverage is complete except CONTRACT `CR-008`, which is correctly unresolved because the API has no confirmation-password field; no unsupported case will be invented.

The suite is aggregated and validated: 76 traceable candidates with stable IDs `API-001`–`API-076`, no records removed, and complete reviewed coverage apart from the intentionally unexecutable confirmation-field rule. I’m doing the final artifact/status integrity check now.

Pool A Phase 2 is complete.

- Final suite: [candidate-api-tests.csv](D:/GitHub/SoftwareTesting-HW06/review/pool-a/candidate-api-tests.csv)
- Total: 76 cases — CONTRACT 26, DOMAIN 36, STATE 5, SECURITY 9
- IDs: `API-001`–`API-076`
- [Shared API context](D:/GitHub/SoftwareTesting-HW06/review/pool-a/shared-api-context.md) refreshed
- [Orchestration status](D:/GitHub/SoftwareTesting-HW06/review/pool-a/orchestration-status.md) marked `COMPLETE`

All reviewed coverage is represented except `CR-008`, because the confirmation-password field has no documented API mapping. No field or missing behavior was invented, and no tests were executed.
````

- **File Modifications:**
  - `File:` `review/pool-a/shared-api-context.md`.
    - `Action:` edited.
    - `Deleted:` Stale Phase 1-only interpretations that treated reviewed requiredness, HTTP oracles, JWT applicability, weak-password OTP effects, and added security scenarios as unresolved.
    - `Replaced With:` Phase 2 review provenance and approved report hashes; structured-row precedence for stale STATE and SECURITY narrative conflicts; reviewed required-field/type/null rules; `application/json`, `200`, `400`, and conditional `429` external oracles; SEC-02 not-applicable interpretation; reviewed STATE `TR-005`; SECURITY `SS-001`–`SS-009`; and preserved specification gaps.
    - `Appended:` None.
  - `File:` `review/pool-a/orchestration-status.md`.
    - `Action:` edited.
    - `Deleted:` Stale Phase 1 `AWAITING_HUMAN_REVIEW` state, outdated report hashes, pending generation state, and review-only gate record.
    - `Replaced With:` Explicit-approval gate provenance, current reviewed report hashes, Phase 2 configuration, `COMPLETE` status, specialist fragment counts and hashes, parent aggregation validation, final CSV hash, and preserved limitations.
    - `Appended:` None.
  - `File:` `review/pool-a/candidates/contract-tests.json`.
    - `Action:` created.
    - `Deleted:` None.
    - `Replaced With:` None.
    - `Appended:` 26 Phase 2 CONTRACT candidates covering `CR-001`–`CR-007` and `CR-009`–`CR-012`; `CR-008` remained explicitly unresolved because confirmation transport is unspecified.
  - `File:` `review/pool-a/candidates/domain-tests.json`.
    - `Action:` created.
    - `Deleted:` None.
    - `Replaced With:` None.
    - `Appended:` 36 Phase 2 DOMAIN candidates covering `DP-001`–`DP-026` and `DB-001`–`DB-006`.
  - `File:` `review/pool-a/candidates/state-tests.json`.
    - `Action:` created.
    - `Deleted:` None.
    - `Replaced With:` None.
    - `Appended:` Five Phase 2 STATE candidates covering `TR-001`–`TR-005`, including the reviewed `TR-005` OTP-preservation decision.
  - `File:` `review/pool-a/candidates/security-tests.json`.
    - `Action:` created.
    - `Deleted:` None.
    - `Replaced With:` None.
    - `Appended:` Nine Phase 2 SECURITY candidates covering `SS-001`–`SS-009`, including reviewed external brute-force and account-enumeration scenarios and SEC-02 not-applicable treatment.
  - `File:` `review/pool-a/candidate-api-tests.csv`.
    - `Action:` created.
    - `Deleted:` None.
    - `Replaced With:` None.
    - `Appended:` Parent-aggregated 76-record candidate suite with exactly nine required columns, stable IDs `API-001`–`API-076`, preserved specialist IDs, and per-category counts CONTRACT 26, DOMAIN 36, STATE 5, SECURITY 9.
- **Verdict:** INCOMPLETE
- **Reasoning:**
  - The generated suite has good coverage and 76 test cases, but 8 cases are incomplete or unclear.
  - Some cases assume undefined behavior, such as OTP expiry or rate-limit thresholds.
  - Some security cases are not directly executable with Postman.
- **Student Fixes:** Continued guiding the agent to revise the incomplete or unclear test cases.

### Artifact 7

- **User:** Vương Ngũ Tín Thành
- **Date and Time:** 2026-08-20 20:24:33 GMT+7
- **Model Used:** GPT-5.6 Sol (parent and inherited specialist agents)
- **Skill Used:**
  - `api-test-generator`
  - `contract-test-generator`
  - `domain-test-generator`
  - `state-transition-test-generator`
  - `security-test-generator`
  - `ai-audit`
- **Prompt:**

````markdown
Revise the Pool A test cases to fix these 8 issues: 

- `API-030`: Make it exploratory or remove it because extra JSON properties have no defined expected behavior. 
- `API-059`: Treat `Aa1!bbbb#` as valid because it already meets the required password rules. 
- `API-025`, `API-065`, `API-072`: Do not assume an OTP expiry duration. Keep expiry behavior testable only if a real expiry point can be configured or observed. 
- `API-068`: Mark it as a white-box/storage verification test because Postman alone cannot prove whether passwords are stored in plaintext. 
- `API-075`: Do not invent a rate-limit threshold. Make the test conditional on a known configured limit. 
- `API-076`: Replace the vague account-enumeration oracle with a clear comparison rule for status, response body, and observable behavior. 

Keep the reviewed Phase-1 requirements as the source of truth. 

After editing, revalidate all Pool A test cases and report which cases were changed.
````

- **AI Output:**

````markdown
I’ll use the reviewed `api-test-generator` workflow to revise the category-owned candidates behind those eight final IDs, preserve the Phase 1 authority, then rebuild and revalidate the 76-row CSV without renumbering unrelated cases. I’ll treat `API-030` as exploratory rather than remove it, preserving traceability and stable IDs.

The fragments confirm the eight referenced IDs map cleanly to four specialist-owned cases/groups. Several are partially corrected already, but I’ll make each requested constraint explicit—for example, expiry cases will be conditional on an observable/configurable expiry point, and the enumeration case will compare status, normalized body structure/content, password state, and other externally observable effects.

All four specialists completed scoped revisions without changing counts or coverage. I’m now checking the revised provisional cases against the eight requested fixes, then I’ll regenerate the final CSV so the same final IDs remain attached to the corrected content.

Full-suite validation passes: 76 rows, 76 unique sequential IDs, zero schema/category/endpoint errors, zero true within-category duplicates, and unchanged CR/DP/DB/TR/SS coverage. I’m updating the parent traceability records with the revised fragment and CSV hashes plus the eight-case change log.

Revised [Pool A test cases](D:/GitHub/SoftwareTesting-HW06/review/pool-a/candidate-api-tests.csv).

Changed cases:

- `API-025`, `API-065`, `API-072`: require a configurable or objectively observable expiry point; otherwise blocked.
- `API-030`: explicitly exploratory, with no pass/fail oracle.
- `API-059`: `Aa1!bbbb#` is valid and expects `200 OK`.
- `API-068`: explicitly white-box/storage verification; not Postman-verifiable alone.
- `API-075`: conditional on a known configured abuse-control limit.
- `API-076`: precise status, body, redirect, content-type, side-effect, and timing comparison rules.

Validation passed: 76 cases, 76 unique sequential IDs, nine required fields per case, unchanged coverage, and zero true duplicates. No tests were executed.
````

- **File Modifications:**
  - `File:` `review/pool-a/candidates/contract-tests.json`.
    - `Action:` edited.
    - `Deleted:` `CONTRACT-P025` preconditions and oracle that did not explicitly block execution when the real expiry point could not be established.
    - `Replaced With:` `CONTRACT-P025` preconditions, expected result, and notes requiring a real configurable or objectively observable expiry point; otherwise `BLOCKED / NOT EXECUTABLE` with no SUT verdict.
    - `Appended:` None.
  - `File:` `review/pool-a/candidates/domain-tests.json`.
    - `Action:` edited.
    - `Deleted:` `DOMAIN-P004` wording that did not explicitly exclude deterministic conformance scoring, and `DOMAIN-P033`'s unresolved acceptance oracle for `Aa1!bbbb#`.
    - `Replaced With:` `DOMAIN-P004` as exploratory/characterization-only with no pass/fail oracle; `DOMAIN-P033` as a valid-password success case expecting reviewed `200 OK` because all required character classes are present and `#` is not prohibited.
    - `Appended:` None.
  - `File:` `review/pool-a/candidates/state-tests.json`.
    - `Action:` edited.
    - `Deleted:` `STATE-P003` setup that could be read as permitting a synthetic or assumed expiry point.
    - `Replaced With:` `STATE-P003` execution gate requiring supported configuration or objective observation of the real SUT expiry point, with no request sent and a blocked result when ST-02 cannot be established.
    - `Appended:` None.
  - `File:` `review/pool-a/candidates/security-tests.json`.
    - `Action:` edited.
    - `Deleted:` Ambiguous executability/oracles in `SECURITY-P001`, `SECURITY-P005`, `SECURITY-P008`, and `SECURITY-P009` concerning storage verification, OTP expiry, rate-limit configuration, and account-enumeration comparison.
    - `Replaced With:` Explicit white-box/storage access for P001; real-expiry execution gating for P005; a known authoritative abuse-control limit for P008; and exact status, semantic JSON or exact non-JSON body, content-type, redirect, password/token/metadata, and conditional timing comparison rules for P009.
    - `Appended:` None.
  - `File:` `review/pool-a/candidate-api-tests.csv`.
    - `Action:` replaced content.
    - `Deleted:` Prior aggregate representations of final IDs `API-025`, `API-030`, `API-059`, `API-065`, `API-068`, `API-072`, `API-075`, and `API-076`.
    - `Replaced With:` Rebuilt 76-row suite preserving IDs `API-001`–`API-076` and incorporating all eight corrected cases; final SHA-256 `3C50ACA8A132222E82E6AFC0607B4C055F22069AEF9FB10429CF326CF6C24081`.
    - `Appended:` None.
  - `File:` `review/pool-a/orchestration-status.md`.
    - `Action:` edited.
    - `Deleted:` Superseded candidate-fragment and CSV hashes plus the prior statement that both DP-004 and DP-024 were characterization cases.
    - `Replaced With:` Current fragment/CSV hashes, an eight-case post-generation revision log, revalidation results, and corrected treatment of DP-004 as exploratory and DP-024 as valid for `Aa1!bbbb#`.
    - `Appended:` None.
  - `File:` `review/pool-a/shared-api-context.md`.
    - `Action:` edited.
    - `Deleted:` Less-specific expiry, storage-verification, rate-limit, enumeration, extra-property, and additional-password-character assumptions.
    - `Replaced With:` Real-expiry execution gates, valid treatment of `Aa1!bbbb#`, exploratory treatment of extra properties, white-box SEC-01 verification, configured-limit-only SS-008 execution, and explicit SS-009 comparison rules.
    - `Appended:` None.
- **Verdict:** VALID
- **Reasoning:** The agent correctly resolved found test defects.
- **Student Fixes:** None

### Artifact 8

- **User:** Vương Ngũ Tín Thành
- **Date and Time:** 2026-08-20 20:47:31 GMT+7
- **Model Used:** GPT-5.6 Sol
- **Skill Used:** `ai-audit`
- **Prompt:**

````markdown
Base on [pool-a](review/pool-a/), fill in [Main_Report.md](Main_Report.md).
````

- **AI Output:**

````markdown
I’ll inspect the report template and the completed Pool A artifacts, then fill only the relevant sections with the reviewed analysis, final test-suite results, revisions, and validation evidence.

The deliverable CSV already matches the final Pool A suite byte-for-byte (76 cases, same SHA-256), so the existing `test-cases/a-forgot-password.csv` link is correct. I’ll now populate Sections A.2–A.6 and update the report date, while leaving Pools B and C untouched.

Filled the Pool A sections in [Main_Report.md](D:/GitHub/SoftwareTesting-HW06/Main_Report.md):

- Contract, domain, state-transition, and security analyses
- Reviewed assumptions and unresolved behavior
- Final counts: 26 CONTRACT, 36 DOMAIN, 5 STATE, 9 SECURITY
- Revision and validation summary for all 76 cases
- Updated report date to 2026-08-20

All report links, IDs, counts, and the final CSV checksum were verified. Pools B and C were unchanged.
````

- **File Modifications:**
  - `File:` `Main_Report.md`.
    - `Action:` edited.
    - `Deleted:` Report and last-updated dates of `2026-08-18`; empty Pool A Sections A.2–A.5; and blank Contract, Domain, State Transition, Security, and Total counts in Section A.6.
    - `Replaced With:` Report and last-updated dates of `2026-08-20`; Pool A contract analysis covering request fields, `CR-001`–`CR-012`, reviewed HTTP assumptions, and unresolved `CR-008`; domain analysis covering `DP-001`–`DP-026`, `DB-001`–`DB-006`, exploratory `API-030`, and valid `API-059`; state analysis covering `ST-01`–`ST-03`, `TR-001`–`TR-005`, and observable/configurable expiry gating; security applicability for `SEC-01`–`SEC-07` and scenarios `SS-001`–`SS-009`; test counts of 26 CONTRACT, 36 DOMAIN, 5 STATE, 9 SECURITY, and 76 total; plus stable IDs, eight revised cases, validation evidence, and final CSV SHA-256 `3C50ACA8A132222E82E6AFC0607B4C055F22069AEF9FB10429CF326CF6C24081`.
    - `Appended:` None.
- **Verdict:** VALID
- **Reasoning:** The agent correctly summarized pool A process into main report.
- **Student Fixes:** None
