import argparse
import csv
import hashlib
import json
import re
import subprocess
import threading
from datetime import datetime, timezone, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "test-cases" / "a-forgot-password.csv"
OUT_PATH = ROOT / "postman" / "pool-a-forgot-password.postman_collection.json"
REPORT_PATH = ROOT / "postman" / "pool-a-conversion-report.md"
STATE_PATH = ROOT / "postman" / "pool-a-validation-results.json"
DEFAULT_SCHEMA_PATH = ROOT / "postman" / "postman-v2.1.0-schema.json"
GMT7 = timezone(timedelta(hours=7))

REQUIRED_COLUMNS = {
    "Test ID", "Endpoint", "Category", "Test Objective", "Preconditions",
    "Request Input", "Expected Result", "Specification Basis", "Assumptions / Notes",
}

FLOW_LABELS = {
    "API-076": ["Request A - registered email", "Request B - non-existing email"],
    "API-077": ["Request A - concurrent participant", "Request B - concurrent participant"],
    "API-078": ["Step 1 - text/plain", "Step 2 - JSON retry"],
    "API-079": ["Step 1 - empty body", "Step 2 - valid retry"],
    "API-080": ["Step 1 - object password", "Step 2 - string retry"],
    "API-081": ["Step 1 - Account A injection string", "Step 2 - Account B integrity check"],
}

# These four cases intentionally fail before usable server-side request state exists.
# Every other reviewed case has an explicit fixture readiness gate.
NO_SERVER_FIXTURE_IDS = {"API-002", "API-003", "API-028", "API-029"}
EXPIRY_IDS = {"API-025", "API-065", "API-072"}
WHITE_BOX_IDS = {"API-068"}
PARTIAL_MANUAL_ORACLE_IDS = {
    "API-025", "API-046", "API-047", "API-050", "API-052", "API-055",
    "API-057", "API-063", "API-065", "API-067", "API-068", "API-069",
    "API-070", "API-071", "API-072", "API-073", "API-074", "API-076",
    "API-077", "API-078", "API-081",
}


def now_gmt7():
    return datetime.now(GMT7).strftime("%Y-%m-%d %H:%M:%S GMT+7")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def load_rows():
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows or not REQUIRED_COLUMNS.issubset(rows[0]):
        raise RuntimeError("CSV is empty or missing required reviewed fields")
    ids = [row["Test ID"] for row in rows]
    if len(ids) != 82 or len(ids) != len(set(ids)):
        raise RuntimeError(f"Expected 82 unique reviewed test IDs, found {len(ids)} rows / {len(set(ids))} unique")
    return rows


def variable_name(label):
    words = re.findall(r"[A-Za-z0-9]+", label)
    if not words:
        return "fixtureValue"
    return words[0].lower() + "".join(word[:1].upper() + word[1:] for word in words[1:])


def replace_placeholders(text):
    return re.sub(r"<([^>]+)>", lambda match: "{{" + variable_name(match.group(1)) + "}}", text)


def json_fragments(text):
    fragments = []
    stack = []
    start = None
    quoted = False
    escaped = False
    pairs = {"}": "{", "]": "["}
    for index, char in enumerate(text):
        if start is None:
            if char in "{[":
                start = index
                stack = [char]
            continue
        if escaped:
            escaped = False
        elif char == "\\" and quoted:
            escaped = True
        elif char == '"':
            quoted = not quoted
        elif not quoted:
            if char in "{[":
                stack.append(char)
            elif char in "}]":
                if not stack or stack[-1] != pairs[char]:
                    start, stack = None, []
                    continue
                stack.pop()
                if not stack:
                    fragments.append(text[start:index + 1])
                    start = None
    return fragments


def structured_input(text):
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(value, dict) or not ({"Headers", "Body", "Raw Body"} & set(value)):
        return None
    headers = value.get("Headers", {})
    if not isinstance(headers, dict):
        raise RuntimeError("Structured Request Input Headers must be an object")
    if "Raw Body" in value:
        raw = value["Raw Body"]
        if not isinstance(raw, str):
            raise RuntimeError("Structured Request Input Raw Body must be a string")
        body_kind = "raw"
    elif "Body" in value:
        raw = json.dumps(value["Body"], ensure_ascii=False, separators=(",", ":"))
        body_kind = "json"
    else:
        raw, body_kind = "", "empty"
    return {
        "headers": [{"key": str(key), "value": str(val), "type": "text"} for key, val in headers.items()],
        "raw": replace_placeholders(raw),
        "body_kind": body_kind,
    }


