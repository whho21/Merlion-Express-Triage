import styles from './Pages.module.css';

// Client-facing explainer used in the pitch: what the assistant checks, what it refuses, and its known data limits.
const PIPELINE = [
  { title: 'Customer email', text: 'Parsed for order number, claim and complaint type. Personal data masked.', src: '90 complaint emails' },
  { title: 'Identify the order', text: 'Order numbers repeat across v1 and v2. If both match, the assistant asks instead of guessing.', src: 'orders (SQL)' },
  { title: 'Gather evidence', text: 'Delivery record, POD scan, GPS pings near delivery time, rate card.', src: 'SQL · 80 POD scans · 60k GPS pings · rate card' },
  { title: 'Apply the guide', text: 'Resolution Guide v2 decides the action and who must approve it.', src: 'Resolution Guide v2' },
  { title: 'Cite & check', text: 'Every fact links to its table, file or image. Unsupported claims are removed.', src: 'all sources' },
];

const LIMITS = [
  ['POD after 1 Feb 2026', 'Not on file (vendor app). The assistant says so; it does not imply a check.'],
  ['Delivery attempts', 'Only the latest attempt is kept. Third-attempt charges are passed to CS to confirm with the driver.'],
  ['GPS time', 'Vendor GPS is UTC; ops shows Singapore time (+8 h). Converted before comparing.'],
  ['Rate card', 'April 2026 card applied to all orders, per client. Weight-band upper limits are inclusive.'],
  ['Public holidays', 'Singapore PH calendar; no standard delivery on a PH.'],
  ['Case log', 'Hand-typed by five people: duplicate rows merged, zone re-derived from the address.'],
];

const GUARDRAILS = [
  'Recommends only — never refunds, messages customers or edits orders.',
  'Refunds above S$50 and 3+ complaints a month on a corporate account go to the Head of CX.',
  'Does not use NRIC to verify identity (PDPA). Masks phone, email, NRIC and unit numbers.',
  'Refuses instructions to ignore its rules; says “not on file” instead of guessing.',
];

export default function HowItWorksPage() {
  return (
    <div className={styles.page}>
      <header className={styles.pageHeader}>
        <div>
          <h1 className={styles.h1}>How the assistant works</h1>
          <p className={styles.lede}>Five checks per complaint, answered only from Merlion Express data, with every fact cited.</p>
        </div>
      </header>

      <ol className={styles.pipeline}>
        {PIPELINE.map((p, i) => (
          <li key={p.title} className={`card ${styles.pipeStep}`}>
            <span className={styles.pipeNum}>{i + 1}</span>
            <strong>{p.title}</strong>
            <p>{p.text}</p>
            <span className={styles.pipeSrc}>{p.src}</span>
          </li>
        ))}
      </ol>

      <div className={styles.twoCol}>
        <section className={`card ${styles.defs}`}>
          <h3 className={styles.h3}>Guardrails</h3>
          <ul className={styles.limitList}>
            {GUARDRAILS.map((g) => (
              <li key={g}>{g}</li>
            ))}
          </ul>
        </section>
        <section className={`card ${styles.defs}`}>
          <h3 className={styles.h3}>What the data cannot tell us</h3>
          <dl>
            {LIMITS.map(([k, v]) => (
              <div key={k} className={styles.defRow}>
                <dt>{k}</dt>
                <dd>{v}</dd>
              </div>
            ))}
          </dl>
          <p className={styles.mockNote}>Client answers of 16 Nov 2026 (Q01–Q08). Final wording to be checked by A/B/C against the implemented rules.</p>
        </section>
      </div>
    </div>
  );
}
