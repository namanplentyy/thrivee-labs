# The trust graph: nodes, edges and what stays private

- Status: **draft**, companion to [the v0.3 referral contract](referrals.md)

v0.2 modelled a person. v0.3 models the people around them, as a graph of documents rather than as fields inside the profile.

## 1. Nodes

| Node | Identifier prefix | Custodian |
|---|---|---|
| Career profile | `profile:` | The candidate |
| Opportunity intent | `intent:` | The candidate |
| Party | `party:` | Declared by whichever trust document names it |
| Relationship assertion | `relationship:` | The party who asserted it, subject to the counterparty's confirmation |
| Referral availability | `referral-availability:` | The referrer |
| Endorsement | `endorsement:` | The endorser |
| Referral | `referral:` | Jointly held; it exists because two people approved it |
| Hiring intent | `requisition:` | The employer. **Reserved and deferred** |
| Disclosure grant | `grant:` | The person granting. **Reserved and deferred** |

A `Party` is not a `CareerProfile`. It is the smallest thing that can be pointed at: it says *who*, and where to reach them, and nothing about their career. A referrer who has never joined the platform is a party with an `identifierUri` and a null `profileRef`, which is why v0.3 never has to fabricate a profile for a professor or a former manager.

## 2. Edges

```
Candidate ───── HAS_RELATIONSHIP ──────▶ Referrer
                (RelationshipAssertion: partyARef → partyBRef)

Relationship ── OCCURRED_IN ───────────▶ Engagement          (contexts[].engagementRef)
Relationship ── CONFIRMED_BY ──────────▶ Party               (counterparty.confirmedByRef)
Relationship ◀─ VERIFIES ─────────────── Verification        (targetRef)

Endorser ────── ENDORSES ──────────────▶ Candidate           (Endorsement: endorserRef → subjectRef)
Endorsement ─── SUPPORTS ──────────────▶ Capability          (targetRefs)
Endorsement ─── RESTS_ON ──────────────▶ Relationship        (basisRefs)
                                         Engagement
                                         Evidence, Artifact

Referrer ────── IS_AVAILABLE_FOR ──────▶ Scope               (ReferralAvailability: subjectRef → scope)

Referrer ────── REFERS ────────────────▶ Candidate           (Referral: referrerRef → candidateRef)
Referral ────── FOR ───────────────────▶ HiringIntent        (opportunity.opportunityRef, deferred)
Referral ────── DRAWS_ON ──────────────▶ Relationship        (relationshipRefs)
                                         Endorsement         (endorsementRefs)
Referral ────── APPROVED_BY ───────────▶ Party               (approvals[].actorRef)
Referral ────── PERMITS_UNDER ─────────▶ DisclosureGrant     (disclosureGrantRefs, deferred)
```

Every edge is a stable identifier. No edge is a name string: two people with the same display name are two parties, and a party with no display name is still a usable node.

## 3. JSON-LD semantics

The published context is `contexts/trust-v0.3.context.jsonld`. It carries the v0.2 career terms verbatim plus the trust reference properties, each typed `@id` so an expanded document is a real graph rather than a tree of strings. Instances keep the same six-term inline context v0.2 uses, so no `@`-prefixed key appears inside an entity and the transport form stays a pure key rename.

Set-valued reference terms — `targetRefs`, `basisRefs`, `relationshipRefs`, `endorsementRefs`, `disclosureGrantRefs` — declare `"@container": "@set"`, so a single value and a list expand identically.

**On external vocabularies.** `schema.org` has `schema:knows`, and it is deliberately *not* used as the term for a relationship assertion. `schema:knows` says two people know each other and nothing else: it cannot express who asserted it, whether the other party agreed, in which engagement it happened, or whether anybody checked. Collapsing `RelationshipAssertion` onto it would discard exactly the distinctions this layer exists to make. It is a broader relation that a consumer may infer from ours; it is not a substitute for it. Where an external term genuinely fits without loss — `schema:Person`, `schema:Organization` for a party's kind — mapping is welcome.

## 4. Reference resolution across documents

v0.2 requires every reference to resolve inside its own document, with one documented exception. The trust layer is inherently multi-document, so v0.3 states the rule at the level of a **bundle**: the candidate's profile and intent, plus the trust documents an agent holds.

| Reference class | Must resolve |
|---|---|
| Within-document (`parties[]`, approvals, scope entries, disclosure selectors) | In its own document |
| Cross-document (`engagementRef`, `targetRefs`, `basisRefs`, `relationshipRefs`, `endorsementRefs`, `availabilityRef`, `candidateRef`) | Anywhere in the bundle |
| Deferred (`requisition:`, `grant:`) | Nowhere. Reserved for contracts this repository has not implemented |

A reference outside those three classes is a dangling reference and is rejected. `scripts/validate_v0_3.py` resolves the whole bundle at once, which is why a referral citing an endorsement of a different candidate, or an endorsement of a capability the profile does not have, fails rather than passing quietly.

Identifiers may legitimately repeat across documents — the same party, the same scope entry — because documents are exchanged independently. What may not vary is who a party is: `partyKind`, `profileRef` and `identifierUri` must agree everywhere the identifier appears.

## 5. Privacy properties of the graph

The graph is designed so that the interesting question an employer agent can ask without permission is a **count**, not a list.

1. `RelationshipAssertion` may not default to `agent-discoverable`. Relationship documents are restricted or withheld.
2. Names are exposed only through a referrer's own `ReferralAvailability.discoverability: "named"`, or after that referrer approved a referral and a grant covers it.
3. A referral cannot widen the candidate's profile policy; anything the profile marks `withheld` stays withheld.
4. Nothing in the layer records who searched, who viewed, or who asked. Those belong to an audit log, which is not part of this contract and must never enter a career profile.

The worked query is `examples/v0.3/queries/how-many-referral-paths-exist.json`: at an explicit date it resolves two eligible paths, discloses one name because that referrer opted in, and withholds the other.
