"""Answer agent-oriented questions from the v0.2 synthetic documents.

Each fixture states a question, the deterministic steps that resolve it, and the
expected answer. The point is to prove the schema carries enough structured
information to answer the question. The resolver only reads, filters and follows
references: it does not score, rank, or match candidates, and it never reads the
system clock -- every time-dependent fixture supplies an explicit `asOf`.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import validate_examples as v01  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "examples" / "v0.2"
FIXTURES = EXAMPLES / "queries"

DOCUMENTS = {
    "career-profile": EXAMPLES / "career-profile.synthetic.jsonld",
    "opportunity-intent": EXAMPLES / "opportunity-intent.synthetic.jsonld",
}

VISIBILITY_PRECEDENCE = ("entityRefs", "sensitivities", "collections")


class FixtureError(AssertionError):
    pass


def resolve_pointer(value: Any, pointer: str) -> Any:
    if pointer in ("", "/"):
        return value
    current = value
    for raw in pointer.lstrip("/").split("/"):
        token = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(current, list):
            if not token.isdigit() or int(token) >= len(current):
                return None
            current = current[int(token)]
        elif isinstance(current, dict):
            if token not in current:
                return None
            current = current[token]
        else:
            return None
    return current


def entity_index(document: dict[str, Any]) -> dict[str, tuple[str, dict[str, Any]]]:
    """Every entity in a top-level collection, with the collection that holds it."""
    index: dict[str, tuple[str, dict[str, Any]]] = {}
    for collection, value in document.items():
        if not isinstance(value, list):
            continue
        for item in value:
            if isinstance(item, dict) and isinstance(item.get("id"), str):
                index[item["id"]] = (collection, item)
    return index


def resolve_visibility(document: dict[str, Any], entity_ref: str) -> str:
    """Precedence: entityRefs, then sensitivities, then collections, then the default.

    Conflicting rules within one tier are rejected by validate_v0_2.check_disclosure,
    so this resolution is deterministic.
    """
    index = entity_index(document)
    if entity_ref not in index:
        raise FixtureError(f"{entity_ref!r} is not an entity in a top-level collection.")
    collection, entity = index[entity_ref]
    sensitivity = entity.get("sensitivity")

    matches: dict[str, str] = {}
    for rule in document["disclosure"]["rules"]:
        selector = rule["selector"]
        if entity_ref in selector["entityRefs"]:
            matches.setdefault("entityRefs", rule["visibility"])
        if sensitivity is not None and sensitivity in selector["sensitivities"]:
            matches.setdefault("sensitivities", rule["visibility"])
        if collection in selector["collections"]:
            matches.setdefault("collections", rule["visibility"])

    for dimension in VISIBILITY_PRECEDENCE:
        if dimension in matches:
            return matches[dimension]
    return document["disclosure"]["defaultVisibility"]


def expired_ids(document: dict[str, Any], as_of: str) -> list[str]:
    """Ids of state whose validity window has closed on `as_of`."""
    expired: list[str] = []
    document_id = document.get("profileId") or document.get("intentId")
    for path, value in v01.walk(document):
        if not isinstance(value, dict):
            continue
        validity = value.get("validity")
        if not isinstance(validity, dict):
            continue
        valid_until = validity.get("validUntil")
        if valid_until is None or valid_until >= as_of[: len(valid_until)]:
            continue
        identifier = value.get("id") or (document_id if path == () else None)
        if identifier is not None:
            expired.append(identifier)
    return expired


def matches_condition(item: dict[str, Any], field: str, condition: Any, results: dict[str, Any]) -> bool:
    actual = resolve_pointer(item, field) if field.startswith("/") else item.get(field)
    if isinstance(condition, dict) and "in" in condition:
        allowed = condition["in"]
        if isinstance(allowed, str) and allowed.startswith("$"):
            allowed = results[allowed[1:]]
        return actual in (allowed or [])
    return actual == condition


def load_document(name: str) -> dict[str, Any]:
    if name not in _DOCUMENT_CACHE:
        _DOCUMENT_CACHE[name] = v01.load_json(DOCUMENTS[name])
    return _DOCUMENT_CACHE[name]


_DOCUMENT_CACHE: dict[str, dict[str, Any]] = {}


def run_step(step: dict[str, Any], fixture: dict[str, Any], results: dict[str, Any]) -> Any:
    document = load_document(step["document"])
    operation = step["op"]

    if operation == "pointer":
        return resolve_pointer(document, step["pointer"])

    if operation == "collect":
        items = document[step["collection"]]
        for field, condition in step.get("where", {}).items():
            items = [item for item in items if matches_condition(item, field, condition, results)]
        selector = step.get("select", "/id")
        return [resolve_pointer(item, selector) for item in items]

    if operation == "follow":
        index = entity_index(document)
        start = index[step["from"]][1]
        references = start[step["refs"]]
        if isinstance(references, str):
            references = [references]
        selector = step.get("select", "/id")
        return [resolve_pointer(index[reference][1], selector) for reference in references]

    if operation == "visibility":
        return resolve_visibility(document, step["entityRef"])

    if operation == "expired":
        return expired_ids(document, step.get("asOf", fixture["asOf"]))

    raise FixtureError(f"Unknown fixture operation {operation!r}")


def run_fixture(fixture: dict[str, Any]) -> list[str]:
    results: dict[str, Any] = {}
    problems: list[str] = []

    for step in fixture["steps"]:
        try:
            results[step["name"]] = run_step(step, fixture, results)
        except Exception as error:  # noqa: BLE001 - reported per fixture
            problems.append(f"step {step['name']!r} failed: {error}")
            return problems

    for name, expected in fixture["expect"].items():
        if name not in results:
            problems.append(f"expected step {name!r} was never resolved")
            continue
        if results[name] != expected:
            problems.append(
                f"{name}: expected {json.dumps(expected)}, resolved {json.dumps(results[name])}"
            )
    return problems


def main() -> int:
    fixture_paths = sorted(FIXTURES.glob("*.json"))
    if not fixture_paths:
        print(f"No query fixtures found in {FIXTURES}")
        return 1

    failures = 0
    for path in fixture_paths:
        fixture = v01.load_json(path)
        problems = run_fixture(fixture)
        if problems:
            failures += 1
            print(f"FAIL {fixture['id']}: {fixture['question']}")
            for problem in problems:
                print(f"       {problem}")
        else:
            print(f"ok   {fixture['id']}: {fixture['question']}")

    if failures:
        print(f"\n{failures} of {len(fixture_paths)} query fixtures did not resolve as expected.")
        return 1

    print(f"\nAll {len(fixture_paths)} agent queries were answered from the documents alone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
