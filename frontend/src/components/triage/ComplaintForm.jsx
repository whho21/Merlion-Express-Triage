import { useState } from 'react';
import { SAMPLE_EMAILS } from '../../fixtures/complaints.js';
import styles from './Triage.module.css';

const MIN_LENGTH = 20;
const MAX_LENGTH = 8000;

// Lesson 2.11: validate on submit and on blur; field-level error message.
// (Yup is the class library; plain checks are used here to avoid a new dependency for two rules.)
function validate(text) {
  const t = text.trim();
  if (!t) return 'Paste the customer email first.';
  if (t.length < MIN_LENGTH) return `That looks too short to triage (at least ${MIN_LENGTH} characters).`;
  if (t.length > MAX_LENGTH) return `Please paste one email at a time (max ${MAX_LENGTH} characters).`;
  return null;
}

export default function ComplaintForm({ value, onChange, onSubmit, submitting, isMock }) {
  const [error, setError] = useState(null);
  const [touched, setTouched] = useState(false);
  const [scenario, setScenario] = useState('');

  function handleSubmit(e) {
    e.preventDefault();
    const err = validate(value);
    setError(err);
    setTouched(true);
    if (!err) onSubmit({ emailText: value, simulateFailure: scenario === 'error' });
  }

  function loadSample(id) {
    setScenario(id);
    const sample = SAMPLE_EMAILS.find((s) => s.id === id);
    if (sample) {
      onChange(sample.text);
      setError(null);
    }
  }

  return (
    <form className={`card ${styles.formCard}`} onSubmit={handleSubmit} noValidate>
      <div className={styles.formHeader}>
        <div>
          <h2 className={styles.h2}>Triage a complaint</h2>
          <p className={styles.mutedText}>Paste one customer email. The assistant identifies the order, gathers evidence and recommends a resolution under the Resolution Guide.</p>
        </div>
        {isMock && (
          <label className={styles.sampleLabel}>
            <span>Demo scenario</span>
            <select value={scenario} onChange={(e) => loadSample(e.target.value)}>
              <option value="">Choose a synthetic email…</option>
              {SAMPLE_EMAILS.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.label}
                </option>
              ))}
            </select>
          </label>
        )}
      </div>

      <label htmlFor="email-text" className="visually-hidden">
        Customer email
      </label>
      <textarea
        id="email-text"
        className={`${styles.textarea} ${touched && error ? styles.textareaError : ''}`}
        rows={8}
        value={value}
        placeholder={'Subject: …\n\nPaste the full customer email here.'}
        onChange={(e) => {
          onChange(e.target.value);
          if (touched) setError(validate(e.target.value));
        }}
        onBlur={() => {
          setTouched(true);
          setError(validate(value));
        }}
        aria-invalid={Boolean(touched && error)}
        aria-describedby="email-help email-error"
        disabled={submitting}
      />
      <div className={styles.formFooter}>
        <p id="email-help" className={styles.helpText}>
          Personal data (phone, email, NRIC, unit no.) is masked before it is shown or stored. The assistant only recommends; it never pays or messages customers.
        </p>
        <button type="submit" className="btn btn-primary" disabled={submitting}>
          {submitting ? 'Triaging…' : 'Triage complaint'}
        </button>
      </div>
      {touched && error && (
        <p id="email-error" className={styles.fieldError} role="alert">
          {error}
        </p>
      )}
    </form>
  );
}
