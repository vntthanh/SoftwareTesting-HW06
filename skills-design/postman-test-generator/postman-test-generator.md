# AI-Driven Postman Test Generator

## 1. Purpose

Convert the final reviewed API test cases in a CSV file into an executable Postman collection.

This supporting agent does not design new test cases. It implements the reviewed test cases as Postman requests and test scripts while preserving traceability to the source CSV.

## 2. Inputs

- `test_case_csv_path`: path to the final reviewed test-case CSV for one pool
- `api_specification`: API specification used to resolve endpoint, authentication, and contract details
- `conversion_report_path`: location of the Postman conversion report
- `collection_output_path`: location of the generated Postman collection
- `base_url_variable`: Postman base URL variable (default: `{{baseUrl}}`)
- `student_id_variable`: Postman student ID variable (default: `{{studentId}}`)

## 3. Output

An executable Postman Collection v2.1 containing the reviewed test cases.

For each converted test case:

- Request name containing the Test ID and Test Objective
- HTTP method and endpoint
- Required request headers
- Request body or parameters
- Preconditions or setup notes
- Assertions for expected status and machine-checkable expected results
- Source metadata for traceability

The collection also includes the required `X-Student-Id: {{studentId}}` header.
