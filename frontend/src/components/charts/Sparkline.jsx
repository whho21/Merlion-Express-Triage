/** Tiny trend line for KPI tiles. Decorative: the tile states the number in text. */
export default function Sparkline({ values, color = 'var(--brand-500)', width = 96, height = 28 }) {
  if (!values?.length) return null;
  const max = Math.max(1, ...values);
  const min = Math.min(...values);
  const span = Math.max(1, max - min);
  const pts = values
    .map((v, i) => `${((i / Math.max(1, values.length - 1)) * (width - 4) + 2).toFixed(1)},${(height - 3 - ((v - min) / span) * (height - 6)).toFixed(1)}`)
    .join(' ');
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} aria-hidden="true">
      <polyline points={pts} fill="none" stroke={color} strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  );
}
