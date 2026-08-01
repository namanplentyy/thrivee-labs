import type { CareerProfile, CareerProfileTransport } from "./types.js";

/** Convert a provider-safe transport object to canonical JSON-LD losslessly. */
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
/** Convert canonical JSON-LD to the structured-output-safe transport form. */
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
