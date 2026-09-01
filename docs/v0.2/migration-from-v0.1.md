# Migrating v0.1 to v0.2

v0.1 is not deprecated and its schemas, examples, validator and documentation are unchanged. A v0.1 profile stays valid against v0.1. Migration is a deliberate conversion, and parts of it require human review rather than a script.

## Document split

A v0.1 `CareerProfile` becomes one v0.2 `CareerProfile` and, only when the source expressed market intent, one `OpportunityIntent`.

| v0.1 | v0.2 | Migration behaviour |
|---|---|---|
| `intent.targets[]` | `OpportunityIntent.targetRoles[]` | Keep `role` and `industry`. `occupation` and `career-family` are new and require a deliberate classification |
| `intent.constraints[]` kind `location` | `preferredLocations[]` | Set `granularity` to what the source supports. Do not widen a city to a region or add a country code the source does not state |
| `intent.constraints[]` kind `remote-work` | `workMode` | Map the stated wording to one enumerated mode, or `unknown` |
| `intent.constraints[]` kind `availability` | `availability` | Split a stated start date and a stated notice period into their own fields |
| `intent.constraints[]` kind `compensation` | `compensationExpectation` | Only when an amount, currency and period are stated. Otherwise leave null and warn |
| `intent.constraints[]` kind `relocation` | `relocation` | `conditional` requires the stated condition text |
| `intent.constraints[]` kind `work-authorization` | `CareerProfile.attributes[]` | Work authorisation is persistent and belongs in the profile, not in market state |
| `intent.constraints[]` kinds `schedule`, `travel`, `other` | `constraints[]` | Carried over unchanged |
| `intent.preferences[]` kinds `location`, `remote-work` | typed fields above | A preference for a place or a mode is expressed once, in the typed field |
| `intent.preferences[]` kinds `role`, `industry` | `targetRoles[]`, or `constraints[]` when the source stated a filter | Preserve whether the source expressed an aspiration or a hard filter |
| `intent.preferences[]` other kinds | `preferences[]` | Carried over unchanged |
| Empty `intent` | No intent document | Absence of intent is not `not-looking`. Do not create an empty intent document |

## Within the career profile

| v0.1 | v0.2 | Migration behaviour |
|---|---|---|
| `skills[]` | `capabilities[]` | Rename identifiers from `skill:` to `capability:` and set `capabilityKind` (see cautions) |
| `skills[].contextRefs` | `capabilities[].contextRefs` | Unchanged |
| `skills[].evidenceLinks[]` | top-level `evidence[]` plus `capabilities[].evidenceRefs` | Hoist each link, keep its identifier and relation, and set `subjectRef` to the capability that held it |
| `evidenceLink.targetRef` naming `artifact:` or `credential:` | `artifacts[]` entry plus a resolving `targetRef` | v0.1 allowed these references to resolve to nothing. Declare the artifact, or repoint the evidence at the engagement that is actually documented |
| `skills[].taxonomyMappings[]` | top-level `taxonomyMappings[]` | Add an identifier, `subjectRef`, `mappingStatus: "mapped"`, a `matchType`, and `validity` with nulls where nothing is known |
| Absent taxonomy mapping | optionally an `unmapped` record | Use `mappingMethod: "not-attempted"` unless a review actually took place, in which case use `reviewed-no-match` |
| `history[].periods[]` | same, plus `period:` identifiers | Assign stable identifiers in source order |
| `warnings[]` | same, plus `warning:` identifiers | Assign stable identifiers in source order |
| Every entity | plus `type` | Add the type constant the schema declares |
| `sourceDocuments[]` | plus `type` and `ingestedAt` | `ingestedAt` is when the document entered the system, or null if unknown |
| — | `freshness` | Compute from the document. See cautions |
| — | `disclosure` | See cautions |
| — | `validity` on identity claims, capabilities, artifacts, attributes, verifications, taxonomy mappings and disclosure | Nulls throughout unless the source states a date |
| — | `verifications[]` | Empty for a resume-derived profile |
| `@context` | plus `skos`, `id`, `type` | The two aliases make `id` and `type` JSON-LD keywords |

## Cautions

- **Capability kinds are a review step, not a lookup.** An unreviewed v0.1 skill migrates to `capabilityKind: "skill"`. Reclassifying an entry as `tool`, `knowledge` or `practice` is a human judgement about what the source said. A `practice` in particular asserts that the person did the thing, which a bare skill list does not support. Emit a warning for entries whose kind has not been reviewed.
- **Do not fabricate verification.** A v0.1 claim carrying `institution-verified` or `peer-endorsed` now requires a confirmed `Verification` record. If no verifier, method and date are actually known, downgrade the claim to `unverified` or `self-attested` rather than inventing a verifier.
- **Do not invent validity dates.** A migrated profile knows when it was produced, so `observedAt` may be set. It usually does not know when the subject last confirmed anything, so `lastConfirmedAt` stays null and `freshness.lastSubjectConfirmedAt` stays null with it.
- **Freshness is computed, not asserted.** The three derived fields must equal the latest corresponding values in the document; the validator rejects a profile that overstates them.
- **Disclosure defaults are the producer's, not the subject's.** A migrated profile has no subject-configured policy. Set `basis: "producer-default"` on the policy and its rules, and choose a default your deployment can defend. Only mark a rule `subject-configured` when the subject actually configured it.
- **Do not promote a suggestion.** A v0.1 mapping that was never reviewed does not become a v0.2 `mapped` record. Move it into `candidates[]` with `method: "agent-suggested"` and set the mapping status to `ambiguous`, with an ambiguity record to match.
- **Identifiers are document-local.** Renaming `skill:x` to `capability:x` is safe as long as every reference is renamed with it. Run `scripts/validate_v0_2.py`, which now requires every reference to resolve.
- The v0.1 cautions still apply: do not re-derive `isCurrent` mechanically, do not migrate section labels into `contextRefs`, do not create evidence from topical similarity, and do not turn interests into intent.
