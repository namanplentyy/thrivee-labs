# Agent query fixtures for the trust layer

The v0.3 fixtures live in `examples/v0.3/queries/` and run through the same `scripts/run_query_fixtures.py` as the v0.2 ones, in one pass. See [the v0.2 fixture notes](../v0.2/queries.md) for the format; this page covers what v0.3 adds.

These fixtures are a schema-coverage test, not a query language, not a matching engine and not a ranking of referral paths. The runner reads, filters and follows references. It never reads the system clock: every time-dependent fixture supplies an explicit `asOf`.

## What the trust layer needed from the runner

The supply-side fixtures answer questions from one document. Trust questions span several, so the runner gained four operations. They read; none of them decides anything.

| `op` | Purpose | Fields |
|---|---|---|
| `across` | Read one value from each of several named documents that match | `documents`, optional `where`, optional `inWindowAt`, `select` |
| `count` | Count an earlier step's result | `of` (`"$stepName"`) |
| `inWindow` | Whether a document's own validity window contains an explicit date | `document`, optional `asOf` |
| `disclose` | Read a party's detail *only* where that party opted in to being named | `document`, `entityRef`, `select` |

`where` also gained `{"contains": value}`, with an optional `select` pointer for lists of entities, so a fixture can ask whether a scope lists a domain or whether a relationship carries a type.

`disclose` is worth reading as a statement of the privacy contract rather than as a convenience. It returns a value only when the document's `discoverability` is `named` **and** the entity resolves to `agent-discoverable` under that document's disclosure policy. Otherwise it returns `null`. Willingness to be asked is not permission to be named.

## What the fixtures cover

| Fixture | Demonstrates |
|---|---|
| `who-is-willing-to-refer` | Willingness is a separate document, and a lapsed one drops out even though it still says `open` |
| `how-many-referral-paths-exist` | The privacy property: two paths, one name, one anonymous count |
| `referral-paths-for-a-candidate` | Three relationships in three different trust states, including a type extension |
| `referral-or-platform-suggestion` | The most important distinction in the layer, read from `origin`, `approvals`, `status`, `referredAt` and grants |
| `has-everyone-approved` | Per-actor approval with attribution and dates, and the employer's deliberate absence |
| `what-can-this-person-vouch-for` | An endorsement resolving to real capabilities, with its basis |
| `endorsement-from-someone-who-supervised` | A qualified "no": the GIS endorsement is real but comes from a professor, not a supervisor |
| `has-the-referral-expired` | The same document answering differently at two dates, with `status` unchanged |
| `what-the-employer-may-see` | The referral defers to a grant, and the profile's `withheld` still wins |
| `facts-instead-of-a-referral-score` | Every input a consumer might weigh, and two score fields that resolve to nothing |
| `absence-is-not-a-refusal` | Four distinct states: stated refusal, no document, current willingness, lapsed willingness |

## Adding a fixture

Add a JSON file to `examples/v0.3/queries/`. Prefer a question an employer agent or a candidate's agent would really ask, and keep including the negative cases — the questions whose correct answer is that nobody has said. A fixture that can only pass by inventing a name, a willingness or an approval is a finding about the schema, not about the fixture.

Two questions are deliberately not fixtures here, because answering them would mean building something this project excludes: which candidate is the better hire, and which referral path is worth more. The documents carry the facts; the weighing belongs to the consumer.
