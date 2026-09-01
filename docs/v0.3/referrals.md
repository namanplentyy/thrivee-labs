# Referral and trust contract v0.3

- Status: **draft**
- Schema version: `0.3.0`
- Canonical schemas: `schemas/relationship-assertion.v0.3.schema.json`, `schemas/referral-availability.v0.3.schema.json`, `schemas/endorsement.v0.3.schema.json`, `schemas/referral.v0.3.schema.json`
- JSON-LD context: `contexts/trust-v0.3.context.jsonld`

The JSON Schemas are authoritative for structure. This document is authoritative for the semantic rules that JSON Schema cannot express. `scripts/validate_v0_3.py` implements those rules and `scripts/test_v0_3_rules.py` proves each one rejects a violating document.

v0.1 and v0.2 are unchanged in meaning and remain valid. See [versioning](versioning.md) for what v0.3 does and does not touch.

## 1. Why referrals are not a field on `CareerProfile`

Hiring in professional niches is not decided by candidate-role fit alone. Employers rely on people who can credibly vouch for a candidate. That fact does not make a referral part of a career profile.

A referral is contextual, usually employer- and role-specific, permissioned, time-sensitive, created by another person, potentially withdrawn, and it changes constantly while the candidate's career history does not. `CareerProfile` therefore gains nothing in v0.3: no `referrals[]`, no `endorsements[]`, no `connections[]`. The trust layer is a graph of separate documents *around* the profile.

```
CareerProfile + OpportunityIntent          supply
            ↕
      Matching Layer
            ↕
RoleProfile + HiringIntent                 demand (design only)

            +

RelationshipAssertion + ReferralAvailability + Endorsement + Referral
            ↓
        Trust Layer                        v0.3
            ↓
      DisclosureGrant                      (design only)
```

## 2. Four documents

| Document | `@type` | Answers | Lifetime |
|---|---|---|---|
| Relationship assertion | `RelationshipAssertion` | Who knows whom, and in what context | Long-lived. A past relationship stays true |
| Referral availability | `ReferralAvailability` | Is this party currently willing to be asked for referrals, and about what | Temporary. Carries a validity window and expires |
| Endorsement | `Endorsement` | What can this party vouch for about this candidate, and on what basis | Medium. Reusable across opportunities |
| Referral | `Referral` | Will this party refer this candidate for this opportunity, and has everyone agreed | Short, role-specific, expires |

Each is a standalone document with its own identifier, its own `validity`, its own `disclosure` policy and its own custodian. `ReferralAvailability` is to referrals what `OpportunityIntent` is to job search: the temporary half, held apart from the durable facts.

**Having a relationship is not willingness to refer.** A person may know hundreds of people and want no referral requests at all. **Absence is absence**: a party with no `ReferralAvailability` has not stated `not-available`, exactly as a person with no `OpportunityIntent` has not stated `not-looking`.

## 3. Parties, and referrers who have no profile

A referrer is often a professor, a former manager or an industry contact who has never created a `CareerProfile`. v0.3 does not invent one for them.

Every trust document declares the parties it names in `parties[]`. A `Party` is a routing handle, modelled on the existing `verifier` definition: a kind, an optional profile reference, an optional display name, an optional routable `identifierUri`, and an assurance level. It carries no history, no capabilities and no evidence.

| Situation | Representation |
|---|---|
| The candidate | `partyKind: person`, `profileRef` naming their `CareerProfile` |
| A referrer who uses the platform | `partyKind: person`, `profileRef` naming their profile |
| A referrer who does not | `partyKind: person`, `profileRef: null`, `identifierUri` routing to them |
| An organisation providing context | `partyKind: organization` |

At least one of `profileRef`, `identifierUri` or `displayName` must be present, so a party is always addressable.

`identityAssurance` above `self-asserted` requires a confirmed `Verification` in the same document whose `targetRef` names the party. Assurance is a checked fact, not a label. Documents may legitimately differ on assurance for the same party, because assurance is evidence held by that document; they may never differ on `partyKind`, `profileRef` or `identifierUri`, because those say *who the party is*.

## 4. Relationship assertions, and the three states of knowing someone

`relationshipTypes` uses a closed vocabulary — `manager`, `direct-report`, `colleague`, `project-collaborator`, `professor`, `student`, `intern-supervisor`, `classmate`, `alumni-connection`, `client`, `mentor`, `other` — and `other` is not a dumping ground: it requires at least one `relationshipTypeExtensions[]` entry carrying the subject's own wording. A relationship the enumeration cannot express is stated in the subject's words rather than approximated.

