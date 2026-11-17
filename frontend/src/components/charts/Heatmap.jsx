import { useState } from 'react';
import styles from './Charts.module.css';

const STEPS = ['var(--surface-2)', '#cde2fb', '#9ec5f4', '#6da7ec', '#3987e5', '#256abf', '#104281'];

/** Zone × category heatmap, single blue sequential ramp. Cell values are printed so colour is never the only cue. */
export default function Heatmap({ rows, columns, rowKey = 'zone', ariaLabel }) {
  const [hover, setHover] = useState(null);
  const max = Math.max(1, ...rows.flatMap((r) => r.values));
  const step = (v) => (v === 0 ? 0 : Math.min(STEPS.length - 1, 1 + Math.floor((v / max) * (STEPS.length - 2))));

  return (
    <div className={styles.heatWrap} role="img" aria-label={ariaLabel}>
      <div className={styles.heatGrid} style={{ gridTemplateColumns: `86px repeat(${columns.length}, minmax(30px, 1fr))` }}>
        <span />
        {columns.map((c) => (
          <span key={c} className={styles.heatCol} title={c}>
            {c}
          </span>
        ))}
        {rows.map((r) => (
          <Row key={r[rowKey]} r={r} rowKey={rowKey} columns={columns} step={step} hover={hover} setHover={setHover} />
        ))}
      </div>
      <p className={styles.heatHint} aria-live="polite">
        {hover ? `${hover.row} · ${hover.col}: ${hover.value} complaint${hover.value === 1 ? '' : 's'}` : 'Hover a cell for details. Darker = more complaints.'}
      </p>
    </div>
  );
}

function Row({ r, rowKey, columns, step, hover, setHover }) {
  return (
    <>
      <span className={styles.heatRow}>{r[rowKey]}</span>
      {r.values.map((v, i) => {
        const s = step(v);
        const isHover = hover?.row === r[rowKey] && hover?.col === columns[i];
        return (
          <span
            key={columns[i]}
            className={`${styles.heatCell} ${isHover ? styles.heatCellHover : ''}`}
            style={{ background: STEPS[s], color: s >= 4 ? '#fff' : 'var(--text-primary)' }}
            onMouseEnter={() => setHover({ row: r[rowKey], col: columns[i], value: v })}
            onMouseLeave={() => setHover(null)}
          >
            {v || ''}
          </span>
        );
      })}
    </>
  );
}