def request_specs(row):
    test_id = row["Test ID"]
    structured = structured_input(row["Request Input"])
    if structured is not None:
        return [structured]
    if test_id == "API-002":
        return [{
            "headers": [{"key": "Content-Type", "value": "application/json", "type": "text"}],
            "raw": '{"email":"test@domain.com","resetToken":"123456","newPassword":"NewPassword123!"',
            "body_kind": "raw",
        }]
    fragments = json_fragments(row["Request Input"])
    labels = FLOW_LABELS.get(test_id)
    count = len(labels) if labels else 1
    specs = []
    for step in range(count):
        if test_id == "API-079" and step == 0:
            raw = ""
            body_kind = "empty"
        elif step < len(fragments):
            raw = replace_placeholders(fragments[step])
            body_kind = "json"
        else:
            raise RuntimeError(f"{test_id} step {step + 1}: no reviewed body representation could be resolved")
        content_type = "text/plain" if test_id == "API-078" and step == 0 else "application/json"
        headers = [{"key": "Content-Type", "value": content_type, "type": "text"}]
        if test_id == "API-082":
            headers.append({"key": "Authorization", "value": "Bearer definitely-not-a-valid-jwt", "type": "text"})
        specs.append({"headers": headers, "raw": raw, "body_kind": body_kind})
    return specs


def expected_status(row, step=0):
    special = {
        "API-076": [400, 400], "API-077": [None, None], "API-078": [None, 200],
        "API-079": [400, 200], "API-080": [400, 200], "API-081": [200, 200],
    }
    test_id = row["Test ID"]
    if test_id in special:
        return special[test_id][step]
    if test_id in {"API-030", "API-075"}:
        return None
    matches = re.findall(r"\b(200|201|204|400|401|403|404|409|415|422|429|500)\b", row["Expected Result"])
    return int(matches[0]) if matches else None


def execution_flags(row):
    test_id = row["Test ID"]
    flags = []
    if test_id not in NO_SERVER_FIXTURE_IDS:
        flags.append("SERVER-SIDE FIXTURE REQUIRED")
    if test_id in EXPIRY_IDS:
        flags.extend(["OBSERVABLE EXPIRY POINT", "BLOCKED / NOT EXECUTABLE UNTIL EXPIRY FIXTURE IS CONFIRMED"])
    if test_id in WHITE_BOX_IDS:
        flags.append("WHITE-BOX VERIFICATION")
    if test_id == "API-075":
        flags.extend([
            "CONFIGURED RATE LIMIT",
            "BLOCKED / NOT EXECUTABLE UNTIL AUTHORITATIVE LIMIT IS SUPPLIED",
            "MANUAL / DATA-DRIVEN REPEATED EXECUTION REQUIRED",
            "SINGLE REQUEST TEMPLATE ONLY — REPEAT THROUGH THE AUTHORITATIVE CONFIGURED TRIGGER",
        ])
    if test_id == "API-077":
        flags.append("MANUAL CONCURRENT DISPATCH")
    if test_id == "API-030":
        flags.append("EXPLORATORY / MANUAL ORACLE REQUIRED")
    elif test_id in PARTIAL_MANUAL_ORACLE_IDS:
        flags.append("PARTIALLY AUTOMATED / MANUAL ORACLE REQUIRED")
    return flags


def fixture_ready_variable(test_id):
    return "fixtureReady" + test_id.replace("-", "").title()


def template_variables(value):
    return set(re.findall(r"{{\s*([A-Za-z0-9_.-]+)\s*}}", value))


def required_variables(row, spec):
    required = set()
    for header in spec["headers"]:
        required.update(template_variables(header["value"]))
    required.update(template_variables(spec["raw"]))
    required.discard("baseUrl")
    required.discard("studentId")
    if row["Test ID"] not in NO_SERVER_FIXTURE_IDS:
        required.add(fixture_ready_variable(row["Test ID"]))
    return sorted(required)


