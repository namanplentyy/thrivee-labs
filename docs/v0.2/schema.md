# Career schema v0.2 contract

- Status: **draft**
- Schema version: `0.2.0`
- Canonical schemas: `schemas/career-profile.v0.2.schema.json`, `schemas/opportunity-intent.v0.2.schema.json`
- JSON-LD context: `contexts/career-v0.2.context.jsonld`

The JSON Schemas are authoritative for structure. This document is authoritative for semantic rules that cannot be expressed completely in JSON Schema. `scripts/validate_v0_2.py` implements those rules and `scripts/test_v0_2_rules.py` proves each one rejects a violating document.

v0.1 is unchanged and remains valid. v0.2 is a separate version, not a patch of v0.1.

## 1. Two documents

v0.2 separates a person's persistent career state from their temporary position in the employment market.

| Document | `@type` | Holds | Lifetime |
|---|---|---|---|
| Career profile | `CareerProfile` | identity, history, capabilities, artifacts, evidence, verifications, taxonomy mappings, interests, languages, attributes | Persistent. Grows; entries are not deleted when a job search ends |
| Opportunity intent | `OpportunityIntent` | looking status, availability, target roles, preferred locations, work mode, relocation, employment types, compensation expectation | Temporary. Carries a validity window and expires |

The intent document names its subject with `subjectRef`. The profile carries no reference back, so market state can change, expire, or be deleted without rewriting career history. A person may have no intent document at all; that is not the same as `not-looking`, which is a stated position.

Placement follows one question: does this stay true when the person stops looking for work? Work authorisation, languages and credentials stay true and belong in the profile. A notice period, an availability date and a target role do not, and belong in the intent document.

All collection properties are present even when empty, in both documents. A producer that could not process a section emits a warning rather than omitting the section.

## 2. Claims and provenance

