---
name: postman-test-generator
description: Convert a final reviewed API test-case CSV for one test pool into a Postman Collection v2.1 that preserves the reviewed cases, traceability, required headers, and Newman compatibility. Use when the test cases are already approved and need implementation in Postman; do not use it to design, expand, or revise test cases.
---

# Postman Test Generator

Convert reviewed API test cases into an executable Postman collection without changing the test design.

## Required Inputs

Resolve these inputs from the user's request or repository context:

- `test_case_csv_path`: final reviewed test-case CSV for one pool.
- `api_specification`: API specification used only to resolve transport and contract details needed for implementation.
- `conversion_report_path`: Markdown report path for conversion traceability and validation results.
- `collection_output_path`: output path for the Postman collection JSON.
- `base_url_variable`: Postman base URL variable; default `{{baseUrl}}`.
- `student_id_variable`: Postman student ID variable; default `{{studentId}}`.

Do not ask for optional values when the defaults are sufficient. Do not add a human-review step: the CSV is assumed to contain the final reviewed test cases.

## Preserve the Reviewed Test Design

The CSV is the authority for test intent. The API specification is supporting authority for endpoint implementation details such as URL shape, parameter placement, content type, and authentication mechanism.

- Do not invent new test cases, partitions, boundaries, state transitions, security attacks, or expected outcomes.
- Do not silently repair or reinterpret a reviewed case.
- Preserve each source Test ID, test type, objective, request input, expected status, and expected result.
- If the CSV and API specification are materially inconsistent and the case cannot be implemented faithfully, record the conflict in the conversion report instead of changing the test semantics.
- Keep one Postman request item per reviewed CSV test case unless the source case explicitly requires a setup request or multi-request sequence.

## Conversion Workflow

1. Read the CSV and API specification.
2. Validate that every row contains enough information to identify the test case, request input, expected status, and expected result. Accept equivalent column names when their meaning is unambiguous; do not require an unrelated `Test Case File` column.
3. Create a Postman Collection v2.1.
4. For each CSV row:
   - Resolve HTTP method and endpoint from the reviewed case and API specification.
   - Name the request with the Test ID and Test Objective.
   - Use `{{baseUrl}}` or the supplied `base_url_variable` rather than embedding an environment-specific host.
   - Add required request headers, including `X-Student-Id: {{studentId}}` or the supplied `student_id_variable`.
   - Configure authentication according to the API specification using collection or environment variables for runtime-dependent credentials or tokens.
   - Map request inputs to the correct path, query, header, form, or body locations without changing their values or purpose.
   - Add a status assertion for the reviewed expected status code.
   - Add Postman test assertions for machine-checkable parts of the reviewed expected result. Do not invent assertions for expectations that are not present in the CSV.
   - Preserve non-machine-checkable expectations as traceability notes and identify them in the conversion report.
   - Attach source traceability in the request description or other Postman-compatible metadata: Test ID, Test Type, and Test Objective.
   - Place the request in a folder named for its reviewed test type when grouping is useful.
5. Ensure runtime-dependent values such as base URL, student ID, authentication tokens, and resource IDs use variables rather than hard-coded local values.
6. Write the collection JSON to `collection_output_path`.
7. Write the conversion report to `conversion_report_path`.
8. Validate the collection and report the validation result. Do not execute requests against a live API merely to prove Newman compatibility unless the user has provided an appropriate target and authorized that execution.

## Postman and Newman Requirements

The collection must be valid Postman Collection v2.1 JSON and should require no manual editing before use with Postman or Newman once normal runtime variable values are supplied.

For generated test scripts:

- Use Postman sandbox APIs supported by Newman, such as `pm.test`, `pm.expect`, `pm.response`, and `pm.variables`/appropriate scoped variables.
- Avoid browser-only APIs, interactive prompts, local absolute paths, or assumptions about the Postman desktop UI.
- Keep assertions deterministic and derived from the reviewed expected result.
- Use variable references for values that differ between environments or executions.

Newman compatibility means the collection structure and scripts are runnable by Newman. It does not require performing a live run when credentials, prerequisite data, or a safe target are unavailable.

## Conversion Report

Create a concise Markdown report that records:

- source CSV path;
- API specification used;
- generated collection path;
- total source rows and total generated test request items;
- mapping of each Test ID to its generated request name and folder/test type;
- which reviewed expectations were encoded as machine-checkable assertions;
- any non-machine-checkable expectations retained as notes;
- any conversion conflicts or unresolved implementation details;
- collection validation result;
- Newman runtime validation result when an authorized run was actually performed, otherwise state that runtime execution was not performed.

The report is evidence of conversion, not a second test-design document. Do not add new test cases or redesign analysis to it.

## Validation Invariants

Before finishing, verify at minimum:

- every reviewed CSV row has a corresponding Postman test item or an explicit conversion error in the report;
- request names preserve Test ID and Test Objective;
- every applicable request includes `X-Student-Id` using the configured variable;
- HTTP method, endpoint, headers, authentication, and input placement match the API specification without changing the reviewed test intent;
- every generated request has an expected-status assertion;
- machine-checkable reviewed expected results have corresponding assertions;
- traceability contains Test ID, Test Type, and Test Objective;
- runtime-dependent values are parameterized;
- collection JSON parses successfully and declares Postman Collection v2.1;
- generated test scripts avoid constructs that require the Postman GUI.

If Newman is installed and a safe, authorized execution target with all required runtime values is available, a Newman run may be used as additional validation. Otherwise perform structural/script validation and state the runtime limitation in the conversion report.
