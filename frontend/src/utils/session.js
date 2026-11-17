// Remembers the last session ID in this browser so the UI can recover after a backend restart.
const SESSION_KEY = 'merlion-last-session-id';

export function rememberSession(id) {
  try {
    if (id) localStorage.setItem(SESSION_KEY, id);
    else localStorage.removeItem(SESSION_KEY);
  } catch {
    // storage unavailable — recovery will report nothing to recover
  }
}

export function readRememberedSession() {
  try {
    return localStorage.getItem(SESSION_KEY);
  } catch {
    return null;
  }
}
