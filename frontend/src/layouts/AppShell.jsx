import { isMock } from '../api/client.js';
import styles from './AppShell.module.css';

const NAV = [
  { path: '/triage', label: 'Complaint triage', icon: '✉' },
  { path: '/weekly', label: 'Weekly insights', icon: '▤' },
  { path: '/how-it-works', label: 'How it works', icon: 'ⓘ' },
];

export default function AppShell({ current, children }) {
  return (
    <div className={styles.shell}>
      <aside className={styles.sidebar}>
        <div className={styles.brand}>
          <span className={styles.logo} aria-hidden="true">
            ME
          </span>
          <div>
            <strong>Merlion Express</strong>
            <span>CS Triage Assistant</span>
          </div>
        </div>
        <nav aria-label="Main">
          <ul className={styles.nav}>
            {NAV.map((n) => (
              <li key={n.path}>
                <a href={`#${n.path}`} className={`${styles.navLink} ${current === n.path ? styles.active : ''}`} aria-current={current === n.path ? 'page' : undefined}>
                  <span aria-hidden="true" className={styles.navIcon}>
                    {n.icon}
                  </span>
                  {n.label}
                </a>
              </li>
            ))}
          </ul>
        </nav>
        <div className={styles.sideFoot}>
          <span className={`${styles.envBadge} ${isMock ? styles.envMock : styles.envLive}`}>{isMock ? 'MOCK · synthetic data' : 'LIVE API'}</span>
          <span>Recommendation-only</span>
          <span>Team 2 · AIE1-FT capstone</span>
        </div>
      </aside>
      <main className={styles.main}>{children}</main>
    </div>
  );
}
