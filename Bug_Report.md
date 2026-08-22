# Bug Report

## Feature FR-03: Forgot Password / Password Reset

### Reset token accepts non-string JSON numbers

**Impacted Test Cases:** API-009, API-044

The endpoint accepts an issued `resetToken` represented as a JSON number and completes the reset, instead of enforcing the documented string representation and returning `400 Bad Request`.

### Invalid new passwords bypass server-side validation

**Impacted Test Cases:** API-016, API-017, API-018, API-020, API-021, API-022, API-023, API-024, API-046, API-047, API-050, API-052, API-055, API-057, API-060, API-061, API-062, API-067, API-080

The endpoint accepts missing, null, non-string, empty, and weak `newPassword` values with `200 OK` instead of rejecting them. API-080 further shows that an object-valued password is accepted and consumes the reset token, because the subsequent corrected retry returns `400 Bad Request`.

### Unsupported content type causes an internal server error

**Impacted Test Cases:** API-078

Sending otherwise valid JSON as `text/plain` causes `500 Internal Server Error` instead of a safe `4xx` rejection. The same token remains usable when the request is retried correctly as `application/json`.

### Reset passwords are stored in plaintext

**Impacted Test Cases:** API-068

Completed manual database verification confirmed that a successful reset stores the exact submitted password in plaintext instead of a secure hash.

## Feature FR-09: Discount Coupons

### Percent coupons use an invalid discount calculation

**Impacted Test Cases:** Pool B API-001, API-016, API-035, API-047, API-051, API-052, API-060, API-073, API-074

Qualifying percent coupons produce zero or negative discounts and increase the final amount instead of applying the FR-09 percentage formula.

### Coupon minimum-order equality is incorrectly rejected

**Impacted Test Cases:** Pool B API-002, API-003, API-022, API-031, API-033, API-071

Orders exactly equal to `min_order_amount` are rejected even though FR-09 C3 defines the minimum boundary as inclusive.

### Coupon application does not validate JWT credentials

**Impacted Test Cases:** Pool B API-013, API-014, API-020, API-021, API-061, API-062, API-063, API-064

Requests with missing, malformed, invalid-signature, or expired JWTs can receive successful coupon calculations instead of being denied.

### Unsupported content type causes an internal server error

**Impacted Test Cases:** Pool B API-068

Sending an otherwise valid apply-coupon body as `text/plain` causes `500 Internal Server Error` instead of safe client-error handling. This is consolidated into the existing cross-pool unsupported-content-type issue already reported for FR-03.
