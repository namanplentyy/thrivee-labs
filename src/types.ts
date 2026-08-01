export const SCHEMA_VERSION = "0.1.0" as const;

export const JSON_LD_CONTEXT = {
  "@vocab": "https://github.com/namanplentyy/thrivee-labs/ns/career#",
  schema: "https://schema.org/",
  ceasn: "https://purl.org/ctdlasn/terms/",
} as const;

export type ProfileId = `profile:${string}`;
export type EntityId = `${string}:${string}`;
export type ClaimId = `claim:${string}`;
export type SourceDocumentId = `source:${string}`;
export type EngagementId = `engagement:${string}`;
export type SharedClaimId = `shared-claim:${string}`;
export type SkillId = `skill:${string}`;
export type EvidenceId = `evidence:${string}`;
export type AmbiguityId = `ambiguity:${string}`;

export interface JsonLdContext {
  "@vocab": typeof JSON_LD_CONTEXT["@vocab"];
  schema: typeof JSON_LD_CONTEXT.schema;
  ceasn: typeof JSON_LD_CONTEXT.ceasn;
}

export interface TransportJsonLdContext {
  vocab: typeof JSON_LD_CONTEXT["@vocab"];
  schema: typeof JSON_LD_CONTEXT.schema;
  ceasn: typeof JSON_LD_CONTEXT.ceasn;
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
  mediaType: string;
  contentDigest: `sha256:${string}` | null;
  extractionMethod: ExtractionMethod;
  pageCount: number | null;
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

export type IdentityKind =
  | "display-name"
  | "current-location"
  | "contact-route"
  | "stable-id";

export interface IdentityClaim {
  id: `identity:${string}`;
  kind: IdentityKind;
  value: StringClaim;
  sensitivity: Sensitivity;
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
export type NormalizedDate = string;
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
  kind: SharedClaimKind;
  statement: StringClaim;
  candidateEngagementRefs: EngagementId[];
  resolutionStatus: "unresolved" | "resolved";
  resolvedEngagementRefs: EngagementId[];
  ambiguityRef: AmbiguityId;
}

export type EvidenceRelation =
  | "DemonstratedIn"
  | "LearnedIn"
  | "ProducedIn"
  | "AssessedBy"
  | "SupportedBy"
  | "MentionedIn";

export interface EvidenceLink {
  id: EvidenceId;
  relation: EvidenceRelation;
  targetRef:
    | EngagementId
    | SharedClaimId
    | SourceDocumentId
    | `credential:${string}`
    | `artifact:${string}`;
  provenance: Provenance[];
}

export type TaxonomyFramework =
  | "NCO-2015"
  | "ESCO"
  | "O*NET"
  | "CTDL-ASN"
  | "other";

export type TaxonomyMappingMethod =
  | "explicit-in-source"
  | "registry-verified"
  | "manual-reviewed";

export interface TaxonomyMapping {
  framework: TaxonomyFramework;
  code: string;
  uri: string | null;
  label: StringClaim | null;
  mappingMethod: TaxonomyMappingMethod;
  provenance: Provenance[];
}

export interface SkillClaim {
  id: SkillId;
  label: StringClaim;
  claimStatement: StringClaim;
  /** Situational references only; context is not evidence by itself. */
  contextRefs: Array<EngagementId | SharedClaimId>;
  /** Required when the claim statement is agent-inferred. */
  evidenceLinks: EvidenceLink[];
  taxonomyMappings: TaxonomyMapping[];
  ambiguityRefs: AmbiguityId[];
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
  id: `interest:${string}`;
  kind: InterestKind;
  label: StringClaim;
  contextRefs: Array<EngagementId | SharedClaimId>;
}

export type LanguageMode = "reading" | "writing" | "speaking" | "listening";

export interface LanguageClaim {
  id: `language:${string}`;
  language: StringClaim;
  proficiency: StringClaim | null;
  modes: LanguageMode[];
}

export interface PersonalAttributeClaim {
  id: `attribute:${string}`;
  kind: string;
  value: StringClaim;
  sensitivity: Sensitivity;
}

export interface IntentTarget {
  id: `target:${string}`;
  kind: "role" | "industry";
  value: StringClaim;
}

export type IntentConstraintKind =
  | "location"
  | "remote-work"
  | "work-authorization"
  | "compensation"
  | "availability"
  | "schedule"
  | "travel"
  | "relocation"
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
  id: `constraint:${string}`;
  kind: IntentConstraintKind;
  operator: ConstraintOperator;
  value: StringClaim;
}

export type IntentPreferenceKind =
  | "location"
  | "remote-work"
  | "work-environment"
  | "company-stage"
  | "role"
  | "industry"
  | "compensation"
  | "schedule"
  | "travel"
  | "other";

export interface IntentPreference {
  id: `preference:${string}`;
  kind: IntentPreferenceKind;
  value: StringClaim;
}

export interface CareerIntent {
  targets: IntentTarget[];
  constraints: IntentConstraint[];
  preferences: IntentPreference[];
}

export type AmbiguityKind =
  | "association"
  | "shared-description"
  | "repeated-occurrence"
  | "date-interpretation"
  | "classification"
  | "field-value"
  | "other";

export interface AmbiguityCandidate {
  value: string;
  candidateRefs: EntityId[];
  confidence: number;
  provenance: Provenance[];
}

export interface Ambiguity {
  id: AmbiguityId;
  kind: AmbiguityKind;
  status: "unresolved" | "resolved" | "deferred";
  fieldPath: string;
  reason: StringClaim;
  relatedRefs: EntityId[];
  candidates: AmbiguityCandidate[];
  selectedValue: string | null;
}

export interface Warning {
  code: string;
  severity: "info" | "warning" | "error";
  message: string;
  relatedRefs: EntityId[];
}

export interface CareerProfile {
  "@context": JsonLdContext;
  "@type": "CareerProfile";
  schemaVersion: typeof SCHEMA_VERSION;
  profileId: ProfileId;
  sourceDocuments: SourceDocument[];
  identity: IdentityClaim[];
  history: Engagement[];
  sharedClaims: SharedClaim[];
  skills: SkillClaim[];
  interests: InterestClaim[];
  languages: LanguageClaim[];
  attributes: PersonalAttributeClaim[];
  intent: CareerIntent;
  ambiguities: Ambiguity[];
  warnings: Warning[];
}

export interface CareerProfileTransport
  extends Omit<CareerProfile, "@context" | "@type"> {
  jsonldContext: TransportJsonLdContext;
  jsonldType: "CareerProfile";
}
