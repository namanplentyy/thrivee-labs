"""Schema, semantic, reference, temporal and round-trip checks for the v0.3 trust layer.

v0.1 and v0.2 keep their own validators and are untouched. This module imports
validate_v0_2 by path and reuses its shared checks — source locators, validity
windows, disclosure precedence, taxonomy rules and the elevated-verification rule
— rather than restating them, because the trust documents reuse the v0.2 shared
definitions verbatim.

The trust layer is a graph of documents, not one document, so references are
resolved across a bundle: the v0.2 CareerProfile and OpportunityIntent plus every
v0.3 trust document. Two identifier namespaces are deliberately unresolvable here:
`requisition:` binds to the future HiringIntent contract and `grant:` to the future
DisclosureGrant contract. Both are recorded as deferred rather than silently
accepted as dangling.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator

sys.path.insert(0, str(Path(__file__).resolve().parent))

import validate_examples as v01  # noqa: E402
import validate_v0_2 as v02  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SCHEMAS = ROOT / "schemas"
EXAMPLES = ROOT / "examples" / "v0.3"
CONTEXT_DOCUMENT = ROOT / "contexts" / "trust-v0.3.context.jsonld"

RELATIONSHIP_SCHEMA = SCHEMAS / "relationship-assertion.v0.3.schema.json"
AVAILABILITY_SCHEMA = SCHEMAS / "referral-availability.v0.3.schema.json"
ENDORSEMENT_SCHEMA = SCHEMAS / "endorsement.v0.3.schema.json"
REFERRAL_SCHEMA = SCHEMAS / "referral.v0.3.schema.json"

DOCUMENT_ID_PROPERTY = {
    "CareerProfile": "profileId",
    "OpportunityIntent": "intentId",
    "RelationshipAssertion": "relationshipId",
    "ReferralAvailability": "referralAvailabilityId",
    "Endorsement": "endorsementId",
    "Referral": "referralId",
}

SCHEMA_BY_TYPE = {
    "RelationshipAssertion": RELATIONSHIP_SCHEMA,
    "ReferralAvailability": AVAILABILITY_SCHEMA,
    "Endorsement": ENDORSEMENT_SCHEMA,
    "Referral": REFERRAL_SCHEMA,
}

TRANSPORT_SCHEMA_BY_TYPE = {
    "RelationshipAssertion": SCHEMAS / "relationship-assertion.transport.v0.3.schema.json",
    "ReferralAvailability": SCHEMAS / "referral-availability.transport.v0.3.schema.json",
    "Endorsement": SCHEMAS / "endorsement.transport.v0.3.schema.json",
    "Referral": SCHEMAS / "referral.transport.v0.3.schema.json",
}

# Identifier namespaces that bind to contracts this repository has not implemented.
# They are reserved, not dangling: a consumer resolves them elsewhere or not at all.
DEFERRED_NAMESPACES = ("requisition:", "grant:")

ELEVATED_ASSURANCE = {
    "contact-verified",
    "domain-verified",
    "institution-verified",
    "platform-verified",
}

ENDORSEMENT_TARGET_NAMESPACES = {
    "capability": {"capability"},
    "skill": {"capability"},
    "artifact": {"artifact"},
    "project": {"engagement"},
    "engagement": {"engagement"},
    "role-performance": {"engagement"},
    "general": {"capability", "artifact", "engagement"},
}

BASIS_NAMESPACES = {"relationship", "engagement", "evidence", "artifact", "capability"}

SCOPE_KIND_BY_COLLECTION = {
    "organizations": "organization",
    "domains": "domain",
    "careerFamilies": "career-family",
}

VISIBILITY_PRECEDENCE = ("entityRefs", "sensitivities", "collections")

# The taxonomy subject registry is shared across document types. A referral
# availability may only classify its own scope entries.
v02.TAXONOMY_SUBJECT_NAMESPACES.setdefault("ReferralAvailability", {"referral-scope"})


fail = v02.fail
SemanticError = v02.SemanticError


def document_id(document: dict[str, Any]) -> str:
    return document[DOCUMENT_ID_PROPERTY[document["@type"]]]


def example_paths() -> list[Path]:
    return sorted(EXAMPLES.rglob("*.synthetic.jsonld"))


def load_bundle() -> dict[str, dict[str, Any]]:
    """Every document an agent would hold about this candidate, keyed by identifier."""
    bundle: dict[str, dict[str, Any]] = {}
    for path in (v02.PROFILE_EXAMPLE, v02.INTENT_EXAMPLE, *example_paths()):
        document = v01.load_json(path)
        bundle[document_id(document)] = document
    return bundle


def parties(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {party["id"]: party for party in document.get("parties", [])}


def collect_ids_with_root(document: dict[str, Any]) -> dict[str, tuple[object, ...]]:
    """v0.2 id collection, plus the document's own identifier at the root path.

    A trust document states facts directly on its root — a counterparty confirmation
    is not nested inside an identified entity — so a Verification targeting the
    document backs elevated provenance anywhere inside it.
    """
    identifiers = v02.collect_ids(document)
    identifier = document_id(document)
    if identifier in identifiers:
        fail(f"{identifier!r} is declared both as the document identifier and as an entity id.")
    identifiers[identifier] = ()
    return identifiers


def known_identifiers(bundle: dict[str, dict[str, Any]]) -> set[str]:
    known: set[str] = set(bundle)
    for document in bundle.values():
        for _, value in v01.walk(document):
            if isinstance(value, dict) and isinstance(value.get("id"), str):
                known.add(value["id"])
    return known


def check_bundle_references(bundle: dict[str, dict[str, Any]]) -> None:
    known = known_identifiers(bundle)
    for identifier, document in bundle.items():
        for path, key, reference in v02.iter_references(document):
            if reference.startswith(DEFERRED_NAMESPACES):
                continue
            if reference not in known:
                fail(
                    f"Unresolved reference {reference!r} at {v01.json_pointer((*path, key))} in "
                    f"{identifier}. Every trust reference must resolve inside the document bundle, "
                    "and only requisition: and grant: identifiers are deferred."
                )


def check_deferred_references(bundle: dict[str, dict[str, Any]]) -> None:
    """A deferred reference must name a reserved namespace, never an arbitrary string."""
    for identifier, document in bundle.items():
        opportunity = document.get("opportunity")
        if isinstance(opportunity, dict):
            if not opportunity["opportunityRef"].startswith("requisition:"):
                fail(f"{identifier} names an opportunity outside the reserved requisition: namespace.")
            if opportunity["bindingStatus"] == "resolved-hiring-intent":
                if opportunity["opportunityRef"] not in known_identifiers(bundle):
                    fail(
                        f"{identifier} claims bindingStatus 'resolved-hiring-intent' but "
                        f"{opportunity['opportunityRef']!r} resolves to nothing. HiringIntent is not "
                        "implemented, so a referral binds to a deferred requisition reference."
                    )


def check_party_consistency(bundle: dict[str, dict[str, Any]]) -> None:
    """One identifier, one person. Documents may disagree about assurance, never about who."""
    seen: dict[str, tuple[str, str | None, str | None, str]] = {}
    for identifier, document in bundle.items():
        for party in document.get("parties", []):
            record = (
                party["partyKind"],
                party["profileRef"],
                party["identifierUri"],
                identifier,
            )
            previous = seen.get(party["id"])
            if previous is None:
                seen[party["id"]] = record
                continue
            if previous[:3] != record[:3]:
                fail(
                    f"{party['id']} describes different parties in {previous[3]} and {identifier}. "
                    "A party identifier is a routing handle and must name one party everywhere."
                )


def check_parties(document: dict[str, Any]) -> None:
    identifier = document_id(document)
    confirmed_targets = {
        verification["targetRef"]
        for verification in document["verifications"]
        if verification["status"] == "confirmed"
    }
    for party in document["parties"]:
        if party["profileRef"] is None and party["identifierUri"] is None and party["displayName"] is None:
            fail(f"{party['id']} in {identifier} has no routable handle at all.")
        if party["identityAssurance"] in ELEVATED_ASSURANCE and party["id"] not in confirmed_targets:
            fail(
                f"{party['id']} claims identityAssurance {party['identityAssurance']!r} in "
                f"{identifier} with no confirmed Verification targeting it. Assurance above "
                "self-asserted is a checked fact, not a label."
            )


def resolve_visibility(document: dict[str, Any], entity_ref: str) -> str | None:
    """Disclosure precedence for one entity: entityRefs, sensitivities, collections, default."""
    collection_of: dict[str, tuple[str, dict[str, Any]]] = {}
    for collection, value in document.items():
        if not isinstance(value, list):
            continue
        for item in value:
            if isinstance(item, dict) and isinstance(item.get("id"), str):
                collection_of[item["id"]] = (collection, item)
    if entity_ref not in collection_of:
        return None
    collection, entity = collection_of[entity_ref]
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


# ------------------------------------------------------- relationship rules ---

def check_relationship(document: dict[str, Any]) -> None:
    identifier = document_id(document)
    party_a, party_b = document["partyARef"], document["partyBRef"]

    if party_a == party_b:
        fail(f"{identifier} relates {party_a} to itself.")
    if document["assertedByRef"] not in {party_a, party_b}:
        fail(
            f"{identifier} is asserted by {document['assertedByRef']}, who is neither party to it. "
            "A relationship is asserted by one of the two people in it."
        )

    counterparty = document["counterparty"]
    status = counterparty["status"]
    confirmed_by = counterparty["confirmedByRef"]
    last_confirmed = document["validity"]["lastConfirmedAt"]

    if status == "confirmed":
        if confirmed_by not in {party_a, party_b}:
            fail(f"{identifier} is confirmed by {confirmed_by}, who is not a party to it.")
        if confirmed_by == document["assertedByRef"]:
            fail(
                f"{identifier} is confirmed by the same party that asserted it. A unilateral claim "
                "must not become a mutually confirmed relationship without the other party acting."
            )
        if not counterparty["provenance"]:
            fail(f"{identifier} is confirmed with no provenance for how the confirmation was captured.")
        if last_confirmed != counterparty["confirmedAt"]:
            fail(
                f"{identifier} records confirmedAt {counterparty['confirmedAt']!r} but "
                f"validity.lastConfirmedAt {last_confirmed!r}. Confirmation is the same event in both."
            )
    else:
        if confirmed_by is not None or counterparty["confirmedAt"] is not None:
            fail(f"{identifier} is {status!r} but names a confirming party or date.")
        if last_confirmed is not None:
            fail(
                f"{identifier} is {status!r} but validity.lastConfirmedAt is set. An unconfirmed "
                "relationship has not been confirmed by anyone."
            )
        elevated = [
            provenance
            for provenance in counterparty["provenance"]
            if provenance["verificationStatus"] == "peer-endorsed"
        ]
        if elevated:
            fail(
                f"{identifier} is {status!r} but carries peer-endorsed provenance. A unilateral "
                "claim must stay distinguishable from a confirmed one."
            )

    if document["disclosure"]["defaultVisibility"] == "agent-discoverable":
        fail(
            f"{identifier} defaults to agent-discoverable. The relationship graph is restricted by "
            "default so that it cannot be harvested as a directory of people's networks."
        )

    for context in document["contexts"]:
        start, end = context["from"], context["to"]
        if start is not None and end is not None and end < start:
            fail(f"{context['id']} in {identifier} ends before it starts.")


# -------------------------------------------------------- endorsement rules ---

def check_endorsement(document: dict[str, Any]) -> None:
    identifier = document_id(document)
    endorser = parties(document).get(document["endorserRef"])
    if endorser is None:
        fail(f"{identifier} names endorser {document['endorserRef']}, who is not declared in it.")

    is_subject = endorser["profileRef"] == document["subjectRef"]
    if is_subject and not document["selfAttested"]:
        fail(
            f"{identifier} is attributed to the candidate themselves but is not marked selfAttested. "
            "Self-attestation is representable, but it must be stated rather than disguised as a "
            "third-party reference."
        )
    if document["selfAttested"] and not is_subject:
        fail(f"{identifier} is marked selfAttested but its endorser is not the subject.")

    for path, value in v01.walk(document):
        if not isinstance(value, dict) or "method" not in value or "verificationStatus" not in value:
            continue
        if value["method"] == "agent-inferred":
            fail(
                f"{identifier} carries agent-inferred provenance at {v01.json_pointer(path)}. "
                "An endorsement is a human act; a machine cannot vouch for anyone."
            )
        if document["selfAttested"] and value["verificationStatus"] != "self-attested":
            fail(
                f"{identifier} is selfAttested but claims verificationStatus "
                f"{value['verificationStatus']!r} at {v01.json_pointer(path)}."
            )

    allowed = ENDORSEMENT_TARGET_NAMESPACES[document["scope"]]
    for reference in document["targetRefs"]:
        namespace = reference.split(":", 1)[0]
        if namespace not in allowed:
            fail(
                f"{identifier} has scope {document['scope']!r} and may only endorse "
                f"{sorted(allowed)}, but names {reference!r}."
            )
    for reference in document["basisRefs"]:
        namespace = reference.split(":", 1)[0]
        if namespace not in BASIS_NAMESPACES:
            fail(
                f"{identifier} cites basis {reference!r}; a basis must name a relationship, "
                "engagement, evidence, artifact or capability."
            )


# ------------------------------------------------------- availability rules ---

def check_availability(document: dict[str, Any]) -> None:
    identifier = document_id(document)
    scope = document["scope"]
    populated = [
        name
        for name in ("organizations", "domains", "careerFamilies", "relationshipRequirements")
        if scope[name]
    ]
    status = document["status"]["value"]
    discoverability = document["discoverability"]["value"]

    if document["validity"]["validFrom"] is None:
        fail(f"{identifier} has no validity.validFrom; willingness is time-bounded state.")

    if status == "not-available":
        if populated:
            fail(
                f"{identifier} states not-available but populates {populated}. A stated refusal has "
                "no scope."
            )
        if discoverability != "none":
            fail(f"{identifier} states not-available but remains discoverable as {discoverability!r}.")
    if status == "limited" and not populated:
        fail(
            f"{identifier} states limited availability with an empty scope, which says nothing about "
            "what the referrer is willing to be asked."
        )

    for collection, expected_kind in SCOPE_KIND_BY_COLLECTION.items():
        for entry in scope[collection]:
            if entry["kind"] != expected_kind:
                fail(
                    f"{entry['id']} sits in scope.{collection} but has kind {entry['kind']!r}."
                )
            if expected_kind == "organization" and entry["organizationRef"] is None:
                fail(f"{entry['id']} scopes an organization without naming one.")

    if document["subjectRef"] not in parties(document):
        fail(f"{identifier} names subject {document['subjectRef']}, who is not declared in it.")


# ----------------------------------------------------------- referral rules ---

def check_referral(document: dict[str, Any], bundle: dict[str, dict[str, Any]]) -> None:
    identifier = document_id(document)
    local_parties = parties(document)
    approvals = document["approvals"]
    status = document["status"]

    by_role: dict[str, list[dict[str, Any]]] = {}
    for entry in approvals:
        by_role.setdefault(entry["role"], []).append(entry)
        if entry["actorRef"] not in local_parties:
            fail(f"{entry['id']} in {identifier} names an actor not declared in the document.")
        for provenance in entry["provenance"]:
            if provenance["method"] == "agent-inferred":
                fail(
                    f"{entry['id']} in {identifier} carries agent-inferred provenance. An approval "
                    "is a decision a person took, never one an agent derived."
                )

    for role in ("referrer", "candidate"):
        if len(by_role.get(role, [])) > 1:
            fail(f"{identifier} records more than one {role} approval.")

    referrer_approval = next(iter(by_role.get("referrer", [])), None)
    candidate_approval = next(iter(by_role.get("candidate", [])), None)

    if referrer_approval and referrer_approval["actorRef"] != document["referrerRef"]:
        fail(
            f"{identifier} has a referrer approval by {referrer_approval['actorRef']}, who is not "
            f"the referrer {document['referrerRef']}."
        )
    if candidate_approval:
        actor = local_parties[candidate_approval["actorRef"]]
        if actor["profileRef"] != document["candidateRef"]:
            fail(
                f"{identifier} has a candidate approval by {candidate_approval['actorRef']}, who "
                f"does not resolve to the candidate {document['candidateRef']}."
            )

    if status == "active":
        if referrer_approval is None or referrer_approval["decision"] != "approved":
            fail(
                f"{identifier} is active without an approved referrer decision. A referral is not "
                "actionable because a relationship exists; it is actionable because people agreed."
            )
        if candidate_approval is None or candidate_approval["decision"] != "approved":
            fail(f"{identifier} is active without an approved candidate decision.")
        if not document["disclosureGrantRefs"]:
            fail(
                f"{identifier} is active but names no disclosure grant. What the employer may read "
                "is decided by a grant, and a referral without one discloses nothing."
            )
        if document["validity"]["validFrom"] is None:
            fail(f"{identifier} is active with no validity.validFrom.")

    if document["referredAt"] is not None and status != "active":
        fail(
            f"{identifier} records referredAt while its status is {status!r}. A referral is only "
            "transmitted once it is active."
        )

    if document["availabilityRef"] is not None:
        availability = bundle.get(document["availabilityRef"])
        if availability is None:
            fail(f"{identifier} names an availability document that is not in the bundle.")
        elif availability["subjectRef"] != document["referrerRef"]:
            fail(
                f"{identifier} cites {document['availabilityRef']}, which states the willingness of "
                f"{availability['subjectRef']}, not of the referrer {document['referrerRef']}."
            )
        else:
            # Comparing the two documents' own windows keeps this decidable without a clock.
            closed = availability["validity"]["validUntil"]
            started = document["validity"]["validFrom"]
            if status == "active" and closed is not None and started is not None and closed < started:
                fail(
                    f"{identifier} is active from {started} but cites "
                    f"{document['availabilityRef']}, whose window closed on {closed}. A closed "
                    "availability is not an open one."
                )

    for reference in document["endorsementRefs"]:
        endorsement = bundle[reference]
        if endorsement["subjectRef"] != document["candidateRef"]:
            fail(
                f"{identifier} cites {reference}, which endorses {endorsement['subjectRef']} and not "
                f"the referred candidate {document['candidateRef']}."
            )

    for reference in document["relationshipRefs"]:
        relationship = bundle[reference]
        endpoints = {relationship["partyARef"], relationship["partyBRef"]}
        if document["referrerRef"] not in endpoints:
            fail(
                f"{identifier} cites {reference}, which does not involve the referrer "
                f"{document['referrerRef']}."
            )
        candidate_endpoints = {
            party_id
            for party_id in endpoints
            if parties(relationship)[party_id]["profileRef"] == document["candidateRef"]
        }
        if not candidate_endpoints:
            fail(
                f"{identifier} cites {reference}, which does not involve the referred candidate "
                f"{document['candidateRef']}."
            )


def check_referral_does_not_widen_policy(
    document: dict[str, Any], bundle: dict[str, dict[str, Any]]
) -> None:
    """A referral points at grants; it never publishes what the subject's policy protects."""
    identifier = document_id(document)
    profile = bundle[document["candidateRef"]]
    for rule in document["disclosure"]["rules"]:
        if rule["visibility"] != "agent-discoverable":
            continue
        for reference in rule["selector"]["entityRefs"]:
            subject_visibility = resolve_visibility(profile, reference)
            if subject_visibility is not None and subject_visibility != "agent-discoverable":
                fail(
                    f"{rule['id']} in {identifier} makes {reference!r} agent-discoverable, but the "
                    f"candidate's profile policy says {subject_visibility!r}. A referral may not "
                    "disclose beyond the policy and the grants it points at."
                )


