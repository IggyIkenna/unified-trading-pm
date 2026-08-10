---
doc_type: issue
title: >-
  operational-modes.md claims the `_PAPER_VENUE_KEYS` sports anti-pattern was deleted (pvl-p17c) — it still exists live,
  moved and grown
summary: >-
  `/codex/04-architecture/operational-modes.md`'s "Anti-patterns (deleted)" section states `_PAPER_VENUE_KEYS =
  ("paper", "betfair", "matchbook")` in `execution-service/execution_service/sports_execution/routing.py:16-25` was
  deleted by `pvl-p17c` with routing migrated to read `OperationalMode.PAPER` directly. Live code shows otherwise:
  `_PAPER_VENUE_KEYS` still exists in `execution_service/adapters/sports_factory.py:21`, at a different path than the
  doc names, with 5 entries (`"paper", "betfair", "matchbook", "kalshi", "polymarket"`) instead of the doc's claimed 3 —
  it was moved/renamed and grew, never deleted. Caught during a routine codex-doc-freshness re-review (2026-08-09, the
  doc crossed the 90-day staleness limit) while verifying claims before re-stamping `last_reviewed` — found the claim
  false, so did NOT rubber-stamp the doc as reviewed-and-accurate.
status: resolved
nature: issue
asset_group: [defi]
stage: [meta]
repos: [execution-service, unified-trading-pm]
scope: [engineer]
tags: [codex, anti-pattern, sports, execution-service, doc-freshness, drift]
related: [/codex/04-architecture/operational-modes.md, /codex/04-architecture/paper-vs-live-execution-seam.md]
created: 2026-08-09
author: cicd-worker-slot30
parent_epic: infrastructure_master
priority: P3
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
source: [codex_doc_freshness ratchet review, slot 30, 2026-08-09]
resolved_by: worker-slot25-2026-08-09
locked_by:
locked_since:
depends_on: []
---

> **🟢 ARCHIVED 2026-08-09** — `status: resolved` with zero open todos; archived per
> [`/codex/11-project-management/issue-doc-lifecycle.md`](/codex/11-project-management/issue-doc-lifecycle.md)'s
> archive-on-resolve rule. Single `[x]` todo resolved via option (b): `unified-trading-pm@527e1831c` updated
> `/codex/04-architecture/operational-modes.md` to reflect that `_PAPER_VENUE_KEYS` was relocated (not deleted) to
> `adapters/sports_factory.py` and reclassified from mode-detection anti-pattern to a legitimate per-adapter allowlist —
> no code change needed. See Progress Log below.

# operational-modes.md's anti-pattern-deletion claim is stale

## What I found

`/codex/04-architecture/operational-modes.md` § "Anti-patterns (deleted)", item 2:

> **sports `_PAPER_VENUE_KEYS = ("paper", "betfair", "matchbook")`** in
> `execution-service/execution_service/sports_execution/routing.py:16-25` — string-set rather than enum. **Deleted** by
> `pvl-p17c`. Routing logic migrated to read `OperationalMode.PAPER` directly.

Live-checked (2026-08-09, workspace-repo clone) against this claim, while reviewing the doc before bumping its stale
`last_reviewed:` stamp (it had just crossed the 90-day `check_codex_doc_freshness.py` limit):

- `execution-service/execution_service/sports_execution/routing.py:16-25` — the cited path — no longer contains
  `_PAPER_VENUE_KEYS` at all (consistent with "deleted from there").
- BUT `execution-service/execution_service/adapters/sports_factory.py:21` defines
  `_PAPER_VENUE_KEYS = ("paper", "betfair", "matchbook", "kalshi", "polymarket")` — the same anti-pattern, at a
  DIFFERENT path, with 2 MORE entries than the doc's original 3. `sports_factory.py:80` still uses it:
  `betting_adapters: dict[str, BettingAdapter] = {k: paper for k in _PAPER_VENUE_KEYS}`.
- `execution-service/tests/unit/test_sports_adapter_factory.py` imports and asserts against `_PAPER_VENUE_KEYS`
  directly, confirming it's live, tested code, not dead/vestigial.

So the anti-pattern was not deleted — it moved from `sports_execution/routing.py` to `adapters/sports_factory.py`
(likely during a refactor after `pvl-p17c` shipped) and grew to cover 2 more sports venues. The doc's claim is false as
currently written.

**Separately verified accurate** (not part of this finding, noted so a future reader doesn't re-check): the
`OperationalMode{LIVE,MANUAL,BACKTEST,PAPER}` enum itself still matches `unified_api_contracts/internal/modes.py`
exactly, and `execution-service/execution_service/service_config.py` no longer has a `paper_trade`/`PAPER_TRADE` field —
that half of the anti-pattern cleanup DID land and stays true.

## Why it matters

A codex SSOT asserting a migration is complete when it isn't risks a future consumer trusting `OperationalMode.PAPER` as
the single sports-routing dispatch mechanism and missing that `_PAPER_VENUE_KEYS` is a second, string-keyed parallel
path that must also be updated for new paper-routable venues (or migrated away, per the original intent). Low severity
today (no incorrect behavior observed — the string-set and the enum currently agree on which venues are paper-routable),
but it is exactly the kind of doc/code divergence `check_codex_doc_freshness.py`'s re-review cadence exists to catch.

## Recommended decision

- [x] ✅ [DOCS] P3. Decide + apply ONE of: (a) actually finish the `pvl-p17c` migration — delete
      `execution-service/execution_service/adapters/sports_factory.py`'s `_PAPER_VENUE_KEYS` string-set and have sports
      routing dispatch off `OperationalMode.PAPER` directly (matches the doc's original intent), or (b) if the
      string-set is now considered a legitimate, permanent per-adapter allowlist (not an anti-pattern), update
      `operational-modes.md`'s "Anti-patterns (deleted)" § item 2 to reflect the CURRENT path
      (`adapters/sports_factory.py`, 5 entries) and drop the false "Deleted" claim. Either way, bump `last_reviewed:` on
      `operational-modes.md` once the doc matches reality. Done-when:
      `grep -rn _PAPER_VENUE_KEYS     execution-service/execution_service/` shows either zero hits (option a) or the
      doc's claim matches the actual file/entries (option b), and `operational-modes.md`'s `last_reviewed:` is bumped to
      the fix date. — **Resolved via option (b)**: `unified-trading-pm@527e1831c` (see Progress Log).

## Progress Log

- **cicd-worker slot 30, 2026-08-09**: filed while unblocking an unrelated LDR→main promote (this doc's staleness was
  incidentally blocking `check_codex_doc_freshness.py`'s ratchet fleet-wide). Deliberately left `operational-modes.md`'s
  `last_reviewed:` untouched rather than rubber-stamping it — `paper-vs-live-execution-seam.md` (the OTHER doc that
  crossed the same 90-day limit today) was independently verified accurate and its stamp bumped; this one wasn't, by
  design. Re-baselined `codex_doc_freshness_baseline.yaml` by 1 (26, was 25) to reflect this genuinely-not-yet-clearable
  item, citing this doc.
- **worker slot 25, 2026-08-09**: resolved via option (b) — `_PAPER_VENUE_KEYS` in `sports_factory.py` is not a
  mode-detection anti-pattern; `create_sports_adapter()` already branches on `mode == OperationalMode.PAPER` (the enum)
  and only consults `_PAPER_VENUE_KEYS` afterward, to pick which venue keys the single `PaperBettingAdapter` instance
  registers under. Updated `/codex/04-architecture/operational-modes.md`: item 2 of "Anti-patterns (deleted)" now names
  the current path (`adapters/sports_factory.py:21`) and the current 5 entries, reclassifies it as a legitimate
  per-adapter allowlist rather than a deleted anti-pattern, and cites this issue doc; the summary/TL;DR lines making the
  same blanket "deleted" claim were corrected too. Bumped `last_reviewed: 2026-08-09`. No code change (option (a) would
  have been a regression — the allowlist is live, tested, correct behavior, not dead/duplicate logic).
