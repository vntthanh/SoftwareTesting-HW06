# HW06 CI/CD Report

## Pipeline scope

[`Newman full API suite`](.github/workflows/newman.yml) runs on every push to `main`, every pull request, and manual dispatch. One job executes all three reviewed collections against the pinned EShop SUT:

| Pool | Endpoint | Reviewed cases | Collection requests |
| --- | --- | ---: | ---: |
| A | `POST /api/reset-password` | 82 | 88 |
| B | `POST /api/apply-coupon` | 74 | 74 |
| C | `PUT /api/admin/orders/:id/status` | 85 | 93 |
| **Total** | **All assigned endpoints** | **241** | **255** |

Pool A uses the existing deterministic seeder. Pools B and C use their existing fixture-aware runners, which restore controlled database state after execution. CI submits every collection item to Newman; any skip remains the reviewed collection's own explicit blocked/manual behavior. CI does not filter Test IDs or change collection assertions. It records each pool's exit code, continues through all three pools even if an earlier pool fails, and fails the job if any pool fails.

Every run uploads the three Newman JSON reports, three HTML reports, and the SUT log as `newman-full-suite-<run-id>-<attempt>` for 30 days.

## Required two-commit evidence procedure

The evidence must come from two distinct pushed commits, not two modes of one workflow run.

### Sample commit 1 — all pass

1. Ensure the pinned SUT revision satisfies every automated assertion in all three collections. Update the workflow's SUT `ref` if the fixes are in a newer SUT commit.
2. Run the complete workflow locally or on a branch and confirm Pools A, B, and C contain zero failed assertions.
3. Commit and push the passing baseline, for example: `ci: add full Newman all-pass baseline`.
4. Preserve the resulting green Actions run and all uploaded reports.

The currently pinned teaching SUT commit has confirmed defects recorded in `Main_Report.md`; therefore it cannot honestly supply this green sample until those defects are fixed. Do not use `--suppress-exit-code`, exclude failing Test IDs, or label a run with failed assertions as all-pass.

### Sample commit 2 — intentional single failure

1. Start from the exact all-pass commit.
2. Change exactly one assertion in one collection and label it clearly as intentional. A minimal option is to change only Pool C `API-001`'s expected state from `confirmed` to an impossible sample value, without changing its request or fixtures.
3. Commit that one-line change separately, for example: `test: demonstrate one intentional Newman failure`.
4. Push it and confirm all 241 cases execute, the job is red, and exactly one assertion fails.
5. Preserve the red run and reports. Revert the intentional assertion afterward in a separate cleanup commit so the final branch returns to green.

## Evidence placeholders

### Commit 1 — all-pass sample

- Commit SHA: `TODO`
- Commit URL: `TODO`
- GitHub Actions run URL: `TODO`
- Run date/time (GMT+7): `TODO`
- Observed totals: `TODO — 241 cases executed; 0 failed assertions`
- Screenshot: `TODO — add under reports/ci/evidence/ and link here`
- Artifact name: `TODO — newman-full-suite-<run-id>-<attempt>`

### Commit 2 — intentional single-failure sample

- Parent commit SHA: `TODO — must equal the all-pass sample SHA above`
- Commit SHA: `TODO`
- Commit URL: `TODO`
- GitHub Actions run URL: `TODO`
- Run date/time (GMT+7): `TODO`
- Intentional one-line assertion change: `TODO — file, Test ID, and assertion`
- Observed totals: `TODO — 241 cases executed; exactly 1 failed assertion`
- Screenshot: `TODO — add under reports/ci/evidence/ and link here`
- Artifact name: `TODO — newman-full-suite-<run-id>-<attempt>`
