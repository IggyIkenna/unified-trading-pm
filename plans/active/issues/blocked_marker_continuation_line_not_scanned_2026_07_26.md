---
doc_type: issue
title:
  "`BLOCKED-*` marker only stops re-dispatch when it's on the checkbox's OWN physical line — ~50 fleet todos have it
  only in continuation text"
summary: >-
  Found while triaging why `sports_satellite_ao_dispatch_batch5-014` (odds-api 3-league backfill, gated on a deactivated
  API key) was dispatched a THIRD time despite two prior slots (4, 10) documenting it as BLOCKED-CREDENTIALS.
  `regen_backlog_from_plan.py`'s `_parse_open_todos` matches `_NON_DISPATCHABLE_RE` only against the single physical
  line `_UNCHECKED_RE` matched (the checkbox's own line) — never against continuation/annotation paragraphs written
  underneath it, which is the common authoring pattern when a worker adds a `BLOCKED-*` note AFTER the original todo
  text already exists. A corpus-wide grep across `plans/active/*.md` found ~50 unchecked checkboxes where a
  `BLOCKED-(CREDENTIALS|OPERATOR|BILLING|UPSTREAM-OUTAGE|PLAYWRIGHT|JURISDICTION)` marker exists only in text below the
  checkbox, not on the checkbox's own line — every one of those is a live re-dispatch risk, not just the sports case
  that surfaced it.
status: open
nature: notes
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [dispatch, backlog-regen, blocked-marker, worker-lifecycle, fleet-wide]
related:
  [
    /plans/active/issues/sports_odds_api_key_deactivated_2026_07_26.md,
    /plans/active/sports_satellite_ao_dispatch_batch5_2026_07_26.md,
    /plans/archive/issues/backlog_blocked_marker_stale_brief_redispatch_2026_07_08.md,
  ]
created: 2026-07-26
last_updated: 2026-07-26
parent_epic: agent_operating_framework_master
priority: P2
source: [sports_satellite_ao_dispatch_batch5-014]
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
estimate_class: refactor
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.4
assigned_role: backend_engineer
drift_direction: advance-code
locked_since:
depends_on: []
supersedes:
superseded_by:
---

# BLOCKED-\* marker not scanned outside the checkbox's own line

## What I found

`sports_satellite_ao_dispatch_batch5-014` was dispatched to me (slot 6) as its THIRD worker: slot-4 found the odds-api
key `DEACTIVATED_KEY` and wrote a `**BLOCKED-CREDENTIALS 2026-07-26 (slot-4)**` annotation paragraph directly below the
todo's checkbox line in `plans/active/sports_satellite_ao_dispatch_batch5_2026_07_26.md`; slot-10 was dispatched again,
re-verified the key was still dead, and correctly reasoned that the fix was the `BLOCKED-<TOKEN>` marker taxonomy — but
applied it only to a _separate_ sub-todo it had itself derived (inside
`issues/sports_odds_api_key_deactivated_2026_07_26.md`), not the original plan checkbox. I was dispatched a third time
against the SAME original checkbox, re-verified the key was still dead myself, and traced why: the checkbox's own line
(`plans/active/sports_satellite_ao_dispatch_batch5_2026_07_26.md:261`,
`- [ ] [DATA] P2. Backfill the 3 odds-api league gaps...`) never contained the marker text — it was written a few lines
below, in prose. Read `server/regen_backlog_from_plan.py`'s `_parse_open_todos`
(`for raw_line in text.splitlines(): ... m = _UNCHECKED_RE.match(line) ... description = m.group(1) ...` then
`_NON_DISPATCHABLE_RE.search(description)`) — the loop is strictly per-line; `description` is ONLY the text captured
from the single line the checkbox regex matched. Continuation paragraphs (any subsequent indented/prose lines that are
visually part of the same todo item) are never concatenated into `description`, so a marker written there is invisible
to `_NON_DISPATCHABLE_RE` no matter how clearly a human reader would see it as gating the todo.

This is DIFFERENT from the already-resolved `backlog_blocked_marker_stale_brief_redispatch_2026_07_08.md` (archived,
`resolved_by: agent-orchestrator@3995384`) — that bug was a stale-`brief`-reconcile race for a marker added to a todo
AFTER it was already `queued`/`dispatched`, fixed by `task_still_dispatchable()` re-checking the plan file on skip. That
fix re-reads the plan file correctly, but it re-runs the SAME `_parse_open_todos` line-only match — so it has no way to
see a marker sitting in continuation text either. The 2026-07-08 fix and this bug are orthogonal; fixing one does not
fix the other.

**Blast radius**: a corpus grep confirms this is not a one-off. Across `plans/active/*.md`, ~50 unchecked checkboxes
have a `BLOCKED-(CREDENTIALS|OPERATOR|BILLING|UPSTREAM-OUTAGE|PLAYWRIGHT|JURISDICTION)` marker present only in
continuation text below the checkbox, never on the checkbox's own line (method: for each unchecked checkbox, scan
forward until the next `- [` line, flag if the marker appears in that span but not on the checkbox line itself).
Examples (not exhaustive — see the grep recipe below): `ao_satellite_ao_dispatch_batch1_2026_07_26.md:178`,
`cefi_satellite_ao_dispatch_batch1_2026_07_25.md:214`, `defi_migration_audit_log_2026_07_24.md:271`,
`sports_satellite_ao_dispatch_batch2_2026_07_24.md:690`, `tradfi_satellite_ao_dispatch_batch4_2026_07_26.md:211`. I did
NOT mass-edit these — many are likely already `done`/superseded/moot (the pattern-match alone doesn't prove the todo is
still actively re-dispatching), and a corpus-wide edit across every AG's plans is its own properly-scoped audit, not a
side effect of one sports P2 task. This doc exists so that audit is tracked, not lost.

