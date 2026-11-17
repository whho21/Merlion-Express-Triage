import { useState } from 'react';
import styles from './Charts.module.css';

/**
 * Horizontal ranked bar list (HTML, not SVG, so labels never collide and it
 * stays readable on a projector). Items flagged `unknown` are hatched grey —
 * unknown attribution is shown, never dropped.
 * items: [{ label, value, color?, unknown?, sub? }]
 */
export default function BarList({ items, color = 'var(--series-1)', valueFormat = (v) => v, maxItems, onSelect, selected }) {
  const [hover, setHover] = useState(null);
  const shown = maxItems ? items.slice(0, maxItems) : items;
  const max = Math.max(1, ...shown.map((i) => i.value));
  return (
    <ul className={styles.barList}>
      {shown.map((item) => {
        const isSelected = selected === item.label;
        const content = (
          <>
            <span className={styles.barLabel}>
              {item.label}
              {item.sub && <span className={styles.barSub}>{item.sub}</span>}
            </span>
            <span className={styles.barTrack} aria-hidden="true">
              <span
                className={`${styles.barFill} ${item.unknown ? styles.hatched : ''}`}
                style={{
                  width: `${(item.value / max) * 100}%`,
                  background: item.unknown ? undefined : item.color ?? color,
                }}
              />
            </span>
            <span className={styles.barValue}>{valueFormat(item.value)}</span>
          </>
        );
        return (
          <li
            key={item.label}
            className={`${styles.barRow} ${hover === item.label ? styles.barRowHover : ''} ${isSelected ? styles.barRowSelected : ''}`}
            onMouseEnter={() => setHover(item.label)}
            onMouseLeave={() => setHover(null)}
          >
            {onSelect ? (
              <button
                type="button"
                className={styles.barButton}
                aria-pressed={isSelected}
                onClick={() => onSelect(isSelected ? null : item.label)}
              >
                {content}
              </button>
            ) : (
              <div className={styles.barButton}>{content}</div>
            )}
          </li>
        );
      })}
    </ul>
  );
}
