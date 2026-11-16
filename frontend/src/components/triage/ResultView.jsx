import { useState } from 'react';
import { CitationList, CitationRefs } from './Citations.jsx';
import StatusBanner from './StatusBanner.jsx';
import GpsTimeline from '../charts/GpsTimeline.jsx';
import styles from './Triage.module.css';

const EVIDENCE_ICON = { found: '✓', partial: '!', not_found: '∅', failed: '✕', ambiguous: '?' };
const EVIDENCE_TEXT = { found: 'Found', partial: 'Partial', not_found: 'Not on file', failed: 'Failed', ambiguous: 'Ambiguous' };

export default function ResultView({ result, onChooseCandidate, onFollowUp, busy }) {
  return (
    <div className={styles.result}>
      <StatusBanner result={result} />

      {result.follow_up_answer && (
        <div className={`card ${styles.answerCard}`}>
          <span className={styles.kicker}>Follow-up answer</span>
          <p>{result.follow_up_answer}</p>
        </div>
      )}

      <div className={styles.resultGrid}>
        <div className={styles.mainCol}>
          {result.status === 'ambiguous' && result.candidates?.length > 0 && (
            <CandidatePicker result={result} onChoose={onChooseCandidate} busy={busy} />
          )}

          {result.recommendation && <RecommendationCard rec={result.recommendation} />}

          {result.abstention && !result.recommendation && (
            <div className={`card ${styles.abstainCard}`}>
              <span className={styles.kicker}>{result.status === 'refused' ? 'Why this was refused' : 'No recommendation'}</span>
              <p>{result.abstention.reason}</p>
              {result.guardrail?.pii_masked?.length > 0 && (
                <p className={styles.mutedText}>Masked: {result.guardrail.pii_masked.join(', ')}</p>
              )}
            </div>
          )}

          {result.conflicts?.length > 0 && <Conflicts conflicts={result.conflicts} />}

          {result.evidence?.length > 0 && (
            <section aria-label="Evidence">
              <h3 className={styles.h3}>Evidence</h3>
              <div className={styles.evidenceGrid}>
                {result.evidence.map((ev) => (
                  <EvidenceCard key={ev.key} ev={ev} />
                ))}
              </div>
            </section>
          )}

          {result.limitations?.length > 0 && (
            <div className={styles.limitations}>
              <strong>Limitations</strong>
              <ul>
                {result.limitations.map((l) => (
                  <li key={l}>{l}</li>
                ))}
              </ul>
            </div>
          )}

          {result.session_id && ['found', 'partial'].includes(result.status) && <FollowUpBox onAsk={onFollowUp} busy={busy} />}
        </div>

        <aside className={styles.sideCol}>
          {result.order && <OrderCard order={result.order} />}
          {result.complaint?.claims?.length > 0 && (
            <div className={`card ${styles.sideCard}`}>
              <h3 className={styles.h3}>
                What the customer claims <CitationRefs ids={result.complaint.citations} />
              </h3>
              <ul className={styles.claims}>
                {result.complaint.claims.map((c) => (
                  <li key={c}>{c}</li>
                ))}
              </ul>
            </div>
          )}
          <div className={`card ${styles.sideCard}`}>
            <h3 className={styles.h3}>Sources</h3>
            <CitationList citations={result.citations} />
          </div>
        </aside>
      </div>
    </div>
  );
}

function RecommendationCard({ rec }) {
  return (
    <div className={`card ${styles.recCard}`}>
      <div className={styles.recTop}>
        <span className={styles.kicker}>Recommended resolution · for CS to action</span>
        {rec.approval_required ? (
          <span className={`${styles.pill} ${styles.pillWarn}`}>
            <span aria-hidden="true">⚠</span> Needs approval: {rec.approver}
          </span>
        ) : (
          <span className={`${styles.pill} ${styles.pillGood}`}>
            <span aria-hidden="true">✓</span> Agent can action
          </span>
        )}
      </div>
      <div className={styles.recAction}>
        <span className={styles.recVerb}>{rec.action}</span>
        {rec.amount_sgd != null && rec.amount_sgd > 0 && <span className={styles.recAmount}>S${rec.amount_sgd.toFixed(2)}</span>}
      </div>
      <p className={styles.recSummary}>{rec.summary}</p>
      <p className={styles.recWhy}>
        <strong>Why: </strong>
        {rec.rationale} <CitationRefs ids={rec.citations} />
      </p>
      <p className={styles.recFoot}>Recommendation only. The assistant does not refund, message customers or change orders.</p>
    </div>
  );
}

