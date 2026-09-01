# Agent query fixtures

A schema is only agent-native if an agent can answer real questions from it without guessing. The fixtures in `examples/v0.2/queries/` state a question, the deterministic steps that resolve it against the synthetic documents, and the expected answer. `scripts/run_query_fixtures.py` runs them as part of `npm run check`.

These fixtures are a schema-coverage test, not a query language and not a matching engine. The runner reads, filters and follows references. It does not score, rank or recommend, and it never reads the system clock: every time-dependent fixture supplies an explicit `asOf`.

## Fixture format

```json
{
  "id": "query:availability-and-location",
  "question": "Is this person open to work, in what mode, where, and from when?",
  "asOf": "2026-09-01",
  "notes": ["Why this question matters."],
  "steps": [
    { "name": "workMode", "op": "pointer", "document": "opportunity-intent", "pointer": "/workMode/value" }
  ],
  "expect": { "workMode": "hybrid" }
}
```

`document` is `career-profile` or `opportunity-intent`. Every step is named, and `expect` compares a step result to a literal value. A step whose expected value is `null` or `[]` is as meaningful as any other: it proves the schema can express "not stated" without inventing a value.

## Operations

| `op` | Purpose | Fields |
|---|---|---|
| `pointer` | Read one value | `pointer` (JSON Pointer) |
| `collect` | Filter a top-level collection and read one field from each match | `collection`, optional `where`, `select` |
| `follow` | Resolve a reference property to entities and read one field from each | `from`, `refs`, `select` |
| `visibility` | Resolve the disclosure policy for one entity | `entityRef` |
| `expired` | List identifiers whose validity window closed | optional `asOf` |

`where` matches a field against a literal, or against `{"in": [...]}`, or against `{"in": "$stepName"}` to use an earlier step's result. `select` is a JSON Pointer evaluated inside each matched entity, defaulting to `/id`.

## What the current fixtures cover

| Fixture | Demonstrates |
|---|---|
| `availability-and-location` | Market state answers on its own, without touching career history |
| `evidence-behind-a-capability` | Capability to evidence to artifact, then verification found by `targetRef` |
| `tools-versus-demonstrated-practice` | The distinction v0.1 could not express |
| `what-an-agent-may-see` | Disclosure precedence, including an entity rule overriding a sensitivity rule |
| `occupation-and-taxonomy-certainty` | Adopted codes with match type, alongside ambiguous and unmapped subjects |
| `supply-and-demand-share-an-occupation-code` | The join the future demand-side documents will use |
| `what-has-gone-stale` | The same documents answering differently at two explicit dates |
| `compensation-expectation-is-unknown` | A negative case: "not stated" is reachable structurally |
| `unknown-taxonomy-stays-unknown` | Three kinds of not-knowing stay distinguishable |

## Adding a fixture

Add a JSON file to `examples/v0.2/queries/`. Prefer a question an agent would really ask on behalf of a person or an employer, and include the negative cases: the questions whose correct answer is that the documents do not say. A fixture that can only pass by inventing a value is a finding about the schema, not about the fixture.
