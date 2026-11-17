import { useState } from 'react';
import styles from './Charts.module.css';

/**
 * Stacked columns over time (part-to-whole per week). Segments keep a fixed
 * entity order and colour; Unknown is hatched. 2px surface gap between segments.
 * Hover = per-column tooltip; click = select that week.
 * columns: [{ key, label, values: { [seriesKey]: number } }]
 * series:  [{ key, label, color, hatched? }]
 */
export default function StackedColumns({ columns, series, selectedKey, onSelect, height = 260, ariaLabel, formatLabel = (l) => l }) {
  const [hover, setHover] = useState(null);
  const width = 720;
  const pad = { top: 14, right: 8, bottom: 30, left: 34 };
  const innerW = width - pad.left - pad.right;
  const innerH = height - pad.top - pad.bottom;
  const totals = columns.map((c) => series.reduce((s, se) => s + (c.values[se.key] ?? 0), 0));
  const niceMax = Math.max(5, Math.ceil(Math.max(...totals, 1) / 5) * 5);
  const slot = innerW / columns.length;
  const barW = Math.min(36, slot * 0.62);
  const y = (v) => (v / niceMax) * innerH;
  const ticks = [0, niceMax / 2, niceMax];

  const hovered = hover != null ? columns[hover] : null;

  return (
    <div className={styles.chartWrap}>
      <svg viewBox={`0 0 ${width} ${height}`} className={styles.svg} role="img" aria-label={ariaLabel} onMouseLeave={() => setHover(null)}>
        <defs>
          <pattern id="hatch-unknown" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
            <rect width="6" height="6" fill="var(--surface-2)" />
            <rect width="2" height="6" fill="var(--series-unknown)" />
          </pattern>
        </defs>
        {ticks.map((t) => (
          <g key={t}>
            <line x1={pad.left} x2={width - pad.right} y1={pad.top + innerH - y(t)} y2={pad.top + innerH - y(t)} className={styles.grid} />
            <text x={pad.left - 8} y={pad.top + innerH - y(t)} className={styles.axisText} textAnchor="end" dominantBaseline="middle">
              {t}
            </text>
          </g>
        ))}
        {columns.map((c, i) => {
          const cx = pad.left + slot * i + slot / 2;
          const isSel = c.key === selectedKey;
          const segs = series.map((se, j) => {
            const below = series.slice(0, j).reduce((s, prev) => s + (c.values[prev.key] ?? 0), 0);
            return { se, v: c.values[se.key] ?? 0, below };
          });
          return (
            <g
              key={c.key}
              onMouseEnter={() => setHover(i)}
              onClick={() => onSelect?.(c.key)}
              style={{ cursor: onSelect ? 'pointer' : undefined }}
            >
              <rect x={pad.left + slot * i} y={pad.top} width={slot} height={innerH} fill={isSel ? 'var(--brand-100)' : hover === i ? 'var(--surface-2)' : 'transparent'} />
              {segs.map(({ se, v, below }) =>
                v > 0 ? (
                  <rect
                    key={se.key}
                    x={cx - barW / 2}
                    y={pad.top + innerH - y(below + v)}
                    width={barW}
                    height={Math.max(0, y(v) - 2)}
                    rx={2}
                    fill={se.hatched ? 'url(#hatch-unknown)' : se.color}
                  />
                ) : null,
              )}
              <text x={cx} y={pad.top + innerH - y(totals[i]) - 6} textAnchor="middle" className={isSel ? styles.axisTextStrong : styles.axisText}>
                {totals[i]}
              </text>
              <text x={cx} y={height - 10} textAnchor="middle" className={isSel ? styles.axisTextStrong : styles.axisText}>
                {formatLabel(c.label)}
              </text>
            </g>
          );
        })}
      </svg>
      {hovered && (
        <div
          className={styles.tooltip}
          style={{
            left: `${((pad.left + slot * hover + slot / 2) / width) * 100}%`,
            transform: hover > columns.length / 2 ? 'translateX(-105%)' : 'translateX(12px)',
          }}
          role="status"
        >
          <strong>Week of {formatLabel(hovered.label)}</strong>
          {[...series].reverse().map((se) => (
            <div key={se.key} className={styles.tooltipRow}>
              <span className={`${styles.swatch} ${se.hatched ? styles.hatched : ''}`} style={{ background: se.hatched ? undefined : se.color }} aria-hidden="true" />
              <span>{se.label}</span>
              <span className={styles.tooltipValue}>{hovered.values[se.key] ?? 0}</span>
            </div>
          ))}
          <div className={styles.tooltipRow}>
            <span />
            <span>Total</span>
            <span className={styles.tooltipValue}>{totals[hover]}</span>
          </div>
          {onSelect && <div className={styles.muted}>Click to open this week</div>}
        </div>
      )}
    </div>
  );
}
