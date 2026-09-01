export const SCHEMA_VERSION = "0.2.0" as const;

export const JSON_LD_CONTEXT = {
  "@vocab": "https://github.com/namanplentyy/thrivee-labs/ns/career#",
  schema: "https://schema.org/",
  ceasn: "https://purl.org/ctdlasn/terms/",
  skos: "http://www.w3.org/2004/02/skos/core#",
  id: "@id",
  type: "@type",
} as const;

export interface JsonLdContext {
  "@vocab": typeof JSON_LD_CONTEXT["@vocab"];
  schema: typeof JSON_LD_CONTEXT.schema;
  ceasn: typeof JSON_LD_CONTEXT.ceasn;
  skos: typeof JSON_LD_CONTEXT.skos;
  /** JSON-LD keyword alias, so every `id` is a node identifier. */
  id: "@id";
  /** JSON-LD keyword alias, so every `type` is a node type. */
  type: "@type";
}

export interface TransportJsonLdContext
  extends Omit<JsonLdContext, "@vocab"> {
  vocab: typeof JSON_LD_CONTEXT["@vocab"];
}

/* ------------------------------------------------------------------ */
/* Identifiers                                                         */
/* ------------------------------------------------------------------ */

export type EntityId = `${string}:${string}`;
export type ProfileId = `profile:${string}`;
export type IntentId = `intent:${string}`;
export type ClaimId = `claim:${string}`;
export type SourceDocumentId = `source:${string}`;
export type IdentityId = `identity:${string}`;
export type EngagementId = `engagement:${string}`;
export type PeriodId = `period:${string}`;
export type SharedClaimId = `shared-claim:${string}`;
export type CapabilityId = `capability:${string}`;
export type ArtifactId = `artifact:${string}`;
export type EvidenceId = `evidence:${string}`;
export type VerificationId = `verification:${string}`;
export type TaxonomyMappingId = `taxonomy-mapping:${string}`;
export type InterestId = `interest:${string}`;
export type LanguageId = `language:${string}`;
export type AttributeId = `attribute:${string}`;
export type AmbiguityId = `ambiguity:${string}`;
export type WarningId = `warning:${string}`;
export type DisclosureId = `disclosure:${string}`;
export type DisclosureRuleId = `disclosure-rule:${string}`;
export type TargetId = `target:${string}`;
export type LocationId = `location:${string}`;
export type EmploymentTypeId = `employment-type:${string}`;
export type CompensationId = `compensation:${string}`;
export type ConstraintId = `constraint:${string}`;
export type PreferenceId = `preference:${string}`;

/* ------------------------------------------------------------------ */
/* Shared primitives                                                   */
/* ------------------------------------------------------------------ */

/** `YYYY`, `YYYY-MM`, or `YYYY-MM-DD`. */
export type NormalizedDate = string;
/** `YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SSZ`. */
export type Instant = string;

/**
 * Temporal metadata for state that can become stale. `lastConfirmedAt` is set
 * only when the subject or an authoritative issuer confirmed the state;
 * extraction time is not confirmation.
 */
export interface Validity {
  validFrom: NormalizedDate | null;
  validUntil: NormalizedDate | null;
  observedAt: Instant | null;
  lastConfirmedAt: Instant | null;
}

export type ExtractionMethod =
  | "native-text"
  | "document-parser"
  | "ocr"
  | "user-entry"
  | "api-import"
  | "other";

export interface SourceDocument {
  id: SourceDocumentId;
  type: "SourceDocument";
  mediaType: string;
  contentDigest: `sha256:${string}` | null;
  extractionMethod: ExtractionMethod;
  pageCount: number | null;
  ingestedAt: Instant | null;
}

export type TextNormalization =
  | "exact"
  | "unicode-normalized"
  | "whitespace-normalized"
  | "extraction-substitution"
  | "unavailable";

/** Character offsets are zero-based and end-exclusive in extracted document text. */
export interface SourceLocator {
  documentId: SourceDocumentId;
  page: number | null;
  charStart: number | null;
  charEnd: number | null;
  sourceText: string | null;
  textDigest: `sha256:${string}` | null;
  textNormalization: TextNormalization;
}

export type ProvenanceMethod =
  | "resume-explicit"
  | "user-entered"
  | "agent-inferred"
  | "institution-issued"
  | "peer-endorsed"
  | "deterministic-normalization";

export type VerificationStatus =
  | "self-attested"
  | "unverified"
  | "institution-verified"
  | "peer-endorsed";

