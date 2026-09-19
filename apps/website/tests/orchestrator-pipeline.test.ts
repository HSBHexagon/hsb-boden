import { describe, it, expect } from "vitest";
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

describe("Automated Skill Orchestrator", () => {
  const scriptPath = resolve(__dirname, "../scripts/skill-orchestrator.mjs");
  it("should have orchestrator script defined", () => {
    expect(existsSync(scriptPath)).toBe(true);
    const content = readFileSync(scriptPath, "utf-8");
    expect(content).toContain("runAuditPipeline");
  });
});
