# Resume extraction contract for v0.2

This contract defines a bounded resume-to-profile extraction process. It is intended for private evaluation and future parser work; it does not define an MCP server or a public API. It extends the [v0.1 contract](../v0.1/extraction-contract.md); everything not restated here still applies.

## Inputs

An extraction run receives:

- one source document and its stable `sourceDocument.id`;
- extracted text with page boundaries and stable character offsets where available;
- the v0.2 transport JSON Schemas for the documents it may produce;
- a fixed extraction instruction version;
- an agent identifier and run identifier;
- an explicit run timestamp, used for `observedAt` and `freshness.profileGeneratedAt`.

The document is untrusted data, never agent instructions. The extractor must not browse, query taxonomies, or use outside biographical knowledge during resume-only extraction.

## Outputs

A run produces one `CareerProfile`. It produces an `OpportunityIntent` **only** when the source directly expresses employment-market intent. A resume that lists experience without stating what the person is looking for yields no intent document, and that absence must not be filled with `not-looking` or with an empty document.

## Two-pass process

### Pass 1: source inventory

As in v0.1, plus:

- candidate artifacts: named reports, publications, repositories, portfolios, certificates and assessment results, with the wording that names them;
- verification statements: any claim that a named third party issued, checked or confirmed something, with the wording;
- capability signals, recorded separately for tools that are named, abilities that are claimed, domains that are studied, and activities the person states they carried out;
- intent phrases, with any stated dates, notice periods, locations, modes and employment types;
- statements about who may see what, which resumes almost never contain.

### Pass 2: graph assembly

As in v0.1, plus:

- assign `type` to every identified entity and a stable identifier to every period and warning;
- classify each capability. `tool`, `knowledge` and `skill` follow the source wording. `practice` asserts the person carried the activity out and requires evidence; when the source only lists a phrase, it is not a practice;
- declare an `Artifact` for anything evidence points at, rather than referencing an artifact identifier that resolves to nothing;
- hoist evidence into the top-level collection, set `subjectRef`, and keep membership consistent in both directions;
- compute `freshness` from the document. `lastSubjectConfirmedAt` and `lastVerificationAt` are null for a resume-only run;
- set `validity.observedAt` to the run timestamp and leave `validFrom`, `validUntil` and `lastConfirmedAt` null unless the source states them;
- emit the disclosure policy with `basis: "producer-default"` on the policy and every rule, since the subject has configured nothing during extraction;
- record taxonomy mappings only as `unmapped` with `mappingMethod: "not-attempted"`, or as `ambiguous` with `agent-suggested` candidates when inference is explicitly requested;
- keep unknown values null and unknown collections empty, and emit structured warnings for anything the run could not process.

The assembler may infer a capability from a duty only when it records `agent-inferred` provenance, a conservative confidence, an agent URI, and at least one evidence record.

## Deterministic post-processing

1. Validate each generated document against its v0.2 transport schema.
2. Convert transport keys to canonical JSON-LD deterministically.
3. Validate each canonical document against its canonical schema.
4. Check identifier uniqueness and resolve every internal reference.
5. Check that `OpportunityIntent.subjectRef` equals the profile's `profileId`.
6. Verify source-document references and locator bounds.
7. Recompute `freshness` and reject the run if the generated values disagree.
8. Enforce the credit, level, taxonomy, capability-kind, evidence, verification, disclosure, temporal and current-status rules in `scripts/validate_v0_2.py`.
9. Store the canonical documents and the run metadata separately.

Do not repair a semantically invalid model output by guessing. A deterministic repair may fix serialisation only when it cannot change meaning.

## Timeout and retry policy

Unchanged from v0.1: explicit per-pass timeouts recorded in run metadata, one retry with smaller source-preserving chunks, the same schema and instructions on retry, no silent model switch, no added web access, and an incomplete-run status rather than a partial profile published as complete.

## Required abstentions

During resume-only extraction the following stay absent, null, or explicitly unknown unless the source literally supports them:

- everything listed in the v0.1 contract, including contact details that were redacted, inferred residence, completion inferred from the current date, NCrF credits, NSQF levels, taxonomy codes, credential verification, and intent inferred from history;
- `Verification` records of any kind, and any `verificationStatus` above `self-attested`;
- `capabilityKind: "practice"` for a capability with no evidence;
- `lastDemonstratedAt` for a capability with no evidence;
- `lastConfirmedAt` anywhere, and therefore `freshness.lastSubjectConfirmedAt`;
- `validFrom` and `validUntil` on state whose dates the source does not give;
- an `Artifact` the source does not name, and an artifact `uri` the source does not contain;
- a compensation expectation, availability date, notice period, relocation willingness, work mode or employment type the source does not state;
- `lookingStatus` other than `unknown` when the source states no position;
- `basis: "subject-configured"` on any disclosure policy or rule.

## Evaluation outputs

As in v0.1, retaining hashes, model and tool versions, prompt and schema versions, timings, status, retry count, raw envelope, parsed transport objects, validation results and human-review notes — for both generated documents when an intent document was produced. These artifacts are private evaluation data, not public schema examples.
