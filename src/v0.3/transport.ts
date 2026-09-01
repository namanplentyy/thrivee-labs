import type {
  Endorsement,
  EndorsementTransport,
  Referral,
  ReferralAvailability,
  ReferralAvailabilityTransport,
  ReferralTransport,
  RelationshipAssertion,
  RelationshipAssertionTransport,
  TrustDocument,
  TrustDocumentTransport,
} from "./types.js";

/**
 * The alias mapping is identical for every document in every version: `@context`
 * becomes `jsonldContext`, `@context.@vocab` becomes `jsonldContext.vocab`, and
 * `@type` becomes `jsonldType`. Nothing else changes, which is what makes the
 * conversion lossless in both directions.
 */
function canonicalize<T extends TrustDocument>(
  transport: TrustDocumentTransport,
): T {
  const { jsonldContext, jsonldType, ...rest } = transport;
  const { vocab, ...context } = jsonldContext;

  return {
    "@context": { "@vocab": vocab, ...context },
    "@type": jsonldType,
    ...rest,
  } as unknown as T;
}

function transportize<T extends TrustDocumentTransport>(
  canonical: TrustDocument,
): T {
  const { "@context": jsonldContext, "@type": jsonldType, ...rest } = canonical;
  const { "@vocab": vocab, ...context } = jsonldContext;

  return {
    jsonldContext: { vocab, ...context },
    jsonldType,
    ...rest,
  } as unknown as T;
}

/** Convert a provider-safe transport relationship assertion to canonical JSON-LD. */
export function toCanonicalRelationship(
  transport: RelationshipAssertionTransport,
): RelationshipAssertion {
  return canonicalize<RelationshipAssertion>(transport);
}

/** Convert a canonical relationship assertion to the structured-output-safe form. */
export function toTransportRelationship(
  canonical: RelationshipAssertion,
): RelationshipAssertionTransport {
  return transportize<RelationshipAssertionTransport>(canonical);
}

/** Convert a provider-safe transport referral availability to canonical JSON-LD. */
export function toCanonicalAvailability(
  transport: ReferralAvailabilityTransport,
): ReferralAvailability {
  return canonicalize<ReferralAvailability>(transport);
}

/** Convert a canonical referral availability to the structured-output-safe form. */
export function toTransportAvailability(
  canonical: ReferralAvailability,
): ReferralAvailabilityTransport {
  return transportize<ReferralAvailabilityTransport>(canonical);
}

/** Convert a provider-safe transport endorsement to canonical JSON-LD. */
export function toCanonicalEndorsement(
  transport: EndorsementTransport,
): Endorsement {
  return canonicalize<Endorsement>(transport);
}

/** Convert a canonical endorsement to the structured-output-safe form. */
export function toTransportEndorsement(
  canonical: Endorsement,
): EndorsementTransport {
  return transportize<EndorsementTransport>(canonical);
}

/** Convert a provider-safe transport referral to canonical JSON-LD. */
export function toCanonicalReferral(transport: ReferralTransport): Referral {
  return canonicalize<Referral>(transport);
}

/** Convert a canonical referral to the structured-output-safe form. */
export function toTransportReferral(canonical: Referral): ReferralTransport {
  return transportize<ReferralTransport>(canonical);
}
