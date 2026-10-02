export function analyticsPageLocation(location: Pick<Location, "origin" | "pathname">): string {
  const path = /^\/[a-z0-9/_-]*$/i.test(location.pathname) ? location.pathname : "/";
  return location.origin + path;
}
export function analyticsReferrer(referrer: string): string {
  try {
    const url = new URL(referrer);
    return url.protocol === "https:" || url.protocol === "http:" ? url.origin : "";
  } catch { return ""; }
}