# ---------------------------------------------------------------- per type ---

def run_relationship_checks(document: dict[str, Any]) -> None:
    """Every semantic rule a canonical RelationshipAssertion v0.3 must satisfy."""
    identifiers = collect_ids_with_root(document)
    v02.check_source_locators(document)
    v02.check_validity_windows(document, None)
    v02.check_disclosure(document)
    check_parties(document)
    # Before the generic elevated-verification rule, so that a unilateral claim dressed
    # as peer-endorsed is reported as the relationship-state error it actually is.
    check_relationship(document)
    v02.check_verifications(document, identifiers)


def run_availability_checks(document: dict[str, Any]) -> None:
    """Every semantic rule a canonical ReferralAvailability v0.3 must satisfy."""
    identifiers = collect_ids_with_root(document)
    v02.check_source_locators(document)
    v02.check_validity_windows(document, None)
    v02.check_disclosure(document)
    v02.check_verifications(document, identifiers)
    v02.check_taxonomy(document)
    check_parties(document)
    check_availability(document)


def run_endorsement_checks(document: dict[str, Any]) -> None:
    """Every semantic rule a canonical Endorsement v0.3 must satisfy."""
    identifiers = collect_ids_with_root(document)
    v02.check_source_locators(document)
    v02.check_validity_windows(document, None)
    v02.check_disclosure(document)
    v02.check_verifications(document, identifiers)
    check_parties(document)
    check_endorsement(document)


