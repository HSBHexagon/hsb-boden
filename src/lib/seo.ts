import { site } from "../data/site";

export function absoluteUrl(path = "/") {
  if (path.startsWith("http")) return path;
  return `${site.domain}${path.startsWith("/") ? path : `/${path}`}`;
}

export function canonical(path: string) {
  const normalized = path.endsWith("/") ? path : `${path}/`;
  return absoluteUrl(normalized);
}

export function pageTitle(title?: string) {
  return title ?? site.defaultTitle;
}
