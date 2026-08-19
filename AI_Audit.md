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
