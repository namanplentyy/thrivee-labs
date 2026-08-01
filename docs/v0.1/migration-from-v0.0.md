# Migrating the Phase 0 v0.0 prototype to v0.1

The Phase 0 schema was a feasibility probe. v0.1 intentionally makes breaking changes based on the six-resume pilot.

| v0.0 | v0.1 | Migration behavior |
|---|---|---|
| `identity.claims[]` | `identity[]` | Move each claim and wrap its value in a claim object with provenance. |
| `history[].engagementType` | `history[].engagementType.value` | Preserve the type and add provenance for the classification. |
| `dateRaw`, `start`, `end`, `isCurrent` | `periods[]` | Create a structured period with precision, current-status basis, interpretation status, and provenance. |
| One continuous date range | Multiple `periods[]` | Keep repeated or non-contiguous occurrences separate. |
| Flat history strings | Claim objects | Wrap organizations, roles, locations, descriptions, and credential values with claim-level provenance. |
| `skills[].contexts` | `skills[].contextRefs` | Keep only engagement or shared-claim IDs; remove section labels and free text. |
| `skills[].evidenceRefs` | `skills[].evidenceLinks` | Convert IDs into directional evidence objects with a relation and provenance. |
| String taxonomy mappings | Structured `taxonomyMappings[]` | Preserve only explicit, registry-verified, or manually reviewed mappings. |
| Interests represented as skills or intent | `interests[]` | Move interest statements without implying skill or application intent. |
| Languages represented as skills | `languages[]` | Preserve language and explicitly stated proficiency/modes. |
| Unmodeled personal facts in warnings | `attributes[]` | Add only when appropriate, mark sensitivity, and retain provenance. |
| `intent.claims[]` | `intent.targets`, `constraints`, `preferences` | Classify only explicit future-facing statements. Do not migrate interests automatically. |
| Ambiguity described only in warnings | `ambiguities[]`, `sharedClaims[]` | Preserve alternatives and candidate engagement references structurally. |
| Warning strings | Warning objects | Add stable code, severity, message, and related references. |
| `sourceText` only | `source` locator | Add document ID, page, offsets, digest, normalization mode, and source text where available. |
| Literal JSON-LD generation | Transport schema, then canonicalization | Generate provider-safe keys and convert deterministically after validation. |

## Migration cautions

- Do not convert `isCurrent: false` mechanically. Re-evaluate the source against the v0.1 current-status rules.
- Do not migrate section labels from v0.0 `contexts` into v0.1 `contextRefs`.
- Do not create evidence links merely because a skill and engagement are topically similar.
- Do not carry over inferred intent from interest, education, or employment sections.
- Rebuild provenance locators from the source document when offsets or page numbers were not retained in v0.0.
