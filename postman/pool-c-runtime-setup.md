# Pool C Runtime Setup

Pool C contains 85 reviewed cases and 93 requests. API-080 through API-085 are ordered flows and must run in collection order. Do not invoke the collection with plain `newman run`; unwrapped execution is intentionally skipped when the authenticated loopback fixture controller is absent.

The runner snapshots the complete `orders` table and its SQLite sequence. Before each reviewed case, it replaces the table contents with exactly two deterministic rows: the case target and an unrelated sentinel. Flow continuation steps reuse the same target without a reset. The original table is restored in `finally`, including after Newman failure or normal interruption.

The wrapper supplies deterministic non-production JWT variables:

- `adminToken`: valid HS256 JWT with `role = admin`.
- `nonAdminToken`: valid HS256 JWT with `role = user`.
- `malformedToken`: malformed bearer value.
- `forgedToken`: well-formed JWT signed with the wrong key.
- `expiredToken`: correctly signed JWT with `exp = 1`.
- `otherInvalidToken`: correctly signed, not-yet-valid JWT.

Every SUT request receives `X-Student-Id: {{studentId}}` from the collection-level pre-request script. Post-response scripts query the authenticated local fixture controller only where the reviewed expected result provides a machine-checkable state oracle.

Validation without executing Newman:

```powershell
C:\Users\xing0\AppData\Local\Python\bin\python.exe postman\generate_pool_c.py
C:\Users\xing0\AppData\Local\Python\bin\python.exe postman\validate_pool_c_runtime.py --sut-dir D:\GitHub\eshop-sut
C:\Users\xing0\AppData\Local\Python\bin\python.exe .agents\skills\postman-test-generator\scripts\validate_postman_collection.py postman\pool-c-order-management.postman_collection.json postman\postman-v2.1.0-schema.json
```

For the later authorized Newman run, start the SUT first because its startup recreates the database, then use:

```powershell
C:\Users\xing0\AppData\Local\Python\bin\python.exe postman\run_pool_c_with_fixtures.py --sut-dir D:\GitHub\eshop-sut --newman-command npx.cmd newman
```

The wrapper passes through Newman's exit code, requires the exact reset sequence API-001 through API-085 after a successful run, and never prints JWT values.
