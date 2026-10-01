export const GA4_MEASUREMENT_ID = "G-VC4BJBEFTV";
export const PRODUCTION_ANALYTICS_HOST = "www.hsb-boden.de";
export function canTrackAnalyticsLocation(hostname: string, pathname: string): boolean {
  return hostname.toLowerCase() === PRODUCTION_ANALYTICS_HOST && !/^\/abmelden(?:\/|$)/i.test(pathname);
}
