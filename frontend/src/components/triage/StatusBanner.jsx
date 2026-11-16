import styles from './Triage.module.css';

// Status is always icon + words, never colour alone.
const STATUS = {
  found: { icon: '✓', title: 'Order identified — evidence gathered', tone: 'good' },
  partial: { icon: '!', title: 'Partly answered — sources disagree or are incomplete', tone: 'warning' },
  ambiguous: { icon: '?', title: 'Needs your confirmation', tone: 'info' },
  not_found: { icon: '∅', title: 'Not on file', tone: 'neutral' },
  refused: { icon: '⛔', title: 'Request refused by guardrail', tone: 'critical' },
  failed: { icon: '✕', title: 'Could not complete', tone: 'critical' },
};

export default function StatusBanner({ result }) {
  const s = STATUS[result.status] ?? STATUS.failed;
  return (
    <div className={`${styles.banner} ${styles[`tone_${s.tone}`]}`} role="status">
      <span className={styles.bannerIcon} aria-hidden="true">
        {s.icon}
      </span>
      <div>
        <strong>{s.title}</strong>
        <div className={styles.bannerMeta}>
          {result.complaint?.category && <span>Category: {result.complaint.category}</span>}
          {result.order && (
            <span>
              Order <code>{result.order.system_version.toUpperCase()}-{result.order.order_id}</code>
            </span>
          )}
          <span>
            Session <code>{result.session_id}</code>
          </span>
          {result.recovered && <span className={styles.recoveredTag}>recovered after restart</span>}
        </div>
      </div>
    </div>
  );
}
