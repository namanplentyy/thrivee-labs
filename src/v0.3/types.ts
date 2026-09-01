/**
 * v0.3 trust layer: relationships, referral availability, endorsements and referrals.
 *
 * The JSON Schemas must each carry their own copy of the shared definitions,
 * because a single-file structured-output schema cannot use a cross-file `$ref`.
 * TypeScript has no such limitation, so this module imports the v0.2 primitives
 * instead of restating them. `CareerProfile` and `OpportunityIntent` are unchanged
 * and are re-exported here so a consumer of the trust layer has the whole family
 * from one entry point.
 */
import type {
  Ambiguity,
  Claim,
  ClaimId,
  DisclosurePolicy,
  EntityId,
  Instant,
  JsonLdContext,
  NormalizedDate,
  ProfileId,
  Provenance,
  Sensitivity,
  SourceDocument,
  TaxonomyMapping,
  TransportJsonLdContext,
  Validity,
  Verification,
  Warning,
} from "../v0.2/types.js";

export * from "../v0.2/types.js";

export const TRUST_SCHEMA_VERSION = "0.3.0" as const;

/* ------------------------------------------------------------------ */
/* Identifiers                                                         */
/* ------------------------------------------------------------------ */

export type PartyId = `party:${string}`;
export type RelationshipId = `relationship:${string}`;
export type RelationshipContextId = `relationship-context:${string}`;
export type RelationshipTypeExtensionId = `relationship-type:${string}`;
export type ReferralAvailabilityId = `referral-availability:${string}`;
export type ReferralScopeEntryId = `referral-scope:${string}`;
export type EndorsementId = `endorsement:${string}`;
export type ReferralId = `referral:${string}`;
export type ReferralApprovalId = `approval:${string}`;
export type OpportunityReferenceId = `opportunity-reference:${string}`;
export type EngagementRef = `engagement:${string}`;

/**
 * Reserved and deliberately unresolvable in this repository. `requisition:` binds
 * to the future `HiringIntent` contract and `grant:` to the future
 * `DisclosureGrant` contract; both are designed under `docs/design/`.
 */
export type RequisitionRef = `requisition:${string}`;
export type DisclosureGrantRef = `grant:${string}`;

/* ------------------------------------------------------------------ */
/* Party                                                               */
/* ------------------------------------------------------------------ */

export type PartyKind = "person" | "organization";

/**
 * Assurance above `self-asserted` requires a confirmed `Verification` in the same
 * document whose `targetRef` names the party.
 */
export type IdentityAssurance =
  | "unverified"
  | "self-asserted"
  | "contact-verified"
  | "domain-verified"
  | "institution-verified"
  | "platform-verified";

/**
 * A routing handle, not a career record. A referrer who has never created a
 * `CareerProfile` is a party with a null `profileRef` and a routable
 * `identifierUri`, so the trust layer never invents a profile for them.
 * At least one of `profileRef`, `identifierUri` or `displayName` is present.
 */
export interface Party {
  id: PartyId;
  type: "Party";
  partyKind: PartyKind;
  profileRef: ProfileId | null;
  displayName: Claim<string> | null;
  identifierUri: string | null;
  identityAssurance: IdentityAssurance;
  sensitivity: Sensitivity;
  validity: Validity;
  provenance: Provenance[];
}

/* ------------------------------------------------------------------ */
/* Relationship assertion                                              */
/* ------------------------------------------------------------------ */

export type RelationshipType =
  | "manager"
  | "direct-report"
  | "colleague"
  | "project-collaborator"
  | "professor"
  | "student"
  | "intern-supervisor"
  | "classmate"
  | "alumni-connection"
  | "client"
  | "mentor"
  | "other";

/** Required whenever `relationshipTypes` contains `other`, and only then. */
export interface RelationshipTypeExtension {
  id: RelationshipTypeExtensionId;
  type: "RelationshipTypeExtension";
  label: Claim<string>;
  uri: string | null;
}

export interface RelationshipContext {
  id: RelationshipContextId;
  type: "RelationshipContext";
  organizationRef: PartyId | null;
  /** An engagement in the candidate's career profile. */
  engagementRef: EngagementRef | null;
  from: NormalizedDate | null;
  to: NormalizedDate | null;
  note: string | null;
  provenance: Provenance[];
}

