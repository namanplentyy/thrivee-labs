# Thrivee Labs: Agent-Native Career Schema

This repository contains the implementation-facing artifacts for an evidence-aware, agent-native career profile. The canonical representation is JSON-LD; a structurally equivalent transport representation supports model APIs that reject JSON-LD property names in structured-output schemas.

The current draft is **v0.3.0-draft**, which adds a referral and trust layer. **v0.2.0-draft** and **v0.1.0-draft** remain in the repository, unchanged and still valid. None is a stable public standard yet.

v0.2 turns a resume-representation schema into a persistent, agent-queryable career-state schema. It separates who a person is and what they have done from what they currently want from the employment market, makes evidence and verification first-class, and lets state say when it was observed and when it goes stale.

v0.3 adds the people around that person. Hiring in professional niches is not decided by candidate-role fit alone: employers rely on people who can credibly vouch for a candidate. v0.3 represents who knows whom, what each of them will vouch for, whether they currently want to be asked at all, and whether everyone involved has agreed — as documents around the career profile, never as fields inside it.

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

## The trust layer

v0.3 adds four documents, and adds nothing to `CareerProfile`. A referral is contextual, employer-specific, permissioned, time-sensitive, created by somebody else and potentially withdrawn — and it changes constantly while career history does not. So it lives outside the persistent profile, as a graph around it.

| Document | Answers | Lifetime |
|---|---|---|
| `RelationshipAssertion` | Who knows whom, and in what context | Long-lived |
| `ReferralAvailability` | Is this person currently willing to be asked for referrals, and about what | Temporary. Expires |
| `Endorsement` | What can this person vouch for, and on what basis | Reusable across opportunities |
| `Referral` | Will A refer B for opportunity C, and has everyone agreed | Short and role-specific |

Four principles decide most of the design:

- **A relationship is not a willingness to refer.** `ReferralAvailability` is to referrals what `OpportunityIntent` is to a job search, and its absence means absence — not `not-available`.
- **Approval is explicit.** A referral becomes actionable because the referrer and the candidate each approved it, never because an algorithm found a connection. `platform-suggested` records how a workflow started and is never itself a referral.
- **The relationship graph is private by default.** What an employer agent can learn without permission is that *two eligible referral paths exist*, not who is on them. A name appears only where the referrer opted in, or approved.
- **Facts, not scores.** There is no `referralStrength` and no `referrerCredibility`. Relationship type, shared organisation, duration, confirmed-versus-claimed, what was endorsed and when — all present. The weighing belongs to the consumer.

See [the v0.3 referral contract](docs/v0.3/referrals.md) for normative behaviour and [the relationship model](docs/v0.3/relationship-model.md) for the graph and its privacy properties.

## The long-term architecture

```text
CareerProfile + OpportunityIntent          supply     implemented
            ↕
      Matching Layer
            ↕
RoleProfile + HiringIntent                 demand     design only

            +

RelationshipAssertion + ReferralAvailability
      + Endorsement + Referral             trust      implemented
            ↓
      DisclosureGrant                                 design only
```

The demand-side half and the disclosure-grant contract are [designed](docs/design/demand-side-schema.md) but deliberately not implemented. A `Referral` therefore points at a reserved `requisition:` reference rather than duplicating job-description fields, and at reserved `grant:` references rather than becoming its own privacy system.

## What is included

- Canonical JSON-LD schemas for the two v0.2 documents, the four v0.3 trust documents, and the unchanged v0.1 schema.
- Provider-safe transport schemas generated from every canonical schema, with a parity check that stops shared definitions drifting between versions.
- Published JSON-LD contexts with the full term definitions.
- Matching TypeScript interfaces for v0.1, v0.2 and v0.3.
- Lossless canonical/transport conversion utilities.
- Synthetic examples with no real people or organisations, including one coherent referral scenario spanning ten trust documents.
- Validation of schemas, cross-document references, temporal windows, evidence, approvals, disclosure and taxonomy rules, plus negative test suites proving each rule rejects a violating document.
- Agent-query fixtures that answer real questions from the documents alone.
- Implementation notes for extraction, ambiguity, provenance, migration from v0.1, and v0.3 versioning.
- Design documents for the future demand-side schema and disclosure protocol, updated to show how referrals bind to both.

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
  relationship-assertion.v0.3.schema.json
  relationship-assertion.transport.v0.3.schema.json
  referral-availability.v0.3.schema.json
  referral-availability.transport.v0.3.schema.json
  endorsement.v0.3.schema.json
  endorsement.transport.v0.3.schema.json
  referral.v0.3.schema.json
  referral.transport.v0.3.schema.json
  schema-manifest.json
