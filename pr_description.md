🎯 **What:**
Added unit tests for the `trackEvent` function inside `src/lib/tracking.ts`. This closes a testing gap by verifying edge cases around missing `window` object context and verifying successful dataLayer integration.

📊 **Coverage:**
The new tests provide comprehensive coverage of the `trackEvent` function, explicitly checking that:
- It returns early correctly if `window` is `undefined`.
- It safely executes without throwing when `window.dataLayer` exists but is an invalid object type.
- A correct `CustomEvent` is dispatched on `window` using `hsb:tracking` as event type, carrying the right details payload.
- It appropriately defaults to using an empty object for the payload if one isn't explicitly passed.
- It accurately pushes event and payload data to `window.dataLayer` whenever the layer array exists.

✨ **Result:**
Overall reliability is increased. Future changes to tracking event logic or structures can rely on `tests/tracking.test.ts` to detect regressions immediately.