export type CounterpartyStatus =
  | "unconfirmed"
  | "confirmed"
  | "declined"
  | "withdrawn";

/**
 * A party act, deliberately separate from a `Verification`, which is a third party
 * checking the facts. A unilateral claim, a counterparty confirmation and an
 * independent verification are three states and never collapse into one.
 */
export interface CounterpartyConfirmation {
  status: CounterpartyStatus;
  confirmedByRef: PartyId | null;
  confirmedAt: Instant | null;
  note: string | null;
  provenance: Provenance[];
}

export interface RelationshipAssertion {
  "@context": JsonLdContext;
  "@type": "RelationshipAssertion";
  schemaVersion: typeof TRUST_SCHEMA_VERSION;
  relationshipId: RelationshipId;
  parties: Party[];
  partyARef: PartyId;
  partyBRef: PartyId;
  relationshipTypes: RelationshipType[];
  relationshipTypeExtensions: RelationshipTypeExtension[];
  contexts: RelationshipContext[];
  assertedByRef: PartyId;
  counterparty: CounterpartyConfirmation;
  validity: Validity;
  /** Never `agent-discoverable`: the relationship graph is restricted by default. */
  disclosure: DisclosurePolicy;
  sourceDocuments: SourceDocument[];
  verifications: Verification[];
  ambiguities: Ambiguity[];
  warnings: Warning[];
}

export interface RelationshipAssertionTransport
  extends Omit<RelationshipAssertion, "@context" | "@type"> {
  jsonldContext: TransportJsonLdContext;
  jsonldType: "RelationshipAssertion";
}

/* ------------------------------------------------------------------ */
/* Referral availability                                               */
/* ------------------------------------------------------------------ */

export type AvailabilityStatus = "open" | "limited" | "not-available";

/**
 * How much a consumer may learn before the referrer has approved anything.
 * `anonymous-path-only` lets an agent learn that a path exists without learning
 * who is on it.
 */
export type Discoverability = "none" | "anonymous-path-only" | "named";

export type ReferralScopeKind = "organization" | "domain" | "career-family";

export interface ReferralScopeEntry {
  id: ReferralScopeEntryId;
  type: "ReferralScopeEntry";
  kind: ReferralScopeKind;
  label: Claim<string>;
  organizationRef: PartyId | null;
}

export interface AvailabilityScope {
  organizations: ReferralScopeEntry[];
  domains: ReferralScopeEntry[];
  careerFamilies: ReferralScopeEntry[];
  relationshipRequirements: RelationshipType[];
  note: string | null;
}

/**
 * The referral counterpart of `OpportunityIntent`: temporary state that expires.
 * Absence of this document means absence, never `not-available`.
 */
export interface ReferralAvailability {
  "@context": JsonLdContext;
  "@type": "ReferralAvailability";
  schemaVersion: typeof TRUST_SCHEMA_VERSION;
  referralAvailabilityId: ReferralAvailabilityId;
  parties: Party[];
  subjectRef: PartyId;
  status: Claim<AvailabilityStatus> & { id: ClaimId };
  discoverability: Claim<Discoverability> & { id: ClaimId };
  scope: AvailabilityScope;
  /** Subjects are the document's own `referral-scope:` entries. */
  taxonomyMappings: TaxonomyMapping[];
  validity: Validity;
  disclosure: DisclosurePolicy;
  sourceDocuments: SourceDocument[];
  verifications: Verification[];
  ambiguities: Ambiguity[];
  warnings: Warning[];
}

export interface ReferralAvailabilityTransport
  extends Omit<ReferralAvailability, "@context" | "@type"> {
  jsonldContext: TransportJsonLdContext;
  jsonldType: "ReferralAvailability";
}

/* ------------------------------------------------------------------ */
/* Endorsement                                                         */
/* ------------------------------------------------------------------ */

export type EndorsementScope =
  | "general"
  | "capability"
  | "skill"
  | "artifact"
  | "project"
  | "engagement"
  | "role-performance";

/**
 * What one party will vouch for about another, and on what basis. Not tied to one
 * opportunity, so it stays useful across many. An endorsement may never carry
 * `agent-inferred` provenance: a machine cannot vouch for anyone.
 */
