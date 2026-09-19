import { execSync } from "node:child_process";

export function runAuditPipeline() {
  console.log("🚀 [Skill Orchestrator] Starting Autonomous Quality & Performance Audit...");

  // 1. Vitest Performance Test Suite
  console.log("▶ [Skill: web-perf] Running performance unit tests...");
  execSync("npm run test:perf", { stdio: "inherit" });

  // 2. Wrangler Functions Dry-Run
  console.log("▶ [Skill: wrangler & workers-best-practices] Validating edge functions build...");
  execSync("npm run deploy:dry-run", { stdio: "inherit" });

  // 3. Static Type & Astro Check
  console.log("▶ [Skill: a11y-debugging & osvScanner] Running security & schema validations...");
  execSync("npm run check", { stdio: "inherit" });

  console.log("✅ [Skill Orchestrator] All gates passed successfully.");
}

if (process.argv[1]?.endsWith("skill-orchestrator.mjs")) {
  runAuditPipeline();
}
