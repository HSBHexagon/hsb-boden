## 2024-03-20 - Add visual required indicators
**Learning:** Adding a red asterisk wrapped in a single span element to fields in the form prevents css grid layouts from accidentally separating the asterisk to an unexpected grid placement. Providing `aria-hidden="true"` to the asterisk prevents the screenreader from redundantly announcing the required status of the field.
**Action:** Always wrap visual asterisks with `aria-hidden="true"` inside of a shared `<span>` with the field label.