## Why it matters

Every one of these ~50 todos is a live re-dispatch risk identical to the sports case: a worker discovers the block,
documents it thoroughly (often at real cost — a launched VM, a credential probe, a root-cause trace), and the very next
regen tick or dispatch cycle hands the SAME todo to a fresh slot with zero memory of the prior finding, who then has to
re-read the whole annotation trail just to re-derive "still blocked, don't redo this" — pure wasted slot-cycles, and it
compounds: this sports todo alone burned 3 separate dispatches (4, 10, 6) doing the same credential re-check. The
taxonomy comment in `regen_backlog_from_plan.py` documents `BLOCKED-*` as the mechanism specifically meant to prevent
exactly this — the guarantee is false whenever the marker isn't on the checkbox's own line, which is the more natural
place for a worker to write it (the original todo text is usually someone else's; annotating below it, not editing it in
place, is the lower-risk edit).

## Recommended decision

A backend-engineer-craft worker (agent-orchestrator repo, Python) should extend `_parse_open_todos` in
`server/regen_backlog_from_plan.py` to scan the FULL todo block (the checkbox line + every immediately-following line
that is more-indented / not itself a new `- [ ]`/`- [x]` item, i.e. the same continuation-detection boundary this issue
doc's own grep recipe used) for `_NON_DISPATCHABLE_RE`, not just the checkbox's single matched line — while still using
only the checkbox's own line as the `description`/`brief` text (continuation text should gate dispatch, not become part
of the stored brief string, to avoid unrelated brief-matching churn). This is the smallest fix that closes the gap for
every current and future todo, without requiring a corpus-wide rewrite of existing plan text.

Add a regression test: a todo whose checkbox line has no marker but whose continuation paragraph contains
`BLOCKED-CREDENTIALS` → `_parse_open_todos` excludes it from the returned open-todos list (same assertion shape as the
existing marker tests, just with the marker moved to a continuation line in the fixture).

Do NOT fix by mass-editing the ~50 existing occurrences — that's a separate, properly-scoped follow-up (many may already
be resolved) once the parser fix lands; re-derive candidates via the grep recipe above against a fresh _parse_open_todos
read instead of hand-auditing every plan.

- [x] ✅ [BACKEND] P2. Extend `_parse_open_todos` (`server/regen_backlog_from_plan.py`) to scan a todo's full
      continuation block for `_NON_DISPATCHABLE_RE`, not just its checkbox's own physical line, while keeping
      `description`/`brief` derived from the checkbox line only. Add the regression test described above. (repo:
      agent-orchestrator) — agent-orchestrator@e856b56: added `_TODO_BLOCK_BOUNDARY_RE` lookahead (stops at next
      checkbox item or header); `_NON_DISPATCHABLE_RE` now searches checkbox-line + continuation block,
      `description`/`brief` stays checkbox-line only; regression test
      `test_parse_skips_non_dispatchable_marker_in_continuation_text` added; full quality-gates.sh green (1758 passed, 1
      skipped).
