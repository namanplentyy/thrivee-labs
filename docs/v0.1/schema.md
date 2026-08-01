# Career Profile v0.1 schema contract

- Status: **draft**
- Schema version: `0.1.0`
Canonical schema: `schemas/career-profile.v0.1.schema.json`

The JSON Schema is authoritative for structure. This document is authoritative for semantic rules that cannot be expressed completely in JSON Schema.

## 1. Canonical document

A canonical profile is a JSON-LD object with:

- `@type: "CareerProfile"`;
- `schemaVersion: "0.1.0"`;
- a stable `profileId`;
- declared source documents;
- identity, history, shared claims, skills, interests, languages, attributes, intent, ambiguities, and warnings.

All collection properties are present even when empty. This avoids treating an omitted collection as either “unknown” or “known to be empty.” A producer that could not process a section must emit a warning instead of silently omitting it.

## 2. Claim and provenance model

Extracted values are represented as claim objects:

```json
{
  "id": "claim:example",
  "value": "Example value",
  "provenance": []
}
```

Every non-null claim has at least one provenance record. Provenance separates:

- `method`: how the value originated;
- `verificationStatus`: whether another party has verified it;
- `confidence`: confidence in this representation, from `0` to `1`;
- `source`: where the supporting text is located;
- `inferringAgent`: the agent URI, required for agent-inferred claims.

`resume-explicit` means the resume states the value. It does not mean that an employer or institution verified it, so the usual verification status is `self-attested`.

`deterministic-normalization` is for lossless transformations such as converting “May 2025” to `2025-05`. It must not be used to infer completion, calculate credits, or assign taxonomy codes.

### Source locations

Character offsets are zero-based and end-exclusive in the extracted source-document text. `page` is one-based. Producers should provide offsets where the ingestion layer can preserve them.

`sourceText` is retained for inspection, but it is not the sole traceability mechanism. If typography or whitespace was normalized, declare the applicable `textNormalization` value. `textDigest` may contain a SHA-256 digest of the exact cited span.

## 3. Career history and dates

`history` is a source-ordered array of engagements. It supports employment, education, internships, projects, training, certifications, informal work, family-business work, career breaks, and other relevant activities.

Each engagement has one or more `periods`. Multiple periods represent repeated or non-contiguous occurrences without merging them into a false continuous range.

### Current-status rules

| Source evidence | `isCurrent` | `currentStatusBasis` |
|---|---:|---|
| Explicit “Present”, “Ongoing”, or “Pursuing” | `true` | `explicit-ongoing` |
| Explicit “Completed”, “Graduated”, or equivalent | `false` | `explicit-completed` |
| A closed source range with both endpoints | `false` | `source-range-ended` |
| A single year, projected end year, or otherwise unstated status | `null` | `unstated` |
| Current status does not apply | `null` | `not-applicable` |

Calendar time alone must not be used to turn a projected end year into completion. A producer must not compare the resume date with the system clock to infer completion.

When a date has multiple defensible interpretations, set `interpretationStatus` to `ambiguous`, add the possible normalized periods to `alternatives`, and add an ambiguity record when the uncertainty affects another claim.

### Education values

NCrF credits and NSQF levels remain `null` unless they are explicitly present, institution-issued, or manually reviewed from an authoritative mapping outside resume-only extraction. They cannot use `agent-inferred` or `deterministic-normalization` provenance.

## 4. Skills, context, and evidence

`contextRefs` identify the engagements or unresolved shared claims in which a skill is situated. A context is not evidence by itself.

`evidenceLinks` are directional edges to the artifact or activity that supports a skill claim:

- `DemonstratedIn` for work that exercises the capability;
- `LearnedIn` for learning or training;
- `ProducedIn` for an output;
- `AssessedBy` for an assessment;
- `SupportedBy` for general support;
- `MentionedIn` when the source only names the skill.

An agent-inferred skill requires at least one evidence link and must be `unverified`. A skill explicitly listed in the source may have no engagement evidence link when its claim provenance points directly to the skill-list text. Producers should not manufacture broad links to every engagement merely to populate the array.

Taxonomy mappings are allowed only when explicit in the source, verified against a registry, or manually reviewed. v0.1 deliberately has no `agent-inferred` taxonomy mapping method.

## 5. Interests, languages, and attributes

`interests` records areas of interest without implying application intent. “Interested in pharmacology” belongs in `interests`; “seeking pharmacology research roles” may also support an intent target.

`languages` is separate from skills. Producers must preserve the source wording of proficiency rather than convert it to an unsupported scale.

`attributes` provides a controlled extension point for personal statements that do not belong in identity, history, skills, languages, or intent. Each attribute carries a sensitivity classification. Consumers must not treat presence in a profile as authorization to disclose it.

## 6. Intent

Career intent has three non-interchangeable collections:

- `targets`: explicit desired roles or industries;
- `constraints`: hard filters with an operator;
- `preferences`: explicit but negotiable preferences.

An education subject, skill, job history, or interest does not create intent. Intent requires direct source language expressing a target, constraint, or preference.

## 7. Ambiguity and shared claims

When source formatting leaves a statement applicable to multiple engagements, do not assign it arbitrarily. Store it in `sharedClaims` with all candidate engagement references and an `unresolved` status.

`ambiguities` represent uncertain associations, classifications, date interpretations, repeated occurrences, or field values. `selectedValue` must remain `null` while the ambiguity is unresolved or deferred.

Examples include:

- two schools followed by two credentials without an explicit mapping;
- responsibilities printed below two roles without role-level attribution;
- one award statement that lists multiple years;
- certification bullets with no explicit course grouping.

## 8. IDs and references

IDs use stable namespaced strings such as `engagement:example`, `skill:example`, and `claim:example`. IDs must be unique within a profile. References must resolve to an ID in the same profile, except `credential:` and `artifact:` references, which may identify externally managed objects.

The JSON Schema enforces identifier shape. `scripts/validate_examples.py` demonstrates the additional cross-reference and uniqueness checks an implementation must run.

## 9. Warnings

Warnings are structured objects with a stable uppercase code, severity, message, and related references. A warning must describe a concrete limitation of the generated representation; it must not be used as a substitute for representing a known ambiguity.
