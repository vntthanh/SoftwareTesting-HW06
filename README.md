# HW06-AI — API Testing

## Self-Assessment

| No. | Criteria | Maximum | Self-Assessed |
| ---: | --- | ---: | ---: |
| 1 | API 1 — full pipeline: generate, audit, extend, execute, and report bugs | 30 | 30 |
| 2 | API 2 — full pipeline: generate, audit, extend, execute, and report bugs | 30 | 30 |
| 3 | API 3 — full pipeline: generate, audit, extend, execute, and report bugs | 30 | 30 |
| 4 | Agent Skills — AI-driven API test generator | 10 | 10 |
| | **Total** | **100** | **100** |

## Test Summary

| Metric | Total | Counting basis |
| --- | ---: | --- |
| APIs tested | 3 | One API from each of Pools A, B, and C |
| AI-generated test cases | 222 | Pool A: 76; Pool B: 67; Pool C: 79 |
| Human-added test cases | 19 | Pool A: 6; Pool B: 7; Pool C: 6 |
| Final reviewed logical cases | 241 | 222 AI-generated plus 19 human-added cases |
| Logical cases executed | 237 | Cases with an observed execution: Pool A: 78; Pool B: 74; Pool C: 85 |
| Logical cases passed | 187 | Pool A: 55; Pool B: 54; Pool C: 78 |
| Logical cases failed | 50 | Pool A: 23; Pool B: 20; Pool C: 7 |
| Blocked before execution | 4 | Pool A cases with unavailable expiry/rate-limit execution conditions |
| Distinct bugs reported | 10 | Unique GitHub issues linked from the bug report |

The complete CI run accounted for all 241 cases, including the four blocked cases. Newman recorded 407 automated assertions: 356 passed and 51 failed. Assertion totals are not logical-case totals because one logical case may contain multiple requests or assertions, and some cases require a manual oracle.

## Selected APIs

| Pool | API |
| --- | --- |
| A | `POST /api/reset-password` |
| B | `POST /api/apply-coupon` |
| C | `PUT /api/admin/orders/:id/status` |

## Deliverables

- [Main API testing report](Main_Report.md)
- [AI Audit](AI_Audit.md)
- [AI Critique](AI_Critique.md)
- [Bug Report](Bug_Report.md)
- [CI/CD Report](CI_CD_Report.md)
- [Final test-case CSV files](test-cases/)
- [Postman collections and runtime scripts](postman/)
- [Newman HTML and JSON reports](reports/)
- [AI-driven test-generator designs](skills-design/)
- [GitHub Issues](https://github.com/vntthanh/eshop-sut/issues)
- [SUT repository](https://github.com/vntthanh/eshop-sut)

