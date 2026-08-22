"""Generate the reviewed Pool C Postman collection and conversion report."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "test-cases" / "c-order-management.csv"
COLLECTION_PATH = ROOT / "postman" / "pool-c-order-management.postman_collection.json"
REPORT_PATH = ROOT / "postman" / "pool-c-conversion-report.md"

INITIAL_STATUS = {
    **{number: "shipping" for number in (19, 36, 52, 67, 68, 69, 83)},
    **{number: "delivered" for number in (20, 25, 55, 56, 57, 58)},
    **{number: "canceled" for number in (21, 59, 60, 61, 62)},
    **{number: "confirmed" for number in (22, 35, 38, 51, 54, 65, 66)},
}

TARGETS: dict[int, Any] = {
    **{number: "confirmed" for number in range(1, 9)},
    9: "__MALFORMED__", 10: ["confirmed"], 11: "__NO_BODY__", 12: {},
    13: None, 14: 1, 15: "processing", 16: {"status": "confirmed", "unexpected": True},
    17: "__DUPLICATE_CANCELED__", 18: "canceled", 19: "canceled", 20: "pending",
    21: "confirmed", 22: "confirmed", 23: "confirmed", 24: "confirmed", 25: "confirmed",
    26: "confirmed", 27: "confirmed", 28: "confirmed", 29: "confirmed",
    **{number: "confirmed" for number in range(30, 35)},
    35: "shipping", 36: "delivered", 37: "canceled", 38: "pending", 39: "unknown",
    40: "", 41: "Confirmed", 42: None, 43: 1, 44: {}, 45: "__NO_BODY__",
    46: "__MALFORMED__", 47: ["confirmed"], 48: {"status": "confirmed", "extra": "x"},
    49: "__DUPLICATE_SHIPPING__", 50: "confirmed", 51: "shipping", 52: "delivered",
    53: "canceled", 54: "canceled", 55: "pending", 56: "confirmed", 57: "shipping",
    58: "canceled", 59: "pending", 60: "confirmed", 61: "shipping", 62: "delivered",
    63: "shipping", 64: "delivered", 65: "pending", 66: "delivered", 67: "pending",
    68: "confirmed", 69: "canceled", 70: "confirmed", 71: "confirmed", 72: "confirmed",
    73: "confirmed", 74: "confirmed", 75: "confirmed", 76: "confirmed", 77: "confirmed",
    78: "'; UPDATE orders SET status='delivered' WHERE '1'='1", 79: "confirmed",
}

VALID_STATE = {
    1: "confirmed", 18: "canceled", 24: "confirmed", 35: "shipping", 36: "delivered",
    37: "canceled", 50: "confirmed", 51: "shipping", 52: "delivered", 53: "canceled",
    54: "canceled", 70: "confirmed", 79: "confirmed",
}
UNCHANGED_STATE = {
    5, 6, 7, 8, 15, 19, 20, 21, 25, 30, 31, 32, 33, 34, 38, 39, 40,
    *range(55, 70), 71, 72, 73, 74, 75, 76, 77, 78,
}
ERROR_SIGNAL = {5, 6, 7, 8, 19, 20, 21, 25, 30, 31, 32, 33, 34, 38, *range(55, 70), *range(71, 77)}
MESSAGE_SIGNAL = {19, 20, 21, 25, 38, *range(55, 70)}

FLOW_STEPS: dict[int, list[dict[str, Any]]] = {
    80: [
        {"status": "confirmed", "content_type": "text/plain", "four_xx": True, "state": "pending"},
        {"status": "confirmed", "state": "confirmed"},
    ],
    81: [
        {"body": {"status": {"value": "confirmed"}}, "four_xx": True, "state": "pending"},
        {"status": "confirmed", "state": "confirmed"},
    ],
    82: [
        {"status": " confirmed ", "four_xx": True, "state": "pending"},
        {"status": "confirmed", "state": "confirmed"},
    ],
    83: [
        {"status": "canceled", "four_xx": True, "state": "shipping"},
        {"status": "delivered", "state": "delivered"},
    ],
    84: [
        {"status": "confirmed", "state": "confirmed"},
        {"status": "shipping", "state": "shipping"},
        {"status": "delivered", "state": "delivered"},
        {"status": "canceled", "four_xx": True, "state": "delivered"},
    ],
    85: [
        {"status": "confirmed", "auth": "nonadmin", "four_xx": True, "state": "pending"},
        {"status": "confirmed", "auth": "admin", "state": "confirmed"},
    ],
}


def rows() -> list[dict[str, str]]:
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as handle:
        result = list(csv.DictReader(handle))
    expected = [f"API-{number:03d}" for number in range(1, 86)]
    if [row["Test ID"] for row in result] != expected:
        raise RuntimeError("Reviewed CSV must contain API-001 through API-085 exactly once and in order")
    required = {
        "Test ID", "Endpoint", "Category", "Test Objective", "Preconditions", "Request Input",
        "Expected Result", "Specification Basis", "Assumptions / Notes",
    }
    if not result or not required.issubset(result[0]):
        raise RuntimeError(f"Reviewed CSV is missing columns: {sorted(required - set(result[0]))}")
    return result


def auth_header(number: int, step: dict[str, Any] | None = None) -> str | None:
    if step and step.get("auth") == "nonadmin":
        return "Bearer {{nonAdminToken}}"
    if number in {5, 30, 71}:
        return None
    if number == 6:
        return "Basic {{adminToken}}"
    if number == 31:
        return "Bearer"
    if number == 32:
        return "Basic dXNlcjpwYXNz"
    if number in {7, 72}:
        return "Bearer {{malformedToken}}"
    if number in {8, 34, 76}:
        return "Bearer {{nonAdminToken}}"
    if number in {33, 73}:
        return "Bearer {{forgedToken}}"
    if number == 74:
        return "Bearer {{expiredToken}}"
    if number == 75:
        return "Bearer {{otherInvalidToken}}"
    return "Bearer {{adminToken}}"


def path_for(number: int) -> str:
    if number == 3:
        return "/api/admin/orders/status"
    if number == 27:
        return "/api/admin/orders//status"
    if number == 28:
        return "/api/admin/orders/abc/status"
    if number == 29:
        return "/api/admin/orders/null/status"
    if number in {4, 26}:
        return "/api/admin/orders/{{nonexistentOrderId}}/status"
    if number == 77:
        return "/api/admin/orders/%27%20OR%20%271%27%3D%271/status"
    return "/api/admin/orders/{{orderId}}/status"


def body_for(value: Any) -> dict[str, Any] | None:
    if value == "__NO_BODY__":
        return None
    if value == "__MALFORMED__":
        raw = '{"status":"confirmed"'
    elif value == "__DUPLICATE_CANCELED__":
        raw = '{"status":"confirmed","status":"canceled"}'
    elif value == "__DUPLICATE_SHIPPING__":
        raw = '{"status":"confirmed","status":"shipping"}'
    elif isinstance(value, (dict, list)):
        raw = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    else:
        raw = json.dumps({"status": value}, ensure_ascii=False, separators=(",", ":"))
    return {"mode": "raw", "raw": raw, "options": {"raw": {"language": "json"}}}


def description(row: dict[str, str], step_number: int | None = None, total_steps: int | None = None) -> str:
    prefix = ""
    if step_number is not None:
        prefix = f"Ordered flow step {step_number} of {total_steps}. The fixture is reset only before step 1.\n\n"
    return (
        f"{prefix}Test ID: {row['Test ID']}\nCategory: {row['Category']}\n\n"
        f"Objective\n{row['Test Objective']}\n\nPreconditions\n{row['Preconditions']}\n\n"
        f"Reviewed Request Input\n{row['Request Input']}\n\nReviewed Expected Result\n"
        f"{row['Expected Result']}\n\nSpecification Basis\n{row['Specification Basis']}\n\n"
        f"Assumptions / Notes\n{row['Assumptions / Notes']}"
    )


def state_oracle_lines(test_id: str, expected_state: str, check_isolation: bool) -> list[str]:
    lines = [
        "var stateUrl = pm.variables.replaceIn('{{fixtureControlUrl}}') + '/state/' + " + json.dumps(test_id) + ";",
        "var stateKey = pm.variables.replaceIn('{{fixtureControlKey}}');",
        "pm.sendRequest({url: stateUrl, method: 'GET', header: [{key: 'X-Fixture-Control-Key', value: stateKey}]}, function (error, response) {",
        "  pm.test('fixture state oracle is reachable', function () { pm.expect(error).to.equal(null); pm.expect(response.code).to.equal(200); });",
        "  if (error || response.code !== 200) { return; }",
        "  var state = response.json();",
        f"  pm.test('target order state is {expected_state}', function () {{ pm.expect(state.targetStatus).to.equal('{expected_state}'); }});",
    ]
    if check_isolation:
        lines.extend([
            "  pm.test('unrelated order remains confirmed', function () { pm.expect(state.unrelatedStatus).to.equal('confirmed'); });",
            "  pm.test('no order outside the isolated target pair exists', function () { pm.expect(state.orders).to.have.length(2); });",
        ])
    lines.append("});")
    return lines


def test_lines(number: int, test_id: str, step: dict[str, Any] | None = None) -> list[str]:
    lines = [
        "pm.test('X-Student-Id pre-request header is present', function () {",
        "  pm.expect(pm.request.headers.get('X-Student-Id')).to.equal(pm.variables.replaceIn('{{studentId}}'));",
        "});",
        "console.log('[Pool C reviewed response]', 'testId=" + test_id + "', 'request=' + pm.info.requestName, 'status=' + pm.response.code, pm.response.text());",
    ]
    if step:
        if step.get("four_xx"):
            lines.extend([
                "pm.test('reviewed response class is 4xx', function () {",
                "  pm.expect(pm.response.code).to.be.within(400, 499);",
                "});",
            ])
        lines.extend(state_oracle_lines(test_id, step["state"], number in {85}))
        return lines
    if number in ERROR_SIGNAL:
        lines.extend([
            "pm.test('response carries a denial or error signal', function () {",
            "  var body = {}; try { body = pm.response.json(); } catch (ignore) {}",
            "  var hasMessage = typeof body.error === 'string' || typeof body.message === 'string';",
            "  pm.expect(pm.response.code >= 400 || hasMessage).to.equal(true);",
            "});",
        ])
    if number in MESSAGE_SIGNAL:
        lines.extend([
            "pm.test('semantic error includes a non-empty message', function () {",
            "  var body = {}; try { body = pm.response.json(); } catch (ignore) {}",
            "  var value = typeof body.error === 'string' ? body.error : body.message;",
            "  pm.expect(value).to.be.a('string').and.not.empty;",
            "});",
        ])
    state = VALID_STATE.get(number)
    if state is None and number in UNCHANGED_STATE:
        state = INITIAL_STATUS.get(number, "pending")
    if state is not None:
        lines.extend(state_oracle_lines(test_id, state, number in {77, 78, 79}))
    return lines


def make_request(
    row: dict[str, str], number: int, value: Any, *, step: dict[str, Any] | None = None,
    step_number: int | None = None, total_steps: int | None = None,
) -> dict[str, Any]:
    headers: list[dict[str, str]] = []
    auth = auth_header(number, step)
    if auth is not None:
        headers.append({"key": "Authorization", "value": auth, "type": "text"})
    content_type = "application/json"
    if number in {11, 23}:
        content_type = ""
    if step and step.get("content_type"):
        content_type = step["content_type"]
    if content_type:
        headers.append({"key": "Content-Type", "value": content_type, "type": "text"})
    method = "POST" if number == 2 else "PUT"
    name = f"{row['Test ID']} {row['Test Objective']}"
    if step_number is not None:
        name = f"{row['Test ID']} (Step {step_number}/{total_steps}) {row['Test Objective']}"
    request: dict[str, Any] = {
        "method": method,
        "header": headers,
        "url": "{{baseUrl}}" + path_for(number),
        "description": description(row, step_number, total_steps),
    }
    body_value = step.get("body") if step and "body" in step else (step.get("status") if step else value)
    body = body_for(body_value)
    if body is not None:
        request["body"] = body
    return {
        "name": name,
        "event": [{"listen": "test", "script": {"type": "text/javascript", "exec": test_lines(number, row["Test ID"], step)}}],
        "request": request,
        "response": [],
    }


def prerequest_script() -> list[str]:
    return [
        "var evidenceStudentId = pm.variables.replaceIn('{{studentId}}');",
        "pm.request.headers.upsert({key: 'X-Student-Id', value: evidenceStudentId});",
        "console.log('[Pool C execution evidence]', 'request=' + pm.info.requestName, 'method=' + pm.request.method, 'url=' + pm.request.url.toString(), 'studentId=' + evidenceStudentId);",
        "var fixtureMatch = pm.info.requestName.match(/^API-\\d{3}/);",
        "var fixtureTestId = fixtureMatch && fixtureMatch[0];",
        "var isContinuation = /\\(Step [2-9]\\//.test(pm.info.requestName);",
        "var fixtureControlUrl = pm.variables.replaceIn('{{fixtureControlUrl}}');",
        "var fixtureControlKey = pm.variables.replaceIn('{{fixtureControlKey}}');",
        "if (!fixtureTestId || !/^http:\\/\\/127\\.0\\.0\\.1:\\d+$/.test(fixtureControlUrl) || !fixtureControlKey) {",
        "  console.error('[Pool C fixture error]', 'Missing or unsafe local fixture controller configuration', 'request=' + pm.info.requestName);",
        "  pm.execution.skipRequest();",
        "} else if (!isContinuation) {",
        "  pm.sendRequest({",
        "    url: fixtureControlUrl + '/reset/' + fixtureTestId,",
        "    method: 'POST',",
        "    header: [{key: 'X-Fixture-Control-Key', value: fixtureControlKey}]",
        "  }, function (error, response) {",
        "    if (error || response.code !== 200) {",
        "      console.error('[Pool C fixture error]', fixtureTestId, error || ('HTTP ' + response.code));",
        "      pm.execution.skipRequest();",
        "      return;",
        "    }",
        "    var fixture = response.json();",
        "    pm.collectionVariables.set('orderId', String(fixture.orderId));",
        "    pm.collectionVariables.set('unrelatedOrderId', String(fixture.unrelatedOrderId));",
        "    pm.collectionVariables.set('nonexistentOrderId', String(fixture.nonexistentOrderId));",
        "    console.log('[Pool C fixture ready]', fixtureTestId, 'orderId=' + fixture.orderId);",
        "  });",
        "}",
    ]


def make_collection(source_rows: list[dict[str, str]]) -> dict[str, Any]:
    folders = {category: [] for category in ("CONTRACT", "DOMAIN", "STATE", "SECURITY")}
    for row in source_rows:
        number = int(row["Test ID"].split("-")[1])
        if number in FLOW_STEPS:
            steps = FLOW_STEPS[number]
            items = [
                make_request(
                    row, number, step.get("status"), step=step,
                    step_number=index, total_steps=len(steps),
                )
                for index, step in enumerate(steps, 1)
            ]
            folders[row["Category"]].append({
                "name": f"{row['Test ID']} Ordered Flow — {row['Test Objective']}",
                "description": description(row),
                "item": items,
            })
        else:
            folders[row["Category"]].append(make_request(row, number, TARGETS[number]))
    return {
        "info": {
            "_postman_id": "4f99757b-0f11-4dd6-bf42-231272610003",
            "name": "Pool C — Admin Order Management — 85 Reviewed Cases",
            "description": (
                "Generated only from test-cases/c-order-management.csv. Contains 85 reviewed cases "
                "and 93 requests; API-080 through API-085 are preserved as ordered flows. Runtime "
                "fixtures are required through postman/run_pool_c_with_fixtures.py."
            ),
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "event": [{"listen": "prerequest", "script": {"type": "text/javascript", "exec": prerequest_script()}}],
        "item": [{"name": category, "item": folders[category]} for category in folders],
        "variable": [
            {"key": "baseUrl", "value": "http://localhost:3000", "type": "string"},
            {"key": "studentId", "value": "23127261", "type": "string"},
            *[{"key": key, "value": "", "type": "string"} for key in (
                "adminToken", "nonAdminToken", "malformedToken", "forgedToken", "expiredToken",
                "otherInvalidToken", "fixtureControlUrl", "fixtureControlKey", "orderId",
                "unrelatedOrderId", "nonexistentOrderId",
            )],
        ],
    }


def md(value: str) -> str:
    return value.replace("|", "\\|").replace("\r", " ").replace("\n", "<br>")


def make_report(source_rows: list[dict[str, str]]) -> str:
    counts = Counter(row["Category"] for row in source_rows)
    lines = [
        "# Pool C Postman Conversion Report", "", "## Conversion summary", "",
        "- Source: `test-cases/c-order-management.csv` (85 final reviewed rows).",
        "- Review context: `review/pool-c/`.",
        "- Collection: `postman/pool-c-order-management.postman_collection.json`.",
        "- Mapping: 79 single-request cases plus six ordered flows, totaling 85 cases and 93 requests.",
        "- Ordered flows: API-080 (2), API-081 (2), API-082 (2), API-083 (2), API-084 (4), API-085 (2).",
        f"- Categories: CONTRACT {counts['CONTRACT']}; DOMAIN {counts['DOMAIN']}; STATE {counts['STATE']}; SECURITY {counts['SECURITY']}.",
        "- Reviewed expected results are copied unchanged into each request description and this report.",
        "- No Newman execution was performed.", "", "## Runtime and compatibility", "",
        "- `postman/pool_c_fixtures.py` owns an isolated target and unrelated order per case, supplies deterministic Admin/non-Admin and invalid JWT variants, and supports post-request state inspection.",
        "- `postman/run_pool_c_with_fixtures.py` snapshots the complete orders table, resets once per reviewed case (not between flow steps), and restores in `finally`.",
        "- Collection-level pre-request logic upserts `X-Student-Id: {{studentId}}`, requires an authenticated loopback fixture controller, and skips unsafe unwrapped execution.",
        "- Scripts use Newman-supported Collection v2.1 features: `pm.sendRequest`, `pm.test`, variables, request headers, and `pm.execution.skipRequest`.",
        "- Full official Postman v2.1 schema status is recorded in `postman/pool-c-validation-results.json`.",
        "", "## Assertion policy", "",
        "Semantic database-state assertions are generated only where the reviewed result specifies a transition or no-mutation outcome. Exact `4xx` assertions occur only in human cases API-080–API-085. Exploratory/characterization cases retain response logging without invented pass/fail behavior. The contextual relevance of an ‘appropriate message’ remains a manual oracle; only presence of a non-empty error/message is automated.",
        "", "## Row-to-request traceability", "",
        "| Test ID | Category | Requests | Preconditions (preserved) | Reviewed expected result (unchanged) | Generated assertions / unresolved notes |",
        "|---|---|---:|---|---|---|",
    ]
    for row in source_rows:
        number = int(row["Test ID"].split("-")[1])
        request_count = len(FLOW_STEPS.get(number, [None]))
        notes: list[str] = ["X-Student-Id header presence"]
        if number in FLOW_STEPS:
            notes.append("ordered step-specific 4xx/state assertions")
        else:
            if number in ERROR_SIGNAL:
                notes.append("denial/error signal")
            if number in MESSAGE_SIGNAL:
                notes.append("non-empty error/message; contextual appropriateness is manual")
            if number in VALID_STATE or number in UNCHANGED_STATE:
                notes.append("fixture-backed target state")
            if number in {77, 78, 79}:
                notes.append("fixture-backed unrelated-order isolation")
            if len(notes) == 1:
                notes.append("reviewed response remains observational; no behavior oracle invented")
        lines.append(
            f"| {row['Test ID']} | {row['Category']} | {request_count} | {md(row['Preconditions'])} | "
            f"{md(row['Expected Result'])} | {md('; '.join(notes))} |"
        )
    lines.extend([
        "", "## Traceability result", "",
        "All API-001 through API-085 are represented exactly once as reviewed cases. Test ID, category, objective, preconditions, request input, expected result, specification basis, and assumptions/notes are preserved in schema-supported request or flow descriptions. No case was added, removed, merged, or redesigned.", "",
    ])
    return "\n".join(lines)


def main() -> None:
    source_rows = rows()
    collection = make_collection(source_rows)
    COLLECTION_PATH.write_text(json.dumps(collection, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(make_report(source_rows), encoding="utf-8")
    print(f"WROTE: {COLLECTION_PATH}")
    print(f"WROTE: {REPORT_PATH}")


if __name__ == "__main__":
    main()
