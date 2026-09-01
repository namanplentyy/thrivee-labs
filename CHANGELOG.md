# Changelog

All notable changes to the schema and implementation contract are recorded here.

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
