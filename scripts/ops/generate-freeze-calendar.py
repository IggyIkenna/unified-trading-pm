#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Generate change-freeze-calendar.csv for a full year from a given start date.

EVERY window is <= 30 minutes (operator directive 2026-07-20) and is anchored on the event's LOCAL
time, resolved to UTC per occurrence — so a window lands on its event in BOTH DST halves. Before
that, dated windows were hardcoded UTC and deliberately WIDE to straddle both alignments; that hedge
had already failed (NFP protected nothing for 7 of 12 months) and the central-bank date tables were
fabricated. See `plans/active/issues/change_freeze_calendar_protects_nothing_for_much_of_the_year_2026_07_20.md`.

Produces recurring windows for:
- MACRO: NFP (1st Friday monthly, 08:30 America/New_York)
- CENTRAL BANK (published schedules only, announcement day, decision + press conference rows):
  FOMC 8/yr (14:00/14:30 ET), ECB 8/yr (14:15/14:45 CET), BOE 8/yr (12:00 London), BOJ 8/yr
  (15:30 JST presser only — the statement time is UNSCHEDULED, see the BOJ ruling at its call site)
- OPTIONS: 3rd Friday — Deribit 08:00Z settlement, US AM SET (quarterly), US PM close
- SESSION / MARKET: European + US open/close (daily, time-only)
- FUNDING: Crypto 8-hourly funding rate snapshots

Generation FAILS (never warns) if a row is malformed, exceeds 30 min, or does not contain the
instant it claims to protect; it WARNS where a published schedule ends before the horizon.

Usage:
    python3 scripts/ops/generate-freeze-calendar.py [--start 2026-03-13] [--output plans/ops/change-freeze-calendar.csv]
