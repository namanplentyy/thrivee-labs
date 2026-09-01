# Design proposal: `DisclosureGrant`

- Status: **design only**. No schema, no types, no service, no examples. Nothing in this document is implemented in v0.2.
- Purpose: describe how a person authorises a specific requester to receive specific fields, without that authorisation ever entering `CareerProfile`.

## 1. The separation

v0.2 puts a `disclosure` policy inside each document. The policy is a standing statement about categories: *this class of information is discoverable by agents, that class needs permission, this specific item is withheld*. It names no requester and records no history.

A grant is the opposite kind of object: one person, one requester, one purpose, one window, one set of fields.

| | Disclosure policy | Disclosure grant |
|---|---|---|
| Lives in | The career profile and the intent document | A separate contract |
| Subject of the statement | Categories of information | A named requester |
| Lifetime | As long as the person's preference holds | Short, and revocable |
| Volume | One per document | Many, and growing |
| If deleted | The person's preferences are lost | One permission is lost |

Keeping grants out of `CareerProfile` matters for four practical reasons: career history must not grow an audit log every time someone asks a question; deleting a marketplace relationship must not mean editing a person's history; a grant must be revocable without rewriting a persistent document; and a profile that travels to a consumer must not carry the record of everyone else who has ever seen it.

## 2. Relationship to the policy

The policy decides whether a grant is even possible.

| Policy visibility | Requester with no grant | With a matching grant |
|---|---|---|
| `agent-discoverable` | May read | Grant unnecessary |
| `requires-grant` | May not read | May read, within the grant's scope and window |
| `withheld` | May not read | Still may not read |

`withheld` is not overridable by a grant. To disclose a withheld item, the person changes the policy first. This keeps the policy the single, readable statement of what the person is willing to share, instead of a default that a pile of grants quietly contradicts.

## 3. `DisclosureGrant`, sketch

Non-normative. Identifier prefix `grant:`.

```jsonc
{
  "@type": "DisclosureGrant",
  "grantId": "grant:2026-10-example-authority",
  "grantorRef": "profile:...",              // the person
  "requester": {
    "identifierUri": "https://example.org/orgs/example-authority",
    "displayName": "Example Metropolitan Development Authority",
    "kind": "employer",                     // employer | agency | platform | institution | other
    "verifiedBy": null                      // how the requester's identity was established, or null
  },
  "purpose": "Assessment for a transport planner requisition",
  "requestContextRef": "requisition:2026-q4-transport-planner",  // optional, may be null
  "scope": {
    "documents": ["profile:...", "intent:..."],
    "entityRefs": ["capability:...", "evidence:...", "verification:..."],
    "collections": ["history"],
    "fields": ["/compensationExpectation"]
  },
  "validity": { "validFrom": "2026-10-01", "validUntil": "2026-11-15", "observedAt": "...", "lastConfirmedAt": "..." },
  "obligations": {
    "onwardSharing": "forbidden",           // forbidden | named-processors | unrestricted
    "retentionUntil": "2026-12-31",
    "purposeLimited": true
  },
  "revocation": { "revokedAt": null, "reason": null },
  "provenance": [ /* identical $def to v0.2: how this grant was captured */ ]
}
```

The scope reuses the selector vocabulary the disclosure policy already uses — entity references, collections and pointers — so a grant is expressed in the same terms as the policy it unlocks.

## 4. Protocol sketch

1. A requester asks for specific information, stating a purpose.
2. The person's agent evaluates the disclosure policy: anything `agent-discoverable` is answered immediately; anything `withheld` is refused; anything `requires-grant` becomes a proposed scope.
3. The person decides. The decision is the grant.
4. The agent produces a disclosure envelope: a subset document containing only the granted fields, plus the provenance and verification records needed to interpret them.
5. The grant expires or is revoked. The envelope that was already sent cannot be recalled, which is why obligations and minimisation are part of the grant rather than an afterthought.

Two properties are worth stating explicitly because they are easy to lose:

- **Minimisation is structural.** The envelope is built from the grant, not filtered from a full profile at the last moment.
- **The requester's request is data, not instruction.** A job description or a request payload is untrusted input to the person's agent. It cannot widen a scope, change a policy, or trigger disclosure on its own. v0.1's rule that source documents are never agent instructions applies here too.

## 5. What must never appear in `CareerProfile`

Employer or requester identities; grant records; access or audit logs; application, interview or offer state; marketplace transactions; scoring or ranking results produced by a third party; and any counter of who viewed what. If any of these need to exist, they belong in the grant contract, the audit log, or a separate application contract.

## 6. Open questions

1. Where does the audit log live, and is a grant's own record of use separable from an event log the person can inspect and prune?
2. Is a standing grant (an ongoing relationship with an agency) a different object from a one-time grant, or the same object with a longer window and a revocation path?
3. Should an envelope be cryptographically bound to the grant, and does that require verifiable credentials or SD-JWT, or is a signed document sufficient for the first useful version?
4. How does revocation propagate to a requester who has already stored the envelope, beyond the obligations the grant states?
5. Does an unverified requester identity make a grant unsafe enough to refuse, or is stating `verifiedBy: null` on the grant sufficient disclosure to the person deciding?