/**
 * A status other than `self-attested` or `unverified` additionally requires a
 * confirmed {@link Verification} resolving to the claim or its owning entity.
 */
export interface Provenance {
  method: ProvenanceMethod;
  verificationStatus: VerificationStatus;
  confidence: number;
  source: SourceLocator | null;
  inferringAgent: string | null;
}

export interface Claim<T> {
  id: ClaimId;
  value: T;
  provenance: Provenance[];
}

export type StringClaim = Claim<string>;
export type NumberClaim = Claim<number>;

export type Sensitivity = "standard" | "sensitive" | "highly-sensitive";

/* ------------------------------------------------------------------ */
/* Taxonomy mapping                                                    */
/* ------------------------------------------------------------------ */

export type TaxonomyFramework =
  | "NCO-2015"
  | "ESCO"
  | "O*NET"
  | "CTDL-ASN"
  | "NSQF"
  | "other";

export type TaxonomyMatchType =
  | "exact-match"
  | "close-match"
  | "broad-match"
  | "narrow-match"
  | "related-match"
  | "no-match"
  | "unknown";

export type TaxonomyMappingStatus =
  | "mapped"
  | "unmapped"
  | "ambiguous"
  | "rejected";

export type TaxonomyMappingMethod =
  | "explicit-in-source"
  | "registry-verified"
  | "manual-reviewed"
  | "reviewed-no-match"
  | "not-attempted";

export type TaxonomyCandidateMethod =
  | "agent-suggested"
  | "explicit-in-source"
  | "registry-verified"
  | "manual-reviewed";

/** A possible code that has not been adopted. `agent-suggested` is legal only here. */
export interface TaxonomyCandidate {
  code: string;
  uri: string | null;
  label: string | null;
  matchType: Exclude<TaxonomyMatchType, "no-match">;
  method: TaxonomyCandidateMethod;
  confidence: number;
  provenance: Provenance[];
}

/** An unknown mapping stays unknown: record `unmapped` or `ambiguous` rather than guessing. */
export interface TaxonomyMapping {
  id: TaxonomyMappingId;
  type: "TaxonomyMapping";
  subjectRef: EntityId;
  framework: TaxonomyFramework;
  frameworkVersion: string | null;
  mappingStatus: TaxonomyMappingStatus;
  code: string | null;
  uri: string | null;
  label: StringClaim | null;
  matchType: TaxonomyMatchType;
  mappingMethod: TaxonomyMappingMethod;
  candidates: TaxonomyCandidate[];
  validity: Validity;
  notes: string[];
  provenance: Provenance[];
}

/* ------------------------------------------------------------------ */
/* Disclosure                                                          */
/* ------------------------------------------------------------------ */

export type Visibility = "agent-discoverable" | "requires-grant" | "withheld";
export type DisclosureBasis =
  | "subject-configured"
  | "producer-default"
  | "policy-default";

/** Exactly one dimension is populated. Precedence: entityRefs, sensitivities, collections. */
export interface DisclosureSelector {
  entityRefs: EntityId[];
  sensitivities: Sensitivity[];
  collections: string[];
}

export interface DisclosureRule {
  id: DisclosureRuleId;
  type: "DisclosureRule";
  selector: DisclosureSelector;
  visibility: Visibility;
  basis: DisclosureBasis;
  note: string | null;
  validity: Validity;
}

/**
 * What an agent may discover without permission. This never records requester
 * identities, marketplace transactions, or consent history.
 */
export interface DisclosurePolicy {
  id: DisclosureId;
  type: "DisclosurePolicy";
  defaultVisibility: Visibility;
  basis: DisclosureBasis;
  rules: DisclosureRule[];
  notes: string[];
  validity: Validity;
}

/* ------------------------------------------------------------------ */
/* Ambiguity and warnings                                              */
/* ------------------------------------------------------------------ */

export type AmbiguityKind =
  | "association"
  | "shared-description"
  | "repeated-occurrence"
  | "date-interpretation"
  | "classification"
  | "field-value"
  | "taxonomy-mapping"
  | "other";

export interface AmbiguityCandidate {
  value: string;
  candidateRefs: EntityId[];
  confidence: number;
  provenance: Provenance[];
}

export interface Ambiguity {
  id: AmbiguityId;
  type: "Ambiguity";
  kind: AmbiguityKind;
  status: "unresolved" | "resolved" | "deferred";
  fieldPath: string;
  reason: StringClaim;
  relatedRefs: EntityId[];
  candidates: AmbiguityCandidate[];
  selectedValue: string | null;
}

