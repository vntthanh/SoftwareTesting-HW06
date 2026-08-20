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
- **Model Used:** GPT-5
- **Skill Used:** `skill-creator`
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
