🔒 Fix XSS vulnerability in JSON-LD script tag

🎯 What: Fixed an XSS vulnerability in `src/pages/karriere/index.astro` where structured data was embedded without proper serialization via `JSON.stringify`.

⚠️ Risk: Using `JSON.stringify` inside an HTML `<script>` tag can allow an attacker to prematurely close the `<script>` tag by passing data containing `</script>`. This could enable the execution of arbitrary JavaScript, potentially leading to a Cross-Site Scripting (XSS) attack. Although this data might be static currently, any dynamic data injected into it later would pose a severe security risk.

🛡️ Solution: Imported and used the existing `sanitizeJsonLd` function from `src/lib/sanitize.ts` instead of `JSON.stringify`. `sanitizeJsonLd` uses the `serialize-javascript` package with `isJSON: true` to safely serialize data and properly escape characters that could be interpreted as HTML.
