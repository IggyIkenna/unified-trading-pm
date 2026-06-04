#!/usr/bin/env python3
"""Generate change-freeze-calendar.csv for a full year from a given start date.

Produces recurring windows for:
- MACRO: NFP (1st Friday monthly), FOMC (8/yr), ECB (8/yr), BOE (8/yr), BOJ (quarterly)
- SESSION: Asian open/close, European open/close, US open/close
- OPTIONS: 3rd Friday monthly expiry
- FUNDING: Crypto 8-hourly funding rate snapshots
- MARKET: US close, EU open (daily)

Usage:
    python3 scripts/ops/generate-freeze-calendar.py [--start 2026-03-13] [--output plans/ops/change-freeze-calendar.csv]
"""

from __future__ import annotations

import argparse
import csv
import io
from datetime import date, timedelta
from pathlib import Path


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
    """NFP: 1st Friday of each month, 13:25-14:00 UTC."""
    rows: list[Row] = []
    for year, month in months_in_range(start, end):
        d = first_friday(year, month)
        if d < start or d > end:
            continue
        rows.append(
            {
                "window_id": f"NFP_{year}_{month:02d}",
                "event_name": f"NFP {d.strftime('%b')}",
                "event_type": "macro_release",
                "recurrence": "1st_friday_monthly",
                "start_utc": f"{d.isoformat()}T13:25",
                "end_utc": f"{d.isoformat()}T14:00",
                "dst_note": "",
                "block_autonomous": "true",
                "block_prod_deploy": "true",
                "affects_venues": ALL_VENUES,
                "notes": "Non-Farm Payrolls release; high vol",
            }
        )
    return rows


def generate_options_expiry(start: date, end: date) -> list[Row]:
    """Options expiry: 3rd Friday of each month, 19:00-21:30 UTC."""
    rows: list[Row] = []
    quarterly_months = {3, 6, 9, 12}
    for year, month in months_in_range(start, end):
        d = third_friday(year, month)
        if d < start or d > end:
            continue
        is_quarterly = month in quarterly_months
        notes = "Quarterly expiry (triple witching)" if is_quarterly else "Monthly options/futures expiry; pin risk"
        rows.append(
            {
                "window_id": f"OPT_EXPIRY_{year}_{month:02d}",
                "event_name": f"Options Expiry {d.strftime('%b')}",
                "event_type": "options_expiry",
                "recurrence": "3rd_friday_monthly",
                "start_utc": f"{d.isoformat()}T19:00",
                "end_utc": f"{d.isoformat()}T21:30",
                "dst_note": "",
                "block_autonomous": "true",
                "block_prod_deploy": "true",
                "affects_venues": "deribit,ibkr,databento",
                "notes": notes,
            }
        )
    return rows


# FOMC meeting dates for 2026 and 2027 (scheduled 8x/year)
FOMC_DATES: dict[int, list[tuple[int, int]]] = {
    2026: [(1, 28), (3, 18), (5, 6), (6, 17), (7, 29), (9, 16), (11, 4), (12, 16)],
    2027: [(1, 27), (3, 17), (5, 5), (6, 16), (7, 28), (9, 22), (11, 3), (12, 15)],
}

# ECB meeting dates (8x/year, approximate)
ECB_DATES: dict[int, list[tuple[int, int]]] = {
    2026: [(1, 22), (3, 12), (4, 16), (6, 4), (7, 16), (9, 10), (10, 22), (12, 10)],
    2027: [(1, 21), (3, 11), (4, 15), (6, 3), (7, 15), (9, 9), (10, 21), (12, 9)],
}

# BOE meeting dates (8x/year)
BOE_DATES: dict[int, list[tuple[int, int]]] = {
    2026: [(2, 5), (3, 19), (5, 7), (6, 18), (8, 6), (9, 17), (11, 5), (12, 17)],
    2027: [(2, 4), (3, 18), (5, 6), (6, 17), (8, 5), (9, 16), (11, 4), (12, 16)],
}

# BOJ meeting dates (quarterly)
BOJ_DATES: dict[int, list[tuple[int, int]]] = {
    2026: [(1, 24), (4, 28), (7, 15), (10, 29)],
    2027: [(1, 21), (4, 27), (7, 16), (10, 28)],
}


def generate_central_bank(
    name: str,
    dates_map: dict[int, list[tuple[int, int]]],
    start: date,
    end: date,
    start_time: str,
    end_time: str,
    recurrence: str,
    venues: str,
    notes: str,
) -> list[Row]:
    rows: list[Row] = []
    for year in range(start.year, end.year + 1):
        for month, day in dates_map.get(year, []):
            d = date(year, month, day)
            if d < start or d > end:
                continue
            month_label = d.strftime("%b") if recurrence != "quarterly" else f"Q{(month - 1) // 3 + 1}"
            rows.append(
                {
                    "window_id": f"{name}_{year}_{month:02d}",
                    "event_name": f"{name} {month_label}",
                    "event_type": "central_bank",
                    "recurrence": recurrence,
                    "start_utc": f"{d.isoformat()}T{start_time}",
                    "end_utc": f"{d.isoformat()}T{end_time}",
                    "dst_note": "",
                    "block_autonomous": "true",
                    "block_prod_deploy": "true",
                    "affects_venues": venues,
                    "notes": notes,
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

    # Central bank
    rows.extend(
        generate_central_bank(
            "FOMC",
            FOMC_DATES,
            start,
            end,
            "18:00",
            "20:30",
            "8x_yearly",
            ALL_VENUES,
            "Fed rate decision + press conference",
        )
    )
    rows.extend(
        generate_central_bank(
            "ECB",
            ECB_DATES,
            start,
            end,
            "12:15",
            "13:30",
            "8x_yearly",
            "databento,ibkr,ecb",
            "ECB rate decision + press conference",
        )
    )
    rows.extend(
        generate_central_bank(
            "BOE", BOE_DATES, start, end, "12:00", "12:30", "8x_yearly", TRAD_VENUES, "BOE rate decision"
        )
    )
    rows.extend(
        generate_central_bank(
            "BOJ",
            BOJ_DATES,
            start,
            end,
            "02:00",
            "06:00",
            "quarterly",
            TRAD_VENUES,
            "BOJ monetary policy; JPY crosses volatile",
        )
    )

    return rows


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
    write_csv(rows, Path(args.output))


if __name__ == "__main__":
    main()