export interface Endorsement {
  "@context": JsonLdContext;
  "@type": "Endorsement";
  schemaVersion: typeof TRUST_SCHEMA_VERSION;
  endorsementId: EndorsementId;
  parties: Party[];
  endorserRef: PartyId;
  subjectRef: ProfileId;
  scope: EndorsementScope;
  /** Required for every scope but `general`; namespace must match the scope. */
  targetRefs: EntityId[];
  /** A relationship, engagement, evidence, artifact or capability. */
  basisRefs: EntityId[];
  statement: Claim<string> | null;
  /** True exactly when the endorser resolves to the subject's own profile. */
  selfAttested: boolean;
  validity: Validity;
  disclosure: DisclosurePolicy;
  sourceDocuments: SourceDocument[];
  verifications: Verification[];
  ambiguities: Ambiguity[];
  warnings: Warning[];
}

export interface EndorsementTransport
  extends Omit<Endorsement, "@context" | "@type"> {
  jsonldContext: TransportJsonLdContext;
  jsonldType: "Endorsement";
}

/* ------------------------------------------------------------------ */
/* Referral                                                            */
/* ------------------------------------------------------------------ */

/** How the workflow started. `platform-suggested` is never itself a referral. */
export type ReferralOrigin =
  | "candidate-requested"
  | "employer-requested"
  | "referrer-initiated"
  | "platform-suggested";

export type ApprovalRole = "referrer" | "candidate" | "other";

export type ApprovalDecision =
  | "pending"
  | "approved"
  | "declined"
  | "withdrawn"
  | "expired";

/** Any decision other than `pending` carries `decidedAt` and provenance. */
export interface ReferralApproval {
  id: ReferralApprovalId;
  type: "ReferralApproval";
  actorRef: PartyId;
  role: ApprovalRole;
  decision: ApprovalDecision;
  decidedAt: Instant | null;
  note: string | null;
  provenance: Provenance[];
}

export type OpportunityBindingStatus =
  | "deferred-hiring-intent"
  | "resolved-hiring-intent";

/**
 * A stable reference to the opportunity, not a copy of it. Job-description fields
 * are deliberately not duplicated: `label` exists so a document is readable.
 */
export interface OpportunityReference {
  id: OpportunityReferenceId;
  type: "OpportunityReference";
  opportunityRef: RequisitionRef;
  bindingStatus: OpportunityBindingStatus;
  label: Claim<string> | null;
  organizationRef: PartyId | null;
}

/**
 * `pending` until the required actors approve, then `active`. Expiry is not a
 * status: it is computed from `validity.validUntil` against a caller-supplied date.
 */
export type ReferralStatus = "pending" | "active" | "declined" | "withdrawn";

export interface Referral {
  "@context": JsonLdContext;
  "@type": "Referral";
  schemaVersion: typeof TRUST_SCHEMA_VERSION;
  referralId: ReferralId;
  parties: Party[];
  candidateRef: ProfileId;
  referrerRef: PartyId;
  opportunity: OpportunityReference;
  origin: ReferralOrigin;
  relationshipRefs: RelationshipId[];
  endorsementRefs: EndorsementId[];
  availabilityRef: ReferralAvailabilityId | null;
  /** `active` requires an approved `referrer` decision and an approved `candidate` decision. */
  approvals: ReferralApproval[];
  status: ReferralStatus;
  /** Set only while the referral is active. */
  referredAt: Instant | null;
  /** What the employer may read is decided by these grants, not by this document. */
  disclosureGrantRefs: DisclosureGrantRef[];
  validity: Validity;
  disclosure: DisclosurePolicy;
  sourceDocuments: SourceDocument[];
  verifications: Verification[];
  ambiguities: Ambiguity[];
  warnings: Warning[];
}

export interface ReferralTransport extends Omit<Referral, "@context" | "@type"> {
  jsonldContext: TransportJsonLdContext;
  jsonldType: "Referral";
}

/** Every canonical document in the trust layer. */
export type TrustDocument =
  | RelationshipAssertion
  | ReferralAvailability
  | Endorsement
  | Referral;

export type TrustDocumentTransport =
  | RelationshipAssertionTransport
  | ReferralAvailabilityTransport
  | EndorsementTransport
  | ReferralTransport;