export interface Warning {
  id: WarningId;
  type: "Warning";
  code: string;
  severity: "info" | "warning" | "error";
  message: string;
  relatedRefs: EntityId[];
}

/* ------------------------------------------------------------------ */
/* CareerProfile                                                       */
/* ------------------------------------------------------------------ */

/** Factual recency only. Deliberately not a quality, completeness, or strength score. */
export interface Freshness {
  profileGeneratedAt: Instant;
  lastSourceIngestedAt: Instant | null;
  lastSubjectConfirmedAt: Instant | null;
  lastVerificationAt: Instant | null;
  staleAfter: NormalizedDate | null;
}

export type IdentityKind =
  | "display-name"
  | "current-location"
  | "contact-route"
  | "stable-id";

export interface IdentityClaim {
  id: IdentityId;
  type: "IdentityClaim";
  kind: IdentityKind;
  value: StringClaim;
  sensitivity: Sensitivity;
  validity: Validity;
}

export type EngagementType =
  | "employment"
  | "education"
  | "internship"
  | "project"
  | "training"
  | "certification"
  | "volunteer"
  | "award"
  | "publication"
  | "conference"
  | "membership"
  | "career-break"
  | "informal-work"
  | "family-business"
  | "other";

export type EngagementTypeClaim = Claim<EngagementType>;

export type DatePrecision = "day" | "month" | "year" | "mixed" | "unknown";
export type CurrentStatusBasis =
  | "explicit-ongoing"
  | "explicit-completed"
  | "source-range-ended"
  | "unstated"
  | "not-applicable";
export type DateInterpretationStatus =
  | "exact"
  | "normalized"
  | "ambiguous"
  | "unknown";

export interface TemporalAlternative {
  start: NormalizedDate | null;
  end: NormalizedDate | null;
  precision: DatePrecision;
  confidence: number;
  note: string;
}

/**
 * `true` is only valid with explicit ongoing language. `false` requires explicit
 * completion or a source range that has ended. Otherwise use `null`.
 */
export interface TemporalPeriod {
  id: PeriodId;
  type: "TemporalPeriod";
  raw: string | null;
  start: NormalizedDate | null;
  end: NormalizedDate | null;
  precision: DatePrecision;
  isCurrent: boolean | null;
  currentStatusBasis: CurrentStatusBasis;
  interpretationStatus: DateInterpretationStatus;
  occurrenceLabel: string | null;
  alternatives: TemporalAlternative[];
  notes: string[];
  provenance: Provenance[];
}

export interface CredentialDetails {
  credentialName: StringClaim | null;
  fieldOfStudy: StringClaim | null;
  grade: StringClaim | null;
  ncrfCredits: NumberClaim | null;
  nsqfLevel: NumberClaim | null;
}

export interface Engagement {
  id: EngagementId;
  type: "Engagement";
  engagementType: EngagementTypeClaim;
  organization: StringClaim | null;
  roleOrProgram: StringClaim;
  location: StringClaim | null;
  periods: TemporalPeriod[];
  descriptions: StringClaim[];
  credential: CredentialDetails | null;
  ambiguityRefs: AmbiguityId[];
  provenance: Provenance[];
}

export type SharedClaimKind =
  | "description"
  | "responsibility"
  | "achievement"
  | "association"
  | "other";

export interface SharedClaim {
  id: SharedClaimId;
  type: "SharedClaim";
  kind: SharedClaimKind;
  statement: StringClaim;
  candidateEngagementRefs: EngagementId[];
  resolutionStatus: "unresolved" | "resolved";
  resolvedEngagementRefs: EngagementId[];
  ambiguityRef: AmbiguityId;
}

/**
 * `tool` is an instrument (QGIS), `skill` an ability (spatial analysis),
 * `knowledge` a domain, and `practice` something demonstrably done
 * (conducting a transport accessibility analysis).
 */
export type CapabilityKind = "tool" | "skill" | "knowledge" | "practice";

export interface Capability {
  id: CapabilityId;
  type: "Capability";
  capabilityKind: CapabilityKind;
  label: StringClaim;
  claimStatement: StringClaim;
  /** Tools and skills a practice exercised. */
  exercisesRefs: CapabilityId[];
  /** Situational references only; context is not evidence by itself. */
  contextRefs: Array<EngagementId | SharedClaimId>;
  /** Required when the claim statement is agent-inferred or lastDemonstratedAt is set. */
  evidenceRefs: EvidenceId[];
  proficiency: StringClaim | null;
  lastDemonstratedAt: NormalizedDate | null;
  validity: Validity;
  ambiguityRefs: AmbiguityId[];
}

