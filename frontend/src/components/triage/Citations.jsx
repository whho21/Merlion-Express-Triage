import styles from './Triage.module.css';

const TYPE_LABEL = {
  sql: 'Table',
  tabular: 'Spreadsheet',
  image: 'Image',
  document: 'Email / document',
  log: 'GPS log',
};

/** Inline footnote marker, e.g. [3]. Links to the source list so keyboard and screen-reader users can follow it. */
export function CitationRefs({ ids }) {
  if (!ids?.length) return null;
  return (
    <span className={styles.refs}>
      {ids.map((n) => (
        <a key={n} href={`#cite-${n}`} className={styles.ref} aria-label={`Source ${n}`}>
          {n}
        </a>
      ))}
    </span>
  );
}

/** Numbered source list: every fact on screen traces back to a table, file or image. */
export function CitationList({ citations }) {
  if (!citations?.length) {
    return <p className={styles.mutedText}>No sources were used for this answer.</p>;
  }
  return (
    <ol className={styles.citeList}>
      {citations.map((c) => (
        <li key={c.n} id={`cite-${c.n}`} className={styles.citeItem} tabIndex={-1}>
          <span className={styles.citeNum}>{c.n}</span>
          <div>
            <div className={styles.citeTitle}>
              {c.label ?? c.source_id}
              <span className={styles.typeChip}>{TYPE_LABEL[c.type] ?? c.type}</span>
            </div>
            <div className={styles.citeMeta}>
              <code>{c.ref}</code>
              {c.locator && (
                <>
                  {' · '}
                  <code>{c.locator}</code>
                </>
              )}
              {c.record_key && (
                <>
                  {' · '}
                  <code>
                    {c.record_key.system_version}/{c.record_key.order_id}
                  </code>
                </>
              )}
            </div>
          </div>
        </li>
      ))}
    </ol>
  );
}