def prerequest_script(required):
    if not required:
        return None
    ready_vars = [name for name in required if name.startswith("fixtureReady")]
    value_vars = [name for name in required if name not in ready_vars]
    return [
        f"var requiredFixtureValues = {json.dumps(value_vars)};",
        f"var requiredReadinessFlags = {json.dumps(ready_vars)};",
        "var missingFixtureValues = requiredFixtureValues.filter(function (name) { var value = pm.variables.get(name); return value === undefined || value === null || String(value).trim() === '' || /{{.+}}/.test(String(value)); });",
        "var unconfirmedFixtures = requiredReadinessFlags.filter(function (name) { return String(pm.variables.get(name)).toLowerCase() !== 'true'; });",
        "var blockedBy = missingFixtureValues.concat(unconfirmedFixtures);",
        "if (blockedBy.length) { console.error('[Pool A BLOCKED / NOT EXECUTABLE] Missing runtime fixture(s): ' + blockedBy.join(', ')); throw new Error('BLOCKED / NOT EXECUTABLE: supply and confirm required runtime fixtures: ' + blockedBy.join(', ')); }",
    ]


def api076_snapshot_script(store):
    lines = [
        "function api076Snapshot() {",
        "  var contentType = (pm.response.headers.get('Content-Type') || '').split(';')[0].trim().toLowerCase();",
        "  var location = pm.response.headers.get('Location');",
        "  var redirect = (pm.response.code >= 300 && pm.response.code < 400) || location !== undefined;",
        "  var raw = pm.response.text();",
        "  var isJson = contentType.indexOf('json') !== -1;",
        "  var body = raw;",
        "  if (isJson) {",
        "    try {",
        "      body = JSON.parse(raw);",
        "      var paths = JSON.parse(pm.collectionVariables.get('api076NondeterministicFields') || '[]');",
        "      paths.forEach(function (path) { var parts = String(path).split('.'); var cursor = body; for (var i = 0; i < parts.length - 1; i++) { if (!cursor || typeof cursor !== 'object') return; cursor = cursor[parts[i]]; } if (cursor && typeof cursor === 'object') delete cursor[parts[parts.length - 1]]; });",
        "    } catch (error) { isJson = false; body = raw; }",
        "  }",
        "  return { status: pm.response.code, contentType: contentType, redirect: redirect, location: location || null, isJson: isJson, body: body };",
        "}",
    ]
    if store:
        lines.append("pm.collectionVariables.set('__api076RequestA', JSON.stringify(api076Snapshot()));")
    else:
        lines.extend([
            "var api076A = JSON.parse(pm.collectionVariables.get('__api076RequestA') || 'null');",
            "var api076B = api076Snapshot();",
            "pm.test('API-076 - Request A evidence is available', function () { pm.expect(api076A).to.be.an('object'); });",
            "pm.test('API-076 - status behavior matches', function () { pm.expect(api076B.status).to.eql(api076A.status); });",
            "pm.test('API-076 - Content-Type matches', function () { pm.expect(api076B.contentType).to.eql(api076A.contentType); });",
            "pm.test('API-076 - redirect/no-redirect behavior matches', function () { pm.expect(api076B.redirect).to.eql(api076A.redirect); if (api076B.redirect) pm.expect(api076B.location).to.eql(api076A.location); });",
            "pm.test('API-076 - response representation and reviewed body comparison match', function () { pm.expect(api076B.isJson).to.eql(api076A.isJson); pm.expect(api076B.body).to.eql(api076A.body); });",
            "pm.collectionVariables.unset('__api076RequestA');",
        ])
    return lines


def description(row, flags, required, step_label=None):
    parts = [
        f"Test ID: {row['Test ID']}", f"Category: {row['Category']}",
        f"Objective: {row['Test Objective']}",
    ]
    if step_label:
        parts.append(f"Flow step: {step_label}")
    parts.extend([
        "", "Preconditions / Setup:", row["Preconditions"],
        "", "Reviewed request input:", row["Request Input"],
        "", "Reviewed expected result:", row["Expected Result"],
        "", "Specification basis:", row["Specification Basis"],
        "", "Assumptions / Notes:", row["Assumptions / Notes"],
    ])
    if required:
        parts.extend(["", "Required runtime fixtures (request is blocked until supplied/confirmed):", *[f"- {name}" for name in required]])
    if flags:
        parts.extend(["", "Execution classification:", *[f"- {flag}" for flag in flags]])
    return "\n".join(parts)


