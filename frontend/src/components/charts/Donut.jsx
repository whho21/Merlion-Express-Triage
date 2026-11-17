import { useState } from 'react';
import styles from './Charts.module.css';

/** Donut for a part-to-whole mix (≤ 5 slices). Direct legend with values beside it. */
export default function Donut({ slices, centerLabel, ariaLabel }) {
  const [hover, setHover] = useState(null);
  const total = slices.reduce((s, x) => s + x.value, 0) || 1;
  const r = 52;
  const c = 2 * Math.PI * r;
  const gap = 2; // 2px surface gap between segments
  const offsets = slices.map((_, i) => slices.slice(0, i).reduce((sum, x) => sum + (x.value / total) * c, 0));

  return (
    <div className={styles.donutWrap}>
      <svg viewBox="0 0 140 140" className={styles.donut} role="img" aria-label={ariaLabel}>
        <circle cx="70" cy="70" r={r} fill="none" stroke="var(--surface-2)" strokeWidth="18" />
        {slices.map((s, i) => {
          const len = (s.value / total) * c;
          return (
            <circle
              key={s.label}
              cx="70"
              cy="70"
              r={r}
              fill="none"
              stroke={s.color}
              strokeWidth={hover === s.label ? 22 : 18}
              strokeDasharray={`${Math.max(0, len - gap)} ${c}`}
              strokeDashoffset={-offsets[i]}
              transform="rotate(-90 70 70)"
              onMouseEnter={() => setHover(s.label)}
              onMouseLeave={() => setHover(null)}
            />
          );
        })}
        <text x="70" y="66" textAnchor="middle" className={styles.donutValue}>
          {hover ? slices.find((s) => s.label === hover)?.value : total}
        </text>
        <text x="70" y="84" textAnchor="middle" className={styles.donutLabel}>
          {hover ?? centerLabel}
        </text>
      </svg>
      <ul className={styles.donutLegend}>
        {slices.map((s) => (
          <li key={s.label} onMouseEnter={() => setHover(s.label)} onMouseLeave={() => setHover(null)}>
            <span className={styles.swatch} style={{ background: s.color }} aria-hidden="true" />
            <span>{s.label}</span>
            <span className={styles.tooltipValue}>
              {s.value} <span className={styles.muted}>({Math.round((s.value / total) * 100)}%)</span>
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
