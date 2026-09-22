import { isProductionAnalyticsHost } from "./analytics";

export function getCloudflareWebAnalyticsToken(): string | undefined {
  return import.meta.env.PUBLIC_CLOUDFLARE_WEB_ANALYTICS_TOKEN;
}

export function initializeCloudflareAnalytics(
  browserWindow: Window,
  browserDocument: Document,
  hostname = browserWindow.location.hostname,
  token = getCloudflareWebAnalyticsToken(),
) {
  if (!token) return;
  if (!isProductionAnalyticsHost(hostname)) return;
  if (browserDocument.querySelector('script[data-hsb-cf-analytics="true"]')) return;

  const script = browserDocument.createElement("script");
  script.defer = true;
  script.src = "https://static.cloudflareinsights.com/beacon.min.js";
  script.dataset.cfBeacon = JSON.stringify({ token });
  script.dataset.hsbCfAnalytics = "true";
  browserDocument.head.appendChild(script);
}