def request_item(row, spec, step=0, step_label=None):
    test_id = row["Test ID"]
    flags = execution_flags(row)
    required = required_variables(row, spec)
    status = expected_status(row, step)
    tests = [
        f"console.log('[Pool A evidence] {test_id}{(' ' + step_label) if step_label else ''}', pm.request.method, pm.request.url.toString(), 'status=' + pm.response.code, 'responseTimeMs=' + pm.response.responseTime);"
    ]
    if test_id == "API-078" and step == 0:
        tests.extend([
            "pm.test('API-078 - text/plain response is a 4xx client error', function () { pm.expect(pm.response.code).to.be.at.least(400); pm.expect(pm.response.code).to.be.below(500); });",
            "if (pm.response.code !== 415) { console.warn('[API-078 human/external HTTP expectation] Preferred 415 Unsupported Media Type, but any safe 4xx rejection is accepted.'); }",
        ])
    elif status is not None:
        tests.append(f"pm.test('{test_id} - reviewed status is {status}', function () {{ pm.response.to.have.status({status}); }});")
    else:
        tests.append(f"console.warn('[Pool A manual oracle] {test_id}: no automatic status oracle is defined; see request description and conversion report.');")
    if test_id == "API-076":
        tests.extend(api076_snapshot_script(store=(step == 0)))
    if "PARTIALLY AUTOMATED / MANUAL ORACLE REQUIRED" in flags:
        tests.append(f"console.warn('[Pool A partial automation] {test_id}: reviewed observable result includes checks requiring an external/manual oracle.');")
    name = f"{test_id} - {row['Test Objective']}"
    if step_label:
        name += f" [{step_label}]"
    events = []
    pre = prerequest_script(required)
    if pre:
        events.append({"listen": "prerequest", "script": {"type": "text/javascript", "exec": pre}})
    events.append({"listen": "test", "script": {"type": "text/javascript", "exec": tests}})
    item = {
        "name": name,
        "event": events,
        "request": {
            "method": "POST",
            "header": spec["headers"],
            "body": {
                "mode": "raw", "raw": spec["raw"],
                "options": {"raw": {"language": "json" if spec["body_kind"] == "json" else "text"}},
            },
            "url": {"raw": "{{baseUrl}}/api/reset-password", "host": ["{{baseUrl}}"], "path": ["api", "reset-password"]},
            "description": description(row, flags, required, step_label),
        },
    }
    if test_id == "API-076":
        item["protocolProfileBehavior"] = {"followRedirects": False}
    return item


