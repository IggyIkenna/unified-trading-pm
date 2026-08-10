# Epic: cloud cost + credits negotiation
# Lifecycle: DURABLE — re-run whenever fleet token consumption needs re-measuring
# Delete-when: never (the answer has a date on it; re-run, do not trust an old number)
#
# Measures ACTUAL agent-fleet LLM token consumption from Claude Code transcripts
# (~/.claude/projects/**/*.jsonl), split input / cache_write / cache_read / output,
# by day and by model, over a trailing window.
#
# WHY THIS EXISTS: fleet consumption is invisible under flat-fee subscriptions. The
# 2026-08-09 run measured 7.8B tokens/day on the orchestrator alone (98.3% cache
# reads, ~355k cached tokens per request) — a number nobody had, and the single
# largest input to the Google Cloud credits negotiation.
#
# TRAPS HIT BUILDING THIS:
#   * Filter on the record's OWN `timestamp`, not file mtime — mtime only selects
#     candidate files; a long-lived session file contains records outside the window.
#   * `usage` lives under record['message']['usage'], not at the top level.
#   * cache_read dwarfs everything (98%+). Reporting only input+output understates
#     true volume by ~50x. Always report all four classes.
#   * This measures ONE host. The fleet spans the orchestrator VM plus operator
#     laptops — apply an explicit uplift and SAY it is an estimate.
import collections
import datetime
import glob
import json
import os

ROOT = os.path.expanduser("~/.claude/projects")
now = datetime.datetime.now(datetime.UTC)
cut = now - datetime.timedelta(days=7)
by_model = collections.defaultdict(lambda: {"inp": 0, "cc": 0, "cr": 0, "out": 0, "msgs": 0})
by_day = collections.defaultdict(lambda: {"inp": 0, "cc": 0, "cr": 0, "out": 0, "msgs": 0})
sessions = set()
files = 0
lines = 0
for fp in glob.glob(os.path.join(ROOT, "**", "*.jsonl"), recursive=True):
    try:
        if datetime.datetime.fromtimestamp(os.path.getmtime(fp), datetime.UTC) < cut:
            continue
    except OSError:
        continue
    files += 1
    try:
        fh = open(fp, errors="replace")  # noqa: SIM115 -- OSError-from-open() must not abort the whole scan, only skip this file; a `with open(...)` here would need the entire loop body nested inside the try, which is a much larger diff for a stale one-off script
    except OSError:
        continue
    with fh:
        for line in fh:
            lines += 1
            if '"usage"' not in line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            m = r.get("message") or {}
            u = m.get("usage")
            if not isinstance(u, dict):
                continue
            ts = r.get("timestamp")
            if not ts:
                continue
            try:
                t = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except (ValueError, TypeError, AttributeError):
                continue
            if t < cut:
                continue
            model = m.get("model") or "unknown"
            d = t.date().isoformat()
            for tgt in (by_model[model], by_day[d]):
                tgt["inp"] += u.get("input_tokens", 0) or 0
                tgt["cc"] += u.get("cache_creation_input_tokens", 0) or 0
                tgt["cr"] += u.get("cache_read_input_tokens", 0) or 0
                tgt["out"] += u.get("output_tokens", 0) or 0
                tgt["msgs"] += 1
            sessions.add(r.get("sessionId") or fp)


def fmt(n):
    return f"{n:,}"


print(f"files scanned (mtime<7d): {files}   lines: {lines:,}   sessions: {len(sessions)}")
print()
print(f"{'DAY':<12}{'input':>14}{'cache_write':>16}{'cache_read':>16}{'output':>14}{'TOTAL':>16}{'msgs':>8}")
tot = {"inp": 0, "cc": 0, "cr": 0, "out": 0, "msgs": 0}
for d in sorted(by_day):
    v = by_day[d]
    t = v["inp"] + v["cc"] + v["cr"] + v["out"]
    for k in tot:
        tot[k] += v[k]
    print(
        f"{d:<12}{fmt(v['inp']):>14}{fmt(v['cc']):>16}{fmt(v['cr']):>16}{fmt(v['out']):>14}{fmt(t):>16}{v['msgs']:>8}"
    )
T = tot["inp"] + tot["cc"] + tot["cr"] + tot["out"]
print("-" * 96)
print(
    f"{'7-DAY':<12}{fmt(tot['inp']):>14}{fmt(tot['cc']):>16}{fmt(tot['cr']):>16}{fmt(tot['out']):>14}{fmt(T):>16}{tot['msgs']:>8}"
)
print()
print(f"{'MODEL':<42}{'input':>14}{'cache_write':>15}{'cache_read':>16}{'output':>13}{'TOTAL':>16}")
for m, v in sorted(by_model.items(), key=lambda x: -(x[1]["inp"] + x[1]["cc"] + x[1]["cr"] + x[1]["out"])):
    t = v["inp"] + v["cc"] + v["cr"] + v["out"]
    print(f"{m:<42}{fmt(v['inp']):>14}{fmt(v['cc']):>15}{fmt(v['cr']):>16}{fmt(v['out']):>13}{fmt(t):>16}")
with open("tokens7d.json", "w") as _out_fh:
    json.dump(
        {"by_day": by_day, "by_model": by_model, "total": tot, "grand": T, "sessions": len(sessions)}, _out_fh, indent=1
    )
