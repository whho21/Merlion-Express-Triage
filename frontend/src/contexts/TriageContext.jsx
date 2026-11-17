// Lesson 2.6 pattern: Context + useReducer as a small shared store.
// Async calls live in action helpers (not in effects), so the UI stays predictable.

import { useCallback, useMemo, useReducer } from 'react';
import { submitComplaint, sendFollowUp, getSession } from '../api/client.js';
import { initialTriageState, triageReducer } from '../reducers/triageReducer.js';
import { TriageContext } from './triageContextObject.js';
import { rememberSession, readRememberedSession } from '../utils/session.js';

export function TriageProvider({ children }) {
  const [state, dispatch] = useReducer(triageReducer, initialTriageState);

  const run = useCallback(async (request, call, userText) => {
    dispatch({ type: 'requestStarted', request });
    try {
      const result = await call();
      rememberSession(result.session_id);
      dispatch({ type: 'requestSucceeded', result, userText });
    } catch (error) {
      dispatch({ type: 'requestFailed', error });
    }
  }, []);

  const actions = useMemo(
    () => ({
      setEmailText: (text) => dispatch({ type: 'setEmailText', text }),

      submit: ({ emailText, simulateFailure = false }) =>
        run(
          { kind: 'submit', payload: { emailText, simulateFailure } },
          () => submitComplaint({ emailText, simulateFailure }),
          'Complaint email submitted',
        ),

      chooseCandidate: (sessionId, candidate) =>
        run(
          { kind: 'followUp', payload: { sessionId, selectedCandidate: candidate } },
          () => sendFollowUp({ sessionId, selectedCandidate: candidate }),
          `It is the ${candidate.system_version.toUpperCase()} order ${candidate.order_id}.`,
        ),

      askFollowUp: (sessionId, message) =>
        run({ kind: 'followUp', payload: { sessionId, message } }, () => sendFollowUp({ sessionId, message }), message),

      retry: (lastRequest) => {
        if (!lastRequest) return;
        const { kind, payload } = lastRequest;
        if (kind === 'submit') {
          return run(lastRequest, () => submitComplaint(payload), 'Complaint email submitted (retry)');
        }
        if (kind === 'followUp') return run(lastRequest, () => sendFollowUp(payload));
      },

      recover: async () => {
        const id = readRememberedSession();
        if (!id) {
          dispatch({ type: 'requestFailed', error: { message: 'No previous session on this browser.', code: 'NO_SESSION', retryable: false } });
          return;
        }
        dispatch({ type: 'requestStarted', request: { kind: 'recover' } });
        try {
          const result = await getSession(id);
          const firstUser = result.messages?.find((m) => m.role === 'user');
          dispatch({ type: 'recovered', result, emailText: firstUser?.text });
        } catch (error) {
          dispatch({ type: 'requestFailed', error });
        }
      },

      reset: () => {
        rememberSession(null);
        dispatch({ type: 'reset' });
      },
    }),
    [run],
  );

  const value = useMemo(() => ({ state, actions }), [state, actions]);
  return <TriageContext.Provider value={value}>{children}</TriageContext.Provider>;
}