def build_collection(rows):
    categories = {name: [] for name in ("CONTRACT", "DOMAIN", "STATE", "SECURITY")}
    runtime_vars = {"baseUrl": "http://localhost:3000", "studentId": "23127261", "api076NondeterministicFields": "[]"}
    report_rows = []
    for row in rows:
        specs = request_specs(row)
        labels = FLOW_LABELS.get(row["Test ID"])
        items = []
        required_all = set()
        for step, spec in enumerate(specs):
            label = labels[step] if labels else None
            item = request_item(row, spec, step, label)
            items.append(item)
            required_all.update(required_variables(row, spec))
        for name in required_all:
            runtime_vars.setdefault(name, "")
        if labels:
            categories[row["Category"]].append({
                "name": f"{row['Test ID']} - reviewed multi-request flow",
                "description": description(row, execution_flags(row), sorted(required_all)),
                "item": items,
            })
            mapping = "; ".join(item["name"] for item in items)
        else:
            categories[row["Category"]].append(items[0])
            mapping = items[0]["name"]
        report_rows.append({
            "row": row, "mapping": mapping, "statuses": [expected_status(row, step) for step in range(len(specs))],
            "flags": execution_flags(row), "required": sorted(required_all),
        })
    collection = {
        "info": {
            "_postman_id": "b4a0b818-b6cd-4ed4-9fa3-23127261000a",
            "name": "Pool A - Forgot Password / Reset Password Reviewed Tests",
            "description": "Generated only from the final reviewed Pool A CSV. Missing runtime fixtures block requests before transmission. Collection-level scripts inject X-Student-Id and log console evidence.",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "event": [{
            "listen": "prerequest",
            "script": {"type": "text/javascript", "exec": [
                "var resolvedStudentId = pm.variables.replaceIn('{{studentId}}');",
                "pm.request.headers.upsert({ key: 'X-Student-Id', value: resolvedStudentId });",
                "console.log('[Pool A evidence] X-Student-Id injected from {{studentId}}:', resolvedStudentId, 'request=' + pm.info.requestName);",
            ]},
        }],
        "variable": [{"key": key, "value": value, "type": "string"} for key, value in sorted(runtime_vars.items())],
        "item": [{"name": category, "item": categories[category]} for category in categories],
    }
    return collection, report_rows


def status_oracle_label(test_id, step, status):
    if test_id == "API-078" and step == 0:
        return "any 4xx (415 human/external expectation; safe 400 acceptable)"
    return str(status) if status is not None else "none (reviewed manual/conditional oracle)"


def load_state(collection_hash=None):
    if not STATE_PATH.exists():
        return {}
    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    if collection_hash and state.get("collectionSha256") != collection_hash:
        return {}
    return state


def save_state(state):
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def generate():
    rows = load_rows()
    collection, _ = build_collection(rows)
    serialized = json.dumps(collection, ensure_ascii=False, indent=2) + "\n"
    serialized_bytes = serialized.encode("utf-8")
    new_hash = hashlib.sha256(serialized_bytes).hexdigest().upper()
    old_state = load_state()
    OUT_PATH.write_bytes(serialized_bytes)
    if old_state.get("collectionSha256") == new_hash:
        state = old_state
    else:
        state = {"collectionSha256": new_hash, "generatedAt": now_gmt7()}
    save_state(state)
    print(f"GENERATED: 82 logical test IDs; collection SHA-256 {new_hash}")


def walk_requests(items):
    for item in items:
        if "request" in item:
            yield item
        yield from walk_requests(item.get("item", []))


def static_validate():
    rows = load_rows()
    collection = json.loads(OUT_PATH.read_text(encoding="utf-8"))
    requests = list(walk_requests(collection.get("item", [])))
    by_id = {}
    for item in requests:
        match = re.match(r"(API-\d{3})\b", item.get("name", ""))
        if not match:
            raise RuntimeError(f"Generated request lacks a logical Test ID: {item.get('name')}")
        by_id.setdefault(match.group(1), []).append(item)
    expected_ids = [row["Test ID"] for row in rows]
    if set(by_id) != set(expected_ids):
        raise RuntimeError(f"Logical ID mismatch; missing={sorted(set(expected_ids)-set(by_id))}, unexpected={sorted(set(by_id)-set(expected_ids))}")
    expected_counts = {test_id: len(labels) for test_id, labels in FLOW_LABELS.items()}
    for test_id in expected_ids:
        expected = expected_counts.get(test_id, 1)
        if len(by_id[test_id]) != expected:
            raise RuntimeError(f"{test_id}: expected {expected} request(s), found {len(by_id[test_id])}")
    defined = {variable["key"]: variable.get("value", "") for variable in collection.get("variable", [])}
    referenced = template_variables(json.dumps(collection, ensure_ascii=False))
    undefined = sorted(referenced - set(defined))
    if undefined:
        raise RuntimeError(f"Undefined Postman variables: {undefined}")
    for row in rows:
        expected_specs = request_specs(row)
        actual_items = by_id[row["Test ID"]]
        for index, (expected, actual) in enumerate(zip(expected_specs, actual_items), start=1):
            request = actual["request"]
            if request["body"]["raw"] != expected["raw"]:
                raise RuntimeError(f"{row['Test ID']} step {index}: request body differs from reviewed CSV representation")
            actual_headers = [(h["key"].lower(), h["value"]) for h in request.get("header", [])]
            expected_headers = [(h["key"].lower(), h["value"]) for h in expected["headers"]]
            if actual_headers != expected_headers:
                raise RuntimeError(f"{row['Test ID']} step {index}: request headers differ from reviewed CSV representation")
            required = required_variables(row, expected)
            empty_references = sorted(name for name in template_variables(expected["raw"] + json.dumps(expected["headers"])) if not defined.get(name))
            if any(name not in required for name in empty_references):
                raise RuntimeError(f"{row['Test ID']} step {index}: empty referenced variable is not blocked by the request fixture gate")
            if row["Test ID"] not in NO_SERVER_FIXTURE_IDS and fixture_ready_variable(row["Test ID"]) not in required:
                raise RuntimeError(f"{row['Test ID']} step {index}: server-side fixture readiness gate is missing")
    # Independent check for all 36 structured Domain rows. This deliberately does
    # not call request_specs() or structured_input(), so a shared parser defect
    # cannot make generation and validation agree on the same wrong wrapper body.
    independently_checked = 0
    for row in rows:
        try:
            source = json.loads(row["Request Input"])
        except json.JSONDecodeError:
            continue
        if not isinstance(source, dict) or not ({"Headers", "Body", "Raw Body"} & set(source)):
            continue
        independently_checked += 1
        actual_request = by_id[row["Test ID"]][0]["request"]
        source_headers = source.get("Headers", {})
        independent_headers = [(str(key).lower(), str(value)) for key, value in source_headers.items()]
        actual_headers = [(header["key"].lower(), header["value"]) for header in actual_request.get("header", [])]
        if actual_headers != independent_headers:
            raise RuntimeError(f"{row['Test ID']}: independent structured-header assertion failed")
        if "Raw Body" in source:
            independent_body = source["Raw Body"]
        elif "Body" in source:
            independent_body = json.dumps(source["Body"], ensure_ascii=False, separators=(",", ":"))
        else:
            independent_body = ""
        independent_body = re.sub(r"<([^>]+)>", lambda match: "{{" + variable_name(match.group(1)) + "}}", independent_body)
        if actual_request["body"]["raw"] != independent_body:
            raise RuntimeError(f"{row['Test ID']}: independent structured-body assertion failed")
        if actual_request["body"]["raw"] == row["Request Input"]:
            raise RuntimeError(f"{row['Test ID']}: metadata wrapper was transmitted as the request body")
    if independently_checked != 36:
        raise RuntimeError(f"Expected 36 independently checked structured rows, found {independently_checked}")
    collection_hash = sha256(OUT_PATH)
    state = load_state(collection_hash)
    state.update({
        "collectionSha256": collection_hash,
        "static": {
            "status": "PASS", "validatedAt": now_gmt7(), "logicalTestIds": len(by_id),
            "generatedRequests": len(requests), "multiRequestFlows": {key: len(value) for key, value in FLOW_LABELS.items()},
            "undefinedVariables": [], "requestBodyMismatches": [], "unexpectedOrMissingTestIds": [],
            "independentStructuredMappings": independently_checked,
        },
    })
    save_state(state)
    print(f"STATIC PASS: 82 logical IDs, {len(requests)} requests, 6 reviewed multi-request flows, 36 independently verified structured mappings, 0 undefined variables, 0 body/header mismatches")


def schema_validate(schema_path):
    try:
        import jsonschema
    except ImportError as error:
        raise RuntimeError("Python package jsonschema is required for full schema validation") from error
    collection = json.loads(OUT_PATH.read_text(encoding="utf-8"))
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    if "collection/v2.1" not in collection.get("info", {}).get("schema", ""):
        raise RuntimeError("Collection does not declare Postman Collection v2.1")
    validator = jsonschema.validators.validator_for(schema)
    validator.check_schema(schema)
    errors = sorted(validator(schema).iter_errors(collection), key=lambda item: list(item.absolute_path))
    if errors:
        details = "; ".join(f"/{'/'.join(map(str, error.absolute_path))}: {error.message}" for error in errors)
        raise RuntimeError("Full Postman v2.1 schema validation failed: " + details)
    collection_hash = sha256(OUT_PATH)
    state = load_state(collection_hash)
    state.update({
        "collectionSha256": collection_hash,
        "schema": {"status": "PASS", "validatedAt": now_gmt7(), "schemaPath": str(schema_path.relative_to(ROOT)).replace("\\", "/")},
    })
    save_state(state)
    print("SCHEMA PASS: collection conforms to the full supplied Postman Collection v2.1 schema")


class CompatibilityHandler(BaseHTTPRequestHandler):
    captured = []

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8")
        self.__class__.captured.append({"path": self.path, "studentId": self.headers.get("X-Student-Id"), "body": body})
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b"{}")

    def log_message(self, *args):
        return


