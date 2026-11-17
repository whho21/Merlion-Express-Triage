// SYNTHETIC weekly complaint data for the mock API. No client data.
// Deterministic (seeded) so screenshots and tests are repeatable.
// Shape mirrors D's proposed weekly contract (B computes, C exposes) —
// see docs/02-Design/frontend-ui-contract-draft.md.
//
// Definitions follow the client's 16 Nov answers (Q01, Q03): one complaint = one case,
// repeat rows merged, five ops zones taken from the delivery address, Resolution Guide v2 applies.

export const ZONES = ['North', 'North-East', 'East', 'Central', 'West'];
export const UNKNOWN = 'Unknown';

export const CATEGORIES = [
  'Late delivery',
  'Parcel not received',
  'Damaged / thrown',
  'Wrong address',
  'COD overcharge',
  'Item missing',
  'Failed delivery',
  'Public holiday',
];

export const RESOLUTIONS = ['Refund', 'Re-deliver', 'Reject', 'Apology only', 'Compensate'];

const DRIVERS = Array.from({ length: 18 }, (_, i) => `DRV${101 + i}`);
const DRIVER_ZONE = Object.fromEntries(DRIVERS.map((d, i) => [d, ZONES[i % ZONES.length]]));

// Small seeded RNG (mulberry32) so values never change between runs.
function rng(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function isoDate(d) {
  return d.toISOString().slice(0, 10);
}

// Mondays from 6 Oct 2025 to 29 Jun 2026 (the case-log window), Singapore weeks.
function buildWeeks() {
  const out = [];
  const start = new Date(Date.UTC(2025, 9, 6));
  const end = new Date(Date.UTC(2026, 5, 29));
  for (let d = new Date(start); d <= end; d.setUTCDate(d.getUTCDate() + 7)) out.push(isoDate(d));
  return out;
}

export const WEEKS = buildWeeks();

function weekEnd(weekStart) {
  const d = new Date(`${weekStart}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + 6);
  return isoDate(d);
}

// Per-week raw generation -----------------------------------------------------
const zoneWeight = { North: 0.8, 'North-East': 1.1, East: 0.9, Central: 1.3, West: 1.0 };
const hotDrivers = { DRV104: 2.6, DRV109: 2.1 }; // synthetic "problem" drivers so the chart has a story

function generateWeek(weekStart, index) {
  const r = rng(1000 + index * 97);
  const migrationBump = weekStart >= '2026-02-02' && weekStart <= '2026-03-16' ? 1.8 : 1; // Feb migration story
  const base = Math.round((9 + r() * 8) * migrationBump);

  const cases = [];
  for (let i = 0; i < base; i++) {
    const weightedDrivers = DRIVERS.flatMap((d) => Array(Math.round((hotDrivers[d] ?? 1) * 4)).fill(d));
    let driver = weightedDrivers[Math.floor(r() * weightedDrivers.length)];
    let zone = DRIVER_ZONE[driver];
    if (r() < 1 - zoneWeight[zone] / 1.4) zone = ZONES[Math.floor(r() * ZONES.length)];
    if (r() < 0.09) zone = UNKNOWN; // zone typed blank in case log, address not resolvable
    if (r() < 0.11) driver = UNKNOWN; // driver blank / not a DRV code
    const lateBias = migrationBump > 1 ? 0.45 : 0.28;
    const category =
      r() < lateBias ? 'Late delivery' : CATEGORIES[1 + Math.floor(r() * (CATEGORIES.length - 1))];
    const resolution = RESOLUTIONS[Math.floor(r() * RESOLUTIONS.length)];
    const refund = resolution === 'Refund' ? Math.round((5 + r() * 70) * 100) / 100 : 0;
    const voucher = resolution === 'Compensate' ? [10, 20, 30][Math.floor(r() * 3)] : 0;
    cases.push({
      zone,
      driver,
      category,
      resolution,
      refund,
      voucher,
      approvalNeeded: refund > 50,
      approved: refund > 50 ? r() > 0.2 : false,
      guideGap: r() < 0.12,
    });
  }
  const duplicates = Math.floor(r() * 3) + (migrationBump > 1 ? 2 : 0);
  const compliments = r() < 0.4 ? 1 : 0;
  return { cases, duplicates, compliments };
}

const RAW = Object.fromEntries(WEEKS.map((w, i) => [w, generateWeek(w, i)]));

function countBy(items, key, universe) {
  const out = Object.fromEntries(universe.map((u) => [u, 0]));
  for (const it of items) out[it[key]] = (out[it[key]] ?? 0) + 1;
  return out;
}

export function buildWeeklyResponse(weekStart) {
  const week = RAW[weekStart];
  if (!week) return null;
  const { cases, duplicates, compliments } = week;

  const byZone = countBy(cases, 'zone', [...ZONES, UNKNOWN]);
  const byCategory = countBy(cases, 'category', CATEGORIES);
  const byResolution = countBy(cases, 'resolution', RESOLUTIONS);

  const driverMap = {};
  for (const c of cases) {
    const d = (driverMap[c.driver] ??= { driver_code: c.driver, complaints: 0, zones: {}, categories: {} });
    d.complaints += 1;
    d.zones[c.zone] = (d.zones[c.zone] ?? 0) + 1;
    d.categories[c.category] = (d.categories[c.category] ?? 0) + 1;
  }
  const top = (obj) => Object.entries(obj).sort((a, b) => b[1] - a[1])[0]?.[0] ?? '-';
  const byDriver = Object.values(driverMap)
    .map((d) => ({
      driver_code: d.driver_code,
      complaints: d.complaints,
      main_zone: top(d.zones),
      top_category: top(d.categories),
    }))
    .sort((a, b) => b.complaints - a.complaints);

  const zoneCategory = [...ZONES, UNKNOWN].map((z) => ({
    zone: z,
    values: CATEGORIES.map((cat) => cases.filter((c) => c.zone === z && c.category === cat).length),
  }));

  const idx = WEEKS.indexOf(weekStart);
  const trend = WEEKS.slice(Math.max(0, idx - 11), idx + 1).map((w) => {
    const wc = RAW[w].cases;
    return { week_start: w, total: wc.length, by_zone: countBy(wc, 'zone', [...ZONES, UNKNOWN]) };
  });

  const sum = (k) => Math.round(cases.reduce((s, c) => s + c[k], 0) * 100) / 100;

  return {
    period: { week_start: weekStart, week_end: weekEnd(weekStart), timezone: 'Asia/Singapore' },
    synthetic: true,
    definitions: [
      ['Week', 'Monday 00:00 to Sunday 23:59, Singapore time, by date the case was opened.'],
      ['Complaint', 'One complaint = one case. Repeat rows for the same customer, order and issue are merged (client rule, Q01).'],
      ['Excluded', 'Compliments and non-complaint emails are not counted.'],
      ['Zone', 'One of five ops zones (North, North-East, East, Central, West) from the town in the delivery address (client, Q03). Not the rate-card price band.'],
      ['Driver', 'Driver code on the case or delivery record. Name look-alikes are not merged.'],
      ['Unknown', 'Shown, never dropped: zone or driver could not be attributed from the sources.'],
    ],
    totals: {
      rows_logged: cases.length + duplicates,
      complaints: cases.length,
      duplicates_merged: duplicates,
      compliments_excluded: compliments,
      unknown_zone: byZone[UNKNOWN],
      unknown_driver: driverMap[UNKNOWN]?.complaints ?? 0,
      refunds_sgd: sum('refund'),
      vouchers_sgd: sum('voucher'),
      approvals_needed: cases.filter((c) => c.approvalNeeded).length,
      approvals_missing: cases.filter((c) => c.approvalNeeded && !c.approved).length,
      guide_gaps: cases.filter((c) => c.guideGap).length,
    },
    by_zone: Object.entries(byZone).map(([zone, complaints]) => ({ zone, complaints })),
    by_driver: byDriver,
    by_category: Object.entries(byCategory).map(([category, complaints]) => ({ category, complaints })),
    by_resolution: Object.entries(byResolution).map(([resolution, cases]) => ({ resolution, cases })),
    zone_category: { zones: [...ZONES, UNKNOWN], categories: CATEGORIES, rows: zoneCategory },
    trend,
    limitations: [
      'SYNTHETIC demo data. Real figures come from B’s weekly_complaints through C’s API.',
      'Case-log zone is typed by hand; B re-derives zone from the delivery address.',
      'Some case-log dates are typed day-first and month-first; B normalises them before weeks are counted.',
    ],
    citations: [
      { n: 1, source_id: 'tabular:case_log', type: 'tabular', ref: 'data/tabular/CS_case_log.xlsx#Case Log', locator: `date_opened:${weekStart}..${weekEnd(weekStart)}`, label: 'CS case log' },
      { n: 2, source_id: 'sql:deliveries', type: 'sql', ref: 'merlion_express.deliveries', locator: 'driver/address join', label: 'Delivery records' },
      { n: 3, source_id: 'policy:resolution_guide_v2', type: 'tabular', ref: 'data/tabular/CS_case_log.xlsx#Resolution Guide', locator: 'all rows', label: 'Resolution Guide v2' },
    ],
  };
}
