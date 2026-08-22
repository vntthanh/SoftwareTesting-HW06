---
name: newman-result-analyzer
description: Analyze Newman JSON execution results into a normalized run summary and per-test-case outcome report. Use for assertion results, request or script errors, multi-request flows, skipped cases, and explicit manual-oracle requirements; do not diagnose or group SUT bugs.
---

# Newman Result Analyzer

Turn a Newman JSON reporter artifact into an execution-evidence report. Keep test execution facts separate from defect analysis: do not group failures, assign severity, or infer SUT root causes.

The analyzer must not:

- Convert failed assertions directly into SUT bugs.
- Group failures by root cause.
- Assign bug severity.
- Infer SUT implementation root causes.
- Modify expected results or test cases.
- Create GitHub issues.

## Inputs and output

Require:

- `newman_json`: the Newman JSON execution-result path.
- `output_report_path`: the destination for the analysis.

Use the requested output format when it is clear from the destination; otherwise write Markdown. If the input is not valid JSON or lacks recognizable Newman run data, report the validation error and do not write a report that could be mistaken for a complete analysis.

## Identify logical test cases

1. Traverse collection leaf requests in collection order, including nested folders. Use the embedded collection snapshot to establish the intended request set when available.
2. Derive each Test ID from explicit metadata such as `Test ID:` first, then from a stable leading identifier in the item or assertion name, such as `API-001`. Do not invent an ID; retain the item name and flag an unresolved identity when no reliable ID exists.
3. Group requests with the same Test ID into one logical test case. Preserve every request name as an ordered flow step rather than collapsing a multi-request flow into one request.
4. Match `run.executions` to collection items by immutable item ID where possible. Use names or Test IDs only as documented fallbacks, and disclose ambiguous matches.
5. Keep iteration-specific executions visible when a request ran more than once. Aggregate them into the logical test case only after recording each observed execution.

If the JSON omits the embedded collection or another authoritative intended-case list, analyze observed executions but state that `BLOCKED_NOT_EXECUTED` and `NOT_EXECUTED` coverage cannot be determined completely.

## Classify outcomes

Use Newman execution objects, assertion error objects, request errors, and entries in `run.failures`. Do not treat an HTTP 4xx or 5xx response as a failure by itself; the result depends on the automated assertion oracle.

Classify each logical test case with exactly one status:

- `RUNTIME_ERROR`: a pre-request or test script failed outside an ordinary assertion failure.
- `REQUEST_ERROR`: request construction, DNS, connection, TLS, timeout, or another send/transport failure prevented a normal response.
- `FAIL_ASSERTION`: at least one automated assertion failed and no runtime or request error takes precedence.
- `PASS`: all assertions that ran passed and no request or runtime error occurred. If no automated assertions existed, use `PASS` only for execution status, set Assertion Result to `NO_AUTOMATED_ASSERTIONS`, and explain that no automated behavior oracle ran.
- `BLOCKED_NOT_EXECUTED`: the intended collection item has no execution and explicit collection evidence marks it blocked or deliberately skipped, such as `pm.execution.skipRequest()` with a blocked/unsupported reason.
- `NOT_EXECUTED`: the intended collection item has no execution and there is no explicit blocked evidence. Common possibilities include filters, `--bail`, control-flow changes, or an interrupted run; record only the cause supported by evidence.

For a logical case with multiple steps or iterations, use this precedence: `REQUEST_ERROR`, `RUNTIME_ERROR`, `FAIL_ASSERTION`, `PASS`. Use a not-executed status only when none of the case's intended steps executed. If some intended steps ran and others did not, classify from the observed executions and describe the missing steps in Execution Notes.

Do not classify an ordinary Chai/Postman assertion failure as `RUNTIME_ERROR`. Correlate duplicate representations of the same error across `execution.assertions` and `run.failures` so one event is not counted twice.

## Manual-oracle requirement

Record manual-oracle need independently of execution status. Mark it `YES` only when collection metadata, descriptions, scripts, or another provided authoritative artifact explicitly says that a manual, white-box, persistence, external-side-effect, concurrency, visual, or similar non-automated check remains. Include the reason. Otherwise mark it `NO`; absence of assertions alone is not proof that a manual oracle was intended.

An automated `PASS` does not satisfy an explicitly required manual oracle. State that the automated portion passed while the manual check remains pending.

## Calculate the run summary

Report:

- Collection name.
- Execution time, preferably start, completion, and duration from Newman timings.
- Total requests.
- Total assertions, passed assertions, and failed assertions.
- Request errors, pre-request script errors, and test script errors.
- Number of distinct logical test cases with one or more failed automated assertions.

Prefer Newman's `run.stats` and timings for run-level totals, then reconcile them against detailed executions and failures. Count error occurrences for the three error totals, but count unique Test IDs for logical cases with failed assertions. Calculate passed assertions as assertions that actually ran without an error; do not count pending or skipped assertions as passed. If source totals and reconstructed totals disagree, preserve the source values, show the discrepancy, and avoid silently normalizing it away.

## Write the report

Include a run-summary section followed by one record per logical test case with these fields:

- Test ID
- Execution Status
- Request / Flow Step
- HTTP Status
- Assertion Result
- Failure / Error Message
- Manual Oracle Required
- Execution Notes

For multi-request flows, show each step's HTTP status, assertions, and errors in execution order within the case record. Use `N/A` for genuinely inapplicable values and distinguish it from unavailable evidence. Preserve concise original failure messages; do not rewrite them as defect causes.

Finish with coverage or reconciliation notes when the artifact is incomplete, matching was ambiguous, intended items were not executed, manual checks remain, or Newman summary counts disagree with reconstructed evidence. Write the report to `output_report_path`, then return that path and a concise count of each execution status.
