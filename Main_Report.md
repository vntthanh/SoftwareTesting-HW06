# HW06-AI — API Testing Main Report

## 1. Student and Assignment Information

| Field | Value |
| --- | --- |
| Student ID | 23127261 |
| Student name | Vương Ngũ Tín Thành |
| Class | 23KTPM2 |
| Assignment | HW06-AI — API Testing |
| System under test | EShop |
| SUT repository | <https://github.com/ttbhanh/eshop-sut> |
| Submission repository | <https://github.com/vntthanh/SoftwareTesting-HW06> |
| Report date | 2026-08-18 |
| Last updated | 2026-08-18 |

## 2. Selected APIs

| Pool | Feature | Selected API | Main Testing Focus |
| --- | --- | --- | --- |
| A | FR-03 – Forgot Password / Password Reset | `POST /api/reset-password` | Input validation, reset-token behavior, password rules, security |
| B | FR-09 – Discount Coupons | `POST /api/apply-coupon` | Coupon eligibility, amount boundaries, user constraints, calculation |
| C | FR-18 – Admin Order Management | `PUT /api/admin/orders/:id/status` | Authorization, order-state transitions, invalid transitions |

## 3. Agent Skills

### 3.1. Agent Skills Overall

| Component | Type | Responsibility |
| --- | --- | --- |
| **API Test Generator** | Coordinator | Coordinates the complete API test-generation process and combines results |
| **Domain Test Generator** | Specialized generator | Performs equivalence partitioning and Boundary Value Analysis |
| **State Transition Test Generator** | Specialized generator | Models states and valid/invalid transitions when applicable |
| **Security Test Generator** | Specialized generator | Derives security tests from applicable SEC-01–SEC-07 requirements |
| **Contract Test Generator** | Specialized generator | Validates request and response contracts/schema |
| **AI Audit** | Reused supporting skill | Records AI interactions and file modifications into the AI Audit Report |

The first five components form the **AI-driven API Test Generator architecture** designed for HW06.

The **AI Audit** skill (reused from homework `HW05-AI`) operates alongside this architecture. It records the AI-assisted workflow so that the generation, review, correction, and implementation activities remain auditable.

### 3.2. Skills Design

The design artifacts for the **API Test Generator** and its four specialized generators are stored in the `skills-design/` folder. Each generator has its own subfolder containing its design specification and corresponding diagram.

The **AI Audit** skill is not included in this folder because it is a reusable skill carried over from HW05.

## Pool A: Forgot Password

### A.1. Introduction

Pool A covers **FR-03 – Forgot Password / Password Reset**. This report selects `POST /api/reset-password`, which resets a user's password using an email address, reset token, and new password.

### A.2. Contractual Testing Analysis

### A.3. Domain Testing Analysis

### A.4. State Transition Testing Analysis

### A.5. Security Testing Analysis

### A.6. Test Cases

The final reviewed test cases for this pool are stored in: [`test-cases/a-forgot-password.csv`](test-cases/a-forgot-password.csv)

The test cases were derived from the reviewed analyses in Sections A.2–A.5.

| Testing Type | Number of Test Cases |
| --- | ---: |
| Contractual Testing | |
| Domain Testing | |
| State Transition Testing | |
| Security Testing | |
| **Total** | |

## Pool B: Discount Coupons

### B.1. Introduction

Pool B covers **FR-09 – Discount Coupons**. This report selects `POST /api/apply-coupon`, which applies a coupon to an order amount and returns the calculated `discount_amount` and `final_amount`.

### B.2. Contractual Testing Analysis

### B.3. Domain Testing Analysis

### B.4. State Transition Testing Analysis

### B.5. Security Testing Analysis

### B.6. Test Cases

The final reviewed test cases for this pool are stored in: [`test-cases/b-discount-coupons.csv`](test-cases/b-discount-coupons.csv)

The test cases were derived from the reviewed analyses in Sections A.2–A.5.

| Testing Type | Number of Test Cases |
| --- | ---: |
| Contractual Testing | |
| Domain Testing | |
| State Transition Testing | |
| Security Testing | |
| **Total** | |

## Pool C: Admin Order Management

### C.1. Introduction

Pool C covers **FR-18 – Admin Order Management**. This report selects `PUT /api/admin/orders/:id/status`, which allows an Admin user to update an order to one of the supported states: `pending`, `confirmed`, `shipping`, `delivered`, or `canceled`.

### C.2. Contractual Testing Analysis

### C.3. Domain Testing Analysis

### C.4. State Transition Testing Analysis

### C.5. Security Testing Analysis

### C.6. Test Cases

The final reviewed test cases for this pool are stored in [`test-cases/c-order-management.csv`](test-cases/c-order-management.csv).

The test cases were derived from the reviewed analyses in Sections A.2–A.5.

| Testing Type | Number of Test Cases |
| --- | ---: |
| Contractual Testing | |
| Domain Testing | |
| State Transition Testing | |
| Security Testing | |
| **Total** | |
