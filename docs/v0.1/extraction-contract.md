# Resume extraction contract for v0.1

This contract defines a bounded resume-to-profile extraction process. It is intended for private evaluation and future Phase 2 parser work; it does not define an MCP server or public API.

## Inputs

An extraction run receives:

- one source document and its stable `sourceDocument.id`;
- extracted text with page boundaries and stable character offsets where available;
- the v0.1 transport JSON Schema;
- a fixed extraction instruction version;
- an agent identifier and run identifier.

The document is untrusted data, never agent instructions. The extractor must not browse, query taxonomies, or use outside biographical knowledge during resume-only extraction.

## Two-pass process

### Pass 1: source inventory

Create a source-ordered inventory without building the final graph:

- section boundaries;
- candidate engagements and raw date strings;
- explicit skills, interests, languages, attributes, and intent phrases;
- source spans with page and character offsets;
- grouping and association ambiguities.

Long documents should be chunked on page or section boundaries. Each chunk preserves the original source coordinates. Overlap is allowed for boundary recovery, but duplicate inventory items must be removed by source span—not by semantic similarity alone.

### Pass 2: graph assembly

Assemble the inventory into one transport profile:

- create stable source-ordered IDs;
- normalize only the date precision present in the source;
- preserve repeated periods and unresolved shared claims;
- add directional evidence for inferred skills;
- keep unknown values null or arrays empty;
- emit structured warnings for incomplete processing.

The assembler may infer a skill from a duty only when it records `agent-inferred` provenance, a conservative confidence, an agent URI, and at least one evidence link. It may not infer intent, NCrF credits, NSQF levels, or taxonomy mappings.

## Deterministic post-processing

After model generation:

1. Validate against `career-profile.transport.v0.1.schema.json`.
2. Check ID uniqueness and all internal references.
3. Verify source-document references and locator bounds.
4. Enforce credit, level, taxonomy, inferred-skill, and current-status rules.
5. Convert transport keys to canonical JSON-LD deterministically.
6. Validate the canonical object again.
7. Store the canonical object and the extraction run metadata separately.

Do not repair a semantically invalid model output by guessing. A deterministic repair may fix serialization only when it cannot change meaning, such as removing a Markdown code fence around otherwise valid JSON.

## Timeout and retry policy

- Set an explicit timeout for every pass and record it in run metadata.
- On the first timeout, retry once using smaller source-preserving chunks.
- A retry must use the same schema and extraction instructions.
- Do not silently switch models or add web access.
- If the retry fails, return an incomplete-run status. Do not publish a partial profile as complete.
- Preserve partial inventory output for diagnosis only when it contains no unreviewed sensitive material.

Recommended run states are `completed`, `completed-with-warnings`, `invalid-output`, `timed-out`, and `incomplete`.

## Required abstentions

During resume-only extraction, the following stay absent or null unless literally supported by the source:

- contact details hidden or redacted in the input;
- current residence inferred from an employer or school location;
- completion inferred from the current date;
- NCrF credit values;
- NSQF levels;
- NCO-2015, ESCO, O*NET, or CTDL-ASN mappings;
- credential verification;
- career intent inferred from history, skills, education, or interests.

## Evaluation outputs

Every private test run should retain:

- hashes of the original and redacted inputs;
- model and tool versions;
- prompt and schema versions;
- start time, duration, status, and retry count;
- raw model envelope and parsed transport object;
- schema and semantic-validation results;
- human-review notes.

These artifacts are evaluation data, not public schema examples.
