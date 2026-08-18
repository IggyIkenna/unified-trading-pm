#!/usr/bin/env python3
# Epic: system_readiness_master
# Lifecycle: permanent
# Delete-when: NA
"""Banned-term / disclosure checker for the six client-facing presentation artefacts
under codex/14-customer-journeys/commercial-model/*.html.

Root cause (client_artefact_remediation_2026_08_18.md § E, operator ruling): measured
2026-08-18, no checker anywhere greps client artefacts for the banned client name — the
six-hit stop-ship in strategy-service-deep-dive.html was found only because an audit was
commissioned. Nothing would have caught a recurrence tomorrow. This check closes that gap.

Scans RAW FILE TEXT, not rendered prose — deliberately no HTML parser (BeautifulSoup /
lxml would strip or normalise element boundaries). One of the original stop-ship hits was
inside an SVG <text> element, invisible to a check that only walks visible DOM text nodes.
A plain string/regex scan over the file's own bytes catches it identically to every other
occurrence, by construction.

Two independent severities, per the plan's own instruction that a hard-fail-on-any-hit
class and a warn-for-review class are NOT the same thing:

  HARD (zero-tolerance, no baseline): a hit is always wrong, there is no legitimate use.
    - the banned client name (ClearLoop)
    - in-progress maturity labels leaking verbatim (CODE_NOT_WRITTEN / CODE_WRITTEN) --
      see show-dont-show-discipline.md "All paths" bullet 3
    - internal ops route prefixes as literal path tokens (/admin/, /ops/, /config/,
      /devops/) -- see show-dont-show-discipline.md "All paths" bullet 4

  WARN (shrinking ratchet, for-review): a hit is USUALLY a leak but has a legitimate
  shape ("net carry (annualised, bps)" is a real, intended phrase per the plan's own
  example) -- performance-figure patterns (a bare percentage next to a return/yield
  word, Sharpe/CAGR/IRR/APY/APR mentions, "backtest return"). Ratchet-baselined like
  check_reference_paths.py's shrinking ratchets: a live count ABOVE the baseline fails
  (a NEW warn-pattern landed); lower the baseline as reviewed hits are confirmed benign
  or fixed. NEVER hand-raise it.

Rules are derived from, not restated from, the codex SSOT:
  /codex/14-customer-journeys/_ssot-rules/06-show-dont-show-discipline.md
Extending the HARD set (competitor names, internal pricing-column leakage) is explicitly
OUT of this first cut -- rule 06 names them but gives no fixed, groundable vocabulary to
match against, and inventing one here would be exactly the kind of unmeasured claim this
plan exists to stop making. Add them the moment a concrete term list exists.

Usage:
  python3 scripts/plan-hygiene/check_artefact_disclosure.py [--quiet] [--update-baseline]
Exit 0 if hard-hit count is 0 AND warn count <= baseline. NEVER hand-raise the baseline.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

PM_DIR = Path(__file__).resolve().parents[2]
ARTEFACT_DIR = PM_DIR / "codex" / "14-customer-journeys" / "commercial-model"
BASELINE_PATH = Path(__file__).resolve().parent / "artefact_disclosure_baseline.yaml"

# --- HARD (zero tolerance) ---------------------------------------------------
BANNED_CLIENT_NAME_RE = re.compile(r"clearloop", re.IGNORECASE)
MATURITY_LEAK_RE = re.compile(r"\bCODE_NOT_WRITTEN\b|\bCODE_WRITTEN\b")
INTERNAL_ROUTE_RE = re.compile(r"(?<![\w-])/(?:admin|ops|config|devops)/[\w/-]*")

# --- WARN (shrinking ratchet, for-review) ------------------------------------
PERFORMANCE_FIGURE_RE = re.compile(
    r"\b\d{1,3}(?:\.\d+)?\s?%\s*(?:APY|APR|CAGR|IRR|return|yield|Sharpe)\b"
    r"|\bSharpe\s+ratio\b"
    r"|\bbacktest(?:ed)?\s+return\b"
    r"|\bannuali[sz]ed\s+return\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Baseline:
    warn_count: int = 0
    note: str = ""


def load_baseline() -> Baseline:
    if not BASELINE_PATH.exists():
        return Baseline()
    raw = yaml.safe_load(BASELINE_PATH.read_text(encoding="utf-8")) or {}
    return Baseline(warn_count=int(raw.get("warn_count", 0)), note=str(raw.get("note") or ""))


def write_baseline(warn_count: int, existing: Baseline) -> None:
    """Shrinking ratchet -- never raised above the existing baseline."""
    new_warn = min(warn_count, existing.warn_count) if existing.warn_count else warn_count
    BASELINE_PATH.write_text(
        "# Baseline for check_artefact_disclosure.py -- performance-figure WARN patterns\n"
        "# across the six client artefacts (operator ruling, client_artefact_remediation_\n"
        "# 2026_08_18.md § E). Shrinking ratchet: a live count ABOVE this fails (a NEW\n"
        "# warn-pattern landed); lower it (--update-baseline) once reviewed hits are\n"
        '# confirmed benign (e.g. "net carry (annualised, bps)") or fixed. NEVER hand-raise.\n'
        "#\n"
        "# The HARD set (banned client name, maturity-label leak, internal route leak) has\n"
        "# NO baseline -- any hit is a fail, always. This file only tracks the WARN class.\n"
        "#\n"
        "# SSOT: /codex/14-customer-journeys/_ssot-rules/06-show-dont-show-discipline.md.\n"
        f"note: Seeded 2026-08-18 alongside the checker.\n"
        f"warn_count: {new_warn}\n",
        encoding="utf-8",
    )


def target_files() -> list[Path]:
    if not ARTEFACT_DIR.exists():
        return []
    return sorted(ARTEFACT_DIR.glob("*.html"))


def _line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def scan_file(p: Path) -> tuple[list[str], list[str]]:
    """(hard_violations, warn_violations) for one file's raw text."""
    text = p.read_text(encoding="utf-8")
    rel = p.relative_to(PM_DIR).as_posix()
    hard: list[str] = []
    warn: list[str] = []

    for m in BANNED_CLIENT_NAME_RE.finditer(text):
        hard.append(f"{rel}:{_line_of(text, m.start())}: banned client name '{m.group(0)}'")
    for m in MATURITY_LEAK_RE.finditer(text):
        hard.append(f"{rel}:{_line_of(text, m.start())}: internal maturity label '{m.group(0)}' leaked verbatim")
    for m in INTERNAL_ROUTE_RE.finditer(text):
        hard.append(f"{rel}:{_line_of(text, m.start())}: internal ops route '{m.group(0)}'")
    for m in PERFORMANCE_FIGURE_RE.finditer(text):
        warn.append(f"{rel}:{_line_of(text, m.start())}: performance-figure pattern '{m.group(0)}' -- review")

    return hard, warn


