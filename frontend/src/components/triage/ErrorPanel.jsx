import styles from './Triage.module.css';

const FRIENDLY = {
  NETWORK: 'The triage service is not reachable. Check that the backend is running, then retry.',
  TIMEOUT: 'The assistant took too long. Retrying usually works; if not, the LLM endpoint may be busy.',
  DEPENDENCY_UNAVAILABLE: 'One data source did not respond. Nothing was guessed. Retry, or continue later.',
  SESSION_NOT_FOUND: 'That session is no longer available. Start a new triage.',
  NO_SESSION: 'There is no previous session saved in this browser.',
};

export default function ErrorPanel({ error, onRetry, onReset }) {
  const retryable = error?.retryable !== false;
  return (
    <div className={`${styles.banner} ${styles.tone_critical}`} role="alert">
      <span className={styles.bannerIcon} aria-hidden="true">
        ✕
      </span>
      <div className={styles.errorBody}>
        <strong>{FRIENDLY[error?.code] ?? 'Something went wrong.'}</strong>
        <div className={styles.bannerMeta}>
          <span>{error?.message}</span>
          {error?.code && (
            <span>
              Code <code>{error.code}</code>
            </span>
          )}
        </div>
        <div className={styles.errorActions}>
          {retryable && (
            <button type="button" className="btn btn-primary" onClick={onRetry}>
              Retry
            </button>
          )}
          <button type="button" className="btn" onClick={onReset}>
            Start over
          </button>
        </div>
      </div>
    </div>
  );
}
