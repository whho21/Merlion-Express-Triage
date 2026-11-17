import { useEffect, useMemo, useState } from 'react';
import { getWeekly, getWeeks, isMock } from '../api/client.js';
import ChartFrame from '../components/charts/ChartFrame.jsx';
import StackedColumns from '../components/charts/StackedColumns.jsx';
import BarList from '../components/charts/BarList.jsx';
import Heatmap from '../components/charts/Heatmap.jsx';
import Donut from '../components/charts/Donut.jsx';
import Sparkline from '../components/charts/Sparkline.jsx';
import { CitationList } from '../components/triage/Citations.jsx';
import styles from './Pages.module.css';

// Colour follows the entity (zone), never its rank. Unknown is hatched grey.
const ZONE_COLOR = {
  North: 'var(--series-1)',
  'North-East': 'var(--series-2)',
  East: 'var(--series-3)',
  Central: 'var(--series-4)',
  West: 'var(--series-5)',
  Unknown: 'var(--series-unknown)',
};
const RESOLUTION_COLOR = {
  Refund: 'var(--series-1)',
  'Re-deliver': 'var(--series-2)',
  Reject: 'var(--series-3)',
  'Apology only': 'var(--series-4)',
  Compensate: 'var(--series-5)',
};

const fmtWeek = (w) =>
  new Date(`${w}T00:00:00Z`).toLocaleDateString('en-SG', { day: 'numeric', month: 'short', timeZone: 'UTC' });
