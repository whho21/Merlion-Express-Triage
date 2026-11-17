// Runtime configuration (Lesson 2.11 pattern: import.meta.env + VITE_ prefix).
// Only non-secret values belong here. The LLM key never reaches the browser.

const env = import.meta.env ?? {};

export const API_BASE = (env.VITE_API_BASE_URL ?? '').replace(/\/$/, '');

// Default to mock mode until C's API is reachable. Set VITE_USE_MOCK=false to call the real API.
export const USE_MOCK = env.VITE_USE_MOCK !== 'false' || API_BASE === '';

export const REQUEST_TIMEOUT_MS = 45000;
