🧪 [testing] add tests for buildFaqJsonLd in schema.ts

🎯 **What:** The testing gap addressed
The function `buildFaqJsonLd` in `src/lib/schema.ts` had no tests verifying its logic to generate Schema.org `FAQPage` JSON-LD from an array of questions and answers.

📊 **Coverage:** What scenarios are now tested
- Single FAQ item
- Multiple FAQ items
- Empty array

✨ **Result:** The improvement in test coverage
`src/lib/schema.ts` `buildFaqJsonLd` functionality is fully tested and its contract is locked in. The new tests run green in Vitest along with the rest of the test suite.
