from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parent.parent
CANONICAL_SCHEMA = ROOT / "schemas" / "career-profile.v0.1.schema.json"
TRANSPORT_SCHEMA = ROOT / "schemas" / "career-profile.transport.v0.1.schema.json"
CANONICAL_EXAMPLE = ROOT / "examples" / "career-profile.synthetic.jsonld"
TRANSPORT_EXAMPLE = ROOT / "examples" / "career-profile.transport.synthetic.json"
CONVERTER = ROOT / "scripts" / "convert-profile.mjs"


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def json_pointer(parts: Iterable[object]) -> str:
    encoded = [str(part).replace("~", "~0").replace("/", "~1") for part in parts]
    return "/" + "/".join(encoded)


def validate_schema(instance: Any, schema: dict[str, Any], label: str) -> None:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(instance), key=lambda error: list(error.path))
    if errors:
        formatted = "\n".join(
            f"  {json_pointer(error.absolute_path)}: {error.message}" for error in errors
        )
        raise AssertionError(f"{label} failed JSON Schema validation:\n{formatted}")


def walk(value: Any) -> Iterable[tuple[tuple[object, ...], Any]]:
    stack: list[tuple[tuple[object, ...], Any]] = [((), value)]
    while stack:
        path, current = stack.pop()
        yield path, current
        if isinstance(current, dict):
            for key, child in reversed(list(current.items())):
                stack.append(((*path, key), child))
        elif isinstance(current, list):
            for index in range(len(current) - 1, -1, -1):
                stack.append(((*path, index), current[index]))


def validate_semantics(profile: dict[str, Any]) -> None:
    ids: dict[str, str] = {}
    for path, value in walk(profile):
        if isinstance(value, dict) and isinstance(value.get("id"), str):
            identifier = value["id"]
            pointer = json_pointer((*path, "id"))
            if identifier in ids:
                raise AssertionError(
                    f"Duplicate id {identifier!r} at {pointer}; first used at {ids[identifier]}"
                )
            ids[identifier] = pointer

    source_ids = {document["id"] for document in profile["sourceDocuments"]}
    known_refs = set(ids) | {profile["profileId"]}

    for path, value in walk(profile):
        if not isinstance(value, dict):
            continue

        source = value.get("source")
        if isinstance(source, dict):
            document_id = source["documentId"]
            if document_id not in source_ids:
                raise AssertionError(
                    f"Unknown provenance document {document_id!r} at "
                    f"{json_pointer((*path, 'source', 'documentId'))}"
                )
            start, end = source["charStart"], source["charEnd"]
            if (start is None) != (end is None):
                raise AssertionError(
                    f"Character offsets must both be set or both be null at {json_pointer(path)}"
                )
            if start is not None and end <= start:
                raise AssertionError(
                    f"charEnd must be greater than charStart at {json_pointer(path)}"
                )

        for key, candidate in value.items():
            if key in {"documentId", "id", "profileId"}:
                continue
            refs: list[str] = []
            if key.endswith("Ref") and isinstance(candidate, str):
                refs = [candidate]
            elif key.endswith("Refs") and isinstance(candidate, list):
                refs = [item for item in candidate if isinstance(item, str)]
            elif key == "targetRef" and isinstance(candidate, str):
                refs = [candidate]

            for reference in refs:
                if reference.startswith(("credential:", "artifact:")):
                    continue
                if reference not in known_refs:
                    raise AssertionError(
                        f"Unresolved reference {reference!r} at {json_pointer((*path, key))}"
                    )

    for engagement in profile["history"]:
        credential = engagement["credential"]
        if credential is None:
            continue
        for field_name in ("ncrfCredits", "nsqfLevel"):
            claim = credential[field_name]
            if claim is None:
                continue
            disallowed = {
                provenance["method"]
                for provenance in claim["provenance"]
                if provenance["method"]
                in {"agent-inferred", "deterministic-normalization"}
            }
            if disallowed:
                raise AssertionError(
                    f"{field_name} cannot be agent-inferred or calculated: {sorted(disallowed)}"
                )


def assert_transport_has_no_jsonld_keys(schema: Any) -> None:
    for path, value in walk(schema):
        if isinstance(value, dict):
            for key in value:
                if key.startswith("@"):
                    raise AssertionError(
                        f"Transport schema contains provider-unsafe key {key!r} at {json_pointer(path)}"
                    )


def convert(mode: str, input_path: Path) -> Any:
    completed = subprocess.run(
        ["node", str(CONVERTER), mode, str(input_path)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def main() -> None:
    canonical_schema = load_json(CANONICAL_SCHEMA)
    transport_schema = load_json(TRANSPORT_SCHEMA)
    canonical_example = load_json(CANONICAL_EXAMPLE)
    transport_example = load_json(TRANSPORT_EXAMPLE)

    Draft202012Validator.check_schema(canonical_schema)
    Draft202012Validator.check_schema(transport_schema)
    assert_transport_has_no_jsonld_keys(transport_schema)

    validate_schema(canonical_example, canonical_schema, "Canonical example")
    validate_schema(transport_example, transport_schema, "Transport example")
    validate_semantics(canonical_example)

    generated_transport = convert("--to-transport", CANONICAL_EXAMPLE)
    if generated_transport != transport_example:
        raise AssertionError(
            "Transport example is stale. Regenerate it with scripts/convert-profile.mjs."
        )

    round_tripped = convert("--to-canonical", TRANSPORT_EXAMPLE)
    if round_tripped != canonical_example:
        raise AssertionError("Canonical/transport conversion is not lossless.")

    print("Schemas, references, examples, and transport round-trip are valid.")


if __name__ == "__main__":
    main()
