"""Negative tests: every v0.2 rule must actually reject a violating document.

Each case mutates a copy of a synthetic example and asserts that either the JSON
Schema layer or the semantic layer rejects it. A rule that no test can break is
not a rule.
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path
from typing import Any, Callable

from jsonschema import Draft202012Validator, FormatChecker

sys.path.insert(0, str(Path(__file__).resolve().parent))

import validate_examples as v01  # noqa: E402
import validate_v0_2 as v02  # noqa: E402

Mutate = Callable[[dict[str, Any]], None]

PROFILE_SCHEMA = v01.load_json(v02.PROFILE_SCHEMA)
INTENT_SCHEMA = v01.load_json(v02.INTENT_SCHEMA)
PROFILE = v01.load_json(v02.PROFILE_EXAMPLE)
INTENT = v01.load_json(v02.INTENT_EXAMPLE)


def capability(profile: dict[str, Any], identifier: str) -> dict[str, Any]:
    return next(item for item in profile["capabilities"] if item["id"] == identifier)


def mapping(document: dict[str, Any], identifier: str) -> dict[str, Any]:
    return next(item for item in document["taxonomyMappings"] if item["id"] == identifier)


# --------------------------------------------------------------- profile ---

def unresolved_evidence_reference(profile: dict[str, Any]) -> None:
    capability(profile, "capability:qgis")["evidenceRefs"] = ["evidence:does-not-exist"]


def duplicate_identifier(profile: dict[str, Any]) -> None:
    profile["artifacts"][1]["id"] = profile["artifacts"][0]["id"]


def wrong_confirmation_freshness(profile: dict[str, Any]) -> None:
    profile["freshness"]["lastSubjectConfirmedAt"] = "2026-08-14T09:14:00Z"


def freshness_after_generation(profile: dict[str, Any]) -> None:
    profile["freshness"]["profileGeneratedAt"] = "2026-08-14T09:00:00Z"


def unbacked_institution_verification(profile: dict[str, Any]) -> None:
    profile["verifications"] = [
        verification
        for verification in profile["verifications"]
        if verification["id"] != "verification:mplan-credential-confirmed"
    ]


def evidence_direction_mismatch(profile: dict[str, Any]) -> None:
    evidence = next(
        item for item in profile["evidence"] if item["id"] == "evidence:qgis-mentioned"
    )
    evidence["subjectRef"] = "capability:spatial-analysis"


def exercises_cycle(profile: dict[str, Any]) -> None:
    capability(profile, "capability:spatial-analysis")["exercisesRefs"] = [
        "capability:accessibility-analysis-practice"
    ]


def tool_exercises_capability(profile: dict[str, Any]) -> None:
    capability(profile, "capability:qgis")["exercisesRefs"] = ["capability:spatial-analysis"]


def inferred_taxonomy_adoption(profile: dict[str, Any]) -> None:
    entry = mapping(profile, "taxonomy-mapping:mobility-cell-nco")
    entry["provenance"] = [
        {
            "method": "agent-inferred",
            "verificationStatus": "unverified",
            "confidence": 0.6,
            "source": None,
            "inferringAgent": "https://example.org/agents/resume-parser",
        }
    ]


def ambiguous_mapping_without_record(profile: dict[str, Any]) -> None:
    ambiguity = next(
        item for item in profile["ambiguities"] if item["id"] == "ambiguity:esco-mapping-uncertain"
    )
    ambiguity["relatedRefs"] = [
        reference
        for reference in ambiguity["relatedRefs"]
        if not reference.startswith("taxonomy-mapping:")
    ]


def inverted_validity_window(profile: dict[str, Any]) -> None:
    capability(profile, "capability:qgis")["validity"]["validFrom"] = "2026-01"
    capability(profile, "capability:qgis")["validity"]["validUntil"] = "2025-01"


def unknown_disclosure_collection(profile: dict[str, Any]) -> None:
    profile["disclosure"]["rules"][2]["selector"]["collections"] = ["salaryHistory"]


def conflicting_disclosure_rules(profile: dict[str, Any]) -> None:
    duplicate = copy.deepcopy(profile["disclosure"]["rules"][0])
    duplicate["id"] = "disclosure-rule:conflicting"
    duplicate["visibility"] = "agent-discoverable"
    profile["disclosure"]["rules"].append(duplicate)


def inferred_credential_level(profile: dict[str, Any]) -> None:
    profile["history"][0]["credential"]["nsqfLevel"] = {
        "id": "claim:mplan-nsqf-level",
        "value": 6,
        "provenance": [
            {
                "method": "agent-inferred",
                "verificationStatus": "unverified",
                "confidence": 0.5,
                "source": None,
                "inferringAgent": "https://example.org/agents/resume-parser",
            }
        ],
    }


def inferred_capability_without_evidence(profile: dict[str, Any]) -> None:
    capability(profile, "capability:accessibility-analysis-practice")["evidenceRefs"] = []


def last_demonstrated_without_evidence(profile: dict[str, Any]) -> None:
    entry = capability(profile, "capability:transport-demand-modelling")
    entry["lastDemonstratedAt"] = "2023-05"
    entry["evidenceRefs"] = []


def unmapped_with_code(profile: dict[str, Any]) -> None:
    entry = mapping(profile, "taxonomy-mapping:qgis-esco")
    entry["code"] = "S1.7.1"


def ambiguous_with_single_candidate(profile: dict[str, Any]) -> None:
    entry = mapping(profile, "taxonomy-mapping:spatial-analysis-esco")
    entry["candidates"] = entry["candidates"][:1]


def current_period_with_end_date(profile: dict[str, Any]) -> None:
    profile["history"][1]["periods"][0]["end"] = "2026-08"


def agent_suggested_adopted_as_method(profile: dict[str, Any]) -> None:
    entry = mapping(profile, "taxonomy-mapping:mobility-cell-nco")
    entry["mappingMethod"] = "agent-suggested"


def two_selector_dimensions(profile: dict[str, Any]) -> None:
    selector = profile["disclosure"]["rules"][0]["selector"]
    selector["collections"] = ["attributes"]


def missing_capability_type(profile: dict[str, Any]) -> None:
    capability(profile, "capability:qgis")["capabilityKind"] = "superpower"


# ---------------------------------------------------------------- intent ---

def intent_subject_mismatch(intent: dict[str, Any]) -> None:
    intent["subjectRef"] = "profile:someone-else"


def intent_without_start(intent: dict[str, Any]) -> None:
    intent["validity"]["validFrom"] = None


def compensation_without_currency(intent: dict[str, Any]) -> None:
    intent["compensationExpectation"] = {
        "id": "compensation:expectation",
        "type": "CompensationExpectation",
        "amountMin": 900000,
        "amountMax": 1200000,
        "currency": None,
        "period": None,
        "basis": "ctc",
        "negotiable": True,
        "note": None,
        "validity": {
            "validFrom": "2026-08-01",
            "validUntil": None,
            "observedAt": "2026-08-14T09:12:00Z",
            "lastConfirmedAt": None,
        },
        "provenance": [
            {
                "method": "user-entered",
                "verificationStatus": "self-attested",
                "confidence": 1,
                "source": None,
                "inferringAgent": None,
            }
        ],
    }


def inverted_compensation_range(intent: dict[str, Any]) -> None:
    compensation_without_currency(intent)
    intent["compensationExpectation"]["currency"] = "INR"
    intent["compensationExpectation"]["period"] = "year"
    intent["compensationExpectation"]["amountMax"] = 500000


def typed_dimension_as_constraint(intent: dict[str, Any]) -> None:
    intent["constraints"][0]["kind"] = "compensation"


def unresolved_relocation_target(intent: dict[str, Any]) -> None:
    intent["relocation"]["targetLocationRefs"] = ["location:mumbai"]


PROFILE_CASES: list[tuple[str, str, Mutate, str]] = [
    ("semantic", "an evidence reference that resolves to nothing", unresolved_evidence_reference, "Unresolved reference"),
    ("semantic", "a duplicated entity id", duplicate_identifier, "Duplicate id"),
    ("semantic", "freshness that overstates subject confirmation", wrong_confirmation_freshness, "must be factual"),
    ("semantic", "recency values later than generation time", freshness_after_generation, "later than profileGeneratedAt"),
    ("semantic", "institution-verified provenance with no verification record", unbacked_institution_verification, "no confirmed Verification"),
    ("semantic", "evidence pointing at a capability that does not list it", evidence_direction_mismatch, "agree in both directions"),
    ("semantic", "a cycle in exercisesRefs", exercises_cycle, "cycle"),
    ("semantic", "a tool that claims to exercise a skill", tool_exercises_capability, "must not exercise"),
    ("semantic", "an adopted taxonomy code with agent-inferred provenance", inferred_taxonomy_adoption, "belongs in candidates"),
    ("semantic", "an ambiguous mapping with no ambiguity record", ambiguous_mapping_without_record, "no ambiguity record"),
    ("semantic", "a validity window that ends before it starts", inverted_validity_window, "validUntil precedes validFrom"),
    ("semantic", "a disclosure rule naming a collection that does not exist", unknown_disclosure_collection, "does not have"),
    ("semantic", "two disclosure rules disagreeing on the same selector", conflicting_disclosure_rules, "conflicting"),
    ("semantic", "an agent-inferred NSQF level", inferred_credential_level, "cannot be agent-inferred"),
    ("schema", "an agent-inferred capability with no evidence", inferred_capability_without_evidence, ""),
    ("schema", "lastDemonstratedAt with no evidence", last_demonstrated_without_evidence, ""),
    ("schema", "an unmapped taxonomy record that still carries a code", unmapped_with_code, ""),
    ("schema", "an ambiguous mapping with a single candidate", ambiguous_with_single_candidate, ""),
    ("schema", "a current period that also has an end date", current_period_with_end_date, ""),
    ("schema", "agent-suggested used as an adopted mapping method", agent_suggested_adopted_as_method, ""),
    ("schema", "a disclosure selector using two dimensions", two_selector_dimensions, ""),
    ("schema", "an unknown capability kind", missing_capability_type, ""),
]

INTENT_CASES: list[tuple[str, str, Mutate, str]] = [
    ("semantic", "intent pointing at a different profile", intent_subject_mismatch, "does not resolve to profile"),
    ("semantic", "intent with no validity start", intent_without_start, "validFrom must be set"),
    ("semantic", "a compensation range that ends below its floor", inverted_compensation_range, "lower than amountMin"),
    ("semantic", "a relocation target that is not a preferred location", unresolved_relocation_target, "Unresolved reference"),
    ("schema", "a compensation amount with no currency or period", compensation_without_currency, ""),
    ("schema", "a typed dimension restated as an untyped constraint", typed_dimension_as_constraint, ""),
]


def schema_rejects(instance: dict[str, Any], schema: dict[str, Any]) -> bool:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return any(True for _ in validator.iter_errors(instance))


def run() -> int:
    failures: list[str] = []

    for layer, description, mutate, expected in PROFILE_CASES:
        candidate = copy.deepcopy(PROFILE)
        mutate(candidate)
        if layer == "schema":
            if not schema_rejects(candidate, PROFILE_SCHEMA):
                failures.append(f"the profile schema accepted {description}")
            continue
        try:
            v02.run_profile_checks(candidate)
        except AssertionError as error:
            if expected not in str(error):
                failures.append(
                    f"{description} was rejected for the wrong reason: {error}"
                )
        else:
            failures.append(f"the semantic checks accepted {description}")

    for layer, description, mutate, expected in INTENT_CASES:
        candidate = copy.deepcopy(INTENT)
        mutate(candidate)
        if layer == "schema":
            if not schema_rejects(candidate, INTENT_SCHEMA):
                failures.append(f"the intent schema accepted {description}")
            continue
        try:
            v02.run_intent_checks(candidate, PROFILE)
        except AssertionError as error:
            if expected not in str(error):
                failures.append(
                    f"{description} was rejected for the wrong reason: {error}"
                )
        else:
            failures.append(f"the semantic checks accepted {description}")

    total = len(PROFILE_CASES) + len(INTENT_CASES)
    if failures:
        print(f"{len(failures)} of {total} v0.2 rule tests failed:")
        for failure in failures:
            print(f"  {failure}")
        return 1

    print(f"All {total} v0.2 rule tests rejected their violating document.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