`contexts[]` anchors the relationship to where and when it happened, and `engagementRef` names an engagement in the candidate's profile, so a relationship points at a dated, evidenced context instead of floating free.

Three states must stay distinguishable, and the schema keeps them apart:

| State | How it is represented |
|---|---|
| The candidate says they know someone | `counterparty.status: "unconfirmed"`, provenance `user-entered` / `self-attested` |
| The other party confirms | `counterparty.status: "confirmed"`, with `confirmedByRef`, `confirmedAt` and its own provenance |
| A third party verifies the facts | A `Verification` record whose `targetRef` names the relationship |

These are different dimensions, not points on one scale. A confirmation is a *party act*; a verification is a *third party checking*. Normatively:

- `assertedByRef` must be one of the two parties.
- A confirmation must come from the party that did not assert it. A unilateral claim cannot confirm itself.
- A confirmed relationship carries provenance for the confirmation, and `validity.lastConfirmedAt` equals `counterparty.confirmedAt`.
- An unconfirmed relationship names no confirming party or date, leaves `lastConfirmedAt` null, and must not carry `peer-endorsed` provenance.
- The two parties must be different, and a context must not end before it starts.

## 5. Endorsements

An endorsement is not a referral. It is not tied to one opportunity and often stays useful across many.

`scope` states what kind of thing is endorsed — `general`, `capability`, `skill`, `artifact`, `project`, `engagement`, `role-performance` — and any scope other than `general` requires at least one `targetRefs` entry naming what is being endorsed. The namespace must match the scope: a `capability` or `skill` endorsement names capabilities, an `artifact` endorsement names artifacts, and `project`, `engagement` and `role-performance` name engagements.

"Can vouch for spatial analysis, based on the coursework I taught" is machine-readable. "Strong candidate" is representable as `scope: general`, and it is deliberately much weaker information.

`basisRefs` states what the endorsement rests on, and may only name a relationship, engagement, evidence, artifact or capability.

Two rules protect the meaning of the word:

- **No agent-inferred provenance anywhere in an endorsement.** A machine cannot vouch for anyone.
- **Self-attestation is stated, never disguised.** If the endorser's party resolves to the subject's own profile, `selfAttested` must be `true`, and every provenance record must then carry `verificationStatus: self-attested`. A candidate praising themselves is representable; a candidate praising themselves while appearing to be a third-party reference is not.

## 6. Referral availability

| Field | Meaning |
|---|---|
| `status` | `open`, `limited`, or `not-available`, as a claim with provenance |
| `discoverability` | `none`, `anonymous-path-only`, or `named` |
| `scope` | Organisations, domains, career families, and the relationship types the referrer will consider |
| `validity` | `validFrom` is required; willingness is time-bounded state |

Rules:

- `not-available` is a stated refusal, so its scope is empty and its discoverability is `none`.
- `limited` requires at least one populated scope dimension, because limited availability with no scope says nothing.
- Scope entries sit in the collection matching their `kind`, and an organisation scope entry names an organisation party.
- Scope entries may carry `taxonomyMappings`, so "willing to help with urban transport roles" joins to the same NCO or ESCO code the candidate's engagements carry, instead of matching free text.

Expiry is evaluated against a caller-supplied reference date, never the system clock. An availability whose window has closed is not open, and it is not `not-available` either.

## 7. Referrals

A `Referral` is one referrer, one candidate, one opportunity.

`origin` records how the workflow started: `candidate-requested`, `employer-requested`, `referrer-initiated` or `platform-suggested`. **`platform-suggested` is never itself a referral.** It records that software noticed a possible path, and nothing more.

`opportunity` carries a stable `requisition:` reference with `bindingStatus: "deferred-hiring-intent"`. Job-description fields are not duplicated into the referral; `label` exists so a document is readable, not so a requisition can be reconstructed from it. When the demand side is implemented, `opportunityRef` resolves to a `HiringIntent` and the binding status becomes `resolved-hiring-intent`. Claiming that status today fails validation, because nothing resolves.

### 7.1 Approvals are first-class

```jsonc
"approvals": [
  { "actorRef": "party:s-example", "role": "referrer",  "decision": "approved", "decidedAt": "..." },
  { "actorRef": "party:a-example", "role": "candidate", "decision": "approved", "decidedAt": "..." }
]
```

