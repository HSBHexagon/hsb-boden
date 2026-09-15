export function toTelephoneHref(phone: string): string {
  return `tel:${phone.replace("(0)", "").replace(/[^+\d]/g, "")}`;
}