export type ArtifactKind =
  | "document"
  | "report"
  | "publication"
  | "repository"
  | "portfolio-item"
  | "dataset"
  | "design"
  | "presentation"
  | "credential-record"
  | "assessment-result"
  | "reference-letter"
  | "media"
  | "other";

/** A thing that exists and can substantiate a claim, declared even when no URI is available. */
export interface Artifact {
  id: ArtifactId;
  type: "Artifact";
  artifactKind: ArtifactKind;
  title: StringClaim;
  description: StringClaim | null;
  uri: string | null;
  custodian: StringClaim | null;
  sourceDocumentRef: SourceDocumentId | null;
  accessMode: "public" | "on-request" | "private" | "unknown";
  validity: Validity;
  provenance: Provenance[];
}

export type EvidenceRelation =
  | "DemonstratedIn"
  | "LearnedIn"
  | "ProducedIn"
  | "AssessedBy"
  | "SupportedBy"
  | "MentionedIn";

/** A directional edge from a capability claim to what supports it. */
export interface Evidence {
  id: EvidenceId;
  type: "Evidence";
  relation: EvidenceRelation;
  subjectRef: CapabilityId;
  targetRef:
    | EngagementId
    | SharedClaimId
    | ArtifactId
    | SourceDocumentId
    | PeriodId;
  notes: string[];
  validity: Validity;
  provenance: Provenance[];
}

export interface Verifier {
  name: StringClaim;
  kind:
    | "issuing-institution"
    | "employer"
    | "professional-body"
    | "assessment-provider"
    | "peer"
    | "platform"
    | "other";
  identifierUri: string | null;
}

/** Who checked what, how, when, and with what outcome. Targets carry no back-references. */
export interface Verification {
  id: VerificationId;
  type: "Verification";
  targetRef:
    | EvidenceId
    | ArtifactId
    | CapabilityId
    | EngagementId
    | SharedClaimId
    | ClaimId;
  verifier: Verifier;
  method:
    | "issuer-confirmation"
    | "document-inspection"
    | "registry-lookup"
    | "assessment"
    | "peer-endorsement"
    | "other";
  status: "confirmed" | "contradicted" | "inconclusive" | "pending";
  verifiedAt: Instant | null;
  statement: StringClaim | null;
  supportingArtifactRef: ArtifactId | null;
  validity: Validity;
  provenance: Provenance[];
}

export type InterestKind =
  | "field"
  | "industry"
  | "role"
  | "technology"
  | "activity"
  | "subject"
  | "other";

export interface InterestClaim {
  id: InterestId;
  type: "Interest";
  kind: InterestKind;
  label: StringClaim;
  contextRefs: Array<EngagementId | SharedClaimId>;
}

export type LanguageMode = "reading" | "writing" | "speaking" | "listening";

export interface LanguageClaim {
  id: LanguageId;
  type: "LanguageClaim";
  language: StringClaim;
  proficiency: StringClaim | null;
  modes: LanguageMode[];
}

export interface PersonalAttributeClaim {
  id: AttributeId;
  type: "PersonalAttribute";
  kind: string;
  value: StringClaim;
  sensitivity: Sensitivity;
  validity: Validity;
}

/** The persistent representation of a person. Market intent lives in {@link OpportunityIntent}. */
export interface CareerProfile {
  "@context": JsonLdContext;
  "@type": "CareerProfile";
  schemaVersion: typeof SCHEMA_VERSION;
  profileId: ProfileId;
  freshness: Freshness;
  disclosure: DisclosurePolicy;
  sourceDocuments: SourceDocument[];
  identity: IdentityClaim[];
  history: Engagement[];
  sharedClaims: SharedClaim[];
  capabilities: Capability[];
  artifacts: Artifact[];
  evidence: Evidence[];
  verifications: Verification[];
  taxonomyMappings: TaxonomyMapping[];
  interests: InterestClaim[];
  languages: LanguageClaim[];
  attributes: PersonalAttributeClaim[];
  ambiguities: Ambiguity[];
  warnings: Warning[];
}

export interface CareerProfileTransport
  extends Omit<CareerProfile, "@context" | "@type"> {
  jsonldContext: TransportJsonLdContext;
  jsonldType: "CareerProfile";
}