def main() -> int:
    quiet = "--quiet" in sys.argv
    update = "--update-baseline" in sys.argv

    files = target_files()
    hard_violations: list[str] = []
    warn_violations: list[str] = []
    for p in files:
        h, w = scan_file(p)
        hard_violations.extend(h)
        warn_violations.extend(w)

    baseline = load_baseline()

    if not quiet:
        print(f"Artefact disclosure check ({len(files)} file(s) scanned):")
        print()
        for v in hard_violations:
            print(f"  HARD  {v}")
        for v in warn_violations:
            print(f"  WARN  {v}")
        print()

    hard_n, warn_n = len(hard_violations), len(warn_violations)
    hard_ok = hard_n == 0
    warn_ok = warn_n <= baseline.warn_count

    print(f"{'✅' if hard_ok else '❌'} check_artefact_disclosure (hard): {hard_n} violation(s) (zero-tolerance)")
    print(
        f"{'✅' if warn_ok else '❌'} check_artefact_disclosure (warn): {warn_n} performance-figure pattern(s) "
        f"(baseline {baseline.warn_count})"
    )

    if update:
        write_baseline(warn_n, baseline)
        print(f"Baseline updated: warn_count={min(warn_n, baseline.warn_count or warn_n)}")

    return 0 if (hard_ok and warn_ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
