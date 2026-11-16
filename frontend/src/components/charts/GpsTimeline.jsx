import styles from './Charts.module.css';

/**
 * Distance of the driver's GPS pings from the delivery address over time,
 * with the recorded delivery time marked. Visualises the "GPS vs delivery time" check.
 * points: [{ t: 'HH:MM' (SGT), dist: metres }]
 */
export default function GpsTimeline({ points, deliveredAt }) {
  const width = 440;
  const height = 120;
  const pad = { top: 10, right: 12, bottom: 22, left: 40 };
  const innerW = width - pad.left - pad.right;
  const innerH = height - pad.top - pad.bottom;
  const max = Math.max(200, ...points.map((p) => p.dist));
  const x = (i) => pad.left + (i / Math.max(1, points.length - 1)) * innerW;
  const y = (d) => pad.top + (d / max) * innerH; // closer = higher
  const deliveredIndex = points.findIndex((p) => p.t >= deliveredAt);
  const near = 200;

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className={styles.svg}
      role="img"
      aria-label={`Driver distance from address over time. Delivery recorded at ${deliveredAt} SGT. Closest ping ${Math.min(...points.map((p) => p.dist))} metres.`}
    >
      <rect x={pad.left} y={pad.top} width={innerW} height={y(near) - pad.top} className={styles.nearBand} />
      <text x={pad.left + 4} y={pad.top + 11} className={styles.axisText}>
        within {near} m
      </text>
      <line x1={pad.left} x2={width - pad.right} y1={y(0)} y2={y(0)} className={styles.grid} />
      <text x={pad.left - 6} y={y(0)} className={styles.axisText} textAnchor="end" dominantBaseline="middle">
        0 m
      </text>
      <text x={pad.left - 6} y={y(max)} className={styles.axisText} textAnchor="end" dominantBaseline="middle">
        {max >= 1000 ? `${(max / 1000).toFixed(1)}k` : max} m
      </text>
      <polyline
        points={points.map((p, i) => `${x(i)},${y(p.dist)}`).join(' ')}
        fill="none"
        stroke="var(--series-1)"
        strokeWidth="2"
        strokeLinejoin="round"
      />
      {points.map((p, i) => (
        <circle key={p.t} cx={x(i)} cy={y(p.dist)} r="4" fill="var(--series-1)" stroke="var(--surface-1)" strokeWidth="2">
          <title>{`${p.t} SGT — ${p.dist} m from address`}</title>
        </circle>
      ))}
      {deliveredIndex >= 0 && (
        <g>
          <line
            x1={x(deliveredIndex) - innerW / (points.length - 1) / 2}
            x2={x(deliveredIndex) - innerW / (points.length - 1) / 2}
            y1={pad.top}
            y2={pad.top + innerH}
            className={styles.deliveredLine}
          />
          <text
            x={x(deliveredIndex) - innerW / (points.length - 1) / 2 + 4}
            y={pad.top + 11}
            className={styles.axisTextStrong}
          >
            delivered {deliveredAt}
          </text>
        </g>
      )}
      <text x={pad.left} y={height - 6} className={styles.axisText}>
        {points[0].t}
      </text>
      <text x={width - pad.right} y={height - 6} className={styles.axisText} textAnchor="end">
        {points[points.length - 1].t} SGT
      </text>
    </svg>
  );
}
