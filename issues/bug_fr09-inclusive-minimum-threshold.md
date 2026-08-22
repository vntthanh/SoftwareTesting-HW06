---
labels: bug, fr-09, medium
---

## Bug: Coupon minimum-order equality is incorrectly rejected

**Impacted Test Case ID(s):** Pool B API-002, API-003, API-022, API-031, API-033, API-071

### Description

The apply-coupon endpoint treats `min_order_amount` as an exclusive boundary. Orders whose total exactly equals the coupon minimum are rejected even though FR-09 C3 explicitly requires `total_amount >= min_order_amount`.

### Steps to Reproduce

1. Seed an active, unexpired coupon with remaining usage and a known `min_order_amount`.
2. Send `POST /api/apply-coupon` with a valid JWT and `total_amount` exactly equal to that minimum.
3. Repeat with SAVE10, BIGBUY, VIP100, and a coupon whose minimum is zero.
4. Observe the response.

### Expected Result

The coupon qualifies at the exact minimum and returns the documented fixed or percentage discount calculation.

### Actual Result

The endpoint returns `400 Bad Request` with a below-minimum error at the exact boundary, and the expected calculation fields are absent. The Pool B Newman artifact records six affected boundary failures: [`pool-b-run.json`](../reports/pool-b/pool-b-run.json).

### Environment

- **Browser/OS:** Newman CLI on Windows (browser not applicable)
- **Version:** EShop requirements v2.0; Newman 6.2.2
