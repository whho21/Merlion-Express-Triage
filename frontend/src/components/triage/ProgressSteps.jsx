import styles from './Triage.module.css';

const STEPS = [
  'Reading the email',
  'Identifying the order (v1 / v2)',
  'Delivery record & POD',
  'GPS trail near delivery time',
  'Rate card & Resolution Guide',
  'Checking citations',
];

/**
 * Loading state. While the backend has no streaming, this is an honest "what the assistant
 * checks" list, not fake progress: no step is ticked before the answer arrives.
 */
export default function ProgressSteps() {
  return (
    <div className={`card ${styles.progressCard}`} role="status" aria-live="polite">
      <div className={styles.spinner} aria-hidden="true" />
      <div>
        <strong>Triaging… usually 5–20 seconds</strong>
        <ol className={styles.stepList}>
          {STEPS.map((s) => (
            <li key={s}>{s}</li>
          ))}
        </ol>
      </div>
    </div>
  );
}