function CandidatePicker({ result, onChoose, busy }) {
  return (
    <div className={`card ${styles.clarifyCard}`}>
      <span className={styles.kicker}>Clarification needed</span>
      <p className={styles.clarifyQ}>{result.clarification?.question}</p>
      {result.clarification?.hint && <p className={styles.mutedText}>{result.clarification.hint}</p>}
      <div className={styles.candidates}>
        {result.candidates.map((c) => (
          <div key={`${c.system_version}-${c.order_id}`} className={styles.candidate}>
            <div className={styles.candidateHead}>
              <code className={styles.sysTag}>{c.system_version.toUpperCase()}</code>
              <strong>Order {c.order_id}</strong>
              <CitationRefs ids={c.citations} />
            </div>
            <dl className={styles.facts}>
              <dt>Created</dt>
              <dd>{c.created}</dd>
              <dt>Status</dt>
              <dd>{c.status}</dd>
              <dt>Zone</dt>
              <dd>{c.zone}</dd>
              <dt>Postal</dt>
              <dd>{c.postal_code}</dd>
            </dl>
            <p className={styles.mutedText}>{c.evidence_for}</p>
            <button type="button" className="btn" disabled={busy} onClick={() => onChoose(c)}>
              It is this {c.system_version.toUpperCase()} order
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

function Conflicts({ conflicts }) {
  return (
    <section className={`card ${styles.conflictCard}`} aria-label="Conflicting sources">
      <span className={styles.kicker}>
        <span aria-hidden="true">⚠</span> Sources disagree — shown side by side, not resolved silently
      </span>
      {conflicts.map((c) => (
        <div key={c.field} className={styles.conflict}>
          <strong>{c.field}</strong>
          <div className={styles.conflictValues}>
            {c.values.map((v) => (
              <div key={v.source} className={styles.conflictValue}>
                <span className={styles.conflictBig}>{v.value}</span>
                <span className={styles.mutedText}>
                  {v.source} <CitationRefs ids={[v.citation]} />
                </span>
              </div>
            ))}
          </div>
          <p className={styles.mutedText}>{c.note}</p>
        </div>
      ))}
    </section>
  );
}

function EvidenceCard({ ev }) {
  const [open, setOpen] = useState(ev.status !== 'not_found');
  return (
    <div className={`card ${styles.evCard} ${styles[`ev_${ev.status}`] ?? ''}`}>
      <button type="button" className={styles.evHead} aria-expanded={open} onClick={() => setOpen((o) => !o)}>
        <span className={styles.evIcon} aria-hidden="true">
          {EVIDENCE_ICON[ev.status] ?? '•'}
        </span>
        <span className={styles.evTitle}>{ev.title}</span>
        <span className={styles.evStatus}>{EVIDENCE_TEXT[ev.status] ?? ev.status}</span>
      </button>
      <p className={styles.evSummary}>
        {ev.summary} <CitationRefs ids={ev.citations} />
      </p>
      {open && (
        <>
          {ev.facts?.length > 0 && (
            <dl className={styles.facts}>
              {ev.facts.map(([k, v]) => (
                <div key={k} className={styles.factRow}>
                  <dt>{k}</dt>
                  <dd>{v}</dd>
                </div>
              ))}
            </dl>
          )}
          {ev.gps && <GpsTimeline points={ev.gps} deliveredAt={ev.deliveredAt} />}
          {ev.note && <p className={styles.mutedText}>{ev.note}</p>}
        </>
      )}
    </div>
  );
}

function OrderCard({ order }) {
  return (
    <div className={`card ${styles.sideCard}`}>
      <h3 className={styles.h3}>
        Order <CitationRefs ids={order.citations} />
      </h3>
      <dl className={styles.facts}>
        <div className={styles.factRow}>
          <dt>System</dt>
          <dd>
            <code className={styles.sysTag}>{order.system_version.toUpperCase()}</code>
          </dd>
        </div>
        <div className={styles.factRow}>
          <dt>Order no.</dt>
          <dd>{order.order_id}</dd>
        </div>
        <div className={styles.factRow}>
          <dt>Customer</dt>
          <dd>{order.customer}</dd>
        </div>
        <div className={styles.factRow}>
          <dt>Postal code</dt>
          <dd>{order.postal_code}</dd>
        </div>
        <div className={styles.factRow}>
          <dt>Ops zone</dt>
          <dd>{order.zone}</dd>
        </div>
        <div className={styles.factRow}>
          <dt>Driver</dt>
          <dd>{order.driver_code}</dd>
        </div>
        <div className={styles.factRow}>
          <dt>Promised</dt>
          <dd>{order.promised_date}</dd>
        </div>
      </dl>
    </div>
  );
}

function FollowUpBox({ onAsk, busy }) {
  const [text, setText] = useState('');
  const suggestions = ['Was the POD checked?', 'What time was the GPS ping?', 'Who needs to approve this?'];
  function submit(e) {
    e.preventDefault();
    if (!text.trim()) return;
    onAsk(text.trim());
    setText('');
  }
  return (
    <form className={`card ${styles.followCard}`} onSubmit={submit}>
      <label htmlFor="follow-up" className={styles.kicker}>
        Ask a follow-up (same session)
      </label>
      <div className={styles.followRow}>
        <input id="follow-up" value={text} onChange={(e) => setText(e.target.value)} placeholder="e.g. Was the POD checked?" disabled={busy} />
        <button type="submit" className="btn btn-primary" disabled={busy || !text.trim()}>
          Ask
        </button>
      </div>
      <div className={styles.chips}>
        {suggestions.map((s) => (
          <button key={s} type="button" className={styles.chip} disabled={busy} onClick={() => onAsk(s)}>
            {s}
          </button>
        ))}
      </div>
    </form>
  );
}