def run_referral_checks(document: dict[str, Any], bundle: dict[str, dict[str, Any]]) -> None:
    """Every semantic rule a canonical Referral v0.3 must satisfy."""
    identifiers = collect_ids_with_root(document)
    v02.check_source_locators(document)
    v02.check_validity_windows(document, None)
    v02.check_disclosure(document)
    v02.check_verifications(document, identifiers)
    check_parties(document)
    check_referral(document, bundle)
    check_referral_does_not_widen_policy(document, bundle)


CHECKS = {
    "RelationshipAssertion": lambda document, bundle: run_relationship_checks(document),
    "ReferralAvailability": lambda document, bundle: run_availability_checks(document),
    "Endorsement": lambda document, bundle: run_endorsement_checks(document),
    "Referral": run_referral_checks,
}


def run_bundle_checks(bundle: dict[str, dict[str, Any]]) -> None:
    check_bundle_references(bundle)
    check_deferred_references(bundle)
    check_party_consistency(bundle)
    for document in bundle.values():
        check = CHECKS.get(document["@type"])
        if check is not None:
            check(document, bundle)


# ----------------------------------------------------------------- harness ---

def check_context_parity(documents: Iterable[dict[str, Any]]) -> None:
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


def check_manifest(manifest: dict[str, Any]) -> None:
    entry = manifest["versions"]["0.3.0"]
    if entry.get("reusesSupplySideFrom") != "0.2.0":
        fail("Manifest entry 0.3.0 must declare that it reuses the v0.2 supply-side documents.")
    for key in ("jsonLdContext", "semanticContract", "converter"):
        if not (ROOT / entry[key]).is_file():
            fail(f"Manifest path does not exist: {entry[key]!r}")
    for name, paths in entry["documents"].items():
        for key in ("canonicalSchema", "transportSchema"):
            if not (ROOT / paths[key]).is_file():
                fail(f"Manifest path for {name} does not exist: {paths[key]!r}")


