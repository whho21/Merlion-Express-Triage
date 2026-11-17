"""Synthetic weekly aggregates for demo profiles and eval runs; never production.

Numbers mirror the agreed example in docs/02-Design/frontend-ui-contract-draft.md
§3 so D and E build against the frozen shape. Label all output as Demo Data
(api-catalog section 7).
"""
from __future__ import annotations

from backend.api_service.weekly import WeeklyNotFound

DEFINITIONS = [
    ['Week', 'Monday–Sunday, Asia/Singapore, by case-log Date Opened.'],
    ['Complaint', 'One canonical case after deduplication; compliments excluded.'],
    ['Duplicate', 'Multiple case-log rows merged into one case; merged rows counted separately.'],
    ['Zone', 'Operations zone from the delivery-address town; unresolved attribution stays Unknown.'],
    ['Unknown', 'Cases whose driver or zone cannot be resolved from reviewed mappings.'],
    ['Guide gap', 'Historical agent resolution differs from Resolution Guide v2 (client Q02).'],
]

TOTALS = {
    'rows_logged': 27, 'complaints': 25, 'duplicates_merged': 2, 'compliments_excluded': 0,
    'unknown_zone': 4, 'unknown_driver': 2, 'refunds_sgd': 268.18, 'vouchers_sgd': 130.0,
    'approvals_needed': 3, 'approvals_missing': 0, 'guide_gaps': 5,
}

LIMITATIONS = [
    'Synthetic demo data; not client aggregates.',
    'Weekly SQL views are not published yet; these numbers are fixtures for UI and runner work.',
]


class FixtureWeeklySource:
    """Demo source behind the same boundary as the real one."""

    available = True
    synthetic = True

    def weeks(self):
        return ['2026-02-09', '2026-02-16']

    def result(self, week_start):
        if week_start not in self.weeks():
            raise WeeklyNotFound('no published coverage for this week')
        return {
            'period': {'week_start': week_start, 'week_end': '2026-02-22', 'timezone': 'Asia/Singapore'},
            'definitions': DEFINITIONS,
            'totals': TOTALS,
            'by_zone': [
                {'zone': 'North', 'complaints': 6}, {'zone': 'North-East', 'complaints': 4},
                {'zone': 'East', 'complaints': 3}, {'zone': 'Central', 'complaints': 5},
                {'zone': 'West', 'complaints': 3}, {'zone': 'Unknown', 'complaints': 4},
            ],
            'by_driver': [
                {'driver_code': 'DRV109', 'complaints': 3, 'main_zone': 'Central', 'top_category': 'COD overcharge'},
                {'driver_code': 'DRV107', 'complaints': 2, 'main_zone': 'North', 'top_category': 'Late delivery'},
                {'driver_code': 'Unknown', 'complaints': 2, 'main_zone': 'Unknown', 'top_category': 'Unknown'},
            ],
            'by_category': [
                {'category': 'Late delivery', 'complaints': 7},
                {'category': 'COD overcharge', 'complaints': 5},
                {'category': 'Wrong address', 'complaints': 4},
                {'category': 'Missing item', 'complaints': 3},
            ],
            'by_resolution': [
                {'resolution': 'Refund', 'cases': 5},
                {'resolution': 'Apology only', 'cases': 3},
                {'resolution': 'Re-deliver', 'cases': 2},
            ],
            'zone_category': {
                'zones': ['North', 'North-East', 'East', 'Central', 'West', 'Unknown'],
                'categories': ['Late delivery', 'COD overcharge', 'Wrong address', 'Missing item'],
                'rows': [
                    {'zone': 'North', 'values': [3, 1, 1, 1]},
                    {'zone': 'North-East', 'values': [2, 0, 1, 1]},
                    {'zone': 'East', 'values': [0, 2, 1, 0]},
                    {'zone': 'Central', 'values': [1, 2, 1, 1]},
                    {'zone': 'West', 'values': [1, 0, 0, 2]},
                    {'zone': 'Unknown', 'values': [0, 0, 0, 4]},
                ],
            },
            'trend': [
                {'week_start': '2026-02-02', 'total': 18, 'by_zone': {'North': 4, 'Central': 5, 'Unknown': 2}},
                {'week_start': '2026-02-09', 'total': 21, 'by_zone': {'North': 5, 'Central': 4, 'Unknown': 3}},
                {'week_start': '2026-02-16', 'total': 25, 'by_zone': {'North': 6, 'Central': 5, 'Unknown': 4}},
            ],
            'limitations': LIMITATIONS,
            'citations': [{
                'n': 1, 'source_id': 'tabular:case_log', 'type': 'tabular',
                'ref': 'data/CS_case_log_Oct25-Jun26.xlsx', 'locator': 'sheet:Case Log',
                'record_key': None, 'label': 'CS case log (synthetic fixture)',
            }],
        }
