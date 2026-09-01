# Versioning: what v0.3 changes, and what it deliberately does not

- Status: **draft**

## 1. v0.3 is a release of the schema family, not a new copy of every document

The trust layer needed a version number. Duplicating the 2,500-line `CareerProfile` schema to renumber it would have produced a second copy of a contract whose meaning had not changed, and two files to keep in step forever.

So v0.3 adds documents rather than reissuing them.

| Document | Version | Status in v0.3 |
|---|---|---|
| `CareerProfile` | `0.2.0` | Unchanged. No new fields, no changed semantics |
| `OpportunityIntent` | `0.2.0` | Unchanged |
| `RelationshipAssertion` | `0.3.0` | New |
| `ReferralAvailability` | `0.3.0` | New |
| `Endorsement` | `0.3.0` | New |
| `Referral` | `0.3.0` | New |

**Every existing v0.2 document remains valid, byte for byte.** A profile written before v0.3 needs no migration, no re-extraction and no new field. There is nothing to migrate, which is why this file is a versioning note rather than a migration guide.

## 2. The one change to a v0.2 file

`verification.targetRef` in `schemas/career-profile.v0.2.schema.json` widened its pattern:

```diff
- ^(evidence|artifact|capability|engagement|shared-claim|claim):...
+ ^(evidence|artifact|capability|engagement|shared-claim|claim|party|relationship|endorsement|referral):...
```

This is a relaxation. Every value that was valid before is still valid, and no v0.2 document changes meaning. The widening exists so that the trust documents can reuse the `Verification` definition exactly as written, instead of forking a parallel verification model — which the whole design depends on not doing.

`schemas/opportunity-intent.v0.2.schema.json` is untouched: it has no `verification` definition.

## 3. Shared definitions span the version boundary

A single-file structured-output schema cannot use a cross-file `$ref`, so each document carries its own copy of the definitions it shares. `scripts/build-transport-schema.mjs` enforces that those copies stay byte-identical, and in v0.3 it groups documents by **`defsFamily`** rather than by version number. All six career-family documents share one family, so `validity`, `provenance`, `sourceDocument`, `sourceLocator`, `stringClaim`, `disclosure`, `disclosureRule`, `disclosureSelector`, `taxonomyMapping`, `taxonomyCandidate`, `verification`, `verifier`, `ambiguity` and `warning` cannot drift between v0.2 and v0.3.

Editing a shared definition means editing it in every file of the family and re-running the check.

## 4. What the manifest says

`schemas/schema-manifest.json` gains a `0.3.0` entry that declares `reusesSupplySideFrom: "0.2.0"` and lists the four trust documents under `documents`.

`defaultExtractionVersion` stays `0.2.0`. Resume extraction produces a `CareerProfile`, and that contract has not changed, so the private conversion skill is unaffected by v0.3. Trust documents are not extracted from resumes: a relationship, an endorsement and a referral are created by people acting, not by parsing a document about one person.

## 5. Reuse rather than duplication, in detail

Every primitive the trust layer needed already existed. What v0.3 adds is only what genuinely had no representation.

| Trust-layer need | v0.2 primitive reused | Why not a new one |
|---|---|---|
| Time windows and expiry | `validity` | The brief's `createdAt` / `expiresAt` map to `validFrom` / `validUntil`. One temporal model, one expiry rule, one caller-supplied reference date |
| Who said this, how, from where | `provenance`, `sourceLocator`, `sourceDocument` | Provenance philosophy is the reason a unilateral claim stays distinguishable from a confirmed one |
| A third party checking a fact | `verification`, `verifier` | Creating a second verification model would have been the single biggest mistake available here |
| A person who is not the subject | `verifier`'s shape → `party` | `Party` is the same idea — name, kind, routable URI — generalised to a node the graph can point at |
| What may be read without asking | `disclosure`, `disclosureRule`, `disclosureSelector` | The trust documents get policy for free, and precedence is already deterministic |
| Permission for a named requester | `DisclosureGrant` design | The referral points at grants and refuses to become one |
| Binding to an opening | `HiringIntent` design | A reserved `requisition:` reference now, a resolved binding later. No job-description fields are duplicated |
| Domains and career families | `taxonomyMapping`, `taxonomyCandidate` | A referrer's scope joins to the candidate's occupation code instead of matching free text |
| Text with provenance | `stringClaim` | An endorsement statement is a claim, not a bare string |
| Unclear cases, producer complaints | `ambiguity`, `warning` | Unchanged |
| Cross-document resolution | `check_references(document, known, external)` | The v0.2 validator already took an external-identifier set; v0.3 passes it a bundle |

New definitions were added only for `party`, `relationshipContext`, `relationshipTypeValue`, `relationshipTypeExtension`, `counterpartyConfirmation`, `availabilityStatusClaim`, `discoverabilityClaim`, `availabilityScope`, `referralScopeEntry`, `referralApproval` and `referralOpportunity` — concepts with no prior representation.

## 6. What a future v0.4 would have to do

- Implement `RoleProfile` and `HiringIntent`, at which point `Referral.opportunity.bindingStatus` can legitimately become `resolved-hiring-intent` and the deferred `requisition:` namespace starts resolving.
- Implement `DisclosureGrant`, at which point `disclosureGrantRefs` resolves and the "may not widen the policy" rule can be checked against an actual grant scope rather than against the profile policy alone.
- Neither requires changing anything in v0.2 or v0.3. That is the point of deferring them by reference instead of inlining them.