The v0.1 claim and provenance model is carried over unchanged, including the `resume-explicit`, `deterministic-normalization` and `agent-inferred` rules and the source-locator semantics. See [the v0.1 contract](../v0.1/schema.md#2-claim-and-provenance-model); only the additions below are new.

`verificationStatus` remains a summary dimension on each provenance record. In v0.2 it is also constrained: a status of `institution-verified` or `peer-endorsed` requires a `Verification` record with status `confirmed` whose `targetRef` resolves to that claim or to an entity enclosing it. Provenance inside a `Verification` is exempt, because requiring a verification of a verification would be circular.

## 3. Identifiers, types and references

Every identified entity carries `id` and `type`. The context aliases `id` to `@id` and `type` to `@type`, so each entity is a JSON-LD node rather than an anonymous nested object, while the serialised keys stay free of `@` and remain transport-safe.

Identifier prefixes are URI schemes and are treated as opaque IRIs: `profile:`, `intent:`, `claim:`, `source:`, `identity:`, `engagement:`, `period:`, `shared-claim:`, `capability:`, `artifact:`, `evidence:`, `verification:`, `taxonomy-mapping:`, `interest:`, `language:`, `attribute:`, `ambiguity:`, `warning:`, `disclosure:`, `disclosure-rule:`, `target:`, `location:`, `employment-type:`, `compensation:`, `constraint:`, `preference:`.

Claim wrappers carry an `id` but no `type`: their type is implied by the property that holds them. This is the only identified object without a type.

`contexts/career-v0.2.context.jsonld` holds the full term definitions, including the reference properties typed as `@id` and the `matchType` values aliased to their SKOS mapping relations. Instances keep the smaller inline context so that no `@`-prefixed key appears inside an entity and the transport form stays a pure key rename. The validator checks that the two agree on every term they share. It does not run a JSON-LD processor, so expansion itself is not machine-verified in this repository.

Identifiers are unique within a document. Every property ending in `Ref` or `Refs` must resolve to an identifier declared in the same document. v0.1 exempted `credential:` and `artifact:` references from resolution; v0.2 removes that exemption, since artifacts are now declared entities. The single cross-document reference is `OpportunityIntent.subjectRef`, which must equal the `profileId` of the profile it describes.

## 4. Temporal validity and freshness

State that can become stale carries a `validity` object.

| Field | Meaning |
|---|---|
| `validFrom` | When the state began to hold |
| `validUntil` | When it stops holding. `null` means no stated end, not "forever" |
| `observedAt` | When a producer observed the state |
| `lastConfirmedAt` | When the subject or an authoritative issuer last confirmed it |

Extraction time is an observation, not a confirmation. A profile built from a resume has `observedAt` set and `lastConfirmedAt` null. `validUntil` must not precede `validFrom`.

Consumers must evaluate expiry against an explicit reference date supplied by the caller. Neither a producer nor a consumer may read the system clock to decide that something has lapsed, for the same reason v0.1 forbids inferring completion from the current date.

`freshness` on the profile is factual and derived, not editorial:

| Field | Rule |
|---|---|
| `profileGeneratedAt` | When this representation was produced |
| `lastSourceIngestedAt` | The latest `sourceDocuments[].ingestedAt`, or null |
| `lastSubjectConfirmedAt` | The latest `validity.lastConfirmedAt` in the document, or null |
| `lastVerificationAt` | The latest `verifiedAt` among confirmed verifications, or null |
| `staleAfter` | An explicit stated expiry for the profile as a whole, or null |

The three derived values are validated against the document and must not be later than `profileGeneratedAt`. v0.2 deliberately defines no profile quality, completeness, or strength score. A consumer that wants one computes it and owns it.

## 5. Career history

`history`, its engagement types, current-status rules, date precision, alternatives and the NCrF/NSQF abstentions are unchanged from v0.1. Each period now carries a `period:` identifier so evidence and ambiguity records can reference an occurrence directly.

## 6. Capabilities

v0.2 replaces `skills` with `capabilities` and requires each entry to say what kind of thing it is.

| `capabilityKind` | Meaning | Example |
|---|---|---|
| `tool` | An instrument that is used | QGIS |
| `skill` | An ability that is applied | Spatial analysis |
| `knowledge` | A domain that is known | Transport demand modelling |
| `practice` | Something demonstrably carried out | Conducting a transport accessibility analysis |

`exercisesRefs` records the tools and skills a capability drew on. Only a `skill` or a `practice` may exercise other capabilities; a tool or a body of knowledge may not, and the graph may not contain a cycle.

`contextRefs` situate a capability in an engagement or an unresolved shared claim. Context is not evidence, exactly as in v0.1.

`evidenceRefs` name `Evidence` records. Membership must agree in both directions: if a capability lists an evidence record, that record's `subjectRef` must name the capability, and every evidence record must be listed by its subject. A capability whose `claimStatement` is agent-inferred requires at least one evidence record. So does a non-null `lastDemonstratedAt`, which may only carry a date the source states or a date normalised deterministically from linked evidence.

`proficiency` preserves the source wording and is never converted to an invented scale.

## 7. Artifacts, evidence and verification

Three separate entities model the chain from a claim to what supports it and to who checked it.

```
Capability --evidenceRefs--> Evidence --targetRef--> Artifact | Engagement | SharedClaim | SourceDocument | TemporalPeriod
                                 ^
                                 |  targetRef
                            Verification
```

- `Artifact` is a thing that exists: a report, repository, credential record, assessment result, reference letter, and so on. It is declared even when no URI is available, so that evidence always resolves to something inspectable. `accessMode` states whether it is public, available on request, private, or unknown.
- `Evidence` is a directional edge with the v0.1 relation vocabulary: `DemonstratedIn`, `LearnedIn`, `ProducedIn`, `AssessedBy`, `SupportedBy`, `MentionedIn`. `MentionedIn` remains the honest relation for a capability the source only names.
- `Verification` records who checked something, by what method, when, and with what outcome. It points at its target; targets carry no back-references, so there is exactly one place to update when a verification changes. `status: confirmed` requires a `verifiedAt`.

A verification's `validity` may expire. An expired verification is not retracted; it is a verification whose window has closed, and consumers evaluate that against their own reference date.

## 8. Taxonomy mappings

Mappings are first-class entities with their own identifiers, subject reference, provenance and validity. A mapping may describe a capability, an engagement, an interest or an attribute in a profile, and a target role in an intent document.

| `mappingStatus` | `code` | Meaning |
|---|---|---|
| `mapped` | required | A code has been adopted |
| `unmapped` | null | Reviewed and no code applies, or never attempted. `mappingMethod` distinguishes the two |
| `ambiguous` | null | Several codes are plausible and none has been adopted. At least two candidates are required |
| `rejected` | null | A previously considered code was ruled out |

An adopted code requires `mappingMethod` of `explicit-in-source`, `registry-verified` or `manual-reviewed`, and must not carry `agent-inferred` provenance. `matchType` states how close the correspondence is, using the SKOS mapping relations: `exact-match`, `close-match`, `broad-match`, `narrow-match`, `related-match`.

Unreviewed machine suggestions live in `candidates[]` with `method: agent-suggested` and a confidence. A candidate never becomes the adopted code without review. This preserves v0.1's rule that agents do not assign taxonomy codes, while letting the document say what it suspects and how strongly.

An unknown mapping stays unknown, and stays visible. Recording an `unmapped` or `ambiguous` mapping is preferred to an empty array, because it distinguishes "we looked and found nothing" from "nobody looked". Every ambiguous mapping must be related to an `Ambiguity` record.

## 9. Disclosure

`disclosure` states what an agent may read without asking. It is a policy, not a transaction log.

`visibility` is one of `agent-discoverable`, `requires-grant` or `withheld`. Each rule selects by exactly one dimension, and resolution takes the first match in this order:

1. `selector.entityRefs` names specific entities;
2. `selector.sensitivities` names a sensitivity class;
3. `selector.collections` names a top-level collection;
4. otherwise `defaultVisibility`.

Because each rule uses one dimension and two rules may not give the same selector value conflicting visibilities, resolution is deterministic. A named collection must exist in the document.

`sensitivity` and `visibility` are different things and are not merged: sensitivity classifies what the data is, visibility records what the subject permits. A highly sensitive value may still be withheld outright, which is exactly the case the precedence order exists for.

This object never records requester identities, employer-specific consent history, or marketplace transactions. Authorising a named requester to receive selected fields is the separate `DisclosureGrant` contract, designed in [docs/design/disclosure-grant.md](../design/disclosure-grant.md) and deliberately not implemented in v0.2.

## 10. Opportunity intent

`validity.validFrom` is required: intent is state that started being true at some point. `validUntil` may be null when the subject stated no end date, and consumers then fall back to `lastConfirmedAt` plus their own policy.

Six matching dimensions have typed fields and must be expressed there: preferred locations, work mode, relocation, employment types, availability, and compensation expectation. `constraints` and `preferences` cover everything else — schedule, travel, work environment, company stage, industry, contract duration, team size — and their `kind` enumeration deliberately excludes the typed dimensions, so a producer cannot state the same thing twice in two shapes.

`compensationExpectation` is null unless the subject stated one. An amount requires an explicit currency and period, and `basis` distinguishes gross, net and CTC. Nothing about compensation is inferred from role, location, or history.

`relocation.willingness: conditional` requires stated conditions. An interest, an education subject or a past employer never creates intent; only direct statements do, as in v0.1.

One asymmetry is deliberate and known: locations are structured on the intent side (`locationPreference`, with granularity and an optional country code) but remain claim-wrapped strings in the profile, where they describe where work happened rather than where the person wants to work. Structuring profile-side locations is a later change, and the intent-side definition is the one the demand-side documents will reuse.

## 11. Ambiguity, shared claims and warnings

Unchanged from v0.1, with two additions: the ambiguity `kind` enumeration gains `taxonomy-mapping`, and warnings now carry a `warning:` identifier so other records can reference them.

## 12. What v0.2 does not include

No matching or ranking algorithm, no MCP server or API endpoint, no ATS integration, no marketplace, no recruiter interface, no decentralised identifiers or verifiable-credential envelopes, no consent service, no skill-decay model, and no automated taxonomy inference beyond recording an unreviewed suggestion as a candidate.
