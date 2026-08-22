---
labels: bug, fr-03, fr-09, fr-18, medium
---

## Bug: Unsupported content type causes an internal server error

**Impacted Test Case ID(s):** Pool A API-078, Pool B API-068, Pool C API-080

### Description

The reset-password, apply-coupon, and Admin order-status endpoints return a server error instead of safely rejecting JSON-shaped requests sent as `text/plain`.

### Steps to Reproduce

1. For Pool A, seed a registered account with a valid, unused six-digit reset token and send otherwise valid JSON text to `POST /api/reset-password` with `Content-Type: text/plain`.
2. For Pool B, seed an eligible active coupon and send otherwise valid JSON text to `POST /api/apply-coupon` with a valid JWT and `Content-Type: text/plain`.
3. For Pool C, seed an existing order in `pending` state and send an otherwise valid update to `PUT /api/admin/orders/<existing-pending-order-id>/status` with a valid Admin JWT and `Content-Type: text/plain`.
4. Observe all three responses. Retry the Pool A and Pool C requests with the same inputs using `Content-Type: application/json`.

### Expected Result

Each `text/plain` request receives a safe `4xx` response without executing the endpoint operation. The corrected Pool A and Pool C JSON retries succeed.

### Actual Result

All three `text/plain` requests return `500 Internal Server Error`. The corrected Pool A JSON retry returns `200 OK`, confirming that its failed request did not consume the token. Pool B Newman evidence records the `API-068` 500 response and failed non-5xx assertion: [`pool-b-run.json`](../reports/pool-b/pool-b-run.json). Pool C API-080 leaves the order in `pending`; its corrected JSON retry succeeds and changes the order to `confirmed`, as recorded in [`pool-c.json`](../reports/pool-c/pool-c.json).

![bug_fr03-unsupported-content-type-server-error.png](evidence/bug_fr03-unsupported-content-type-server-error.png)

### Environment

- **Browser/OS:** Newman CLI on Windows (browser not applicable)
- **Version:** EShop requirements v2.0; Newman 6.2.2
