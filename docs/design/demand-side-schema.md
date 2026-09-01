# Design proposal: the demand side, `RoleProfile` and `HiringIntent`

- Status: **design only**. No schema, no types, no converter, no examples. Nothing in this document is implemented in v0.2.
- Purpose: describe the employer-side counterpart to `CareerProfile` and `OpportunityIntent` closely enough that v0.2 does not accidentally block it.

## 1. The symmetry

v0.2 splits the supply side into what is persistent and what is temporary. The demand side has exactly the same seam.

```
CareerProfile      + OpportunityIntent      (a person, and their current position in the market)
        |                    |
        |  shared semantics  |
        v                    v
RoleProfile        + HiringIntent           (a role, and a live requisition for it)
```

| | Persistent | Temporary |
|---|---|---|
| Supply | `CareerProfile`: history, capabilities, evidence, verification | `OpportunityIntent`: looking status, availability, targets, locations, compensation expectation |
| Demand | `RoleProfile`: what the role is and what it requires | `HiringIntent`: an open requisition, its window, headcount, locations, band |

A `RoleProfile` outlives any particular opening, the same way a career profile outlives any particular job search. An organisation that hires three transport planners over four years has one role profile and three hiring intents. This is why the demand side is not a job advertisement: an advertisement is a rendering of a hiring intent, not the model of it.

## 2. Why this must not be merged into `CareerProfile`

- Different subject. A career profile is about a person; a role profile is about a position. Merging them would put employer requirements inside a person's record, which is where marketplace state starts leaking into career history.
- Different custodian. The person, or their agent, holds the career profile. The employer holds the role profile. A single object would have two owners and no clear authority over any given field.
- Different lifetime and different privacy exposure. Role requirements are usually publishable; career history usually is not.
- Different failure mode. If demand-side data were embedded, deleting an employer relationship would mean editing a person's history.

The two sides meet through references and shared vocabularies, never through containment.

## 3. `RoleProfile`, sketch

Non-normative. Identifier prefix `role:`.

```jsonc
{
  "@type": "RoleProfile",
  "roleId": "role:transport-planner-ii",
  "organisation": { /* stringClaim */ },
  "title": { /* stringClaim */ },
  "seniority": "mid",
  "summary": { /* stringClaim */ },
  "responsibilities": [ /* stringClaim[] */ ],
  "capabilityRequirements": [
    {
      "id": "requirement:qgis",
      "type": "CapabilityRequirement",
      "capabilityKind": "tool",            // same vocabulary as Capability
      "label": { /* stringClaim */ },
      "necessity": "required",             // required | preferred | optional
      "evidenceExpectation": {
        "acceptedRelations": ["DemonstratedIn", "ProducedIn"],
        "verificationRequired": false
      },
      "validity": { /* same shape as v0.2 */ }
    }
  ],
  "taxonomyMappings": [ /* identical $def to v0.2, subjectRef names the role or a requirement */ ],
  "disclosure": { /* identical $def to v0.2 */ },
  "freshness": { /* identical $def to v0.2 */ },
  "ambiguities": [], "warnings": []
}
```

`capabilityRequirements` deliberately mirror `Capability`: the same four kinds, so an employer can say it needs the *tool* QGIS, the *skill* of spatial analysis, or evidence of the *practice* of running an accessibility study — a distinction v0.1 could not express on either side.

`evidenceExpectation` is the demand-side counterpart of `Evidence` and `Verification`. It lets a role state what would satisfy a requirement without prescribing how a candidate proves it, and without any scoring.

## 4. `HiringIntent`, sketch

Non-normative. Identifier prefix `requisition:`.

