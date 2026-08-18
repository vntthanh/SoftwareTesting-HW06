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
