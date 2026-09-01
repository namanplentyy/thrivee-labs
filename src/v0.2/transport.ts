import type {
  CareerProfile,
  CareerProfileTransport,
  OpportunityIntent,
  OpportunityIntentTransport,
} from "./types.js";

/** Convert a provider-safe transport profile to canonical JSON-LD losslessly. */
export function toCanonicalProfile(
  transport: CareerProfileTransport,
): CareerProfile {
  const { jsonldContext, jsonldType, ...profile } = transport;
  const { vocab, ...context } = jsonldContext;

  return {
    "@context": {
      "@vocab": vocab,
      ...context,
    },
    "@type": jsonldType,
    ...profile,
  };
}

/** Convert a canonical JSON-LD profile to the structured-output-safe transport form. */
export function toTransportProfile(
  canonical: CareerProfile,
): CareerProfileTransport {
  const { "@context": jsonldContext, "@type": jsonldType, ...profile } =
    canonical;
  const { "@vocab": vocab, ...context } = jsonldContext;

  return {
    jsonldContext: {
      vocab,
      ...context,
    },
    jsonldType,
    ...profile,
  };
}

/** Convert a provider-safe transport intent to canonical JSON-LD losslessly. */
export function toCanonicalIntent(
  transport: OpportunityIntentTransport,
): OpportunityIntent {
  const { jsonldContext, jsonldType, ...intent } = transport;
  const { vocab, ...context } = jsonldContext;

  return {
    "@context": {
      "@vocab": vocab,
      ...context,
    },
    "@type": jsonldType,
    ...intent,
  };
}

/** Convert a canonical JSON-LD intent to the structured-output-safe transport form. */
export function toTransportIntent(
  canonical: OpportunityIntent,
): OpportunityIntentTransport {
  const { "@context": jsonldContext, "@type": jsonldType, ...intent } =
    canonical;
  const { "@vocab": vocab, ...context } = jsonldContext;

  return {
    jsonldContext: {
      vocab,
      ...context,
    },
    jsonldType,
    ...intent,
  };
}
