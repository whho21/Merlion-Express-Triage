"""Weekly reporting boundary for HTTP-04/05 (`/api/weekly/weeks`, `/api/weekly`).

B (Jenn) computes the aggregates; this module only exposes them (contracts
"Weekly summary": B computes; C exposes). The source is injectable like the
structured provider: the production default is unavailable and stays honest
(empty week list, 503 with limitations) until B's reviewed data lands.

Definitions recorded below are C's proposed defaults pending B's confirmation
(client Q01–Q06; catalog section 8 "Reporting definitions"):

- Week: Monday–Sunday, Asia/Singapore, by case-log Date Opened.
- Canonical complaint: one case per deduplicated group; duplicates are merged
  and counted separately, never silently deleted.
- Compliments are excluded from complaint counts.
- Zone: operations zone from the delivery-address town via the reviewed
  mapping; unresolved attribution stays Unknown (client Q03).
- guide_gaps: historical agent resolution differs from Resolution Guide v2,
  which is the authority for every case (client Q02).
- Missing inputs leave metrics null; unknown attribution is never a zero.
"""
from __future__ import annotations

import re
from datetime import date

WEEK_START_RE = re.compile(r'\d{4}-\d{2}-\d{2}')


class WeeklySourceError(Exception):
    pass


class WeeklyUnavailable(WeeklySourceError):
    pass


class WeeklyNotFound(WeeklySourceError):
    pass


def validate_week_start(value) -> str:
    """Require a YYYY-MM-DD Monday; weeks are Monday–Sunday SGT."""
    if not isinstance(value, str) or not WEEK_START_RE.fullmatch(value):
        raise ValueError('week_start must be YYYY-MM-DD')
    day = date.fromisoformat(value)
    if day.weekday() != 0:
        raise ValueError('week_start must be a Monday')
    return value


class UnavailableWeeklySource:
    """Production default: no reviewed aggregate source is configured."""

    available = False
    synthetic = False

    def weeks(self):
        # Catalog HTTP-04: an empty list is the honest no-available-weeks answer.
        return []

    def result(self, week_start):
        raise WeeklyUnavailable('weekly aggregates are not published yet')
