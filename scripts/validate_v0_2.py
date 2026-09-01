"""Schema, semantic, reference, temporal and round-trip checks for v0.2.

v0.1 keeps its own validator. This module imports that file by path so the
private conversion skill, which loads scripts/validate_examples.py directly,
is unaffected.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator

sys.path.insert(0, str(Path(__file__).resolve().parent))

import validate_examples as v01  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SCHEMAS = ROOT / "schemas"
EXAMPLES = ROOT / "examples" / "v0.2"
CONTEXT_DOCUMENT = ROOT / "contexts" / "career-v0.2.context.jsonld"

PROFILE_SCHEMA = SCHEMAS / "career-profile.v0.2.schema.json"
PROFILE_TRANSPORT_SCHEMA = SCHEMAS / "career-profile.transport.v0.2.schema.json"
INTENT_SCHEMA = SCHEMAS / "opportunity-intent.v0.2.schema.json"
INTENT_TRANSPORT_SCHEMA = SCHEMAS / "opportunity-intent.transport.v0.2.schema.json"

PROFILE_EXAMPLE = EXAMPLES / "career-profile.synthetic.jsonld"
PROFILE_TRANSPORT_EXAMPLE = EXAMPLES / "career-profile.transport.synthetic.json"
INTENT_EXAMPLE = EXAMPLES / "opportunity-intent.synthetic.jsonld"
INTENT_TRANSPORT_EXAMPLE = EXAMPLES / "opportunity-intent.transport.synthetic.json"

ELEVATED_VERIFICATION = {"institution-verified", "peer-endorsed"}
TAXONOMY_SUBJECT_NAMESPACES = {
    "CareerProfile": {"capability", "engagement", "interest", "attribute"},
    "OpportunityIntent": {"target"},
}


class SemanticError(AssertionError):
    pass


def fail(message: str) -> None:
    raise SemanticError(message)


def normalize_instant(value: str) -> str:
    return value if "T" in value else f"{value}T00:00:00Z"


def collect_ids(document: Any) -> dict[str, tuple[object, ...]]:
    """Map every declared id to the path of the object that declares it."""
    ids: dict[str, tuple[object, ...]] = {}
    for path, value in v01.walk(document):
        if isinstance(value, dict) and isinstance(value.get("id"), str):
            identifier = value["id"]
            if identifier in ids:
                fail(
                    f"Duplicate id {identifier!r} at {v01.json_pointer((*path, 'id'))}; "
                    f"first used at {v01.json_pointer((*ids[identifier], 'id'))}"
                )
            ids[identifier] = path
    return ids


def iter_references(document: Any) -> Iterable[tuple[tuple[object, ...], str, str]]:
    for path, value in v01.walk(document):
        if not isinstance(value, dict):
            continue
        for key, candidate in value.items():
            if key in {"id", "profileId", "intentId", "documentId"}:
                continue
            if key.endswith("Ref") and isinstance(candidate, str):
                yield path, key, candidate
            elif key.endswith("Refs") and isinstance(candidate, list):
                for item in candidate:
                    if isinstance(item, str):
                        yield path, key, item


def check_references(document: Any, known: set[str], external: set[str]) -> None:
    for path, key, reference in iter_references(document):
        if reference in external:
            continue
        if reference not in known:
            fail(
                f"Unresolved reference {reference!r} at {v01.json_pointer((*path, key))}. "
                "Every v0.2 reference must resolve inside its own document."
            )


def check_source_locators(document: dict[str, Any]) -> None:
    source_ids = {document_entry["id"] for document_entry in document["sourceDocuments"]}
    for path, value in v01.walk(document):
        if not isinstance(value, dict):
            continue
        source = value.get("source")
        if not isinstance(source, dict):
            continue
        if source["documentId"] not in source_ids:
            fail(
                f"Unknown provenance document {source['documentId']!r} at "
                f"{v01.json_pointer((*path, 'source', 'documentId'))}"
            )
        start, end = source["charStart"], source["charEnd"]
        if (start is None) != (end is None):
            fail(f"Character offsets must both be set or both be null at {v01.json_pointer(path)}")
        if start is not None and end <= start:
            fail(f"charEnd must be greater than charStart at {v01.json_pointer(path)}")


def check_credentials(profile: dict[str, Any]) -> None:
    for engagement in profile["history"]:
        credential = engagement["credential"]
        if credential is None:
            continue
        for field_name in ("ncrfCredits", "nsqfLevel"):
            claim = credential[field_name]
            if claim is None:
                continue
            disallowed = sorted(
                {
                    provenance["method"]
                    for provenance in claim["provenance"]
                    if provenance["method"] in {"agent-inferred", "deterministic-normalization"}
                }
            )
            if disallowed:
                fail(f"{field_name} cannot be agent-inferred or calculated: {disallowed}")


def check_capabilities(profile: dict[str, Any]) -> None:
    capabilities = {capability["id"]: capability for capability in profile["capabilities"]}
    evidence = {record["id"]: record for record in profile["evidence"]}

    for capability in profile["capabilities"]:
        if capability["capabilityKind"] in {"tool", "knowledge"} and capability["exercisesRefs"]:
            fail(
                f"{capability['id']} is a {capability['capabilityKind']} and must not exercise "
                "other capabilities; only a skill or a practice may."
            )
        if capability["id"] in capability["exercisesRefs"]:
            fail(f"{capability['id']} exercises itself.")
        for evidence_id in capability["evidenceRefs"]:
            record = evidence[evidence_id]
            if record["subjectRef"] != capability["id"]:
                fail(
                    f"{capability['id']} lists {evidence_id}, but that evidence has subjectRef "
                    f"{record['subjectRef']!r}. Evidence membership must agree in both directions."
                )

    for record in profile["evidence"]:
        subject = capabilities.get(record["subjectRef"])
        if subject is None:
            fail(f"{record['id']} has subjectRef {record['subjectRef']!r}, which is not a capability.")
        if record["id"] not in subject["evidenceRefs"]:
            fail(
                f"{record['id']} points at {subject['id']}, but that capability does not list it "
                "in evidenceRefs."
            )

    # exercisesRefs must not form a cycle.
    state: dict[str, int] = {}

    def visit(capability_id: str, trail: list[str]) -> None:
        if state.get(capability_id) == 1:
            fail("exercisesRefs form a cycle: " + " -> ".join([*trail, capability_id]))
        if state.get(capability_id) == 2:
            return
        state[capability_id] = 1
        for child in capabilities[capability_id]["exercisesRefs"]:
            visit(child, [*trail, capability_id])
        state[capability_id] = 2

    for capability_id in capabilities:
        visit(capability_id, [])


def check_verifications(profile: dict[str, Any], id_paths: dict[str, tuple[object, ...]]) -> None:
    confirmed_targets = {
        verification["targetRef"]
        for verification in profile["verifications"]
        if verification["status"] == "confirmed"
    }

    for path, value in v01.walk(profile):
        if not isinstance(value, dict):
            continue
        if value.get("verificationStatus") not in ELEVATED_VERIFICATION:
            continue
        if path and path[0] == "verifications":
            # A verification's own provenance describes how the record was obtained.
            # Requiring a verification of the verification would be circular.
            continue
        ancestors = {
            identifier
            for identifier, declared_at in id_paths.items()
            if path[: len(declared_at)] == declared_at
        }
        if not ancestors & confirmed_targets:
            fail(
                f"{value['verificationStatus']!r} provenance at {v01.json_pointer(path)} has no "
                "confirmed Verification resolving to the claim or an enclosing entity."
            )


def check_freshness(profile: dict[str, Any]) -> None:
    freshness = profile["freshness"]
    generated = normalize_instant(freshness["profileGeneratedAt"])

    def latest(values: list[str]) -> str | None:
        return max(values, key=normalize_instant) if values else None

    ingested = latest(
        [
            document["ingestedAt"]
            for document in profile["sourceDocuments"]
            if document["ingestedAt"] is not None
        ]
    )
    confirmed = latest(
        [
            value["lastConfirmedAt"]
            for _, value in v01.walk(profile)
            if isinstance(value, dict) and isinstance(value.get("lastConfirmedAt"), str)
        ]
    )
    verified = latest(
        [
            verification["verifiedAt"]
            for verification in profile["verifications"]
            if verification["status"] == "confirmed" and verification["verifiedAt"] is not None
        ]
    )

    expected = {
        "lastSourceIngestedAt": ingested,
        "lastSubjectConfirmedAt": confirmed,
        "lastVerificationAt": verified,
    }
    for field_name, value in expected.items():
        if freshness[field_name] != value:
            fail(
                f"freshness.{field_name} is {freshness[field_name]!r} but the document's latest "
                f"value is {value!r}. Freshness metadata must be factual."
            )

    for field_name in ("lastSourceIngestedAt", "lastSubjectConfirmedAt", "lastVerificationAt"):
        value = freshness[field_name]
        if value is not None and normalize_instant(value) > generated:
            fail(f"freshness.{field_name} is later than profileGeneratedAt.")


def check_validity_windows(document: dict[str, Any], upper_bound: str | None) -> None:
    for path, value in v01.walk(document):
        if not isinstance(value, dict) or "validFrom" not in value or "observedAt" not in value:
            continue
        start, end = value["validFrom"], value["validUntil"]
        if start is not None and end is not None and end < start:
            fail(f"validUntil precedes validFrom at {v01.json_pointer(path)}")
        if upper_bound is None:
            continue
        for field_name in ("observedAt", "lastConfirmedAt"):
            stamp = value[field_name]
            if stamp is not None and normalize_instant(stamp) > upper_bound:
                fail(
                    f"{field_name} at {v01.json_pointer(path)} is later than the document's "
                    "generation time."
                )


def check_disclosure(document: dict[str, Any]) -> None:
    disclosure = document["disclosure"]
    collections = set(document)
    seen: dict[tuple[str, str], str] = {}

    for rule in disclosure["rules"]:
        selector = rule["selector"]
        populated = [name for name in ("entityRefs", "sensitivities", "collections") if selector[name]]
        if len(populated) != 1:
            fail(
                f"{rule['id']} populates {populated or 'no'} selector dimensions; exactly one is "
                "required so that precedence stays deterministic."
            )
        dimension = populated[0]
        for value in selector[dimension]:
            if dimension == "collections" and value not in collections:
                fail(f"{rule['id']} selects collection {value!r}, which this document does not have.")
            key = (dimension, value)
            if key in seen and seen[key] != rule["visibility"]:
                fail(
                    f"{rule['id']} and an earlier rule give {dimension} {value!r} conflicting "
                    "visibilities."
                )
            seen[key] = rule["visibility"]


def check_taxonomy(document: dict[str, Any]) -> None:
    allowed = TAXONOMY_SUBJECT_NAMESPACES[document["@type"]]
    ambiguity_refs = {
        reference
        for ambiguity in document["ambiguities"]
        for reference in ambiguity["relatedRefs"]
    }

    for mapping in document["taxonomyMappings"]:
        namespace = mapping["subjectRef"].split(":", 1)[0]
        if namespace not in allowed:
            fail(
                f"{mapping['id']} maps subject {mapping['subjectRef']!r}; "
                f"{document['@type']} mappings may only describe {sorted(allowed)}."
            )
        if mapping["mappingStatus"] == "mapped":
            inferred = [
                provenance
                for provenance in mapping["provenance"]
                if provenance["method"] == "agent-inferred"
            ]
            if inferred:
                fail(
                    f"{mapping['id']} is mapped but carries agent-inferred provenance. An "
                    "unreviewed suggestion belongs in candidates."
                )
        if mapping["mappingStatus"] == "ambiguous" and mapping["id"] not in ambiguity_refs:
            fail(
                f"{mapping['id']} is ambiguous but no ambiguity record relates to it. Uncertainty "
                "must be represented explicitly."
            )


def check_intent(intent: dict[str, Any], profile: dict[str, Any]) -> None:
    if intent["subjectRef"] != profile["profileId"]:
        fail(
            f"Intent subjectRef {intent['subjectRef']!r} does not resolve to profile "
            f"{profile['profileId']!r}."
        )
    if intent["validity"]["validFrom"] is None:
        fail("OpportunityIntent.validity.validFrom must be set; intent is time-bounded state.")

    for reference in intent["relocation"]["targetLocationRefs"]:
        if not reference.startswith("location:"):
            fail(f"relocation.targetLocationRefs must name preferred locations, found {reference!r}.")

    compensation = intent["compensationExpectation"]
    if compensation is not None:
        low, high = compensation["amountMin"], compensation["amountMax"]
        if low is not None and high is not None and high < low:
            fail("compensationExpectation.amountMax is lower than amountMin.")


def check_transport_example(transport: Any, label: str) -> None:
    for path, value in v01.walk(transport):
        if isinstance(value, dict):
            for key in value:
                if key.startswith("@"):
                    fail(
                        f"{label} contains provider-unsafe key {key!r} at {v01.json_pointer(path)}"
                    )


def check_context_parity(documents: list[dict[str, Any]]) -> None:
    published = v01.load_json(CONTEXT_DOCUMENT)["@context"]
    for document in documents:
        for term, value in document["@context"].items():
            if term not in published:
                fail(f"Context term {term!r} is missing from {CONTEXT_DOCUMENT.name}.")
            if published[term] != value:
                fail(
                    f"Context term {term!r} is {value!r} inline but {published[term]!r} in "
                    f"{CONTEXT_DOCUMENT.name}."
                )


def run_profile_checks(profile: dict[str, Any]) -> None:
    """Every semantic rule a canonical CareerProfile v0.2 must satisfy."""
    identifiers = collect_ids(profile)
    check_references(profile, set(identifiers) | {profile["profileId"]}, set())
    check_source_locators(profile)
    check_credentials(profile)
    check_capabilities(profile)
    check_verifications(profile, identifiers)
    check_freshness(profile)
    check_validity_windows(profile, normalize_instant(profile["freshness"]["profileGeneratedAt"]))
    check_disclosure(profile)
    check_taxonomy(profile)


def run_intent_checks(intent: dict[str, Any], profile: dict[str, Any]) -> None:
    """Every semantic rule a canonical OpportunityIntent v0.2 must satisfy."""
    identifiers = collect_ids(intent)
    # Subject resolution first, so a mismatched subject is reported as such rather
    # than as a generic unresolved reference.
    check_intent(intent, profile)
    check_references(intent, set(identifiers) | {intent["intentId"]}, {profile["profileId"]})
    check_source_locators(intent)
    check_validity_windows(intent, None)
    check_disclosure(intent)
    check_taxonomy(intent)


def check_manifest_documents(manifest: dict[str, Any]) -> None:
    entry = manifest["versions"]["0.2.0"]
    for key in ("jsonLdContext", "migrationGuide"):
        if key not in entry:
            fail(f"Manifest entry 0.2.0 must declare {key}.")
        if not (ROOT / entry[key]).is_file():
            fail(f"Manifest path does not exist: {entry[key]!r}")
    for name, paths in entry["additionalDocuments"].items():
        for key in ("canonicalSchema", "transportSchema"):
            if not (ROOT / paths[key]).is_file():
                fail(f"Manifest path for {name} does not exist: {paths[key]!r}")


def main() -> None:
    profile_schema = v01.load_json(PROFILE_SCHEMA)
    profile_transport_schema = v01.load_json(PROFILE_TRANSPORT_SCHEMA)
    intent_schema = v01.load_json(INTENT_SCHEMA)
    intent_transport_schema = v01.load_json(INTENT_TRANSPORT_SCHEMA)

    for schema in (profile_schema, profile_transport_schema, intent_schema, intent_transport_schema):
        Draft202012Validator.check_schema(schema)
    v01.assert_transport_has_no_jsonld_keys(profile_transport_schema)
    v01.assert_transport_has_no_jsonld_keys(intent_transport_schema)

    manifest = v01.load_json(ROOT / "schemas" / "schema-manifest.json")
    check_manifest_documents(manifest)

    profile = v01.load_json(PROFILE_EXAMPLE)
    intent = v01.load_json(INTENT_EXAMPLE)
    profile_transport = v01.load_json(PROFILE_TRANSPORT_EXAMPLE)
    intent_transport = v01.load_json(INTENT_TRANSPORT_EXAMPLE)

    v01.validate_schema(profile, profile_schema, "Canonical career profile v0.2")
    v01.validate_schema(intent, intent_schema, "Canonical opportunity intent v0.2")
    v01.validate_schema(profile_transport, profile_transport_schema, "Transport career profile v0.2")
    v01.validate_schema(intent_transport, intent_transport_schema, "Transport opportunity intent v0.2")

    check_transport_example(profile_transport, "Transport career profile example")
    check_transport_example(intent_transport, "Transport opportunity intent example")
    check_context_parity([profile, intent])

    run_profile_checks(profile)
    run_intent_checks(intent, profile)

    for label, canonical_path, transport_path, transport_example in (
        ("career profile", PROFILE_EXAMPLE, PROFILE_TRANSPORT_EXAMPLE, profile_transport),
        ("opportunity intent", INTENT_EXAMPLE, INTENT_TRANSPORT_EXAMPLE, intent_transport),
    ):
        generated = v01.convert("--to-transport", canonical_path)
        if generated != transport_example:
            raise AssertionError(
                f"The {label} transport example is stale. Regenerate it with "
                "scripts/convert-profile.mjs."
            )
        round_tripped = v01.convert("--to-canonical", transport_path)
        if round_tripped != v01.load_json(canonical_path):
            raise AssertionError(f"The {label} canonical/transport conversion is not lossless.")

    print(
        "v0.2 schemas, references, temporal windows, evidence, disclosure, taxonomy and "
        "round-trips are valid."
    )


if __name__ == "__main__":
    main()
