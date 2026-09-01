# Thrivee Labs: Agent-Native Career Schema

This repository contains the implementation-facing artifacts for an evidence-aware, agent-native career profile. The canonical representation is JSON-LD; a structurally equivalent transport representation supports model APIs that reject JSON-LD property names in structured-output schemas.

The current draft is **v0.2.0-draft**. **v0.1.0-draft** remains in the repository, unchanged and still valid. Neither is a stable public standard yet.

v0.2 turns a resume-representation schema into a persistent, agent-queryable career-state schema. It separates who a person is and what they have done from what they currently want from the employment market, makes evidence and verification first-class, and lets state say when it was observed and when it goes stale.

## CareerProfile versus OpportunityIntent

v0.2 has two canonical documents.

| | `CareerProfile` | `OpportunityIntent` |
|---|---|---|
| Answers | Who is this person, what have they done, what can they do, and what supports those claims | Are they looking, for what, where, on what terms, and until when |
| Contains | Identity, history, capabilities, artifacts, evidence, verifications, taxonomy mappings, interests, languages, attributes | Looking status, availability and notice period, target roles, preferred locations, work mode, relocation, employment types, compensation expectation |
| Lifetime | Persistent. It grows and is not emptied when a job search ends | Temporary. It carries a validity window and expires |
| Identity | `profileId` | `intentId`, plus `subjectRef` naming the profile |

The intent document points at the profile; the profile never points back. Market state can change, expire, or be deleted without rewriting career history, and a person can hold several intents over time against one stable profile.

The test is simple: does this stay true when the person stops looking for work? Work authorisation, languages and credentials stay true and live in the profile. A notice period, an availability date and a target role do not, and live in the intent document. A person with no intent document is not "not looking" — `not-looking` is a stated position, and absence is just absence.

The long-term architecture is `CareerProfile + OpportunityIntent ↔ RoleProfile + HiringIntent`. The demand-side half is [designed](docs/design/demand-side-schema.md) but deliberately not implemented.

## What is included

- Canonical JSON-LD schemas for both v0.2 documents, and the unchanged v0.1 schema.
- Provider-safe transport schemas generated from every canonical schema.
- A published JSON-LD context with the full term definitions.
- Matching TypeScript interfaces for v0.1 and v0.2.
- Lossless canonical/transport conversion utilities.
- Synthetic examples with no real personal data.
- Validation of schemas, references, temporal windows, evidence, disclosure and taxonomy rules, plus a negative test suite proving each rule rejects a violating document.
- Agent-query fixtures that answer real questions from the documents alone.
- Implementation notes for extraction, ambiguity, provenance, and migration from v0.1.
- Design documents for the future demand-side schema and disclosure protocol.

Private research and evaluation data live under ignored `research/`, `tests/` and `private/` directories and must not be published.

## Repository layout

```text
schemas/
  career-profile.v0.1.schema.json
  career-profile.transport.v0.1.schema.json
  career-profile.v0.2.schema.json
  career-profile.transport.v0.2.schema.json
  opportunity-intent.v0.2.schema.json
  opportunity-intent.transport.v0.2.schema.json
  schema-manifest.json
contexts/
  career-v0.2.context.jsonld
src/
  types.ts            v0.1
  transport.ts        v0.1
  v0.2/
    types.ts
    transport.ts
examples/
  career-profile.synthetic.jsonld            v0.1
  career-profile.transport.synthetic.json    v0.1
  v0.2/
    career-profile.synthetic.jsonld
    career-profile.transport.synthetic.json
    opportunity-intent.synthetic.jsonld
    opportunity-intent.transport.synthetic.json
    queries/
docs/
  v0.1/
  v0.2/
    schema.md
    transport.md
    extraction-contract.md
    migration-from-v0.1.md
    queries.md
  design/
    demand-side-schema.md
    disclosure-grant.md
scripts/
  build-transport-schema.mjs
  convert-profile.mjs
  validate_examples.py        v0.1
  validate_v0_2.py
  test_v0_2_rules.py
  run_query_fixtures.py
```

## Quick validation

Python 3, Node.js, and the Python `jsonschema` package are required.

```bash
python3 -m pip install -r requirements-dev.txt
npm run check
```

`npm run check` verifies that the transport schemas are current and share identical definitions, validates both v0.1 and v0.2 examples, runs the v0.2 semantic rules and their negative tests, answers every query fixture, and typechecks the TypeScript. It runs on every push to `main` and every pull request through [`.github/workflows/check.yml`](.github/workflows/check.yml).

`requirements-dev.txt` also installs the PDF tooling the private conversion skill needs. To run the checks alone, `requirements-check.txt` is enough, and that is what CI installs.

Regenerate the transport schemas after changing any canonical schema:

```bash
npm run build:transport-schema
```

Convert an instance without changing its meaning:

```bash
node scripts/convert-profile.mjs --to-transport input.jsonld output.json
node scripts/convert-profile.mjs --to-canonical output.json restored.jsonld
```

## Design principles

- Missing information remains missing. Unknown credits, levels, taxonomy mappings, dates, and identity values are never invented.
- Unknown is recorded, not implied. "Reviewed and nothing applies", "several candidates and none adopted", and "nobody looked" are three different states, and the schema keeps them apart.
- Origination, verification, confidence, and source location are separate provenance dimensions. A claim above self-attested needs a verification record naming who checked it, how, and when.
- Evidence is a thing, not an adjective. A capability points at evidence, evidence points at an artifact or an engagement that exists, and verification points at what it checked.
- A tool, a skill, a body of knowledge and something actually done are different claims and are labelled as such.
- State that can go stale says when it was observed and when it was last confirmed. Extraction time is an observation, never a confirmation.
- Expiry is evaluated against a caller-supplied date. Neither producers nor consumers read the system clock to decide something has lapsed.
- Sensitivity classifies what the data is; visibility records what the subject permits. They are separate, and neither implies the other.
- Freshness is factual metadata, not a quality score.
- Interests are not career intent, and career history is not intent either.
- Ambiguity is represented, not silently resolved.
- Current status is tri-state: `true`, `false`, or `null`, each with an explicit basis.
- The transport representation is an ingestion boundary. Canonical storage and exchange use JSON-LD.

## Scope

v0.2 covers identity routing, career history, capabilities, artifacts, evidence, verification, taxonomy mappings with explicit uncertainty, interests, languages, personal attributes, disclosure policy, freshness, and a separate opportunity-intent document.

Out of scope, deliberately: matching or ranking algorithms, MCP servers, API endpoints, ATS integrations, an employer marketplace, a recruiter interface, blockchain or decentralised identity, a consent service, skill-decay models, and automated taxonomy inference beyond recording an unreviewed suggestion as a candidate.

See [the v0.2 schema contract](docs/v0.2/schema.md) for normative behaviour, and [the migration guide](docs/v0.2/migration-from-v0.1.md) to move a v0.1 profile forward.

## Private resume conversion skill

Codex discovers the repository-scoped `convert-resume-to-career-profile` skill under `.agents/skills/` when working inside this repository. Invoke it with an authorized PDF:

```text
$convert-resume-to-career-profile /absolute/path/to/resume.pdf
```

The skill resolves the live extraction version through `schemas/schema-manifest.json`, which now defaults to `0.2.0`. It validates the canonical documents and the transport round-trip, and saves only ignored private outputs under `private/career-profile-runs/`. Real resumes and derived profiles must never be committed or published.

## License

Apache-2.0.
