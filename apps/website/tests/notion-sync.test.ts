import { describe, it, expect, vi } from "vitest";
import { mapConcurrent, cmdBulkStatus } from "../scripts/notion-sync.js";

describe("notion-sync performance & correctness", () => {
  describe("mapConcurrent helper", () => {
    it("returns empty array when items array is empty or falsy", async () => {
      expect(await mapConcurrent([], 3, async (x) => x)).toEqual([]);
      // @ts-ignore
      expect(await mapConcurrent(null, 3, async (x) => x)).toEqual([]);
    });

    it("preserves item ordering despite variable async completion times", async () => {
      const items = [100, 20, 50, 10];
      const result = await mapConcurrent(items, 2, async (delay, i) => {
        await new Promise((resolve) => setTimeout(resolve, delay));
        return `item-${i}-${delay}`;
      });

      expect(result).toEqual([
        "item-0-100",
        "item-1-20",
        "item-2-50",
        "item-3-10",
      ]);
    });

    it("enforces max in-flight concurrency limit", async () => {
      let activeCount = 0;
      let maxObservedActive = 0;
      const items = Array.from({ length: 15 }, (_, i) => i);

      await mapConcurrent(items, 3, async () => {
        activeCount++;
        if (activeCount > maxObservedActive) {
          maxObservedActive = activeCount;
        }
        await new Promise((resolve) => setTimeout(resolve, 10));
        activeCount--;
      });

      expect(maxObservedActive).toBeLessThanOrEqual(3);
    });

    it("propagates errors thrown inside mapping function", async () => {
      const items = [1, 2, 3];
      await expect(
        mapConcurrent(items, 2, async (item) => {
          if (item === 2) throw new Error("Failed item 2");
          return item;
        })
      ).rejects.toThrow("Failed item 2");
    });
  });

  describe("cmdBulkStatus benchmark & functionality", () => {
    it("updates all matched pages correctly and executes concurrently faster than sequential", async () => {
      const mockPages = Array.from({ length: 12 }, (_, i) => ({
        id: `page-${i + 1}`,
        properties: {
          Name: { title: [{ text: { content: `Task ${i + 1}` } }] },
          Status: { select: { name: "In Progress" } },
        },
      }));

      const createMockNotion = (delayMs: number) => {
        const updatedPages: Array<{ page_id: string; properties: any }> = [];
        return {
          updatedPages,
          client: {
            databases: {
              query: vi.fn().mockResolvedValue({ results: mockPages }),
            },
            pages: {
              update: vi.fn().mockImplementation(async (params) => {
                await new Promise((resolve) => setTimeout(resolve, delayMs));
                updatedPages.push(params);
                return { id: params.page_id };
              }),
            },
          },
        };
      };

      const delayMs = 20;

      // 1. Sequential execution baseline (concurrency = 1)
      const seqMock = createMockNotion(delayMs);
      const seqStart = performance.now();
      await cmdBulkStatus("db-123", "In Progress", "Done", seqMock.client as any, 1);
      const seqDuration = performance.now() - seqStart;

      // 2. Concurrent execution (concurrency = 4)
      const concMock = createMockNotion(delayMs);
      const concStart = performance.now();
      await cmdBulkStatus("db-123", "In Progress", "Done", concMock.client as any, 4);
      const concDuration = performance.now() - concStart;

      // Verify all pages were updated correctly
      expect(concMock.updatedPages.length).toBe(12);
      expect(concMock.updatedPages[0]).toEqual({
        page_id: "page-1",
        properties: { Status: { select: { name: "Done" } } },
      });

      // Verify speedup: 12 items @ 20ms delay sequentially takes ~240ms.
      // Concurrency 4 takes ~60ms.
      console.log(`Baseline (Sequential): ${seqDuration.toFixed(2)}ms`);
      console.log(`Optimized (Concurrent c=4): ${concDuration.toFixed(2)}ms`);
      console.log(`Speedup factor: ${(seqDuration / concDuration).toFixed(2)}x`);

      expect(concDuration).toBeLessThan(seqDuration * 0.6);
    });
  });
});
