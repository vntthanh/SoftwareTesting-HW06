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