def newman_validate(command):
    collection = json.loads(OUT_PATH.read_text(encoding="utf-8"))
    api001 = next(item for item in walk_requests(collection["item"]) if item["name"].startswith("API-001 "))
    CompatibilityHandler.captured = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), CompatibilityHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    args = command + [
        "run", str(OUT_PATH), "--folder", api001["name"], "--env-var", f"baseUrl=http://127.0.0.1:{port}",
        "--env-var", "fixtureReadyApi001=true", "--reporters", "cli",
    ]
    try:
        result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
    if result.returncode != 0:
        raise RuntimeError("Newman representative compatibility run failed:\n" + result.stdout + "\n" + result.stderr)
    if len(CompatibilityHandler.captured) != 1:
        raise RuntimeError(f"Newman compatibility server expected 1 request, captured {len(CompatibilityHandler.captured)}")
    captured = CompatibilityHandler.captured[0]
    if captured["studentId"] != "23127261":
        raise RuntimeError(f"Newman did not inject expected X-Student-Id; captured {captured['studentId']!r}")
    if captured["body"] != api001["request"]["body"]["raw"]:
        raise RuntimeError("Newman representative request body differed from the generated collection")
    version_result = subprocess.run(command + ["--version"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    version = version_result.stdout.strip() if version_result.returncode == 0 else "unknown"
    collection_hash = sha256(OUT_PATH)
    state = load_state(collection_hash)
    state.update({
        "collectionSha256": collection_hash,
        "newman": {
            "status": "PASS", "validatedAt": now_gmt7(), "version": version,
            "scope": "Representative API-001 compatibility run against a local mock; not full-suite functional SUT execution",
            "requestsExecuted": 1, "sutExecuted": False, "studentIdHeaderCaptured": captured["studentId"],
        },
    })
    save_state(state)
    print(f"NEWMAN PASS: {version}; representative API-001 local-mock run only; real SUT not executed")


def render_report():
    rows = load_rows()
    _, report_rows = build_collection(rows)
    collection_hash = sha256(OUT_PATH)
    state = load_state(collection_hash)
    missing = [name for name in ("static", "schema", "newman") if state.get(name, {}).get("status") != "PASS"]
    if missing:
        raise RuntimeError(f"Cannot finalize conversion report; current collection lacks passing validation stages: {missing}")
    lines = [
        "# Pool A Postman Conversion Report", "", "## Source and conversion constraints", "",
        f"- Source CSV: `test-cases/a-forgot-password.csv` ({len(rows)} reviewed rows)",
        "- API specification: `reference/api_specification.md`",
        "- No logical test cases were added, removed, merged, redesigned, or renumbered. Source traceability alone was corrected for human-authored IDs API-077 through API-082.",
        "- Ordinary rows map to one request; the six explicitly multi-request rows map to named flow folders with two requests each.",
        "- Structured `Headers`, `Body`, and `Raw Body` inputs are mapped to HTTP headers and raw payloads; metadata wrappers are never transmitted.",
        "- `X-Student-Id` is injected by the collection-level pre-request script from `{{studentId}}` (`23127261`) and logged to the Postman/Newman console.",
        "- Empty required fixture variables and unconfirmed server-state fixtures throw `BLOCKED / NOT EXECUTABLE` in the request pre-request script before transmission.",
        "", "## Traceability, fixtures, and oracle coverage", "",
        "| Test ID | Category | Generated request(s) | Automated status oracle(s) | Required runtime fixtures | Execution / oracle classification |",
        "|---|---|---|---|---|---|",
    ]
    escape = lambda value: value.replace("|", "\\|").replace("\r", " ").replace("\n", "<br>")
    for entry in report_rows:
        row = entry["row"]
        statuses = ", ".join(status_oracle_label(row["Test ID"], step, value) for step, value in enumerate(entry["statuses"]))
        lines.append(f"| {row['Test ID']} | {row['Category']} | {escape(entry['mapping'])} | {statuses} | {escape('; '.join(entry['required']) if entry['required'] else 'None')} | {escape('; '.join(entry['flags']) if entry['flags'] else 'FULLY AUTOMATED REVIEWED HTTP ORACLE')} |")
    lines.extend([
        "", "## Automated and manual oracle policy", "",
        "- Explicit HTTP statuses are asserted when unambiguous, but status assertions are not presented as complete when the reviewed result includes additional observable state or behavior.",
        "- API-078 step 1 accepts only a `4xx` client-error status (`400`–`499`). `415 Unsupported Media Type` remains the preferred human/external HTTP expectation rather than a specification requirement; any safe `4xx`, including `400 Bad Request`, is acceptable when the same-OTP JSON retry succeeds.",
        "- API-076 automatically compares the two responses' status, Content-Type, redirect/no-redirect behavior, representation type, and normalized JSON or exact non-JSON body. Only fields predeclared in `api076NondeterministicFields` are removed. Password state, token leakage, and account-metadata disclosure still require the reviewed external/manual oracle.",
        "- Cases labeled `PARTIALLY AUTOMATED / MANUAL ORACLE REQUIRED` retain their full reviewed result in request descriptions; no response-body, persistence, timing, password-state, OTP-state, database, concurrency, or rate-limit assertion is invented.",
        "- API-075 is a single request template, not an automated repeated-guess loop. It remains blocked until an authoritative abuse-control limit is supplied and then requires manual or data-driven repeated execution through that exact configured trigger. API-025, API-065, and API-072 remain blocked until the real expiry point is configured or objectively observed.",
        "", "## Reproducible validation workflow", "",
        "The generator does not rewrite this report during `generate`. Results are keyed to the collection SHA-256 in `postman/pool-a-validation-results.json`, so rerunning deterministic generation preserves successful results for the identical collection. The final report is written only after all gates pass:", "",
        "```powershell",
        "python -m pip install -r postman/requirements-validation.txt",
        "python postman/generate_pool_a.py generate",
        "python postman/generate_pool_a.py validate-static",
        "python postman/generate_pool_a.py validate-schema --schema postman/postman-v2.1.0-schema.json",
        "python postman/generate_pool_a.py validate-newman --newman-command newman",
        "python postman/generate_pool_a.py report",
        "```", "",
        "## Validation results", "",
        f"- Collection SHA-256: `{collection_hash}`",
        f"- Deterministic whole-collection static validation: **PASS** ({state['static']['validatedAt']}). Verified 82 logical IDs, {state['static']['generatedRequests']} generated requests, all six expected two-request flows, no unexpected/missing IDs, no undefined variables, and no request body/header mismatches against the reviewed CSV representation. A separate validation path independently checked all {state['static']['independentStructuredMappings']} structured `Headers`/`Body`/`Raw Body` rows without using the generator's `request_specs()` mapping.",
        f"- Full supplied Postman Collection v2.1 schema validation: **PASS** ({state['schema']['validatedAt']}) using `{state['schema']['schemaPath']}`.",
        f"- Newman {state['newman']['version']} structural/script compatibility: **PASS** ({state['newman']['validatedAt']}). One representative API-001 request ran against a local mock; collection-level header injection, fixture gating, request serialization, console scripting, and the status assertion executed successfully.",
        "- Actual SUT execution: **NOT PERFORMED**. The Newman compatibility result does not claim that the full 82-case suite was functionally executed or that any SUT behavior passed.",
    ])
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("REPORT FINALIZED: all structural/static/schema/Newman compatibility gates PASS; real SUT not executed")


def main():
    parser = argparse.ArgumentParser(description="Generate and reproducibly validate the reviewed Pool A Postman collection")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("generate")
    subparsers.add_parser("validate-static")
    schema_parser = subparsers.add_parser("validate-schema")
    schema_parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA_PATH)
    newman_parser = subparsers.add_parser("validate-newman")
    newman_parser.add_argument("--newman-command", nargs="+", required=True, help="Newman executable command, e.g. newman or pnpm dlx newman")
    subparsers.add_parser("report")
    args = parser.parse_args()
    if args.command == "generate":
        generate()
    elif args.command == "validate-static":
        static_validate()
    elif args.command == "validate-schema":
        schema_validate(args.schema.resolve())
    elif args.command == "validate-newman":
        newman_validate(args.newman_command)
    elif args.command == "report":
        render_report()


if __name__ == "__main__":
    main()
