# AI-Driven API Test Generator

## 1. Purpose

The generator takes an API specification and a selected API endpoint as input and automatically produces candidate API test cases.

The generated test cases should cover the following test dimensions:

- Contractual Testing (covers the schema validation, including request/response structure, required fields, data types, and allowed values)
- Domain Testing (including domain partitioning for every parameter and Boundary Value Analysis)
- State Transition Testing (if applicable)
- Security Testing

## 2. Inputs

- API specification document
- Selected endpoint
- Target test-case count (default: 35)

## 3. Output

A structured set of candidate test cases.

- Test ID
- Endpoint
- Category (DOMAIN / STATE / SECURITY / CONTRACT)
- Test Objective
- Preconditions
- Request Input
- Expected Result
- Specification Basis
- Assumptions / Notes

## 4. Pseudocode

```text
FUNCTION generate_api_tests(
    api_specification,
    selected_endpoint,
    target_count = 35
):

    api_contract = extract_api_contract(
        api_specification,
        selected_endpoint
    )

    IF api_contract is NOT FOUND:
        RETURN error

    test_model = analyze_api_contract(api_contract)

    domain_tests = generate_domain_tests(test_model)
    state_tests = generate_state_tests(test_model)
    security_tests = generate_security_tests(test_model)
    contract_tests = generate_contract_tests(test_model)

    candidate_tests = combine(
        domain_tests,
        state_tests,
        security_tests,
        contract_tests
    )

    candidate_tests = remove_duplicates(candidate_tests)

    FOR EACH test IN candidate_tests:
        attach_specification_basis(test, api_contract)
        
        IF test depends on behavior NOT defined by the specification:
            mark_assumption(test)

    candidate_tests = ensure_required_coverage(
        candidate_tests,
        test_model,
        target_count
    )

    assign_test_ids(candidate_tests)

    RETURN candidate_tests
```
