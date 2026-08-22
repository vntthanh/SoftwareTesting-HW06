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
