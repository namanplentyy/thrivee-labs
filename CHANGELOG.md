# Changelog

All notable changes to the schema and implementation contract are recorded here.

## 0.3.0-draft — 2026-09-01

A referral and trust layer. v0.1 and v0.2 are untouched in meaning and remain valid; `CareerProfile` and `OpportunityIntent` stay at schema version `0.2.0` and are not duplicated. There is nothing to migrate. See [docs/v0.3/versioning.md](docs/v0.3/versioning.md).

### Added

- Four canonical documents around the career profile, never inside it: `RelationshipAssertion` (who knows whom, and in what dated context), `ReferralAvailability` (whether a person currently wants to be asked, and about what), `Endorsement` (what someone will vouch for, and on what basis), and `Referral` (one referrer, one candidate, one opportunity).
- A `Party` primitive modelled on the existing `verifier` shape, so a professor or former manager who has never created a `CareerProfile` can be referenced by a routable identity without one being fabricated for them.
- Three distinguishable relationship states — asserted, confirmed by the counterparty, verified by a third party — with counterparty confirmation modelled as a party act and verification reusing the v0.2 `Verification` record unchanged.
- A closed relationship-type vocabulary with a real extension mechanism: `other` requires a `relationshipTypeExtensions[]` entry carrying the subject's own wording.
- First-class `approvals[]` on a referral. A referral reaches `active` only with an approved referrer decision and an approved candidate decision, each attributed, dated and human-provenanced. `platform-suggested` records how a workflow started and is never itself a referral.
- `discoverability` on referral availability (`none`, `anonymous-path-only`, `named`), so an employer agent can learn that referral paths exist without learning who is on them. Relationship documents may not default to `agent-discoverable`.
- Deferred binding to the two unimplemented contracts: a reserved `requisition:` reference to a future `HiringIntent` with `bindingStatus`, and reserved `grant:` references to future `DisclosureGrant`s. No job-description fields and no disclosure rules are duplicated into a referral, and a referral may not widen the candidate's own disclosure policy.
- Bundle-wide reference resolution: every trust reference must resolve across the candidate's documents, with `requisition:` and `grant:` the only deferred namespaces.
- A published `contexts/trust-v0.3.context.jsonld` typing every trust reference property as `@id`, so the documents expand to a real graph. `schema:knows` is deliberately not used as the relationship term.
- Ten synthetic trust documents forming one coherent scenario on the existing v0.2 synthetic candidate, in canonical and transport form, with no real people or organisations.
- Eleven agent-query fixtures and four new read-only fixture operations (`across`, `count`, `inWindow`, `disclose`), including the privacy case that resolves two referral paths while disclosing one name.
- Forty-three negative tests asserting that each v0.3 rule rejects a violating document.
- Normative documentation: the referral contract, the relationship and graph model, transport notes, fixture notes and a versioning note.

### Changed

- `verification.targetRef` in the v0.2 career-profile schema widened to also accept `party:`, `relationship:`, `endorsement:` and `referral:` targets. This is a relaxation: every previously valid document stays valid, and it exists so the trust layer reuses the `Verification` record rather than forking a second verification model.
- The transport build groups documents by `defsFamily` rather than by version, so shared definitions cannot drift between v0.2 and v0.3.
- The schema manifest gained a `0.3.0` document-set entry declaring `reusesSupplySideFrom: "0.2.0"`. `defaultExtractionVersion` stays `0.2.0`, because resume extraction still produces a v0.2 profile and the private conversion skill is unaffected.

### Deliberately excluded

- No `referrals[]`, `endorsements[]` or `connections[]` field was added to `CareerProfile`.
- No `referralStrength`, `referrerCredibility` or any other aggregate trust score. The factual inputs are exposed instead, and the weighing belongs to the consumer.
- No matching or ranking, referral recommendation, social-graph crawling, messaging, notifications, recruiter or candidate interface, ATS integration, marketplace, consent service, referral payments, reputation scores, fraud detection, MCP server or API endpoint.

### Status

- Draft for private re-evaluation; not yet a stable public standard.

## 0.2.0-draft — 2026-09-01

v0.1 is untouched and still valid. v0.2 is an additional version, and the schema manifest now defaults to it for new extraction runs.

### Added

- A second canonical document, `OpportunityIntent`, holding temporary employment-market state: looking status, availability and notice period, target roles, preferred locations, work mode, relocation, employment types, and an optional compensation expectation, all inside a validity window.
- First-class `Artifact`, `Evidence` and `Verification` entities, replacing evidence links nested inside a skill. Evidence membership must agree in both directions, and a claim above self-attested now requires a confirmed verification record.
- A `capabilities` collection with an explicit `capabilityKind`, distinguishing a tool, a skill, a body of knowledge, and a demonstrated practice, with `exercisesRefs` linking a practice to what it drew on.
- Temporal metadata (`validFrom`, `validUntil`, `observedAt`, `lastConfirmedAt`) on state that can become stale, and factual `freshness` metadata on the profile.
- A disclosure policy distinguishing `agent-discoverable`, `requires-grant` and `withheld`, with deterministic rule precedence and no requester identities or consent history.
- Top-level, provenance-aware taxonomy mappings covering capabilities and occupations, with `mappingStatus`, SKOS-style `matchType`, and unreviewed suggestions confined to `candidates[]`.
- `id` and `type` on every identified entity, JSON-LD keyword aliases in the context, a published context document, and resolution of every reference within a document.
- Agent-query fixtures and a deterministic runner, including negative fixtures whose correct answer is that the documents do not say.
- A negative test suite asserting that each v0.2 rule rejects a violating document.
- Design documents for the future demand-side schema (`RoleProfile` + `HiringIntent`) and the `DisclosureGrant` contract.

### Changed from v0.1

- Career intent moved out of `CareerProfile` into `OpportunityIntent`; work authorisation moved the other way, into profile attributes, because it is persistent.
- `skills[]` became `capabilities[]`; nested `evidenceLinks` and `taxonomyMappings` became top-level collections.
- References to `credential:` and `artifact:` identifiers no longer resolve to nothing.
- The transport build generates every document and fails when shared definitions drift apart.

### Status

- Draft for private re-evaluation; not yet a stable public standard.
- No matching or ranking algorithm, MCP server, API endpoint, ATS integration, marketplace, recruiter interface, decentralised registry, or consent service is included.

## 0.1.0-draft — 2026-08-01

### Added

- Canonical JSON-LD JSON Schema and generated structured-output transport schema.
- Claim-level provenance with source document, page, character offsets, text digest, normalization mode, confidence, verification state, and inferring-agent identity.
- Structured temporal periods with precision, current-status basis, ambiguity state, alternatives, and repeat occurrences.
- Separate representations for interests, languages, personal attributes, career targets, constraints, and preferences.
- Directional skill evidence and explicit distinction between context and evidence.
- Structured taxonomy mappings that exclude unreviewed agent inference.
- Shared claims and ambiguity records for unresolved source associations.
- TypeScript interfaces and lossless canonical/transport converters.
- Synthetic canonical and transport examples plus schema and semantic validation.
- Two-pass extraction, timeout, retry, and deterministic post-processing contract.

### Changed from the Phase 0 prototype

- Replaced flat values and entity-level source snippets with claim wrappers and source locators.
- Replaced flat engagement dates with one or more structured periods.
- Replaced generic intent claims with targets, hard constraints, and explicit preferences.
- Replaced string warnings with coded warning objects.

### Status

- Draft for private re-evaluation; not yet a stable public standard.
- No MCP server, API endpoint, decentralized registry, or automated taxonomy-mapping pipeline is included.
