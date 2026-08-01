# Changelog

All notable changes to the schema and implementation contract are recorded here.

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