/* ------------------------------------------------------------------ */
/* OpportunityIntent                                                   */
/* ------------------------------------------------------------------ */

export type LookingStatus =
  | "actively-looking"
  | "open-to-offers"
  | "not-looking"
  | "unknown";

export type LookingStatusClaim = Claim<LookingStatus>;

export interface NoticePeriod {
  value: number;
  unit: "day" | "week" | "month";
}

/** Unstated availability stays null; a notice period is never derived from a start date. */
export interface Availability {
  availableFrom: NormalizedDate | null;
  noticePeriod: NoticePeriod | null;
  note: StringClaim | null;
  provenance: Provenance[];
}

export interface IntentTarget {
  id: TargetId;
  type: "IntentTarget";
  kind: "role" | "occupation" | "career-family" | "industry";
  value: StringClaim;
}

export interface LocationPreference {
  id: LocationId;
  type: "LocationPreference";
  label: StringClaim;
  granularity:
    | "country"
    | "state-or-region"
    | "city"
    | "district"
    | "site"
    | "other";
  countryCode: string | null;
  strength: "required" | "preferred" | "acceptable";
  provenance: Provenance[];
}

export type WorkMode = "onsite" | "hybrid" | "remote" | "no-preference" | "unknown";
export type WorkModeClaim = Claim<WorkMode>;

export interface Relocation {
  willingness: "willing" | "not-willing" | "conditional" | "unknown";
  conditions: StringClaim | null;
  targetLocationRefs: LocationId[];
  provenance: Provenance[];
}

export type EmploymentType =
  | "full-time"
  | "part-time"
  | "contract"
  | "internship"
  | "apprenticeship"
  | "temporary"
  | "freelance"
  | "volunteer"
  | "other";

export interface EmploymentTypeClaim {
  id: EmploymentTypeId;
  type: "EmploymentTypePreference";
  value: EmploymentType;
  provenance: Provenance[];
}

/** Optional and never inferred. An amount requires an explicit currency and period. */
export interface CompensationExpectation {
  id: CompensationId;
  type: "CompensationExpectation";
  amountMin: number | null;
  amountMax: number | null;
  currency: string | null;
  period: "hour" | "day" | "month" | "year" | "project" | null;
  basis: "gross" | "net" | "ctc" | "unknown" | null;
  negotiable: boolean | null;
  note: StringClaim | null;
  validity: Validity;
  provenance: Provenance[];
}

/**
 * Aspects with no typed field. Location, work mode, relocation, employment type,
 * availability and compensation have typed fields and must not be restated here.
 */
export type IntentAspect =
  | "schedule"
  | "travel"
  | "work-environment"
  | "company-stage"
  | "industry"
  | "contract-duration"
  | "team-size"
  | "other";

export type ConstraintOperator =
  | "equals"
  | "one-of"
  | "none-of"
  | "minimum"
  | "maximum"
  | "requires"
  | "forbids";

export interface IntentConstraint {
  id: ConstraintId;
  type: "IntentConstraint";
  kind: IntentAspect;
  operator: ConstraintOperator;
  value: StringClaim;
}

export interface IntentPreference {
  id: PreferenceId;
  type: "IntentPreference";
  kind: IntentAspect;
  value: StringClaim;
}

/** Temporary employment-market state. It expires; career history never depends on it. */
export interface OpportunityIntent {
  "@context": JsonLdContext;
  "@type": "OpportunityIntent";
  schemaVersion: typeof SCHEMA_VERSION;
  intentId: IntentId;
  subjectRef: ProfileId;
  validity: Validity;
  disclosure: DisclosurePolicy;
  sourceDocuments: SourceDocument[];
  lookingStatus: LookingStatusClaim;
  availability: Availability;
  targetRoles: IntentTarget[];
  preferredLocations: LocationPreference[];
  workMode: WorkModeClaim;
  relocation: Relocation;
  employmentTypes: EmploymentTypeClaim[];
  compensationExpectation: CompensationExpectation | null;
  constraints: IntentConstraint[];
  preferences: IntentPreference[];
  taxonomyMappings: TaxonomyMapping[];
  ambiguities: Ambiguity[];
  warnings: Warning[];
}

export interface OpportunityIntentTransport
  extends Omit<OpportunityIntent, "@context" | "@type"> {
  jsonldContext: TransportJsonLdContext;
  jsonldType: "OpportunityIntent";
}