`decision` is one of `pending`, `approved`, `declined`, `withdrawn`, `expired`. Any decision other than `pending` requires `decidedAt` and provenance.

**A referral reaches `status: "active"` only when every required actor has approved it.** At minimum that is the referrer and the candidate. The employer does not approve a referral; employer interest is the demand event that initiated or receives it.

| Rule | Normative statement |
|---|---|
| Both approvals | `active` requires a `referrer` approval and a `candidate` approval, each `approved` |
| Right people | The referrer approval's actor is the referrer; the candidate approval's actor resolves to `candidateRef` |
| One each | At most one `referrer` and one `candidate` approval per referral |
| Human decisions | No approval may carry `agent-inferred` provenance |
| Transmission | `referredAt` is set only while the referral is active |
| Grant required | An active referral names at least one `disclosureGrantRefs` entry |
| Honest citations | Every cited endorsement endorses this candidate; every cited relationship involves both this referrer and this candidate |
| Honest availability | A cited `availabilityRef` states the willingness of this referrer, not of somebody else |

`status` is `pending`, `active`, `declined` or `withdrawn`. **Expiry is not a status.** It is computed from `validity.validUntil` against a caller-supplied date, following the v0.2 rule that neither producers nor consumers read the system clock. An individual approval may still carry the decision `expired`, because that is a decision that lapsed rather than a document that aged.

## 8. Disclosure: the referral points at grants, it does not become one

The chain is deliberately kept in three parts:

```
Referral approved  →  DisclosureGrant  →  Employer may read the permitted fields
```

The referral names the applicable grants in `disclosureGrantRefs` and stops there. `grant:` identifiers are reserved and deferred; the contract is designed in [docs/design/disclosure-grant.md](../design/disclosure-grant.md) and is not implemented.

One rule connects the two layers today: **a referral may not widen the candidate's own policy.** If a referral's disclosure rules make an entity `agent-discoverable` while the candidate's `CareerProfile` marks it `requires-grant` or `withheld`, the document is rejected. This preserves the design-document rule that `withheld` is not overridable by a grant, and it keeps the profile's policy the single readable statement of what the person is willing to share.

## 9. The relationship graph is restricted by default

That a candidate knows a senior figure must not become a searchable fact.

- `RelationshipAssertion.disclosure.defaultVisibility` may not be `agent-discoverable`. The validator rejects it.
- What an employer agent should be able to learn without permission is *"two eligible referral paths exist"*, not *"S. Example and R. Example can refer this candidate."*
- A name is exposed only where the potential referrer opted in through `ReferralAvailability.discoverability: "named"`, or where they subsequently approved the referral and a grant covers it.

| `discoverability` | What a consumer may learn before any approval |
|---|---|
| `none` | Nothing |
| `anonymous-path-only` | That a path exists, and the factual attributes of the relationship — never the party's name |
| `named` | The referrer's name, subject to the document's disclosure policy |

This is what stops the trust layer becoming a machine-readable directory for harvesting people's professional networks.

## 10. Facts, not scores

There is no `referralStrength`, no `referrerCredibility`, no aggregate trust number, and `additionalProperties: false` means one cannot be added without changing the schema. `provenance.confidence` remains what it is in v0.1 and v0.2: confidence in a single extracted claim, never a judgement about a person.

What the documents expose instead are the inputs a consumer can weigh for itself:

| Fact | Where it lives |
|---|---|
| Relationship type, and manager versus peer | `RelationshipAssertion.relationshipTypes` |
| Shared organisation or project | `contexts[].organizationRef`, `contexts[].engagementRef` |
| Duration and recency | `contexts[].from` / `to`, `validity` |
| Confirmed versus unilateral | `counterparty.status` |
| Independently verified | `verifications[]` |
| What is endorsed, and on what basis | `Endorsement.targetRefs`, `basisRefs`, `scope` |
| When it was endorsed, and when referred | `Endorsement.validity`, `Referral.referredAt` |
| Whether a human actually approved | `Referral.approvals[]` |

An employer agent decides what those facts are worth. This project defines no weighting, no threshold and no ordering — the same position v0.2 takes on matching.

## 11. What v0.3 does not include

No matching or ranking, no referral recommendation algorithm, no social-graph crawling or scraping, no messaging or notifications, no recruiter or candidate interface, no ATS integration, no marketplace, no consent service, no referral payments or bonuses, no reputation scores, no fraud detection, and no MCP server or API endpoint. v0.3 defines the data contracts such systems would exchange; it does not build the systems.
