🧪 Add tests for trust schemas

🎯 **What:** Added tests for the trust data Zod schemas located in `src/lib/trust.ts` that were previously missing test coverage.
📊 **Coverage:** Covered all schemas (`publicationStatusSchema`, `qualificationSchema`, `teamProfileDraftSchema`, `caseStudyMetricSchema`, `caseStudyQuoteSchema`, `caseStudyImageSchema`, `caseStudyApprovalsSchema`, `caseStudyDraftSchema`) ensuring valid scenarios are accepted and invalid data (e.g. wrong enums, short strings, missing references) are rejected.
✨ **Result:** Test coverage improved for critical domain types relating to team profiles and case studies. Ensures strict guarantees on content validation formats.