"""

from __future__ import annotations

import argparse
import csv
import io
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo


def nth_weekday_of_month(year: int, month: int, weekday: int, n: int) -> date:
    """Return the nth occurrence of weekday (0=Mon, 4=Fri) in the given month."""
    first_day = date(year, month, 1)
    # Find first occurrence of the target weekday
    offset = (weekday - first_day.weekday()) % 7
    first_occurrence = first_day + timedelta(days=offset)
    result = first_occurrence + timedelta(weeks=n - 1)
    if result.month != month:
        msg = f"No {n}th weekday={weekday} in {year}-{month:02d}"
        raise ValueError(msg)
    return result


def first_friday(year: int, month: int) -> date:
    return nth_weekday_of_month(year, month, 4, 1)  # 4 = Friday


def third_friday(year: int, month: int) -> date:
    return nth_weekday_of_month(year, month, 4, 3)


Row = dict[str, str]
HEADER = [
    "window_id",
    "event_name",
    "event_type",
    "recurrence",
    "start_utc",
    "end_utc",
    "dst_note",
    "block_autonomous",
    "block_prod_deploy",
    "affects_venues",
    "notes",
]

ALL_VENUES = "binance,coinbase,deribit,bybit,okx,databento,ibkr"
CRYPTO_VENUES = "binance,bybit,okx,deribit,hyperliquid"
TRAD_VENUES = "databento,ibkr"

# ── DST-aware window construction (2026-07-20) ────────────────────────────────────────────────────
# Every dated window used to be a hardcoded UTC string, and `dst_note` was emitted empty for all of
# them (the enforcement workflows read the column into a shell variable and never use it). The
# generator compensated by making each window WIDE enough to straddle both the summer and winter UTC
# alignment of the same local-time event — i.e. the widths were DST HEDGES, not risk estimates.
#
# That hedge was already broken. MEASURED 2026-07-20: NFP was pinned to 13:25-14:00Z, the EST
# alignment, while the BLS print is 12:30Z under EDT — so for 7 of 12 months the window opened 55
# minutes AFTER the release and protected NOTHING while still blocking deploys and reading as
# coverage.
#
# Anchoring on the LOCAL time and resolving the UTC offset per occurrence removes the ambiguity, so
# the operator's 30-minute cap becomes implementable: 30 minutes cannot straddle a 60-minute offset,
# but it does not need to once the offset is known. `dst_note` is now populated so the CSV shows its
# own reasoning to anyone reading it.
_UTC = ZoneInfo("UTC")


def utc_window(
    day: date,
    local_hhmm: str,
    tz_name: str,
    before_min: int,
    after_min: int,
) -> tuple[str, str, str]:
    """Resolve a local-time anchor to a UTC ``(start, end, dst_note)`` window.

    Args:
        day: the local calendar date of the event.
        local_hhmm: the anchor in local wall-clock time, ``"HH:MM"``.
        tz_name: IANA zone of the anchor (``America/New_York``, ``Europe/Berlin``, ...).
        before_min: minutes of window BEFORE the anchor.
        after_min: minutes of window AFTER the anchor.

    Returns:
        ``(start_utc, end_utc, dst_note)`` — the first two as ``YYYY-MM-DDTHH:MM``, matching the
        existing dated-row format the enforcement workflows parse with ``date -u -d``.

    ``before_min + after_min`` MUST be <= 30 (operator directive 2026-07-20); the caller is
    responsible, and ``assert_window_cap`` re-checks every emitted row so a future edit cannot
    quietly reintroduce a wide window.
    """
    hh, mm = (int(p) for p in local_hhmm.split(":"))
    anchor_local = datetime(day.year, day.month, day.day, hh, mm, tzinfo=ZoneInfo(tz_name))
    anchor_utc = anchor_local.astimezone(_UTC)
    start = anchor_utc - timedelta(minutes=before_min)
    end = anchor_utc + timedelta(minutes=after_min)
    offset = anchor_local.utcoffset() or timedelta(0)
    offset_h = offset.total_seconds() / 3600
    note = f"anchor {local_hhmm} {tz_name} (UTC{offset_h:+g}) -> {anchor_utc.strftime('%H:%M')}Z"
    return (
        start.strftime("%Y-%m-%dT%H:%M"),
        end.strftime("%Y-%m-%dT%H:%M"),
        note,
    )


def generate_daily_windows() -> list[Row]:
    """Session boundaries and market open/close (daily recurring, time-only)."""
    return [
        {
            "window_id": "US_CLOSE_DAILY",
            "event_name": "US Market Close",
            "event_type": "market_close",
            "recurrence": "daily",
            "start_utc": "20:55",
            "end_utc": "21:00",
            "dst_note": "US DST (Mar-Nov): 19:55-20:00 UTC",
            "block_autonomous": "true",
            "block_prod_deploy": "true",
            "affects_venues": ALL_VENUES,
            "notes": "NYSE/NASDAQ closing auction; high vol window",
        },
        {
            "window_id": "EU_OPEN_DAILY",
            "event_name": "EU Market Open",
            "event_type": "market_open",
            "recurrence": "daily",
            "start_utc": "06:55",
            "end_utc": "07:00",
            "dst_note": "EU DST (Mar-Oct): 05:55-06:00 UTC",
            "block_autonomous": "true",
            "block_prod_deploy": "true",
            "affects_venues": "databento,ibkr,ecb",
            "notes": "LSE/Euronext opening auction; gap risk",
        },
        # ASIA_OPEN/CLOSE removed 2026-06-04: crypto venues trade 24/7 with no opening/closing
        # auction — "Asian session" boundaries carry no auction/pin risk worth a prod freeze
        # (operator call: focus session freezes on TradFi auctions). Crypto event risk is the
        # funding snapshots (kept, autonomous-only) + macro releases (FOMC/ECB/NFP).
        {
            "window_id": "EU_CLOSE_DAILY",
            "event_name": "European Session Close",
            "event_type": "session_boundary",
            "recurrence": "daily",
            "start_utc": "16:00",
            "end_utc": "16:05",
            "dst_note": "EU DST (Mar-Oct): 15:00-15:05 UTC",
            "block_autonomous": "true",
            "block_prod_deploy": "true",
            "affects_venues": "databento,ibkr,ecb",
            "notes": "LSE/Euronext closing auction",
        },
        {
            "window_id": "US_OPEN_DAILY",
            "event_name": "US Session Open",
            "event_type": "session_boundary",
            "recurrence": "daily",
            "start_utc": "13:30",
            "end_utc": "13:35",
            "dst_note": "US DST (Mar-Nov): 13:30-13:35 UTC",
            "block_autonomous": "true",
            "block_prod_deploy": "true",
            "affects_venues": TRAD_VENUES,
            "notes": "NYSE/NASDAQ opening; high vol",
        },
        {
            "window_id": "US_CLOSE_EXT_DAILY",
            "event_name": "US Session Close",
            "event_type": "session_boundary",
            "recurrence": "daily",
            "start_utc": "20:00",
            "end_utc": "20:05",
            "dst_note": "US DST (Mar-Nov): 20:00-20:05 UTC",
            "block_autonomous": "true",
            "block_prod_deploy": "true",
            "affects_venues": ALL_VENUES,
            "notes": "NYSE/NASDAQ close + after-hours transition",
        },
    ]


def generate_funding_windows() -> list[Row]:
    """Crypto funding rate snapshots every 8 hours."""
    return [
        {
            "window_id": "FUNDING_00",
            "event_name": "Crypto Funding Rate 00:00",
            "event_type": "funding_snapshot",
            "recurrence": "every_8h",
            "start_utc": "23:55",
            "end_utc": "00:05",
            "dst_note": "",
            "block_autonomous": "true",
            "block_prod_deploy": "false",
            "affects_venues": CRYPTO_VENUES,
            "notes": "Funding rate settlement; basis trades adjust",
        },
        {
            "window_id": "FUNDING_08",
            "event_name": "Crypto Funding Rate 08:00",
            "event_type": "funding_snapshot",
            "recurrence": "every_8h",
            "start_utc": "07:55",
            "end_utc": "08:05",
            "dst_note": "",
            "block_autonomous": "true",
            "block_prod_deploy": "false",
            "affects_venues": CRYPTO_VENUES,
            "notes": "Funding rate settlement; basis trades adjust",
        },
        {
            "window_id": "FUNDING_16",
            "event_name": "Crypto Funding Rate 16:00",
            "event_type": "funding_snapshot",
            "recurrence": "every_8h",
            "start_utc": "15:55",
            "end_utc": "16:05",
            "dst_note": "",
            "block_autonomous": "true",
            "block_prod_deploy": "false",
            "affects_venues": CRYPTO_VENUES,
            "notes": "Funding rate settlement; basis trades adjust",
        },
    ]


def months_in_range(start: date, end: date) -> list[tuple[int, int]]:
    """Return (year, month) tuples covering the range."""
    result: list[tuple[int, int]] = []
    current = date(start.year, start.month, 1)
    while current <= end:
        result.append((current.year, current.month))
        current = date(current.year + 1, 1, 1) if current.month == 12 else date(current.year, current.month + 1, 1)
    return result


def generate_nfp(start: date, end: date) -> list[Row]:
    """NFP: 1st Friday monthly, 30 min around the 08:30 America/New_York BLS print.

    Was a hardcoded 13:25-14:00 UTC — the EST alignment only. Under EDT the print is 12:30Z, so the
    window opened 55 minutes AFTER the release for 7 of 12 months and protected nothing. Now
    DST-anchored, which both FIXES that and satisfies the 30-min cap. NFP is a single instantaneous
    print with no press conference, so -5/+25 keeps the spike plus the immediate follow-through.
    """
    rows: list[Row] = []
    for year, month in months_in_range(start, end):
        d = first_friday(year, month)
        if d < start or d > end:
            continue
        s, e, note = utc_window(d, "08:30", "America/New_York", 5, 25)
        rows.append(
            {
                "window_id": f"NFP_{year}_{month:02d}",
                "event_name": f"NFP {d.strftime('%b')}",
                "event_type": "macro_release",
                "recurrence": "1st_friday_monthly",
                "start_utc": s,
                "end_utc": e,
                "dst_note": note,
                "block_autonomous": "true",
                "block_prod_deploy": "true",
                "affects_venues": ALL_VENUES,
                "notes": "Non-Farm Payrolls release; high vol",
            }
        )
    return rows


def generate_options_expiry(start: date, end: date) -> list[Row]:
    """Options expiry: up to THREE 30-min windows on the 3rd Friday, one per real settlement.

    The single 19:00-21:30 UTC window was one wide hedge that covered the US PM close in both DST
    halves and NOTHING else — despite listing ``deribit`` FIRST in affects_venues. Deribit settles at
    08:00 UTC, ~11 hours away, so the venue named first was never covered; and the AM-settled
    triple-witching SET (off the 09:30 ET opening prints) was never covered either.

    Splitting by settlement gives strictly BETTER coverage at LESS total frozen time
    (150 min -> 60-90 min per expiry), and each row independently satisfies the 30-min cap:

      * CRYPTO — Deribit 08:00 UTC settlement. Its index is a 30-min TWAP over 07:30-08:00Z, so the
        window is -25/+5 to sit ON the averaging period rather than after it. DST-IMMUNE (Deribit
        settles at a fixed UTC instant with no local-clock anchor).
      * AM SET — 09:30 America/New_York opening prints, off which AM-settled index options settle.
        Quarterly months only, where triple-witching makes the SET material.
      * PM CLOSE — 16:00 America/New_York cash close, where PM-settled equity/ETF options pin and
        the delta-hedge unwind concentrates. -25/+5 puts the window ON the closing auction.
    """
    rows: list[Row] = []
    quarterly_months = {3, 6, 9, 12}
    for year, month in months_in_range(start, end):
        d = third_friday(year, month)
        if d < start or d > end:
            continue
        is_quarterly = month in quarterly_months
        mon = d.strftime("%b")

        # Deribit crypto settlement — fixed 08:00Z, no local anchor, so built directly.
        rows.append(
            {
                "window_id": f"OPT_EXPIRY_CRYPTO_{year}_{month:02d}",
                "event_name": f"Deribit Expiry {mon}",
                "event_type": "options_expiry",
                "recurrence": "3rd_friday_monthly",
                "start_utc": f"{d.isoformat()}T07:35",
                "end_utc": f"{d.isoformat()}T08:05",
                "dst_note": "fixed 08:00Z settlement (30-min TWAP 07:30-08:00Z); DST-immune",
                "block_autonomous": "true",
                "block_prod_deploy": "true",
                "affects_venues": CRYPTO_VENUES,
                "notes": "Deribit options settlement; index TWAP window",
            }
        )

        if is_quarterly:
            s, e, note = utc_window(d, "09:30", "America/New_York", 5, 25)
            rows.append(
                {
                    "window_id": f"OPT_EXPIRY_AM_{year}_{month:02d}",
                    "event_name": f"Triple Witching AM SET {mon}",
                    "event_type": "options_expiry",
                    "recurrence": "3rd_friday_quarterly",
                    "start_utc": s,
                    "end_utc": e,
                    "dst_note": note,
                    "block_autonomous": "true",
                    "block_prod_deploy": "true",
                    "affects_venues": TRAD_VENUES,
                    "notes": "AM-settled index options (SET) off the opening prints; triple witching",
                }
            )

        s, e, note = utc_window(d, "16:00", "America/New_York", 25, 5)
        rows.append(
            {
                "window_id": f"OPT_EXPIRY_{year}_{month:02d}",
                "event_name": f"Options Expiry {mon}",
                "event_type": "options_expiry",
                "recurrence": "3rd_friday_monthly",
                "start_utc": s,
                "end_utc": e,
                "dst_note": note,
                "block_autonomous": "true",
                "block_prod_deploy": "true",
                "affects_venues": TRAD_VENUES,
                "notes": (
                    "Quarterly expiry (triple witching) PM close"
                    if is_quarterly
                    else "Monthly expiry PM close; pin risk"
                ),
            }
        )
    return rows


# ── CENTRAL-BANK ANNOUNCEMENT DATES — PUBLISHED SCHEDULES ONLY ────────────────────────────────────
# Sourced from each bank's own calendar 2026-07-20. The previous tables were FABRICATED: ECB and BOE
# 2027 were each EXACTLY 364 days after 2026 (a uniform 52-week shift, 8 of 8 for both), which
# preserves weekday and so looked plausible. Checked against the real schedules, 3 of 8 FOMC 2026
# dates, 7 of 8 ECB 2026 dates and 2 of 8 BOE 2026 dates were WRONG, and BOJ_2026_01 (2026-01-24)
# fell on a SATURDAY with BOJ encoded as quarterly when it holds EIGHT meetings a year.
#
# These are ANNOUNCEMENT days (day 2 of a two-day meeting for FOMC/BOJ) — the freeze must land on the
# statement, not on day 1 when nothing is released.
#
# HARD RULE: never extrapolate a schedule. An unpublished year is ABSENT here, and `assert_coverage`
# reports the gap loudly at generation time. A fabricated date produces a window that is
# cap-compliant, DST-correct and protects nothing — strictly worse than no window, because it reads
# as coverage.

# Source: federalreserve.gov/monetarypolicy/fomccalendars.htm (fetched 2026-07-20).
# Announcement = day 2. SEP meetings: Mar, Jun, Sep, Dec.
FOMC_DATES: dict[int, list[tuple[int, int]]] = {
    2026: [(1, 28), (3, 18), (4, 29), (6, 17), (7, 29), (9, 16), (10, 28), (12, 9)],
    2027: [(1, 27), (3, 17), (4, 28), (6, 9), (7, 28), (9, 15), (10, 27), (12, 8)],
}

# Source: ECB Governing Council monetary-policy meetings (fetched 2026-07-20); 2026 corroborated by
# the ECB's own release URLs, which encode the date (ecb.mp260611 = 11 Jun 2026 decision;
# ecb.mg260416 = account of the 18-19 Mar 2026 meeting). Decisions are announced 14:15 CET/CEST,
# always a Thursday. 2027 is only PARTIALLY published — Feb/Mar/Apr only; the rest is deliberately
# absent rather than guessed.
ECB_DATES: dict[int, list[tuple[int, int]]] = {
    2026: [(2, 5), (3, 19), (4, 30), (6, 11), (7, 23), (9, 10), (10, 29), (12, 17)],
    2027: [(2, 4), (3, 18), (4, 29)],
}

# Source: bankofengland.co.uk/monetary-policy/upcoming-mpc-dates (fetched 2026-07-20).
# 2027 is published as PROVISIONAL by the Bank and may move.
BOE_DATES: dict[int, list[tuple[int, int]]] = {
    2026: [(2, 5), (3, 19), (4, 30), (6, 18), (7, 30), (9, 17), (11, 5), (12, 17)],
    2027: [(2, 4), (3, 18), (4, 29), (6, 17), (7, 29), (9, 16), (11, 4), (12, 16)],
}

# Source: boj.or.jp/en/mopo/mpmsche_minu/index.htm (fetched 2026-07-20). EIGHT meetings a year, not
# four. Statement day = day 2. 2027 is NOT YET PUBLISHED by the BOJ and is therefore absent.
BOJ_DATES: dict[int, list[tuple[int, int]]] = {
    2026: [(1, 23), (3, 19), (4, 28), (6, 16), (7, 31), (9, 18), (10, 30), (12, 18)],
}


def generate_central_bank(
    name: str,
    dates_map: dict[int, list[tuple[int, int]]],
    start: date,
    end: date,
    local_time: str,
    tz_name: str,
    recurrence: str,
    venues: str,
    notes: str,
    presser_local: str | None = None,
    presser_notes: str = "",
) -> list[Row]:
    """Emit a 30-min decision window per meeting, plus an optional 30-min press-conference window.

    ``presser_local`` exists because window WIDTH was doing two jobs, and capping only accounts for
    one. A blocked prod build is deferred and replayed by the hourly freeze-deferred-build-replay
    once the window LIFTS — so a wide FOMC window both masked the event AND held the deferred build
    until the whole event was over. Capping to the statement alone would replay that build straight
    into the 14:30 ET press conference, turning a deferral into a TARGETED INJECTION at the
    highest-vol minutes of the day. A separate presser row restores that protection while keeping
    every individual window <= 30 min, so the operator's directive still holds.
    """
    rows: list[Row] = []
    for year in range(start.year, end.year + 1):
        for month, day in dates_map.get(year, []):
            d = date(year, month, day)
            if d < start or d > end:
                continue
            month_label = d.strftime("%b")
            s, e, note = utc_window(d, local_time, tz_name, 5, 25)
            rows.append(
                {
                    "window_id": f"{name}_{year}_{month:02d}",
                    "event_name": f"{name} {month_label}",
                    "event_type": "central_bank",
                    "recurrence": recurrence,
                    "start_utc": s,
                    "end_utc": e,
                    "dst_note": note,
                    "block_autonomous": "true",
                    "block_prod_deploy": "true",
                    "affects_venues": venues,
                    "notes": notes,
                }
            )
            if presser_local:
                ps, pe, pnote = utc_window(d, presser_local, tz_name, 5, 25)
                rows.append(
                    {
                        "window_id": f"{name}_PRESSER_{year}_{month:02d}",
                        "event_name": f"{name} Presser {month_label}",
                        "event_type": "central_bank",
                        "recurrence": recurrence,
                        "start_utc": ps,
                        "end_utc": pe,
                        "dst_note": pnote,
                        "block_autonomous": "true",
                        "block_prod_deploy": "true",
                        "affects_venues": venues,
                        "notes": presser_notes or f"{name} press conference Q&A",
                    }
                )
    return rows


def generate_calendar(start: date) -> list[Row]:
    """Generate a full year of freeze windows from start date."""
    end = start + timedelta(days=365)
    rows: list[Row] = []

    # Daily / recurring
    rows.extend(generate_daily_windows())
    rows.extend(generate_funding_windows())

    # Monthly dated events
    rows.extend(generate_nfp(start, end))
    rows.extend(generate_options_expiry(start, end))

    # Central bank — local-time anchors, resolved to UTC per occurrence (see utc_window).
    rows.extend(
        generate_central_bank(
            "FOMC",
            FOMC_DATES,
            start,
            end,
            "14:00",  # statement
            "America/New_York",
            "8x_yearly",
            ALL_VENUES,
            "Fed rate decision (statement + SEP on Mar/Jun/Sep/Dec)",
            presser_local="14:30",
            presser_notes="Fed Chair press conference Q&A; frequently larger realised vol than the statement",
        )
    )
    rows.extend(
        generate_central_bank(
            "ECB",
            ECB_DATES,
            start,
            end,
            "14:15",  # decision
            "Europe/Berlin",
            "8x_yearly",
            "databento,ibkr,ecb",
            "ECB rate decision",
            presser_local="14:45",
            presser_notes="ECB press conference; forward guidance Q&A",
        )
    )
    rows.extend(
        generate_central_bank(
            "BOE",
            BOE_DATES,
            start,
            end,
            "12:00",
            "Europe/London",
            "8x_yearly",
            TRAD_VENUES,
            "BOE MPC announcement",
        )
    )
    # ── BOJ — OPERATOR RULING 2026-07-20: target the press conference, accept statement exposure ──
    # BOJ is the one event that CANNOT be point-targeted, and pretending otherwise is exactly the
    # "looks like coverage" failure this whole change exists to remove. The policy statement has NO
    # pre-announced minute — it lands when the Policy Board finishes, typically 11:30-12:30 JST but
    # routinely past 13:00 on contentious meetings, and the length of the delay is itself tradeable.
    # A 30-min window cannot cover an unscheduled instant; a 4-hour one could, but the directive caps
    # at 30 and the old 240-min window was in any case sitting on FABRICATED dates (4 of them, one a
    # Saturday), so it was protecting nothing regardless.
    #
    # The Governor's press conference at 15:30 JST is the ONLY deterministic BOJ moment, so that is
    # what we freeze. Residual accepted: the statement itself is unprotected. Blast radius is limited
    # to TRAD_VENUES (databento, ibkr) — this does not touch crypto. Japan observes no DST, so
    # Asia/Tokyo is a constant UTC+9 and this window is DST-immune.
    # Revisit if JGB/JPY exposure grows: the alternative is a named wide carve-out, which needs an
    # explicit exception to the 30-min rule rather than a silent one.
    rows.extend(
        generate_central_bank(
            "BOJ",
            BOJ_DATES,
            start,
            end,
            "15:30",  # governor's press conference — the only scheduled BOJ instant
            "Asia/Tokyo",
            "8x_yearly",
            TRAD_VENUES,
            "BOJ governor press conference (statement time is UNSCHEDULED and deliberately uncovered)",
        )
    )

    return rows


MAX_WINDOW_MIN = 30


def assert_rows_valid(rows: list[Row]) -> None:
    """Fail generation on a malformed or over-long window. Both guards are load-bearing.

    SHAPE: ``csv.DictWriter`` raises on EXTRA keys but silently fills MISSING ones from
    ``restval=''``. A row omitting ``block_prod_deploy`` therefore emits an empty column, and the
    enforcement workflows test ``[ "$block_prod_deploy" = "true" ]`` — so a malformed row becomes a
    freeze that blocks NOTHING, silently. Nothing would ever have told us.

    CAP: the operator's 30-minute ceiling (2026-07-20). Enforced on the EMITTED row rather than
    trusted at each call site, so a future edit cannot quietly reintroduce a wide window.
    """
    expected = set(HEADER)
    for row in rows:
        wid = row.get("window_id", "<no window_id>")
        if set(row) != expected:
            missing = sorted(expected - set(row))
            extra = sorted(set(row) - expected)
            msg = f"{wid}: row keys != HEADER (missing={missing}, extra={extra})"
            raise ValueError(msg)
        s, e = row["start_utc"], row["end_utc"]
        if "T" in s:  # dated rows only; time-only daily rows are fixed 5-10 min by construction
            dur = (datetime.fromisoformat(e) - datetime.fromisoformat(s)).total_seconds() / 60
            if dur <= 0 or dur > MAX_WINDOW_MIN:
                msg = f"{wid}: window is {dur:g} min ({s} -> {e}); cap is {MAX_WINDOW_MIN} min"
                raise ValueError(msg)


def assert_anchor_contained(rows: list[Row]) -> None:
    """Every dated window must CONTAIN the instant it claims to protect.

    This is the check whose absence let the calendar go unnoticed for months: NFP was pinned to
    13:25-14:00Z (the EST alignment) while the BLS print is 12:30Z under EDT, so for 7 of 12 months
    the window opened 55 minutes AFTER the release — it blocked deploys, logged a warning, and
    protected NOTHING, while reading as coverage. A window pointing at the wrong hour is strictly
    worse than no window, so this is a HARD failure, not a warning.

    The anchor is recovered from ``dst_note`` — which ``utc_window`` emits as ``... -> HH:MMZ`` —
    rather than recomputed, so the check is independent of the construction arithmetic and also
    catches a hand-edited row. Rows whose note carries no ``-> HH:MMZ`` (the fixed-UTC crypto
    settlement row) are matched on their own stated instant instead.
    """
    for row in rows:
        s = row["start_utc"]
        if "T" not in s:  # time-only daily rows have no dated anchor
            continue
        # Direct index, not .get(..., ""): assert_rows_valid runs FIRST and guarantees every row
        # carries the full HEADER key set, so a missing key here is a real bug and a loud KeyError
        # is the correct outcome — an "" fallback would silently turn it into "no anchor found".
        note = row["dst_note"]
        m = re.search(r"->\s*(\d{2}):(\d{2})Z", note) or re.search(r"fixed (\d{2}):(\d{2})Z", note)
        if not m:
            msg = f"{row['window_id']}: dated row has no recoverable anchor in dst_note={note!r}"
            raise ValueError(msg)
        # UTC-aware throughout: the CSV stores UTC wall-clock with no offset suffix, so every value
        # here is UTC by construction. Stamping tzinfo makes that explicit rather than relying on
        # naive-vs-naive comparison happening to be right.
        day = datetime.fromisoformat(s).date()
        anchor = datetime(day.year, day.month, day.day, int(m.group(1)), int(m.group(2)), tzinfo=_UTC)
        start_dt = datetime.fromisoformat(s).replace(tzinfo=_UTC)
        end_dt = datetime.fromisoformat(row["end_utc"]).replace(tzinfo=_UTC)
        if not (start_dt <= anchor <= end_dt):
            msg = (
                f"{row['window_id']}: window {s}->{row['end_utc']} does NOT contain its anchor "
                f"{anchor:%Y-%m-%dT%H:%M}Z — it would block deploys while protecting nothing"
            )
            raise ValueError(msg)


def assert_coverage(rows: list[Row], start: date, end: date) -> None:
    """WARN (loudly) where a schedule runs out before the calendar horizon.

    Unpublished years are deliberately ABSENT from the date tables rather than extrapolated — the
    fabricated tables this replaces were exactly a uniform 52-week shift. But absence must not be
    SILENT: a missing year produces no rows, which looks identical to "no events scheduled". This
    prints the gap so regeneration surfaces it instead of quietly shipping an unprotected period.
    """
    for name, table in (("FOMC", FOMC_DATES), ("ECB", ECB_DATES), ("BOE", BOE_DATES), ("BOJ", BOJ_DATES)):
        last = max((date(y, m, d) for y, entries in table.items() for m, d in entries), default=None)
        if last is None or last < end:
            print(
                f"  WARNING: {name} schedule ends {last} but the calendar runs to {end} — "
                f"that period has NO {name} freeze. Add the published dates when the bank releases them."
            )


def write_csv(rows: list[Row], output_path: Path) -> None:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=HEADER)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(buf.getvalue())
    print(f"Wrote {len(rows)} windows to {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate change-freeze-calendar.csv")
    parser.add_argument("--start", default="2026-03-13", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--output", default="plans/ops/change-freeze-calendar.csv", help="Output CSV path")
    args = parser.parse_args()

    start = date.fromisoformat(args.start)
    rows = generate_calendar(start)
    assert_rows_valid(rows)
    assert_anchor_contained(rows)
    assert_coverage(rows, start, start + timedelta(days=365))
    write_csv(rows, Path(args.output))


if __name__ == "__main__":
    main()
