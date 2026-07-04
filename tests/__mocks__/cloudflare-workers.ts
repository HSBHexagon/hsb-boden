export class MockKV {
  private store = new Map<string, string>();

  async get(key: string, type?: "text" | "json" | "arrayBuffer" | "stream"): Promise<any> {
    const val = this.store.get(key);
    if (val === undefined) return null;
    if (type === "json") return JSON.parse(val);
    return val;
  }

  async put(key: string, value: string | ArrayBuffer | ArrayBufferView | ReadableStream, options?: any): Promise<void> {
    this.store.set(key, value as string);
  }

  async delete(key: string): Promise<void> {
    this.store.delete(key);
  }

  reset() {
    this.store.clear();
  }
}

export const mockKVStore = new MockKV();

export const env: Record<string, any> = {
  LEAD_WEBHOOK_URL: "https://script.google.com/macros/s/EXAMPLE/exec",
  RATE_LIMIT_KV: mockKVStore,
};
