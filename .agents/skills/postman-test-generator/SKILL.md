---
name: postman-test-generator
description: Convert final reviewed API test cases from CSV into a traceable, Newman-compatible Postman Collection v2.1. Use after test cases are reviewed; do not use this skill to design or expand test cases.
---

# Postman Test Generator

Convert the reviewed CSV test cases into an executable Postman Collection v2.1 while preserving the test intent and source traceability.

## Scope and authority

- Treat the reviewed CSV as authoritative for test intent, expected behavior, and preconditions.
- Use the API specification only to resolve implementation details such as methods, paths, parameters, authentication, and contract structure.
- Do not invent, remove, merge, or redesign test cases. Flag unresolved mappings instead of silently changing intent.
- Keep the collection executable in Postman and Newman without manual modification, apart from supplying runtime variable values.

## Required outputs

Produce:

1. The Postman Collection v2.1 JSON at `collection_output_path`.
2. A conversion report at `conversion_report_path` that records row-to-request traceability, preserved preconditions/setup notes, generated assertions, unresolved/manual-review notes, Postman schema-validation status, and Newman-compatibility status.

## Conversion workflow

1. Read `test_case_csv_path` and validate the required test-case fields used by the reviewed CSV.
2. Read `api_specification` only as needed to resolve request implementation details.
3. For every CSV row, create exactly one corresponding Postman request unless the row itself explicitly represents a multi-request setup/flow.
4. Name the request with the Test ID and Test Objective, and organize requests under `CONTRACT`, `DOMAIN`, `STATE`, or `SECURITY` according to the reviewed test type.
5. Configure method, URL, parameters/body, required headers, and authentication from the reviewed row plus API specification.
6. Add `X-Student-Id: {{studentId}}` unless the reviewed input explicitly requires another value for that test.
7. Use collection/environment variables for runtime-dependent values such as `baseUrl`, `studentId`, authentication tokens, and resource IDs.
8. Add assertions for the reviewed expected status code and each machine-checkable expected result. Do not fabricate assertions for ambiguous prose; record those as manual/unresolved in the conversion report.
9. Preserve preconditions/setup notes explicitly as described below.
10. Verify traceability completeness before final validation.
11. Validate the serialized candidate against the **full Postman Collection v2.1 JSON Schema**. A parseable JSON document or an `info.schema` v2.1 declaration alone is not sufficient. Follow [references/validation.md](references/validation.md).
12. Check Newman compatibility. Do not claim compatibility if collection scripts depend on Postman-only behavior unavailable to Newman.
13. Write the final collection only after full v2.1 schema validation passes. If validation fails, report the errors and do not present the candidate as a valid final collection.

## Preserve preconditions and setup notes

If a reviewed CSV row contains preconditions, setup notes, prior-state requirements, fixture requirements, or equivalent notes:

- Preserve the source meaning and material details; do not silently omit or compress them away.
- Put them in a schema-supported description field associated with the generated request, under a clear `Preconditions` or `Setup` section.
- Copy them into the conversion report for that Test ID so the source-to-output mapping can be audited.
- When the note implies a runtime action that cannot be encoded safely or unambiguously, keep the note and flag the required manual/setup action rather than inventing automation.

Do **not** add arbitrary custom properties to Postman collection objects just to store preconditions or traceability metadata; such properties can violate the Collection v2.1 schema. Prefer supported description fields plus the external conversion report.

## Traceability checks

Before writing the final collection, verify that:

- Every reviewed CSV test case is represented in the collection.
- Test ID, test type, and test objective remain identifiable.
- Preconditions/setup notes are preserved for every row that supplied them.
- Expected status and machine-checkable expected results map to generated assertions.
- Any unresolved mapping is explicit in the conversion report rather than silently dropped.

## Runtime variables

Default to:

- `base_url_variable = {{baseUrl}}`
- `student_id_variable = {{studentId}}`

Preserve user-supplied variable names when provided.
