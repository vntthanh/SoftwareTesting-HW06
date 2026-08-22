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

# OTP values in these cases are valid baseline data rather than the tested
# dimension. Each independent case obtains a fresh value at runtime.
RUNTIME_OTP_VARIABLES = {
    "API-001": ["otpApi001"],
    "API-004": ["otpApi004"], "API-005": ["otpApi005"], "API-006": ["otpApi006"],
    "API-009": ["otpApi009AsNumber"],
    "API-015": ["otpIssuedForAccountA"],
    "API-016": ["otpApi016"], "API-017": ["otpApi017"], "API-018": ["otpApi018"],
    "API-019": ["otpApi019"], "API-020": ["otpApi020"], "API-021": ["otpApi021"],
    "API-022": ["otpApi022"], "API-023": ["otpApi023"], "API-024": ["otpApi024"],
    "API-026": ["sameOTPAlreadyUsed"], "API-027": ["otpApi027"],
    "API-030": ["otpApi030"], "API-031": ["otpApi031"],
    "API-033": ["otpApi033"], "API-034": ["otpApi034"], "API-035": ["otpApi035"],
    "API-036": ["otpApi036"], "API-037": ["otpApi037"],
    "API-044": ["otpApi044AsNumber"],
    "API-046": ["otpApi046"], "API-047": ["otpApi047"], "API-048": ["otpApi048"],
    "API-049": ["otpApi049"], "API-050": ["otpApi050"], "API-051": ["otpApi051"],
    "API-052": ["otpApi052"], "API-053": ["otpApi053"], "API-054": ["otpApi054"],
    "API-055": ["otpApi055"], "API-056": ["otpApi056"], "API-057": ["otpApi057"],
    "API-058": ["otpApi058"], "API-059": ["otpApi059"], "API-060": ["otpApi060"],
    "API-061": ["otpApi061"], "API-062": ["otpApi062"],
    "API-063": ["otpGeneratedForAccountA"], "API-064": ["otpGeneratedForAccountA"],
    "API-066": ["sameOTPAlreadyUsedByAccountA"],
    "API-067": ["unexpiredUnusedOTPGeneratedForAccountA"],
    "API-068": ["validUnexpiredUnused6DigitOtpForEmail"], "API-069": ["otpApi069"],
    "API-070": ["validUnexpiredUnused6DigitOtpForEmail"],
    "API-071": ["validUnexpiredUnusedOtpIssuedForEmailA"],
    "API-073": ["previouslySuccessfullyUsedOtp"],
    "API-078": ["sameValidOTP", "sameValidOTP"],
    "API-079": [None, "sameValidOTP"],
    "API-080": ["sameValidOTP", "sameValidOTP"],
    "API-081": ["accountAValidOTP", "accountBValidOTP"],
    "API-082": ["validOTP"],
}

OTP_FIXTURE_EMAILS = {
    **{test_id: "test@domain.com" for test_id in {
        "API-001", "API-004", "API-005", "API-006", "API-009", "API-016", "API-017", "API-018",
        "API-019", "API-020", "API-021", "API-022", "API-023", "API-024", "API-026",
        "API-027", "API-030", "API-031", "API-033", "API-034", "API-035", "API-036",
        "API-037", "API-044", "API-046", "API-047", "API-048", "API-049", "API-050", "API-051",
        "API-052", "API-053", "API-054", "API-055", "API-056", "API-057", "API-058",
        "API-059", "API-060", "API-061", "API-062",
    }},
    "API-015": "account-a@domain.com",
    "API-063": "account-a@domain.com", "API-064": "account-a@domain.com",
    "API-066": "account-a@domain.com", "API-067": "account-a@domain.com",
    "API-068": "{{registeredEmail}}", "API-069": "{{registeredEmail}}",
    "API-070": "{{registeredEmail}}", "API-071": "{{registeredEmailA}}",
    "API-073": "{{sameRegisteredEmail}}",
    "API-078": "{{registeredEmail}}", "API-079": "{{registeredEmail}}",
    "API-080": "{{registeredEmail}}", "API-082": "{{registeredEmail}}",
}

REPLAY_SETUP_PASSWORDS = {
    "API-026": "FixtureConsumed1!", "API-066": "FixtureConsumed2!", "API-073": "FixtureConsumed3!",
}

NUMERIC_OTP_IDS = {"API-009", "API-044"}

# These cases only need a registered-account baseline. The intentionally invalid
# OTP literals/types/omissions in their reset requests must remain unchanged.
REGISTRATION_FIXTURE_EMAILS = {
    **{test_id: "test@domain.com" for test_id in {
        "API-007", "API-008", "API-010", "API-011", "API-012",
        "API-014", "API-038", "API-039", "API-040", "API-041", "API-042",
        "API-043", "API-045",
    }},
    "API-074": "{{registeredEmail}}",
}

