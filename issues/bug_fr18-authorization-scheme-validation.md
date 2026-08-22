---
labels: bug, fr-18, medium
---

## Bug: Authorization scheme is not validated

**Impacted Test Case ID(s):** API-006

### Description

The Admin order-status endpoint accepts a valid Admin JWT supplied under the `Basic` authorization scheme and updates the order, although the documented scheme is `Bearer`.

### Steps to Reproduce

1. Seed an existing order in `pending` state and obtain a valid JWT whose role is `admin`.
2. Send `PUT /api/admin/orders/<existing-pending-order-id>/status` with `Authorization: Basic <valid-admin-JWT>`, `Content-Type: application/json`, and body `{"status":"confirmed"}`.
3. Query the order state after the request.

### Expected Result

The non-Bearer request does not satisfy the documented authorization prerequisite and must not update the order.

### Actual Result

The request is authenticated despite using the `Basic` scheme, and the target order changes from `pending` to `confirmed`. The Pool C Newman artifact contains the failed unchanged-state assertion: [`pool-c.json`](../reports/pool-c/pool-c.json).

### Environment

- **Browser/OS:** Newman CLI on Windows (browser not applicable)
- **Version:** EShop requirements v2.0; Newman 6.2.2
