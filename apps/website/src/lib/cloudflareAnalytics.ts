import { isProductionAnalyticsHost } from "./analytics";

export const CLOUDFLARE_WEB_ANALYTICS_TOKEN = "8631653d94cb4fcead06570ed2275043";

export function initializeCloudflareAnalytics(
  browserWindow: Window,
  browserDocument: Document,
  hostname = browserWindow.location.hostname,
) {
  if (!isProductionAnalyticsHost(hostname)) return;
  if (browserDocument.querySelector('script[data-hsb-cf-analytics="true"]')) return;

  const script = browserDocument.createElement("script");
  script.defer = true;
  script.src = "https://static.cloudflareinsights.com/beacon.min.js";
  script.dataset.cfBeacon = JSON.stringify({ token: CLOUDFLARE_WEB_ANALYTICS_TOKEN });
  script.dataset.hsbCfAnalytics = "true";
  browserDocument.head.appendChild(script);
}