FORBIDDEN_ISSUED_OTPS = {"API-014": "654321", "API-045": "654321"}

# Cross-account fixtures are ready only after the secondary registered account
# is also objectively established through forgot-password. API-081 additionally
# preserves Account B's issued OTP for its second flow request.
SECONDARY_OTP_FIXTURES = {
    "API-015": {"email": "account-b@domain.com"},
    "API-031": {"email": "other@domain.com"},
    "API-064": {"email": "account-b@domain.com"},
    "API-071": {"email": "{{registeredEmailB}}"},
    "API-081": {"email": "{{accountBEmail}}", "otp": "accountBValidOTP"},
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
        otp_vars = RUNTIME_OTP_VARIABLES.get(test_id, [])
        otp_var = otp_vars[0] if otp_vars else None
        if otp_var and structured["raw"]:
            if test_id in NUMERIC_OTP_IDS and "{{" not in structured["raw"]:
                structured["raw"] = re.sub(
                    r'("resetToken"\s*:\s*)123456',
                    r'\1{{' + otp_var + '}}', structured["raw"], count=1,
                )
            elif '"resetToken":"{{' not in structured["raw"]:
                structured["raw"] = re.sub(
                    r'("resetToken"\s*:\s*)"123456"',
                    r'\1"{{' + otp_var + '}}"', structured["raw"], count=1,
                )
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
        otp_vars = RUNTIME_OTP_VARIABLES.get(test_id, [])
        otp_var = otp_vars[step] if step < len(otp_vars) else None
        if otp_var and raw:
            if test_id == "API-080" and step == 0:
                raw = raw.replace("{{validOTP}}", "{{sameValidOTP}}")
            elif test_id in NUMERIC_OTP_IDS and "{{" not in raw:
                raw = re.sub(r'("resetToken"\s*:\s*)123456', r'\1{{' + otp_var + '}}', raw, count=1)
            elif '"resetToken":"{{' not in raw:
                raw = re.sub(r'("resetToken"\s*:\s*)"123456"', r'\1"{{' + otp_var + '}}"', raw, count=1)
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
        flags.extend([
            "TRUE CONCURRENT HARNESS REQUIRED",
            "BLOCKED / NOT EXECUTABLE IN SEQUENTIAL POSTMAN / NEWMAN RUNS",
        ])
    if test_id in RUNTIME_OTP_VARIABLES or test_id in REGISTRATION_FIXTURE_EMAILS:
        flags.append("AUTOMATED FORGOT-PASSWORD FIXTURE")
    if test_id in REPLAY_SETUP_PASSWORDS:
        flags.append("AUTOMATED OTP-CONSUMPTION FIXTURE")
    if test_id == "API-013":
        flags.append("BLOCKED / NOT EXECUTABLE UNTIL EXACT CONTROLLED OTP 012345 IS OBJECTIVELY ISSUED")
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
    setup_email = OTP_FIXTURE_EMAILS.get(row["Test ID"]) or REGISTRATION_FIXTURE_EMAILS.get(row["Test ID"])
    if setup_email:
        required.update(template_variables(setup_email))
    secondary = SECONDARY_OTP_FIXTURES.get(row["Test ID"])
    if secondary:
        required.update(template_variables(secondary["email"]))
    return sorted(required)


def otp_fixture_config(row, step):
    test_id = row["Test ID"]
    otp_vars = RUNTIME_OTP_VARIABLES.get(test_id)
    if otp_vars:
        if test_id in {"API-078", "API-079", "API-080", "API-081"} and step > 0:
            return {"carry": otp_vars[step]}
        otp_var = otp_vars[step] if step < len(otp_vars) else None
        if otp_var is not None:
            email = OTP_FIXTURE_EMAILS.get(test_id)
            if test_id == "API-081":
                email = "{{accountAEmail}}" if step == 0 else "{{accountBEmail}}"
            return {"email": email, "otp": otp_var, "replayPassword": REPLAY_SETUP_PASSWORDS.get(test_id)}
        if test_id == "API-079" and step == 0:
            return {"email": OTP_FIXTURE_EMAILS[test_id], "otp": "sameValidOTP", "replayPassword": None}
    if test_id in REGISTRATION_FIXTURE_EMAILS:
        return {"email": REGISTRATION_FIXTURE_EMAILS[test_id], "otp": "__issued" + test_id.replace("-", ""), "registrationOnly": True}
    return None


def fixture_gate(required):
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


def prerequest_script(row, required, step):
    if not required:
        return None
    test_id = row["Test ID"]
    if test_id == "API-077":
        return [
            "console.error('[API-077 BLOCKED / NOT EXECUTABLE] Postman/Newman collection runs are sequential and cannot establish the reviewed concurrency barrier. Use a true concurrent harness.');",
            "throw new Error('BLOCKED / NOT EXECUTABLE: API-077 requires true concurrent dispatch; sequential Newman execution is not evidence.');",
        ]
    fixture = otp_fixture_config(row, step)
    if fixture and fixture.get("carry"):
        carry = fixture["carry"]
        ready_var = fixture_ready_variable(test_id)
        return [
            f"var carriedOtp = pm.collectionVariables.get('{carry}');",
            f"var carriedReady = pm.collectionVariables.get('{ready_var}');",
            f"if (carriedOtp !== undefined) pm.variables.set('{carry}', carriedOtp);",
            f"if (carriedReady !== undefined) pm.variables.set('{ready_var}', carriedReady);",
            *fixture_gate(required),
        ]
    if not fixture:
        return fixture_gate(required)
    ready_var = fixture_ready_variable(test_id)
    otp_var = fixture["otp"]
    email = fixture["email"]
    value_vars = [name for name in required if not name.startswith("fixtureReady")]
    prerequisite_vars = sorted((set(value_vars) | template_variables(email)) - {otp_var})
    secondary_otp_var = SECONDARY_OTP_FIXTURES.get(test_id, {}).get("otp")
    secondary_clear = ([
        f"pm.collectionVariables.unset('{secondary_otp_var}');",
        f"pm.variables.unset('{secondary_otp_var}');",
    ] if secondary_otp_var else [])
    secondary_block_clear = ([
        f"  pm.collectionVariables.unset('{secondary_otp_var}');",
        f"  pm.variables.unset('{secondary_otp_var}');",
    ] if secondary_otp_var else [])
    numeric_otp_fixture = test_id in NUMERIC_OTP_IDS
    lines = [
        f"var fixtureInputVariables = {json.dumps(prerequisite_vars)};",
        "var missingFixtureInputs = fixtureInputVariables.filter(function (name) { var value = pm.variables.get(name); return value === undefined || value === null || String(value).trim() === '' || /{{.+}}/.test(String(value)); });",
        "if (missingFixtureInputs.length) { throw new Error('BLOCKED / NOT EXECUTABLE: supply fixture input(s): ' + missingFixtureInputs.join(', ')); }",
        f"var fixtureEmail = pm.variables.replaceIn({json.dumps(email)});",
        f"pm.collectionVariables.unset('{ready_var}');",
        f"pm.collectionVariables.unset('{otp_var}');",
        f"pm.variables.unset('{ready_var}');",
        f"pm.variables.unset('{otp_var}');",
        *secondary_clear,
        "function blockFixture(message) {",
        "  console.error('[Pool A BLOCKED / NOT EXECUTABLE] ' + message);",
        f"  pm.collectionVariables.unset('{ready_var}');",
        f"  pm.collectionVariables.unset('{otp_var}');",
        f"  pm.variables.unset('{ready_var}');",
        f"  pm.variables.unset('{otp_var}');",
        *secondary_block_clear,
        "  pm.execution.skipRequest();",
        "}",
        *(["var fixtureOtpAttempt = 0;", "function requestOtpFixture() {", "  fixtureOtpAttempt += 1;"] if numeric_otp_fixture else []),
        "pm.sendRequest({",
        "  url: pm.variables.replaceIn('{{baseUrl}}/api/forgot-password'),",
        "  method: 'POST',",
        "  header: [{ key: 'Content-Type', value: 'application/json' }, { key: 'X-Student-Id', value: pm.variables.replaceIn('{{studentId}}') }],",
        "  body: { mode: 'raw', raw: JSON.stringify({ email: fixtureEmail }), options: { raw: { language: 'json' } } }",
        "}, function (fixtureError, fixtureResponse) {",
        "  if (fixtureError) { blockFixture('forgot-password fixture request failed: ' + fixtureError); return; }",
        "  if (fixtureResponse.code !== 200) { blockFixture('forgot-password fixture returned HTTP ' + fixtureResponse.code); return; }",
        "  var fixtureJson;",
        "  try { fixtureJson = fixtureResponse.json(); } catch (error) { blockFixture('forgot-password fixture did not return JSON'); return; }",
        "  var issuedOtp = fixtureJson && fixtureJson.resetToken;",
        "  if (!/^\\d{6}$/.test(String(issuedOtp || ''))) { blockFixture('forgot-password fixture did not return a six-digit resetToken'); return; }",
    ]
    if numeric_otp_fixture:
        lines.append("  if (String(issuedOtp).charAt(0) === '0') { if (fixtureOtpAttempt < 5) { requestOtpFixture(); return; } blockFixture('issued OTP begins with zero; cannot emit it as a JSON number without changing its value/representation after 5 fixture attempts'); return; }")
    forbidden = FORBIDDEN_ISSUED_OTPS.get(test_id)
    if forbidden:
        lines.append(f"  if (String(issuedOtp) === '{forbidden}') {{ blockFixture('issued OTP collided with intentionally invalid literal {forbidden}; rerun for a fresh OTP'); return; }}")
    replay_password = fixture.get("replayPassword")
    if replay_password:
        lines.extend([
            "  pm.sendRequest({",
            "    url: pm.variables.replaceIn('{{baseUrl}}/api/reset-password'),",
            "    method: 'POST',",
            "    header: [{ key: 'Content-Type', value: 'application/json' }, { key: 'X-Student-Id', value: pm.variables.replaceIn('{{studentId}}') }],",
            f"    body: {{ mode: 'raw', raw: JSON.stringify({{ email: fixtureEmail, resetToken: String(issuedOtp), newPassword: '{replay_password}' }}), options: {{ raw: {{ language: 'json' }} }} }}",
            "  }, function (consumeError, consumeResponse) {",
            "    if (consumeError) { blockFixture('OTP-consumption fixture request failed: ' + consumeError); return; }",
            "    if (consumeResponse.code !== 200) { blockFixture('OTP-consumption fixture returned HTTP ' + consumeResponse.code); return; }",
            f"    pm.collectionVariables.set('{otp_var}', String(issuedOtp));",
            f"    pm.variables.set('{otp_var}', String(issuedOtp));",
            f"    pm.collectionVariables.set('{ready_var}', 'true');",
            f"    pm.variables.set('{ready_var}', 'true');",
            "  });",
        ])
    elif test_id in SECONDARY_OTP_FIXTURES:
        secondary = SECONDARY_OTP_FIXTURES[test_id]
        secondary_email = secondary["email"]
        secondary_otp_var = secondary.get("otp")
        lines.extend([
            f"  var secondaryFixtureEmail = pm.variables.replaceIn({json.dumps(secondary_email)});",
            "  pm.sendRequest({",
            "    url: pm.variables.replaceIn('{{baseUrl}}/api/forgot-password'),",
            "    method: 'POST',",
            "    header: [{ key: 'Content-Type', value: 'application/json' }, { key: 'X-Student-Id', value: pm.variables.replaceIn('{{studentId}}') }],",
            "    body: { mode: 'raw', raw: JSON.stringify({ email: secondaryFixtureEmail }), options: { raw: { language: 'json' } } }",
            "  }, function (secondaryError, secondaryResponse) {",
            "    if (secondaryError) { blockFixture('secondary forgot-password fixture request failed: ' + secondaryError); return; }",
            "    if (secondaryResponse.code !== 200) { blockFixture('secondary forgot-password fixture returned HTTP ' + secondaryResponse.code); return; }",
            "    var secondaryJson;",
            "    try { secondaryJson = secondaryResponse.json(); } catch (error) { blockFixture('secondary forgot-password fixture did not return JSON'); return; }",
            "    var secondaryOtp = secondaryJson && secondaryJson.resetToken;",
            "    if (!/^\\d{6}$/.test(String(secondaryOtp || ''))) { blockFixture('secondary forgot-password fixture did not return a six-digit resetToken'); return; }",
            f"    pm.collectionVariables.set('{otp_var}', String(issuedOtp));",
            f"    pm.variables.set('{otp_var}', String(issuedOtp));",
        ])
        if secondary_otp_var:
            lines.extend([
                f"    pm.collectionVariables.set('{secondary_otp_var}', String(secondaryOtp));",
                f"    pm.variables.set('{secondary_otp_var}', String(secondaryOtp));",
            ])
        lines.extend([
            f"    pm.collectionVariables.set('{ready_var}', 'true');",
            f"    pm.variables.set('{ready_var}', 'true');",
            "  });",
        ])
    else:
        lines.extend([
            f"  pm.collectionVariables.set('{otp_var}', String(issuedOtp));",
            f"  pm.variables.set('{otp_var}', String(issuedOtp));",
            f"  pm.collectionVariables.set('{ready_var}', 'true');",
            f"  pm.variables.set('{ready_var}', 'true');",
        ])
    lines.append("});")
    if numeric_otp_fixture:
        lines.extend(["}", "requestOtpFixture();"])
    return lines


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
        parts.extend(["", "Runtime fixtures (automatically established when supported; otherwise request is blocked until supplied/confirmed):", *[f"- {name}" for name in required]])
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
    pre = prerequest_script(row, required, step)
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
            "description": "Generated only from the final reviewed Pool A CSV. Objectively creatable OTP fixtures are established automatically; unresolved fixtures block requests before transmission. Collection-level scripts inject X-Student-Id and log console evidence.",
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
        otp_vars = RUNTIME_OTP_VARIABLES.get(row["Test ID"], [])
        otp_var = otp_vars[0] if otp_vars else None
        if otp_var and independent_body:
            if row["Test ID"] in NUMERIC_OTP_IDS and "{{" not in independent_body:
                independent_body = re.sub(
                    r'("resetToken"\s*:\s*)123456',
                    r'\1{{' + otp_var + '}}', independent_body, count=1,
                )
            elif '"resetToken":"{{' not in independent_body:
                independent_body = re.sub(
                    r'("resetToken"\s*:\s*)"123456"',
                    r'\1"{{' + otp_var + '}}"', independent_body, count=1,
                )
        if actual_request["body"]["raw"] != independent_body:
            raise RuntimeError(f"{row['Test ID']}: independent structured-body assertion failed")
        if actual_request["body"]["raw"] == row["Request Input"]:
            raise RuntimeError(f"{row['Test ID']}: metadata wrapper was transmitted as the request body")
    if independently_checked != 36:
        raise RuntimeError(f"Expected 36 independently checked structured rows, found {independently_checked}")
    for row in rows:
        test_id = row["Test ID"]
        items = by_id[test_id]
        if test_id in RUNTIME_OTP_VARIABLES or test_id in REGISTRATION_FIXTURE_EMAILS:
            for step, item in enumerate(items):
                if test_id in {"API-078", "API-079", "API-080", "API-081"} and step == 1:
                    continue
                scripts = "\n".join(
                    line for event in item.get("event", []) if event.get("listen") == "prerequest"
                    for line in event.get("script", {}).get("exec", [])
                )
                if "/api/forgot-password" not in scripts:
                    raise RuntimeError(f"{test_id} step {step + 1}: automatic forgot-password fixture is missing")
                ready_assignment = f"pm.collectionVariables.set('{fixture_ready_variable(test_id)}', 'true')"
                if ready_assignment not in scripts or "fixtureResponse.code !== 200" not in scripts or "resetToken" not in scripts:
                    raise RuntimeError(f"{test_id} step {step + 1}: readiness is not guarded by successful OTP fixture validation")
    for test_id in NUMERIC_OTP_IDS:
        item = by_id[test_id][0]
        otp_var = RUNTIME_OTP_VARIABLES[test_id][0]
        raw = item["request"]["body"]["raw"]
        scripts = "\n".join(item["event"][0]["script"]["exec"])
        if f'"resetToken":{{{{{otp_var}}}}}' not in raw or f'"resetToken":"{{{{{otp_var}}}}}"' in raw:
            raise RuntimeError(f"{test_id}: issued OTP must be emitted as an unquoted JSON number")
        if "fixtureOtpAttempt < 5" not in scripts or "issued OTP begins with zero" not in scripts:
            raise RuntimeError(f"{test_id}: leading-zero OTP regeneration/blocking guard is missing")
    for test_id in {"API-078", "API-079", "API-080"}:
        first, second = by_id[test_id]
        first_scripts = "\n".join(first["event"][0]["script"]["exec"])
        second_scripts = "\n".join(second["event"][0]["script"]["exec"])
        if "/api/forgot-password" not in first_scripts or "/api/forgot-password" in second_scripts:
            raise RuntimeError(f"{test_id}: flow must issue exactly one OTP in step 1 and carry it into step 2")
        first_vars = template_variables(first["request"]["body"]["raw"])
        second_vars = template_variables(second["request"]["body"]["raw"])
        if test_id != "API-079" and "sameValidOTP" not in first_vars:
            raise RuntimeError(f"{test_id}: step 1 does not use the shared runtime OTP")
        if "sameValidOTP" not in second_vars:
            raise RuntimeError(f"{test_id}: step 2 does not reuse the shared runtime OTP")
    api081_first, api081_second = by_id["API-081"]
    api081_first_scripts = "\n".join(api081_first["event"][0]["script"]["exec"])
    api081_second_scripts = "\n".join(api081_second["event"][0]["script"]["exec"])
    if api081_first_scripts.count("/api/forgot-password") != 2 or "/api/forgot-password" in api081_second_scripts:
        raise RuntimeError("API-081 must issue both account OTPs before step 1 and carry Account B's OTP into step 2")
    api077_scripts = "\n".join(
        line for item in by_id["API-077"] for event in item.get("event", [])
        if event.get("listen") == "prerequest" for line in event.get("script", {}).get("exec", [])
    )
    if "requires true concurrent dispatch" not in api077_scripts or "/api/forgot-password" in api077_scripts:
        raise RuntimeError("API-077 must remain blocked in sequential Postman/Newman execution")
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
    forgot_status = 200
    forgot_tokens = {
        "account-a@domain.com": "246810",
        "account-b@domain.com": "135790",
    }
    forgot_token_queue = []
    reset_statuses = []

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8")
        content_type = self.headers.get("Content-Type", "")
        try:
            parsed = json.loads(body) if body else None
        except json.JSONDecodeError:
            parsed = None
        self.__class__.captured.append({
            "path": self.path, "studentId": self.headers.get("X-Student-Id"),
            "contentType": content_type, "body": body,
        })
        if self.path == "/api/forgot-password":
            status = self.__class__.forgot_status
        elif self.__class__.reset_statuses:
            status = self.__class__.reset_statuses.pop(0)
        elif content_type.startswith("text/plain") or not body:
            status = 415 if content_type.startswith("text/plain") else 400
        else:
            status = 400 if isinstance(parsed, dict) and (
                isinstance(parsed.get("newPassword"), dict) or
                isinstance(parsed.get("resetToken"), (int, float))
            ) else 200
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if self.path == "/api/forgot-password":
            email = parsed.get("email") if isinstance(parsed, dict) else None
            issued_otp = (
                self.__class__.forgot_token_queue.pop(0)
                if self.__class__.forgot_token_queue
                else self.__class__.forgot_tokens.get(email, "246810")
            )
            self.wfile.write(json.dumps({"message": "fixture created", "resetToken": issued_otp}).encode("utf-8"))
        else:
            self.wfile.write(b"{}")

    def log_message(self, *args):
        return


def newman_validate(command):
    collection = json.loads(OUT_PATH.read_text(encoding="utf-8"))
    api001 = next(item for item in walk_requests(collection["item"]) if item["name"].startswith("API-001 "))
    api009 = next(item for item in walk_requests(collection["item"]) if item["name"].startswith("API-009 "))
    api026 = next(item for item in walk_requests(collection["item"]) if item["name"].startswith("API-026 "))
    CompatibilityHandler.captured = []
    CompatibilityHandler.forgot_status = 200
    CompatibilityHandler.forgot_token_queue = []
    CompatibilityHandler.reset_statuses = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), CompatibilityHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    args = command + [
        "run", str(OUT_PATH), "--folder", api001["name"], "--env-var", f"baseUrl=http://127.0.0.1:{port}",
        "--reporters", "cli",
    ]
    try:
        result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        if result.returncode != 0:
            raise RuntimeError("Newman representative compatibility run failed:\n" + result.stdout + "\n" + result.stderr)
        if len(CompatibilityHandler.captured) != 2:
            raise RuntimeError(f"Newman compatibility server expected fixture plus tested request, captured {len(CompatibilityHandler.captured)}")
        fixture_capture, captured = CompatibilityHandler.captured
        if fixture_capture["path"] != "/api/forgot-password" or json.loads(fixture_capture["body"]) != {"email": "test@domain.com"}:
            raise RuntimeError("Newman did not establish the API-001 forgot-password fixture correctly")
        if captured["studentId"] != "23127261":
            raise RuntimeError(f"Newman did not inject expected X-Student-Id; captured {captured['studentId']!r}")
        expected_body = api001["request"]["body"]["raw"].replace("{{otpApi001}}", "246810")
        if captured["body"] != expected_body:
            raise RuntimeError("Newman representative request body differed from the generated collection")

        CompatibilityHandler.captured = []
        CompatibilityHandler.forgot_status = 500
        blocked_result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        if len(CompatibilityHandler.captured) != 1 or CompatibilityHandler.captured[0]["path"] != "/api/forgot-password":
            raise RuntimeError("Newman transmitted the tested reset request after fixture establishment failed")

        CompatibilityHandler.forgot_status = 200
        flow_fixture_results = {}
        for test_id, extra_vars in {
            "API-078": ["registeredEmail=test@domain.com"],
            "API-079": ["registeredEmail=test@domain.com"],
            "API-080": ["registeredEmail=test@domain.com"],
            "API-081": ["accountAEmail=account-a@domain.com", "accountBEmail=account-b@domain.com"],
        }.items():
            CompatibilityHandler.captured = []
            CompatibilityHandler.reset_statuses = []
            flow_args = command + [
                "run", str(OUT_PATH), "--folder", f"{test_id} - reviewed multi-request flow",
                "--env-var", f"baseUrl=http://127.0.0.1:{port}", "--reporters", "cli",
            ]
            for value in extra_vars:
                flow_args.extend(["--env-var", value])
            flow_result = subprocess.run(flow_args, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
            if flow_result.returncode != 0:
                raise RuntimeError(f"Newman {test_id} fixture-flow compatibility run failed:\n" + flow_result.stdout + "\n" + flow_result.stderr)
            forgot_requests = [entry for entry in CompatibilityHandler.captured if entry["path"] == "/api/forgot-password"]
            reset_requests = [entry for entry in CompatibilityHandler.captured if entry["path"] == "/api/reset-password"]
            expected_forgot = 2 if test_id == "API-081" else 1
            if len(forgot_requests) != expected_forgot or len(reset_requests) != 2:
                raise RuntimeError(f"{test_id}: unexpected fixture/reset request counts in Newman compatibility run")
            reset_bodies = []
            for entry in reset_requests:
                if not entry["body"]:
                    continue
                parsed = json.loads(entry["body"])
                if isinstance(parsed, dict):
                    reset_bodies.append(parsed)
            reset_otps = [str(parsed["resetToken"]) for parsed in reset_bodies if "resetToken" in parsed]
            if test_id in {"API-078", "API-080"} and reset_otps != ["246810", "246810"]:
                raise RuntimeError(f"{test_id}: both flow requests did not reuse the issued OTP")
            if test_id == "API-079" and reset_otps != ["246810"]:
                raise RuntimeError("API-079: valid retry did not use the OTP issued before the empty-body step")
            if test_id == "API-081":
                forgot_bodies = [json.loads(entry["body"]) for entry in forgot_requests]
                expected_forgot_bodies = [
                    {"email": "account-a@domain.com"},
                    {"email": "account-b@domain.com"},
                ]
                expected_reset_pairs = [
                    ("account-a@domain.com", "246810"),
                    ("account-b@domain.com", "135790"),
                ]
                actual_reset_pairs = [(body.get("email"), str(body.get("resetToken"))) for body in reset_bodies]
                if forgot_bodies != expected_forgot_bodies:
                    raise RuntimeError("API-081: fixture requests did not use Account A then Account B emails")
                if actual_reset_pairs != expected_reset_pairs or len(set(reset_otps)) != 2:
                    raise RuntimeError("API-081: steps did not use distinct account-specific OTPs")
            flow_fixture_results[test_id] = {"forgotRequests": len(forgot_requests), "resetRequests": len(reset_requests)}
            if test_id == "API-081":
                flow_fixture_results[test_id].update({
                    "fixtureEmails": ["account-a@domain.com", "account-b@domain.com"],
                    "distinctAccountOtpsVerified": True,
                })

        CompatibilityHandler.captured = []
        CompatibilityHandler.reset_statuses = []
        CompatibilityHandler.forgot_token_queue = ["012345", "246810"]
        numeric_args = command + [
            "run", str(OUT_PATH), "--folder", api009["name"],
            "--env-var", f"baseUrl=http://127.0.0.1:{port}", "--reporters", "cli",
        ]
        numeric_result = subprocess.run(numeric_args, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        if numeric_result.returncode != 0:
            raise RuntimeError("Newman API-009 numeric-OTP compatibility run failed:\n" + numeric_result.stdout + "\n" + numeric_result.stderr)
        if len(CompatibilityHandler.captured) != 3:
            raise RuntimeError("API-009: expected leading-zero OTP attempt, regenerated OTP attempt, and one tested reset request")
        if [json.loads(entry["body"]) for entry in CompatibilityHandler.captured[:2]] != [
            {"email": "test@domain.com"}, {"email": "test@domain.com"},
        ]:
            raise RuntimeError("API-009: leading-zero regeneration did not repeat the fixture request for the same account")
        numeric_body = json.loads(CompatibilityHandler.captured[2]["body"])
        if numeric_body.get("resetToken") != 246810 or isinstance(numeric_body.get("resetToken"), bool):
            raise RuntimeError("API-009: issued OTP value was not emitted as the same unquoted JSON number")

        replay_args = command + [
            "run", str(OUT_PATH), "--folder", api026["name"],
            "--env-var", f"baseUrl=http://127.0.0.1:{port}", "--reporters", "cli",
        ]
        CompatibilityHandler.captured = []
        CompatibilityHandler.reset_statuses = [200, 400]
        replay_result = subprocess.run(replay_args, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        if replay_result.returncode != 0:
            raise RuntimeError("Newman API-026 consumed/replay compatibility run failed:\n" + replay_result.stdout + "\n" + replay_result.stderr)
        if len(CompatibilityHandler.captured) != 3:
            raise RuntimeError("API-026: expected OTP request, successful setup reset, and tested replay request")
        replay_fixture, consume_capture, replay_capture = CompatibilityHandler.captured
        consume_body = json.loads(consume_capture["body"])
        replay_body = json.loads(replay_capture["body"])
        if json.loads(replay_fixture["body"]) != {"email": "test@domain.com"}:
            raise RuntimeError("API-026: forgot-password fixture used the wrong email")
        if consume_body != {"email": "test@domain.com", "resetToken": "246810", "newPassword": "FixtureConsumed1!"}:
            raise RuntimeError("API-026: setup reset did not consume the issued OTP as specified")
        if replay_body != {"email": "test@domain.com", "resetToken": "246810", "newPassword": "AnotherPassword123!"}:
            raise RuntimeError("API-026: tested replay did not reuse the consumed OTP")

        CompatibilityHandler.captured = []
        CompatibilityHandler.reset_statuses = [500]
        blocked_replay_result = subprocess.run(replay_args, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        if len(CompatibilityHandler.captured) != 2:
            raise RuntimeError("API-026: tested replay request was transmitted after setup reset failure")
        if CompatibilityHandler.captured[0]["path"] != "/api/forgot-password" or CompatibilityHandler.captured[1]["path"] != "/api/reset-password":
            raise RuntimeError("API-026: failed-setup compatibility path captured unexpected requests")
        replay_fixture_results = {
            "successfulSetup": {"forgotRequests": 1, "setupResetRequests": 1, "testedReplayRequests": 1},
            "failedSetup": {"forgotRequests": 1, "setupResetRequests": 1, "testedReplayRequests": 0},
        }
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
    version_result = subprocess.run(command + ["--version"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    version = version_result.stdout.strip() if version_result.returncode == 0 else "unknown"
    collection_hash = sha256(OUT_PATH)
    state = load_state(collection_hash)
    state.update({
        "collectionSha256": collection_hash,
        "newman": {
            "status": "PASS", "validatedAt": now_gmt7(), "version": version,
            "scope": "Local-mock compatibility runs for API-001, API-009, API-026, and fixture flows API-078 through API-081; not full-suite functional SUT execution",
            "requestsExecuted": 11, "mockHttpRequestsCaptured": 24, "newmanRuns": 9,
            "sutExecuted": False, "studentIdHeaderCaptured": captured["studentId"],
            "automaticOtpFixtureVerified": True, "failedFixtureBlocksTestedRequest": True,
            "numericIssuedOtpVerified": {
                "testId": "API-009", "leadingZeroOtpRegenerated": "012345",
                "issuedString": "246810", "sentJsonNumber": 246810,
            },
            "consumedReplayFixtureVerified": replay_fixture_results,
            "fixtureFlowsVerified": flow_fixture_results,
        },
    })
    save_state(state)
    print(f"NEWMAN PASS: {version}; API-001/API-009/API-026 and fixture-flow local-mock runs only; real SUT not executed")


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
        "- Valid OTP baseline values are generated immediately before each independent case through `POST /api/forgot-password`; intentional API-078/API-079/API-080 flows issue once in step 1 and reuse the same OTP in step 2.",
        "- API-009 and API-044 preserve a freshly issued OTP's decimal value while emitting it as an unquoted JSON number. Leading-zero OTPs are regenerated up to five fixture attempts, then the case is blocked rather than changing the value.",
        "- Cross-account cases validate both registered accounts before readiness; API-081 issues both account OTPs before step 1 and carries Account B's untouched OTP into step 2.",
        "- A fixture's `fixtureReadyApiXXX` flag is cleared before setup and set to `true` only after a 200 forgot-password response returns a six-decimal-digit `resetToken`; replay fixtures additionally require a successful first reset.",
        "- Empty required fixture inputs and fixtures that cannot be objectively established throw `BLOCKED / NOT EXECUTABLE` before the tested request is transmitted.",
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
        "- Literal invalid OTP values remain unchanged whenever token omission, type, shape, issuance, or other invalid-token behavior is the tested dimension.",
        "- API-026/API-066/API-073 readiness is set only after the setup reset successfully consumes the issued OTP; a failed setup reset skips the tested replay request.",
        "- API-077 requests are deliberately blocked in collection/Newman runs because those runners dispatch the folder sequentially; only a true concurrent harness with a synchronization barrier can execute the reviewed race case.",
        "- API-075 is a single request template, not an automated repeated-guess loop. It remains blocked until an authoritative abuse-control limit is supplied and then requires manual or data-driven repeated execution through that exact configured trigger. API-025, API-065, and API-072 remain blocked until the real expiry point is configured or objectively observed. API-013 remains blocked until the exact controlled OTP `012345` is objectively issued.",
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
        f"- Newman {state['newman']['version']} structural/script compatibility: **PASS** ({state['newman']['validatedAt']}). Local-mock runs verified API-001 setup handling, API-009 numeric serialization, API-026 consumed/replay setup success and failure, one-OTP reuse across API-078/API-079/API-080, and distinct Account A/Account B OTPs for API-081; readiness timing, failed-fixture request skipping, headers, serialization, scripts, and status assertions executed successfully.",
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