- [x] [DATA] P3. Once the P2 fix above ships, re-run the corpus grep (recipe in this doc's "What I found" section)
      against live `plans/active/*.md` and spot-check a handful of the flagged todos to confirm the new parser now
      correctly excludes them from the backlog; file any genuinely-still-open ones as a small per-AG cleanup rather than
      editing 50 files in one sweep. (repo: unified-trading-pm) — ✅ DONE 2026-07-26. **Methodology correction**: the
      corpus-grep recipe as literally written above ("scan forward until the next `- [` line") is LOOSER than the
      shipped `_TODO_BLOCK_BOUNDARY_RE` (checkbox line **OR** markdown header), so re-running it verbatim over-counts —
      53 hits vs. the P2 fix's actual 30, because it scans past section headers into unrelated later prose (5/5
      spot-checked over-count hits traced to a `BLOCKED-*` string appearing in a totally different, later section, e.g.
      a Progress Log narrative or an unrelated table — see `cefi_4surface_migration_execution_log_2026_07_24.md:189`,
      whose naive-recipe "marker" was 550+ lines downstream past 3 intervening headers). Re-ran with the corrected
      (header-aware) boundary to match the shipped code exactly: **30 flagged checkboxes**, cross-checked each via a
      direct `_parse_open_todos()` call (exact description-string membership test, not substring matching) — **30/30
      correctly excluded** from the dispatchable backlog. The P2 fix is verified working end-to-end across the live
      corpus, not just a sample. Per-AG breakdown of the 30: cross-cutting 8, defi 6, sports 6, tradfi 6 (5 remaining +
      1 fixed below), prediction 2, cefi 1, meta 1.

      Content spot-check (10/30, one per AG + extra tradfi/sports coverage): 9 are genuinely still-open, correctly
          gated on a real, CURRENT blocker (`BLOCKED-CREDENTIALS`/`-OPERATOR-DECISION`/`-UPSTREAM-OUTAGE`) — no cleanup
          needed, working as intended. **1 genuine defect found and fixed**: `tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md`
          lines 144-155 (two `[AGENT] P2` VIX-wiring todos) quoted a **historical, since-RESOLVED** status verbatim —
          `(was: "... Status: **BLOCKED-OPERATOR-DECISION**.")` — inside prose explaining that the block was later lifted.
          The literal token match still fires on that quoted text even though the decision was made 2026-06-23 and the todo
          is real, unblocked, actionable work — a false-EXCLUSION side effect of the marker regex being purely textual
          (can't distinguish a live block from a quoted historical one). Reworded the quote to drop the literal
          `BLOCKED-<TOKEN>` shape while preserving the meaning (`unified-trading-pm` commit, this same batch); verified via
          direct `_parse_open_todos()` re-run that both VIX todos are now dispatchable. One more example of the SAME
          false-exclusion class was found (`tradfi_satellite_ao_dispatch_batch4_2026_07_26.md:211`, a `[REVIEW] P1` todo
          that quotes several OTHER todos' historical `BLOCKED-*` states while describing its own — genuinely still-open,
          real remaining work: it re-scoped 2 of 3 target P0 items already but the dangling issue-doc reference + the
          `related:` leading-slash convention fix are still outstanding per its own "Done when") — left untouched since it's
          already tracked by its own todo in its own plan; not duplicating that tracking here.

          **Conclusion**: no further per-AG cleanup doc needed — the 29 untouched flagged items are genuinely open and
          correctly excluded (working as designed); the 1 real defect found is fixed; the parser fix (`e856b56`) is
          confirmed correct across the full live corpus.

## Progress Log

- 2026-07-26 (slot 6): Filed after the 3rd dispatch of `sports_satellite_ao_dispatch_batch5-014` to a fresh slot despite
  it being documented BLOCKED-CREDENTIALS twice already. Fixed the immediate instance (moved the marker onto the
  checkbox's own line in `sports_satellite_ao_dispatch_batch5_2026_07_26.md`) and confirmed the general pattern via a
  fleet-wide grep (~50 hits). Not fixing the parser myself — Python backend/dispatcher code in agent-orchestrator is
  outside this slot's `data_engineering` craft scope; filed for a `backend_engineer` worker per RULES.md's craft-scoped
  escalation convention.
- 2026-07-26 (slot 4): Verified the P2 fix (`agent-orchestrator@e856b56`) end-to-end against the live corpus — 30/30
  flagged todos correctly excluded from the dispatchable backlog (direct `_parse_open_todos()` cross-check, not a
  re-implemented approximation). Found + fixed 1 real false-exclusion defect (historical marker text silently hiding
  genuinely-open work) in `tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md`. Full detail + per-AG breakdown in
  the flipped checkbox above. `quickmerge --agent` not applicable (doc-only plan repo) — shipped via direct push per the
  cross-repo PM plan-flip carve-out.
