# Postman Collection v2.1 validation

Use this procedure whenever finalizing a generated collection.

## Required invariant

The generated JSON must validate against the complete official Postman Collection Format v2.1.0 JSON Schema. Do not treat these weaker checks as substitutes:

- JSON parsing succeeds.
- `info.schema` contains a v2.1 URL.
- Required top-level keys happen to be present.
- Postman imports the file without an obvious error.

## Schema source

Use the official Postman Collection Format v2.1.0 schema. The current canonical URI documented by Postman is:

`https://schema.postman.com/json/collection/v2.1.0/collection.json`

Older exported v2.1 collections may declare:

`https://schema.getpostman.com/json/collection/v2.1.0/collection.json`

The declaration identifies the format; validation still requires applying the full schema document to the generated collection.

Prefer a trusted local copy when one is already available. Otherwise retrieve the official schema during execution if network access is allowed. Do not silently downgrade to partial validation if the schema cannot be obtained; report that full schema validation could not be completed.

## Deterministic helper

After obtaining the official schema as a local file, run:

```bash
python scripts/validate_postman_collection.py \
  <collection.json> \
  <postman-v2.1.0-schema.json>
```

The helper:

- parses both JSON documents,
- verifies the collection declares a Postman v2.1 schema URI,
- selects the validator appropriate for the schema document,
- validates the entire collection,
- prints every schema error with its JSON path,
- exits non-zero on any schema error.

A successful exit is the schema-validation gate before `collection_output_path` is finalized.

## Fixing validation failures

Repair the generated Postman structure rather than weakening or editing the schema. Common causes include unsupported custom fields, incorrectly shaped auth objects, malformed URL/body structures, and misplaced script/event properties.

After each repair, rerun full schema validation until it passes, then perform the separate Newman-compatibility check.