contexts/
  career-v0.2.context.jsonld
  trust-v0.3.context.jsonld
src/
  types.ts            v0.1
  transport.ts        v0.1
  v0.2/
    types.ts
    transport.ts
  v0.3/
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
  v0.3/
    relationships/
    endorsements/
    referral-availability/
    referrals/
    queries/
docs/
  v0.1/
  v0.2/
    schema.md
    transport.md
    extraction-contract.md
    migration-from-v0.1.md
    queries.md
  v0.3/
    referrals.md
    relationship-model.md
    transport.md
    queries.md
    versioning.md
  design/
    demand-side-schema.md
    disclosure-grant.md
scripts/
  build-transport-schema.mjs
  convert-profile.mjs
  validate_examples.py        v0.1
  validate_v0_2.py
  validate_v0_3.py
  test_v0_2_rules.py
  test_v0_3_rules.py
  run_query_fixtures.py
```

## Quick validation

Python 3, Node.js, and the Python `jsonschema` package are required.

```bash
python3 -m pip install -r requirements-dev.txt
npm run check
```

`npm run check` verifies that the transport schemas are current and share identical definitions across the whole document family, validates the v0.1, v0.2 and v0.3 examples and their round-trips, runs the v0.2 and v0.3 semantic rules and the negative tests that prove each rule rejects a violating document, answers every query fixture, and typechecks the TypeScript. It runs on every push to `main` and every pull request through [`.github/workflows/check.yml`](.github/workflows/check.yml).

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
- A relationship is not a referral, and a referral is not an endorsement. Each is its own document with its own lifetime and custodian.
- Trust is granted by people, not derived by software. A referral is actionable because the referrer and the candidate each approved it.
- The relationship graph is restricted by default, so that it cannot be harvested as a directory of people's professional networks.

## Scope

v0.2 covers identity routing, career history, capabilities, artifacts, evidence, verification, taxonomy mappings with explicit uncertainty, interests, languages, personal attributes, disclosure policy, freshness, and a separate opportunity-intent document.

v0.3 adds relationship assertions with three distinguishable trust states, referral availability with explicit discoverability, scoped endorsements, and referrals with first-class approvals bound to deferred requisition and grant references.

Out of scope, deliberately: matching or ranking algorithms, referral recommendation, social-graph crawling or scraping, messaging and notifications, MCP servers, API endpoints, ATS integrations, an employer marketplace, recruiter or candidate interfaces, blockchain or decentralised identity, a consent service, referral payments or bonuses, reputation and strength scores, fraud detection, skill-decay models, and automated taxonomy inference beyond recording an unreviewed suggestion as a candidate.

See [the v0.2 schema contract](docs/v0.2/schema.md) and [the v0.3 referral contract](docs/v0.3/referrals.md) for normative behaviour, [the migration guide](docs/v0.2/migration-from-v0.1.md) to move a v0.1 profile forward, and [the v0.3 versioning note](docs/v0.3/versioning.md) for why v0.2 documents need no migration at all.

## Private resume conversion skill

Codex discovers the repository-scoped `convert-resume-to-career-profile` skill under `.agents/skills/` when working inside this repository. Invoke it with an authorized PDF:

```text
$convert-resume-to-career-profile /absolute/path/to/resume.pdf
```

The skill resolves the live extraction version through `schemas/schema-manifest.json`, which now defaults to `0.2.0`. It validates the canonical documents and the transport round-trip, and saves only ignored private outputs under `private/career-profile-runs/`. Real resumes and derived profiles must never be committed or published.

## License

Apache-2.0.