const fmtWeekLong = (w) =>
  new Date(`${w}T00:00:00Z`).toLocaleDateString('en-SG', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' });
const sgd = (n) => `S$${n.toLocaleString('en-SG', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

export default function WeeklyPage() {
  const [weeks, setWeeks] = useState([]);
  const [week, setWeek] = useState(null);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [zoneFilter, setZoneFilter] = useState(null);
  const [showUnknown, setShowUnknown] = useState(true);

  // Lesson 2.5: fetch on mount; loading starts true; state is only set after the await.
  useEffect(() => {
    let ignore = false;
    (async () => {
      try {
        const res = await getWeeks();
        if (ignore) return;
        const latest = res.weeks[res.weeks.length - 1];
        const first = await getWeekly(latest);
        if (ignore) return;
        setWeeks(res.weeks);
        setWeek(latest);
        setData(first);
      } catch (err) {
        if (!ignore) setError(err);
      } finally {
        if (!ignore) setLoading(false);
      }
    })();
    return () => {
      ignore = true;
    };
  }, []);

  async function loadWeek(w) {
    setWeek(w);
    setLoading(true);
    setError(null);
    try {
      setData(await getWeekly(w));
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }

  const step = (delta) => {
    const i = weeks.indexOf(week) + delta;
    if (i >= 0 && i < weeks.length) loadWeek(weeks[i]);
  };

  // Derived values (Lesson 2.3: derive, don't store a second copy in state).
  const view = useMemo(() => (data ? deriveView(data, zoneFilter, showUnknown) : null), [data, zoneFilter, showUnknown]);

  return (
    <div className={styles.page}>
      <header className={styles.pageHeader}>
        <div>
          <h1 className={styles.h1}>Weekly complaints by driver &amp; zone</h1>
          <p className={styles.lede}>Which drivers and zones cause the most complaints — with the counting rules on the page and unknowns kept visible.</p>
        </div>
      </header>

      <div className={`card ${styles.filterBar}`} role="group" aria-label="Filters">
        <div className={styles.weekPicker}>
          <button type="button" className="btn" onClick={() => step(-1)} disabled={loading || weeks.indexOf(week) <= 0} aria-label="Previous week">
            ‹
          </button>
          <label>
            <span className="visually-hidden">Week starting</span>
            <select value={week ?? ''} onChange={(e) => loadWeek(e.target.value)} disabled={!weeks.length}>
              {weeks.map((w) => (
                <option key={w} value={w}>
                  Week of {fmtWeekLong(w)}
                </option>
              ))}
            </select>
          </label>
          <button
            type="button"
            className="btn"
            onClick={() => step(1)}
            disabled={loading || weeks.indexOf(week) >= weeks.length - 1}
            aria-label="Next week"
          >
            ›
          </button>
        </div>
        <div className={styles.filterChips} role="group" aria-label="Zone filter">
          <button type="button" className={`${styles.chip} ${!zoneFilter ? styles.chipOn : ''}`} aria-pressed={!zoneFilter} onClick={() => setZoneFilter(null)}>
            All zones
          </button>
          {Object.keys(ZONE_COLOR).map((z) => (
            <button
              key={z}
              type="button"
              className={`${styles.chip} ${zoneFilter === z ? styles.chipOn : ''}`}
              aria-pressed={zoneFilter === z}
              onClick={() => setZoneFilter(zoneFilter === z ? null : z)}
            >
              <span className={styles.dot} style={{ background: ZONE_COLOR[z] }} aria-hidden="true" />
              {z}
            </button>
          ))}
        </div>
        <label className={styles.toggle}>
          <input type="checkbox" checked={showUnknown} onChange={(e) => setShowUnknown(e.target.checked)} />
          Show unknown attribution
        </label>
      </div>

      {isMock && (
        <p className={styles.mockNote}>
          <strong>Synthetic data.</strong> Numbers are generated for the demo UI. Real figures will come from B’s <code>weekly_complaints</code> via C’s API.
        </p>
      )}

      {error && (
        <div className={styles.errorBox} role="alert">
          Could not load this week: {error.message}{' '}
          <button type="button" className="btn" onClick={() => loadWeek(week)}>
            Retry
          </button>
        </div>
      )}

      {loading && !data && <div className={`card ${styles.skeleton}`}>Loading weekly view…</div>}

      {view && (
        <div className={`${styles.weekly} ${loading ? styles.dim : ''}`} aria-busy={loading}>
          <section className={styles.kpis} aria-label="Key figures">
            <Kpi label="Complaints (all zones)" value={view.totals.complaints} sub={`${data.period.week_start} → ${data.period.week_end} SGT`} spark={view.trendTotals} />
            <Kpi label="Duplicates merged" value={data.totals.duplicates_merged} sub={`${data.totals.rows_logged} rows logged → ${data.totals.complaints} complaints`} />
            <Kpi label="Unknown zone / driver" value={`${data.totals.unknown_zone} / ${data.totals.unknown_driver}`} sub="kept visible, not dropped" tone="neutral" />
            <Kpi label="Refunds + vouchers" value={sgd(data.totals.refunds_sgd + data.totals.vouchers_sgd)} sub={`${sgd(data.totals.refunds_sgd)} refunds · ${sgd(data.totals.vouchers_sgd)} vouchers`} />
            <Kpi
              label="Guide vs agent gaps"
              value={data.totals.guide_gaps}
              sub={`${data.totals.approvals_missing} of ${data.totals.approvals_needed} refunds > $50 lack approval`}
              tone={data.totals.guide_gaps + data.totals.approvals_missing > 0 ? 'warn' : 'good'}
            />
          </section>

          <ChartFrame
            title="Complaints per week, by zone"
            subtitle={`12 weeks to ${fmtWeek(week)} · click a column to open that week`}
            legend={view.zoneSeries.map((s) => ({ label: s.label, color: s.color, hatched: s.hatched }))}
            table={{
              caption: 'Complaints per week by zone',
              columns: ['Week of', ...view.zoneSeries.map((s) => s.label), 'Total'],
              rows: data.trend.map((t) => [
                fmtWeekLong(t.week_start),
                ...view.zoneSeries.map((s) => t.by_zone[s.key] ?? 0),
                view.zoneSeries.reduce((sum, s) => sum + (t.by_zone[s.key] ?? 0), 0),
              ]),
            }}
          >
            <StackedColumns
              series={view.zoneSeries}
              columns={data.trend.map((t) => ({ key: t.week_start, label: t.week_start, values: t.by_zone }))}
              selectedKey={week}
              onSelect={loadWeek}
              formatLabel={fmtWeek}
              ariaLabel="Stacked column chart of weekly complaints by zone over the last 12 weeks"
            />
          </ChartFrame>

          <div className={styles.twoCol}>
            <ChartFrame
              title="Drivers with most complaints"
              subtitle={zoneFilter ? `Drivers whose main zone this week is ${zoneFilter}` : 'All zones · top 10 by complaints this week'}
              table={{
                caption: 'Complaints by driver',
                columns: ['Driver', 'Complaints', 'Main zone', 'Top category'],
                rows: view.drivers.map((d) => [d.driver_code, d.complaints, d.main_zone, d.top_category]),
              }}
            >
              <BarList
                maxItems={10}
                items={view.drivers.map((d) => ({
                  label: d.driver_code,
                  value: d.complaints,
                  sub: `${d.main_zone} · ${d.top_category}`,
                  unknown: d.driver_code === 'Unknown',
                }))}
              />
            </ChartFrame>

            <ChartFrame
              title="Complaints by zone"
              subtitle="Five ops zones from the delivery address (not rate-card bands) · click to filter"
              table={{
                caption: 'Complaints by zone',
                columns: ['Zone', 'Complaints'],
                rows: view.zones.map((z) => [z.zone, z.complaints]),
              }}
            >
              <BarList
                items={view.zones.map((z) => ({ label: z.zone, value: z.complaints, color: ZONE_COLOR[z.zone], unknown: z.zone === 'Unknown' }))}
                onSelect={setZoneFilter}
                selected={zoneFilter}
              />
            </ChartFrame>
          </div>

          <div className={styles.twoCol}>
            <ChartFrame
              title="Zone × complaint type"
              subtitle="Where each kind of complaint concentrates"
              table={{
                caption: 'Complaints by zone and category',
                columns: ['Zone', ...data.zone_category.categories],
                rows: view.heatRows.map((r) => [r.zone, ...r.values]),
              }}
            >
              <Heatmap rows={view.heatRows} columns={data.zone_category.categories} ariaLabel="Heatmap of complaints by zone and category" />
            </ChartFrame>

            <ChartFrame
              title="How complaints were resolved"
              subtitle="Case-log resolution, checked against Resolution Guide v2"
              table={{
                caption: 'Resolution mix',
                columns: ['Resolution', 'Cases'],
                rows: data.by_resolution.map((r) => [r.resolution, r.cases]),
              }}
            >
              <Donut
                centerLabel="cases"
                ariaLabel="Donut chart of resolutions"
                slices={data.by_resolution.map((r) => ({ label: r.resolution, value: r.cases, color: RESOLUTION_COLOR[r.resolution] }))}
              />
            </ChartFrame>
          </div>

          <div className={styles.twoCol}>
            <section className={`card ${styles.defs}`} aria-label="Reporting definitions">
              <h3 className={styles.h3}>How these numbers are counted</h3>
              <dl>
                {data.definitions.map(([k, v]) => (
                  <div key={k} className={styles.defRow}>
                    <dt>{k}</dt>
                    <dd>{v}</dd>
                  </div>
                ))}
              </dl>
              <h3 className={styles.h3}>Limitations</h3>
              <ul className={styles.limitList}>
                {data.limitations.map((l) => (
                  <li key={l}>{l}</li>
                ))}
              </ul>
            </section>
            <section className={`card ${styles.defs}`} aria-label="Sources">
              <h3 className={styles.h3}>Sources</h3>
              <CitationList citations={data.citations} />
            </section>
          </div>
        </div>
      )}
    </div>
  );
}

function Kpi({ label, value, sub, spark, tone }) {
  return (
    <div className={`card ${styles.kpi} ${tone ? styles[`kpi_${tone}`] : ''}`}>
      <span className={styles.kpiLabel}>
        {tone === 'warn' && <span aria-hidden="true">⚠ </span>}
        {label}
      </span>
      <div className={styles.kpiRow}>
        <span className={styles.kpiValue}>{value}</span>
        {spark && <Sparkline values={spark} />}
      </div>
      {sub && <span className={styles.kpiSub}>{sub}</span>}
    </div>
  );
}

function deriveView(data, zoneFilter, showUnknown) {
  const zoneKeys = Object.keys(ZONE_COLOR).filter((z) => (showUnknown ? true : z !== 'Unknown'));
  const visibleZones = zoneFilter ? [zoneFilter] : zoneKeys;
  const zoneSeries = visibleZones.map((z) => ({ key: z, label: z, color: ZONE_COLOR[z], hatched: z === 'Unknown' }));
  const drivers = data.by_driver
    .filter((d) => (zoneFilter ? d.main_zone === zoneFilter : true))
    .filter((d) => (showUnknown ? true : d.driver_code !== 'Unknown'));
  const zones = data.by_zone.filter((z) => (showUnknown ? true : z.zone !== 'Unknown')).sort((a, b) => b.complaints - a.complaints);
  const heatRows = data.zone_category.rows.filter((r) => (showUnknown ? true : r.zone !== 'Unknown')).filter((r) => (zoneFilter ? r.zone === zoneFilter : true));
  return {
    totals: data.totals,
    trendTotals: data.trend.map((t) => t.total),
    zoneSeries,
    drivers,
    zones,
    heatRows,
  };
}