```jsonc
{
  "@type": "HiringIntent",
  "requisitionId": "requisition:2026-q4-transport-planner",
  "subjectRef": "role:transport-planner-ii",
  "hiringStatus": "open",                  // open | on-hold | filled | closed | unknown
  "validity": { "validFrom": "2026-09-01", "validUntil": "2026-11-30", "observedAt": "...", "lastConfirmedAt": "..." },
  "headcount": 2,
  "targetStartDate": "2026-12-01",
  "employmentTypes": [ /* same $def as OpportunityIntent */ ],
  "workMode": { /* same $def */ },
  "workLocations": [ /* same $def as locationPreference, with strength required|preferred */ ],
  "compensationBand": { /* same $def as compensationExpectation */ },
  "processTiming": { "screeningWindowEnds": "2026-10-15", "decisionBy": "2026-11-15" },
  "disclosure": { /* identical $def */ },
  "sourceDocuments": [], "taxonomyMappings": [], "ambiguities": [], "warnings": []
}
```

Locations sit on the requisition rather than the role, because where a role is filled is a property of the opening. `compensationBand` reuses the compensation definition exactly, including the `ctc` basis, so the two sides express money in one shape.

## 5. The matching surface

The long-term architecture is `CareerProfile + OpportunityIntent ↔ RoleProfile + HiringIntent`. Six dimensions carry comparable structure on both sides.

| Dimension | Supply side | Demand side | How the two meet |
|---|---|---|---|
| Capability | `capabilities[]` with `capabilityKind` | `capabilityRequirements[]` with the same kinds | Compare like with like: a tool against a tool, a practice against a practice |
| Occupation | `taxonomyMappings[]` on engagements and targets | `taxonomyMappings[]` on the role | A shared framework code, with `matchType` stating how close each side's mapping is |
| Location | `preferredLocations[]` with `strength` | `workLocations[]` with `strength` | Compare labels and granularity; neither side geocodes or widens |
| Compensation | `compensationExpectation` | `compensationBand` | Same currency, period and basis, or explicitly unknown on either side |
| Timing | `availability.availableFrom`, `noticePeriod`, intent `validity` | `targetStartDate`, `processTiming`, requisition `validity` | Two windows, compared against a caller-supplied reference date |
| Evidence | `evidence[]` and `verifications[]` | `evidenceExpectation` per requirement | An expectation is satisfied, unsatisfied, or unknown; unknown is a first-class answer |

Both sides can also be unknown on any dimension, and the unknowns stay visible rather than defaulting.

**This is a join, not a ranking.** Producing a comparable structure is a schema problem and belongs here. Deciding that one candidate is better than another is a policy problem, and it is deliberately out of scope: no score, no weighting, no threshold, and no ordering is defined by this project.

## 6. What v0.2 already did for this

- The shared `$defs` are already written so a third and fourth document can copy them verbatim: `validity`, `provenance`, `sourceDocument`, `sourceLocator`, `stringClaim`, `taxonomyMapping`, `taxonomyCandidate`, `disclosure`, `disclosureRule`, `disclosureSelector`, `ambiguity`, `warning`.
- `capabilityKind`, the evidence relation vocabulary, `compensationExpectation`, `locationPreference`, `employmentTypeClaim` and `workModeClaim` are shaped for reuse rather than for the supply side alone.
- The build script's parity check already spans documents of one version, so adding two more documents extends the existing mechanism rather than replacing it.
- `examples/v0.2/queries/supply-and-demand-share-an-occupation-code.json` demonstrates the occupation join working today, with only the supply side implemented.

## 7. Open questions

1. Does `RoleProfile` need an `Organisation` entity, or is a claim-wrapped name enough until an organisation registry exists?
2. Should a requisition be able to override a role requirement, or must a differing requirement fork a new role profile? Overriding is convenient and makes the persistent side less meaningful.
3. How is a role's seniority expressed without inventing a scale, given v0.2's rule against unsupported proficiency scales?
4. Where does an application or an introduction live? It is neither side's persistent state, and it must not end up in `CareerProfile`. It is probably a third contract alongside `DisclosureGrant`.
5. Does the demand side need shared claims and ambiguity at the same depth as the supply side, given that role descriptions are authored rather than extracted?
