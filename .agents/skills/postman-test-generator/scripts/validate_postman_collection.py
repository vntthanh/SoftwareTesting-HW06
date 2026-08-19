#!/usr/bin/env python3
"""Validate a Postman collection against a supplied full v2.1 JSON Schema."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    import jsonschema
    from jsonschema.validators import validator_for
except ImportError as exc:  # pragma: no cover - environment dependent
    print(
        "ERROR: Python package 'jsonschema' is required for full Postman schema validation.",
        file=sys.stderr,
    )
    raise SystemExit(2) from exc


V21_SCHEMA_URIS = {
    "https://schema.postman.com/json/collection/v2.1.0/collection.json",
    "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
}


def load_json(path: Path, label: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"ERROR: {label} file not found: {path}", file=sys.stderr)
        raise SystemExit(2)
    except json.JSONDecodeError as exc:
        print(
            f"ERROR: {label} is not valid JSON at line {exc.lineno}, "
            f"column {exc.colno}: {exc.msg}",
            file=sys.stderr,
        )
        raise SystemExit(2)


def json_path(parts: list[Any]) -> str:
    if not parts:
        return "$"
    result = "$"
    for part in parts:
        if isinstance(part, int):
            result += f"[{part}]"
        else:
            key = str(part).replace("\\", "\\\\").replace("'", "\\'")
            result += f"['{key}']"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a Postman Collection v2.1 JSON file against the full supplied schema."
    )
    parser.add_argument("collection", type=Path, help="Generated Postman collection JSON")
    parser.add_argument("schema", type=Path, help="Official Postman v2.1.0 JSON Schema file")
    args = parser.parse_args()

    collection = load_json(args.collection, "Collection")
    schema = load_json(args.schema, "Schema")

    declared_uri = None
    if isinstance(collection, dict):
        info = collection.get("info")
        if isinstance(info, dict):
            declared_uri = info.get("schema")

    if declared_uri not in V21_SCHEMA_URIS:
        print(
            "ERROR: collection info.schema does not declare Postman Collection v2.1.0. "
            f"Found: {declared_uri!r}",
            file=sys.stderr,
        )
        return 1

    try:
        Validator = validator_for(schema)
        Validator.check_schema(schema)
        validator = Validator(schema)
    except jsonschema.exceptions.SchemaError as exc:
        print(f"ERROR: supplied Postman schema is invalid: {exc.message}", file=sys.stderr)
        return 2

    errors = sorted(
        validator.iter_errors(collection),
        key=lambda error: list(error.absolute_path),
    )

    if errors:
        print(f"INVALID: {len(errors)} Postman v2.1 schema error(s) found.", file=sys.stderr)
        for index, error in enumerate(errors, start=1):
            path = json_path(list(error.absolute_path))
            print(f"{index}. {path}: {error.message}", file=sys.stderr)
        return 1

    print("VALID: collection conforms to the supplied Postman Collection v2.1 schema.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
