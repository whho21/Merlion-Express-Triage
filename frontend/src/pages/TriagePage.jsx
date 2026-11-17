import { useTriage } from '../contexts/triageContextObject.js';
import { readRememberedSession } from '../utils/session.js';
import { isMock } from '../api/client.js';
import ComplaintForm from '../components/triage/ComplaintForm.jsx';
import ProgressSteps from '../components/triage/ProgressSteps.jsx';
import ErrorPanel from '../components/triage/ErrorPanel.jsx';
import ResultView from '../components/triage/ResultView.jsx';
import styles from './Pages.module.css';

export default function TriagePage() {
  const { state, actions } = useTriage();
  const busy = state.phase === 'submitting';
  const canRecover = !state.result && Boolean(readRememberedSession());

  return (
    <div className={styles.page}>
      <header className={styles.pageHeader}>
        <div>
          <h1 className={styles.h1}>Complaint triage</h1>
          <p className={styles.lede}>From one customer email to a cited, policy-based recommendation — or an honest “not on file”.</p>
        </div>
        <div className={styles.headerActions}>
          {canRecover && (
            <button type="button" className="btn" onClick={actions.recover} disabled={busy}>
              Resume last session
            </button>
          )}
          {state.result && (
            <button type="button" className="btn" onClick={actions.reset} disabled={busy}>
              New complaint
            </button>
          )}
        </div>
      </header>

      <ComplaintForm
        value={state.emailText}
        onChange={actions.setEmailText}
        onSubmit={actions.submit}
        submitting={busy}
        isMock={isMock}
      />

      {busy && <ProgressSteps />}

      {state.phase === 'error' && (
        <ErrorPanel error={state.error} onRetry={() => actions.retry(state.lastRequest)} onReset={actions.reset} />
      )}

      {state.result && state.phase !== 'submitting' && (
        <ResultView
          result={state.result}
          busy={busy}
          onChooseCandidate={(c) => actions.chooseCandidate(state.sessionId, c)}
          onFollowUp={(msg) => actions.askFollowUp(state.sessionId, msg)}
        />
      )}

      {state.history.length > 1 && (
        <details className={`card ${styles.history}`}>
          <summary>Session history ({state.history.length} messages)</summary>
          <ol>
            {state.history.map((m) => (
              <li key={m.at + m.role + m.text.slice(0, 10)}>
                <strong>{m.role}:</strong> {m.text}
              </li>
            ))}
          </ol>
        </details>
      )}
    </div>
  );
}
