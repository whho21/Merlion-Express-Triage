import { useState } from 'react';
import styles from './Charts.module.css';

/**
 * Wraps every chart: title, subtitle, legend, and a "View as table" toggle.
 * The table view is the accessibility fallback (screen readers, colour-blind users, print).
 */
export default function ChartFrame({ title, subtitle, legend = [], table, children, actions }) {
  const [showTable, setShowTable] = useState(false);
  return (
    <section className={`card ${styles.frame}`} aria-label={title}>
      <header className={styles.frameHeader}>
        <div>
          <h3 className={styles.title}>{title}</h3>
          {subtitle && <p className={styles.subtitle}>{subtitle}</p>}
        </div>
        <div className={styles.frameActions}>
          {actions}
          {table && (
            <button
              type="button"
              className="btn btn-ghost"
              aria-pressed={showTable}
              onClick={() => setShowTable((v) => !v)}
            >
              {showTable ? 'View chart' : 'View as table'}
            </button>
          )}
        </div>
      </header>

      {legend.length > 1 && !showTable && (
        <ul className={styles.legend} aria-label="Legend">
          {legend.map((item) => (
            <li key={item.label}>
              <span
                className={`${styles.swatch} ${item.hatched ? styles.hatched : ''}`}
                style={{ background: item.hatched ? undefined : item.color }}
                aria-hidden="true"
              />
              {item.label}
            </li>
          ))}
        </ul>
      )}

      {showTable && table ? <DataTable {...table} /> : children}
    </section>
  );
}

function DataTable({ columns, rows, caption }) {
  return (
    <div className={styles.tableWrap}>
      <table className={styles.table}>
        {caption && <caption className="visually-hidden">{caption}</caption>}
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c} scope="col">
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i}>
              {r.map((cell, j) =>
                j === 0 ? (
                  <th key={j} scope="row">
                    {cell}
                  </th>
                ) : (
                  <td key={j}>{cell}</td>
                ),
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
