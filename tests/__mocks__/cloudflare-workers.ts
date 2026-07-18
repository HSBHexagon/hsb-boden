export class MockKV {
  private store = new Map<string, string>();

  async get(key: string, _type: "json"): Promise<any> {
    const raw = this.store.get(key);
    if (!raw) return null;
    return JSON.parse(raw);
  }

  async put(key: string, value: string, _options?: { expirationTtl?: number }): Promise<void> {
    this.store.set(key, value);
  }

  reset() {
    this.store.clear();
  }
}

export const mockKV = new MockKV();

export const env: Record<string, any> = {
  LEAD_WEBHOOK_URL: "https://script.google.com/macros/s/EXAMPLE/exec",
  LEAD_WEBHOOK_CONFIG: undefined,
  RATE_LIMIT_KV: mockKV,
};
