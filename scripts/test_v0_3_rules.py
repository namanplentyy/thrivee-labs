"""Negative tests: every v0.3 trust rule must actually reject a violating document.

Each case deep-copies the synthetic bundle, breaks exactly one thing, and asserts
that either the JSON Schema layer or the semantic layer rejects it. A rule that no
test can break is not a rule. This mirrors the v0.2 suite; the difference is that
the trust layer is a graph, so a semantic case is checked against the whole bundle
rather than against one document.
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path
from typing import Any, Callable

from jsonschema import Draft202012Validator, FormatChecker

sys.path.insert(0, str(Path(__file__).resolve().parent))

import validate_examples as v01  # noqa: E402
import validate_v0_3 as v03  # noqa: E402

Mutate = Callable[[dict[str, Any]], None]

BUNDLE = v03.load_bundle()
SCHEMAS = {name: v01.load_json(path) for name, path in v03.SCHEMA_BY_TYPE.items()}

RELATIONSHIP_MANAGED = "relationship:s-example-managed-a-example"
RELATIONSHIP_TAUGHT = "relationship:r-example-taught-a-example"
RELATIONSHIP_UNCONFIRMED = "relationship:a-example-knows-t-example"
ENDORSEMENT_CAPABILITY = "endorsement:r-example-spatial-analysis"
ENDORSEMENT_ROLE = "endorsement:s-example-role-performance"
AVAILABILITY_LIMITED = "referral-availability:s-example-2026"
AVAILABILITY_LAPSED = "referral-availability:t-example-2025"
REFERRAL_ACTIVE = "referral:s-example-refers-a-example"
REFERRAL_SUGGESTED = "referral:platform-suggested-r-example-path"

SELF_ATTESTED = {
    "method": "user-entered",
    "verificationStatus": "self-attested",
    "confidence": 1,
    "source": None,
    "inferringAgent": None,
}
AGENT_INFERRED = {
    "method": "agent-inferred",
    "verificationStatus": "unverified",
    "confidence": 0.6,
    "source": None,
    "inferringAgent": "https://example.org/agents/referral-suggester",
}


def approval(document: dict[str, Any], role: str) -> dict[str, Any]:
    return next(entry for entry in document["approvals"] if entry["role"] == role)


# ---------------------------------------------------------- relationships ---

def confirmed_without_provenance(document: dict[str, Any]) -> None:
    document["counterparty"]["provenance"] = []


def confirmed_by_the_asserter(document: dict[str, Any]) -> None:
    document["counterparty"]["confirmedByRef"] = document["assertedByRef"]


def confirmed_by_an_outsider(document: dict[str, Any]) -> None:
    document["counterparty"]["confirmedByRef"] = "party:example-authority"


def asserted_by_a_bystander(document: dict[str, Any]) -> None:
    document["assertedByRef"] = "party:example-authority"


def confirmation_dates_disagree(document: dict[str, Any]) -> None:
    document["counterparty"]["confirmedAt"] = "2026-08-24T11:05:00Z"


def unilateral_claims_peer_endorsement(document: dict[str, Any]) -> None:
    document["counterparty"]["provenance"] = [
        {**SELF_ATTESTED, "method": "peer-endorsed", "verificationStatus": "peer-endorsed"}
    ]


def unilateral_claims_confirmation_date(document: dict[str, Any]) -> None:
    document["validity"]["lastConfirmedAt"] = "2026-08-20T10:00:00Z"


def relationship_graph_made_public(document: dict[str, Any]) -> None:
    document["disclosure"]["defaultVisibility"] = "agent-discoverable"


def relationship_with_itself(document: dict[str, Any]) -> None:
    document["partyBRef"] = document["partyARef"]


def context_ends_before_it_starts(document: dict[str, Any]) -> None:
    document["contexts"][0]["to"] = "2020"


def unverified_party_claims_assurance(document: dict[str, Any]) -> None:
    document["parties"][1]["identityAssurance"] = "platform-verified"


def extension_without_other(document: dict[str, Any]) -> None:
    document["relationshipTypes"] = ["colleague"]


# ------------------------------------------------------------ endorsements ---

def endorsement_by_the_candidate(document: dict[str, Any]) -> None:
    document["endorserRef"] = "party:a-example"


def endorsement_inferred_by_an_agent(document: dict[str, Any]) -> None:
    document["statement"]["provenance"] = [AGENT_INFERRED]


def endorsed_capability_does_not_exist(document: dict[str, Any]) -> None:
    document["targetRefs"] = ["capability:quantum-transport-modelling"]


def endorsement_scope_disagrees_with_target(document: dict[str, Any]) -> None:
    document["targetRefs"] = ["engagement:mplan"]


def endorsement_basis_is_not_a_basis(document: dict[str, Any]) -> None:
    document["basisRefs"] = ["interest:public-transport-equity"]


def endorsement_scope_without_a_target(document: dict[str, Any]) -> None:
    document["targetRefs"] = []


# ------------------------------------------------------------ availability ---

def refusal_that_still_has_scope(document: dict[str, Any]) -> None:
    document["status"]["value"] = "not-available"


def limited_availability_with_no_scope(document: dict[str, Any]) -> None:
    document["scope"]["organizations"] = []
    document["scope"]["domains"] = []
    document["scope"]["careerFamilies"] = []
    document["scope"]["relationshipRequirements"] = []
    # The classification described a scope entry that no longer exists.
    document["taxonomyMappings"] = []


def scope_entry_in_the_wrong_collection(document: dict[str, Any]) -> None:
    document["scope"]["domains"][0]["kind"] = "career-family"


def availability_without_a_start(document: dict[str, Any]) -> None:
    document["validity"]["validFrom"] = None


def availability_window_ends_before_it_starts(document: dict[str, Any]) -> None:
    document["validity"]["validUntil"] = "2025-01-01"
    document["validity"]["validFrom"] = "2026-08-01"


def availability_classifies_something_else(document: dict[str, Any]) -> None:
    document["taxonomyMappings"][0]["subjectRef"] = "capability:spatial-analysis"


# ---------------------------------------------------------------- referrals ---

def active_without_referrer_approval(document: dict[str, Any]) -> None:
    approval(document, "referrer")["decision"] = "pending"
    approval(document, "referrer")["decidedAt"] = None
    approval(document, "referrer")["provenance"] = []


def active_without_candidate_approval(document: dict[str, Any]) -> None:
    document["approvals"] = [approval(document, "referrer")]


def referrer_approval_by_someone_else(document: dict[str, Any]) -> None:
    approval(document, "referrer")["actorRef"] = "party:example-authority"


def candidate_approval_by_someone_else(document: dict[str, Any]) -> None:
    approval(document, "candidate")["actorRef"] = "party:s-example"


def two_referrer_approvals(document: dict[str, Any]) -> None:
    duplicate = copy.deepcopy(approval(document, "referrer"))
    duplicate["id"] = "approval:s-example-referrer-again"
    document["approvals"].append(duplicate)


def approval_derived_by_an_agent(document: dict[str, Any]) -> None:
    approval(document, "candidate")["provenance"] = [AGENT_INFERRED]


def suggestion_transmitted_as_a_referral(document: dict[str, Any]) -> None:
    document["referredAt"] = "2026-08-27T09:00:00Z"


def active_referral_without_a_grant(document: dict[str, Any]) -> None:
    document["disclosureGrantRefs"] = []


def referral_widens_the_profile_policy(document: dict[str, Any]) -> None:
    document["disclosure"]["rules"][0]["selector"]["entityRefs"] = ["identity:contact-route"]
    document["disclosure"]["rules"][0]["visibility"] = "agent-discoverable"


def endorsement_is_about_someone_else(document: dict[str, Any]) -> None:
    # Repointed at a party that resolves, so the referral's own rule is what rejects
    # this rather than the bundle's reference check.
    document["subjectRef"] = "party:s-example"


def relationship_does_not_involve_the_referrer(document: dict[str, Any]) -> None:
    document["relationshipRefs"] = [RELATIONSHIP_TAUGHT]


def dangling_relationship_reference(document: dict[str, Any]) -> None:
    document["relationshipRefs"] = ["relationship:does-not-exist"]


def availability_of_a_different_party(document: dict[str, Any]) -> None:
    document["availabilityRef"] = "referral-availability:r-example-2026"


def active_referral_cites_a_closed_availability(document: dict[str, Any]) -> None:
    document["availabilityRef"] = AVAILABILITY_LAPSED
    document["referrerRef"] = "party:t-example"
    approval(document, "referrer")["actorRef"] = "party:t-example"
    document["parties"].append(
        {
            "id": "party:t-example",
            "type": "Party",
            "partyKind": "person",
            "profileRef": None,
            "displayName": {
                "id": "claim:t-example-name",
                "value": "T. Example",
                "provenance": [SELF_ATTESTED],
            },
            "identifierUri": "https://example.org/people/t-example",
            "identityAssurance": "self-asserted",
            "sensitivity": "sensitive",
            "validity": {
                "validFrom": None,
                "validUntil": None,
                "observedAt": "2026-08-20T10:00:00Z",
                "lastConfirmedAt": None,
            },
            "provenance": [SELF_ATTESTED],
        }
    )
    document["relationshipRefs"] = []
    document["endorsementRefs"] = []


def opportunity_claims_to_be_resolved(document: dict[str, Any]) -> None:
    document["opportunity"]["bindingStatus"] = "resolved-hiring-intent"


def pending_referral_that_was_transmitted(document: dict[str, Any]) -> None:
    document["referredAt"] = "2026-08-27T09:00:00Z"


def approved_without_a_decision_date(document: dict[str, Any]) -> None:
    approval(document, "referrer")["decidedAt"] = None


def active_referral_with_one_approval(document: dict[str, Any]) -> None:
    document["approvals"] = [approval(document, "referrer")]


# ------------------------------------------------------------ bundle rules ---

def one_identifier_two_people(document: dict[str, Any]) -> None:
    document["parties"][0]["profileRef"] = None
    document["parties"][0]["identifierUri"] = "https://example.org/people/someone-else"


CASES: list[tuple[str, str, str, Mutate, str]] = [
    # relationships
    ("semantic", "a confirmed relationship with no confirmation provenance", RELATIONSHIP_TAUGHT, confirmed_without_provenance, "no provenance"),
    ("semantic", "a relationship confirmed by the party that asserted it", RELATIONSHIP_TAUGHT, confirmed_by_the_asserter, "same party that asserted"),
    ("semantic", "a relationship confirmed by someone who is not party to it", RELATIONSHIP_TAUGHT, confirmed_by_an_outsider, "not a party to it"),
    ("semantic", "a relationship asserted by a bystander", RELATIONSHIP_TAUGHT, asserted_by_a_bystander, "neither party to it"),
    ("semantic", "a confirmation date that disagrees with the recorded confirmation", RELATIONSHIP_TAUGHT, confirmation_dates_disagree, "same event in both"),
    ("semantic", "a unilateral claim presenting itself as peer-endorsed", RELATIONSHIP_UNCONFIRMED, unilateral_claims_peer_endorsement, "stay distinguishable"),
    ("semantic", "a unilateral claim carrying a subject confirmation date", RELATIONSHIP_UNCONFIRMED, unilateral_claims_confirmation_date, "has not been confirmed by anyone"),
    ("semantic", "a relationship graph exposed by default", RELATIONSHIP_TAUGHT, relationship_graph_made_public, "harvested as a directory"),
    ("semantic", "a relationship between a party and itself", RELATIONSHIP_UNCONFIRMED, relationship_with_itself, "to itself"),
    ("semantic", "a relationship context that ends before it starts", RELATIONSHIP_TAUGHT, context_ends_before_it_starts, "ends before it starts"),
    ("semantic", "a party claiming assurance nothing verified", RELATIONSHIP_TAUGHT, unverified_party_claims_assurance, "no confirmed Verification"),
    ("schema", "a type extension without the `other` type it extends", RELATIONSHIP_UNCONFIRMED, extension_without_other, ""),
    # endorsements
    ("semantic", "an endorsement attributed to the candidate without self-attestation", ENDORSEMENT_CAPABILITY, endorsement_by_the_candidate, "not marked selfAttested"),
    ("semantic", "an endorsement inferred by an agent", ENDORSEMENT_CAPABILITY, endorsement_inferred_by_an_agent, "cannot vouch for anyone"),
    ("semantic", "an endorsement of a capability that does not exist", ENDORSEMENT_CAPABILITY, endorsed_capability_does_not_exist, "Unresolved reference"),
    ("semantic", "an endorsement whose scope disagrees with what it names", ENDORSEMENT_CAPABILITY, endorsement_scope_disagrees_with_target, "may only endorse"),
    ("semantic", "an endorsement resting on something that cannot be a basis", ENDORSEMENT_ROLE, endorsement_basis_is_not_a_basis, "a basis must name"),
    ("schema", "a scoped endorsement that names nothing", ENDORSEMENT_ROLE, endorsement_scope_without_a_target, ""),
    # availability
    ("semantic", "a stated refusal that still carries a scope", AVAILABILITY_LIMITED, refusal_that_still_has_scope, "stated refusal has no scope"),
    ("semantic", "limited availability with an empty scope", AVAILABILITY_LIMITED, limited_availability_with_no_scope, "empty scope"),
    ("semantic", "a scope entry sitting in the wrong collection", AVAILABILITY_LIMITED, scope_entry_in_the_wrong_collection, "has kind"),
    ("semantic", "willingness with no start date", AVAILABILITY_LIMITED, availability_without_a_start, "time-bounded state"),
    ("semantic", "an availability window that ends before it starts", AVAILABILITY_LIMITED, availability_window_ends_before_it_starts, "validUntil precedes validFrom"),
    ("semantic", "an availability classifying something other than its own scope", AVAILABILITY_LIMITED, availability_classifies_something_else, "may only describe"),
    # referrals
    ("semantic", "an active referral without referrer approval", REFERRAL_ACTIVE, active_without_referrer_approval, "approved referrer decision"),
    ("semantic", "an active referral without candidate approval", REFERRAL_ACTIVE, active_without_candidate_approval, "approved candidate decision"),
    ("semantic", "a referrer approval given by someone else", REFERRAL_ACTIVE, referrer_approval_by_someone_else, "not the referrer"),
    ("semantic", "a candidate approval given by someone else", REFERRAL_ACTIVE, candidate_approval_by_someone_else, "does not resolve to the candidate"),
    ("semantic", "two referrer approvals on one referral", REFERRAL_ACTIVE, two_referrer_approvals, "more than one referrer approval"),
    ("semantic", "an approval derived by an agent", REFERRAL_ACTIVE, approval_derived_by_an_agent, "never one an agent derived"),
    ("semantic", "a platform suggestion transmitted as though it were a referral", REFERRAL_SUGGESTED, suggestion_transmitted_as_a_referral, "records referredAt"),
    ("semantic", "an active referral that names no disclosure grant", REFERRAL_ACTIVE, active_referral_without_a_grant, "names no disclosure grant"),
    ("semantic", "a referral disclosing more than the candidate's policy allows", REFERRAL_ACTIVE, referral_widens_the_profile_policy, "may not disclose beyond"),
    ("semantic", "a referral whose candidate is not the endorsed subject", ENDORSEMENT_ROLE, endorsement_is_about_someone_else, "not the referred candidate"),
    ("semantic", "a referral citing a relationship the referrer is not in", REFERRAL_ACTIVE, relationship_does_not_involve_the_referrer, "does not involve the referrer"),
    ("semantic", "a referral citing a relationship that does not exist", REFERRAL_ACTIVE, dangling_relationship_reference, "Unresolved reference"),
    ("semantic", "a referral citing somebody else's referral availability", REFERRAL_ACTIVE, availability_of_a_different_party, "not of the referrer"),
    ("semantic", "an active referral citing an availability whose window closed", REFERRAL_ACTIVE, active_referral_cites_a_closed_availability, "not an open one"),
    ("semantic", "a referral claiming to be bound to an unimplemented hiring intent", REFERRAL_ACTIVE, opportunity_claims_to_be_resolved, "resolves to nothing"),
    ("schema", "a pending referral that has already been transmitted", REFERRAL_SUGGESTED, pending_referral_that_was_transmitted, ""),
    ("schema", "an approval decision with no decision date", REFERRAL_ACTIVE, approved_without_a_decision_date, ""),
    ("schema", "an active referral carrying a single approval", REFERRAL_ACTIVE, active_referral_with_one_approval, ""),
    # bundle
    ("semantic", "one party identifier describing two different people", RELATIONSHIP_TAUGHT, one_identifier_two_people, "must name one party everywhere"),
]


def schema_rejects(instance: dict[str, Any], schema: dict[str, Any]) -> bool:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return any(True for _ in validator.iter_errors(instance))


def run() -> int:
    failures: list[str] = []

    for layer, description, target, mutate, expected in CASES:
        bundle = copy.deepcopy(BUNDLE)
        document = bundle[target]
        mutate(document)

        if layer == "schema":
            if not schema_rejects(document, SCHEMAS[document["@type"]]):
                failures.append(f"the {document['@type']} schema accepted {description}")
            continue

        try:
            v03.run_bundle_checks(bundle)
        except AssertionError as error:
            if expected not in str(error):
                failures.append(f"{description} was rejected for the wrong reason: {error}")
        else:
            failures.append(f"the semantic checks accepted {description}")

    if failures:
        print(f"{len(failures)} of {len(CASES)} v0.3 rule tests failed:")
        for failure in failures:
            print(f"  {failure}")
        return 1

    print(f"All {len(CASES)} v0.3 rule tests rejected their violating document.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
