// Single place where the UI talks to the backend.
// Pages never call fetch() directly, so swapping mock -> real API is a config change.
//
// Route paths are PROPOSED (contracts_2026-11-16.md says C decides them). If C picks
// different paths, change them here only.

import { API_BASE, USE_MOCK, REQUEST_TIMEOUT_MS } from '../config.js';
import * as mock from './mockServer.js';
import { ApiError } from './errors.js';

export { ApiError };

export const ROUTES = {
  complaint: '/api/complaints',                 // POST { email_text, session_id? }
  followUp: (sessionId) => `/api/sessions/${sessionId}/messages`, // POST { message, selected_candidate? }
  session: (sessionId) => `/api/sessions/${sessionId}`,           // GET  -> last state (restart recovery)
  weekly: '/api/weekly',                        // GET  ?week_start=YYYY-MM-DD
  health: '/api/health',
};

async function request(path, { method = 'GET', body } = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    const response = await fetch(`${API_BASE}${path}`, {
      method,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });
    // Lesson 2.5: fetch does not throw on 4xx/5xx, so check response.ok ourselves.
    if (!response.ok) {
      let detail = null;
      try {
        detail = await response.json();
      } catch {
        // body was not JSON; keep the status only
      }
      throw new ApiError(detail?.error?.message ?? `Server error: ${response.status}`, {
        status: response.status,
        code: detail?.error?.code ?? 'HTTP_ERROR',
        retryable: detail?.error?.retryable ?? response.status >= 500,
      });
    }
    return await response.json();
  } catch (err) {
    if (err instanceof ApiError) throw err;
    if (err.name === 'AbortError') {
      throw new ApiError('The assistant took too long to answer.', { code: 'TIMEOUT' });
    }
    throw new ApiError('Cannot reach the triage service. Is the backend running?', { code: 'NETWORK' });
  } finally {
    clearTimeout(timer);
  }
}

export function submitComplaint({ emailText, sessionId, simulateFailure = false }) {
  if (USE_MOCK) return mock.submitComplaint({ emailText, sessionId, simulateFailure });
  return request(ROUTES.complaint, { method: 'POST', body: { email_text: emailText, session_id: sessionId } });
}

export function sendFollowUp({ sessionId, message, selectedCandidate }) {
  if (USE_MOCK) return mock.sendFollowUp({ sessionId, message, selectedCandidate });
  return request(ROUTES.followUp(sessionId), {
    method: 'POST',
    body: { message, selected_candidate: selectedCandidate },
  });
}

export function getSession(sessionId) {
  if (USE_MOCK) return mock.getSession(sessionId);
  return request(ROUTES.session(sessionId));
}

export function getWeekly(weekStart) {
  if (USE_MOCK) return mock.getWeekly(weekStart);
  return request(`${ROUTES.weekly}?week_start=${encodeURIComponent(weekStart)}`);
}

export function getWeeks() {
  if (USE_MOCK) return mock.getWeeks();
  return request(`${ROUTES.weekly}/weeks`);
}

export const isMock = USE_MOCK;
