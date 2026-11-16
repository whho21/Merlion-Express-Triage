// In-browser mock of C's API, built only from SYNTHETIC fixtures.
// Lets the React journey be built and demoed before the backend is ready.
// Sessions are kept in sessionStorage so "backend restart" recovery can be demonstrated.

import {
  lateDeliveryResponse,
  ambiguousResponse,
  ambiguousResolvedResponse,
  codConflictResponse,
  damagedResponse,
  notFoundResponse,
  refusalResponse,
} from '../fixtures/complaints.js';
import { WEEKS, buildWeeklyResponse } from '../fixtures/weekly.js';
import { ApiError } from './errors.js';

const STORE_KEY = 'merlion-mock-sessions';
const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function loadStore() {
  try {
    return JSON.parse(sessionStorage.getItem(STORE_KEY) ?? '{}');
  } catch {
    return {};
  }
}

function saveSession(session) {
  try {
    const store = loadStore();
    store[session.session_id] = session;
    sessionStorage.setItem(STORE_KEY, JSON.stringify(store));
  } catch {
    // storage unavailable (private mode); mock still works without recovery
  }
}

let counter = 0;
function newSessionId() {
  counter += 1;
  return `sess-mock-${Date.now().toString(36)}-${counter}`;
}

let failNext = true; // "error" scenario: first call fails, retry succeeds

function pickScenario(text) {
  const t = text.toLowerCase();
  if (/ignore (all )?(your )?(previous )?rules|nric|s\d{7}[a-z]/i.test(text)) return refusalResponse;
  if (t.includes('12345')) return notFoundResponse;
  if (t.includes('97042')) return ambiguousResponse;
  if (t.includes('96310') || t.includes('cod')) return codConflictResponse;
  if (t.includes('98877') || t.includes('broken') || t.includes('damaged')) return damagedResponse;
  return lateDeliveryResponse;
}

export async function submitComplaint({ emailText, sessionId, simulateFailure }) {
  await delay(1400);
  if (simulateFailure && failNext) {
    failNext = false;
    throw new ApiError('Triage service unavailable (503). The SQL tool did not respond.', {
      status: 503,
      code: 'DEPENDENCY_UNAVAILABLE',
      retryable: true,
    });
  }
  if (!simulateFailure) failNext = true;
  const id = sessionId ?? newSessionId();
  const result = pickScenario(emailText)(id);
  saveSession({ session_id: id, email_text: emailText, messages: [{ role: 'user', text: emailText }], last: result });
  return result;
}

export async function sendFollowUp({ sessionId, message, selectedCandidate }) {
  await delay(1100);
  const session = loadStore()[sessionId];
  if (!session) {
    throw new ApiError('Session not found. It may have expired.', { status: 404, code: 'SESSION_NOT_FOUND', retryable: false });
  }
  let result;
  if (selectedCandidate?.system_version === 'v1' && selectedCandidate?.order_id === 97042) {
    result = ambiguousResolvedResponse(sessionId);
  } else if (selectedCandidate) {
    result = {
      ...ambiguousResponse(sessionId),
      status: 'not_found',
      candidates: [],
      clarification: null,
      abstention: {
        reason: 'The v2 order was created after this email was sent, so it cannot be the order complained about. Please check the order number with the customer.',
      },
    };
  } else {
    // free-text follow-up: answer from the evidence already in the session
    result = {
      ...session.last,
      request_id: `req-mock-fu-${Date.now().toString(36)}`,
      follow_up_answer: answerFollowUp(message, session.last),
    };
  }
  session.messages.push({ role: 'user', text: message ?? `Selected ${selectedCandidate.system_version}` });
  session.last = result;
  saveSession(session);
  return result;
}

function answerFollowUp(message, last) {
  const m = (message ?? '').toLowerCase();
  if (m.includes('pod')) {
    const pod = last.evidence?.find((e) => e.key === 'pod');
    return pod ? pod.summary : 'POD has not been checked for this case yet.';
  }
  if (m.includes('gps') || m.includes('time')) {
    const gps = last.evidence?.find((e) => e.key === 'gps');
    return gps ? gps.summary : 'No GPS evidence in this case.';
  }
  if (m.includes('who') && m.includes('approve')) {
    return last.recommendation
      ? `Approver: ${last.recommendation.approver}.`
      : 'There is no recommendation to approve yet.';
  }
  return 'The mock can answer follow-ups about POD, GPS/time, or approval. The real assistant answers from the same session evidence.';
}

export async function getSession(sessionId) {
  await delay(500);
  const session = loadStore()[sessionId];
  if (!session) {
    throw new ApiError('Session not found after restart.', { status: 404, code: 'SESSION_NOT_FOUND', retryable: false });
  }
  return { ...session.last, recovered: true, messages: session.messages };
}

export async function getWeeks() {
  await delay(200);
  return { weeks: WEEKS, timezone: 'Asia/Singapore', synthetic: true };
}

export async function getWeekly(weekStart) {
  await delay(700);
  const data = buildWeeklyResponse(weekStart);
  if (!data) throw new ApiError(`No data for week ${weekStart}.`, { status: 404, code: 'NO_DATA', retryable: false });
  return data;
}