def transport_path(path: Path) -> Path:
    return path.with_name(path.name.replace(".synthetic.jsonld", ".transport.synthetic.json"))


def main() -> None:
    schemas = {
        name: v01.load_json(path) for name, path in SCHEMA_BY_TYPE.items()
    }
    transport_schemas = {
        name: v01.load_json(path) for name, path in TRANSPORT_SCHEMA_BY_TYPE.items()
    }
    for schema in (*schemas.values(), *transport_schemas.values()):
        Draft202012Validator.check_schema(schema)
    for schema in transport_schemas.values():
        v01.assert_transport_has_no_jsonld_keys(schema)

    check_manifest(v01.load_json(SCHEMAS / "schema-manifest.json"))

    canonical_documents = []
    for path in example_paths():
        document = v01.load_json(path)
        type_name = document["@type"]
        v01.validate_schema(document, schemas[type_name], f"Canonical {type_name} {path.name}")

        transport = v01.load_json(transport_path(path))
        v01.validate_schema(
            transport, transport_schemas[type_name], f"Transport {type_name} {path.name}"
        )
        v02.check_transport_example(transport, f"Transport example {path.name}")

        generated = v01.convert("--to-transport", path)
        if generated != transport:
            raise AssertionError(
                f"The transport example {transport_path(path).name} is stale. Regenerate it with "
                "scripts/convert-profile.mjs."
            )
        round_tripped = v01.convert("--to-canonical", transport_path(path))
        if round_tripped != document:
            raise AssertionError(
                f"The canonical/transport conversion for {path.name} is not lossless."
            )
        canonical_documents.append(document)

    check_context_parity(canonical_documents)
    run_bundle_checks(load_bundle())

    print(
        f"v0.3 trust schemas, {len(canonical_documents)} synthetic documents, bundle references, "
        "approvals, disclosure and round-trips are valid."
    )


if __name__ == "__main__":
    main()
