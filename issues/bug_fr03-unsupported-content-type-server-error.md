---
labels: bug, fr-03, fr-09, medium
---

## Bug: Unsupported content type causes an internal server error

**Impacted Test Case ID(s):** Pool A API-078, Pool B API-068

### Description

The reset-password and apply-coupon endpoints do not safely reject JSON-shaped requests sent as `text/plain`. Each endpoint attempts to destructure an unparsed body and produces a server error instead of a client-error response.

### Steps to Reproduce

1. For Pool A, seed a registered account with a valid, unused six-digit reset token and send otherwise valid JSON text to `POST /api/reset-password` with `Content-Type: text/plain`.
2. For Pool B, seed an eligible active coupon and send otherwise valid JSON text to `POST /api/apply-coupon` with a valid JWT and `Content-Type: text/plain`.
3. Observe both responses. For Pool A, retry with the same email, token, and password using `Content-Type: application/json`.

### Expected Result

Each `text/plain` request receives a safe `4xx` response without executing the endpoint operation. The corrected Pool A JSON retry succeeds with `200 OK`.

### Actual Result

Both `text/plain` requests return `500 Internal Server Error`. The corrected Pool A JSON retry returns `200 OK`, confirming that its failed request did not consume the token. Pool B Newman evidence records the `API-068` 500 response and failed non-5xx assertion: [`pool-b-run.json`](../reports/pool-b/pool-b-run.json).

![bug_fr03-unsupported-content-type-server-error.png](evidence/bug_fr03-unsupported-content-type-server-error.png)

### Environment

- **Browser/OS:** Newman CLI on Windows (browser not applicable)
- **Version:** EShop requirements v2.0; Newman 6.2.2
