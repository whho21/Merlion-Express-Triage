// Lesson 2.6 pattern: all triage state transitions in one reducer with explicit actions.

export const initialTriageState = {
  emailText: '',
  phase: 'idle', // idle | submitting | done | error
  result: null,
  error: null,
  sessionId: null,
  history: [], // [{ role: 'user'|'assistant', text, at }]
  lastRequest: null, // { kind: 'submit'|'followUp'|'recover', payload } — used by Retry
};

export function triageReducer(state, action) {
  switch (action.type) {
    case 'setEmailText':
      return { ...state, emailText: action.text };

    case 'requestStarted':
      // A new complaint starts a new conversation; follow-ups and retries keep it.
      return {
        ...state,
        phase: 'submitting',
        error: null,
        lastRequest: action.request,
        ...(action.request?.kind === 'submit' ? { result: null, sessionId: null, history: [] } : {}),
      };

    case 'requestSucceeded': {
      const r = action.result;
      const assistantText =
        r.follow_up_answer ??
        r.recommendation?.summary ??
        r.clarification?.question ??
        r.abstention?.reason ??
        `Status: ${r.status}`;
      return {
        ...state,
        phase: 'done',
        result: r,
        sessionId: r.session_id ?? state.sessionId,
        history: [
          ...state.history,
          ...(action.userText ? [{ role: 'user', text: action.userText, at: Date.now() }] : []),
          { role: 'assistant', text: assistantText, at: Date.now() },
        ],
      };
    }

    case 'requestFailed':
      return { ...state, phase: 'error', error: action.error };

    case 'recovered':
      return {
        ...state,
        phase: 'done',
        result: action.result,
        sessionId: action.result.session_id,
        emailText: action.emailText ?? state.emailText,
        history: [{ role: 'system', text: 'Session recovered after restart.', at: Date.now() }],
      };

    case 'reset':
      return { ...initialTriageState };

    default:
      throw new Error(`Unknown triage action: ${action.type}`);
  }
}
