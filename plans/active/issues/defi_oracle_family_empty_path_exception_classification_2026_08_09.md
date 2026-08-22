---
doc_type: issue
title:
  DeFi RPC-oracle families (Aave, Chainlink) aggregate-zero-path exception ambiguity + Pyth 404 fidelity — deferred
  design questions from defi_clean_path_fetch_evidence_fidelity_scope_2026_07_28.md's DIAG findings
summary: >-
  defi_clean_path_fetch_evidence_fidelity_scope_2026_07_28.md's Aave/Alchemy and Chainlink/Pyth DIAG todos (checkboxes
  2-3, both closed) each surfaced a genuine follow-up in PROSE only — never converted to a tracked `- [ ]` todo, which
  the archival-discipline codex doc (§2, "every follow-up is a canonical todo, never prose") flags as its own defect
  class. Filed here per that doc's step-1 archival-ritual requirement (migrate any deferred item into a real tracked
  todo before archiving the source doc). Three items: (1) Aave's per-reserve RPC-call swallow can hide a real error
  behind a fabricated clean empty-path — a design question (which signal to surface), same shape as the source doc's
  already-resolved item 5. (2) Chainlink's per-feed swallow has the identical ambiguity. (3) Pyth's clean-empty path
  discards an already-in-hand HTTP status, including one case where a real 404 (no data at that timestamp) is
  misreported as a synthesized 200 — this one is bounded/CODE-eligible, not a design question.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [defi, honest-coverage, fetch-evidence, fidelity, manifest, rpc, oracle]
related:
  [
    /plans/archive/2026_08/issues/defi_clean_path_fetch_evidence_fidelity_scope_2026_07_28.md,
    /codex/02-data/honest-absence-downstream-handling.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
  ]
created: "2026-08-09"
author: slot-6
last_updated: "2026-08-09"
source:
  defi_clean_path_fetch_evidence_fidelity_scope-003 dispatch (slot-6), migrated during that doc's archival per
  /codex/12-agent-workflow/plan-completion-and-archival-discipline.md step 1
resolved_by:
locked_by:
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /codex/02-data/honest-absence-downstream-handling.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    market-tick-data-service/market_tick_data_service/cli/handlers/_aave_oracle_collection.py,
    market-tick-data-service/market_tick_data_service/cli/handlers/oracle_prices_handler.py,
  ]
---

# DeFi RPC-oracle families — deferred aggregate-zero-path + Pyth fidelity follow-ups

## What I found

`defi_clean_path_fetch_evidence_fidelity_scope_2026_07_28.md`'s Aave/Alchemy DIAG (checkbox 2) and Chainlink/Pyth DIAG
(checkbox 3) are both closed (read-only research, done as scoped), but each closed-checkbox's own text describes a
concrete follow-up that was never converted into a real `- [ ]` todo — a prose deferral, exactly the anti-pattern
`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` §2 names.

1. **Aave** (`_aave_oracle_collection.py`'s `query_aave_reserves`/`collect_aave_rows`): a per-reserve `except Exception`
   swallows and logs any single RPC failure without surfacing it. If every reserve call for a given day fails this way,
   the shard still reaches `record_aave_empty`'s clean path with a fabricated 200 — indistinguishable from "genuinely
   queried, all returned zero." Proposed alternative (from the source doc): classify+thread the caught exception type
   (transport `HTTPError` w/ real status vs JSON-RPC `Web3RPCError`/`ContractLogicError` vs connection/timeout) into
   `fetch_evidence`, OR surface per-reserve exception counts up so the empty-path recorder can distinguish the two
   cases. This is a genuine human design call (which signal, and how to plumb it through 6 independent per-reserve RPC
   calls) — same shape as the source doc's already-resolved item 5 (governance dual-source merge).
2. **Chainlink** (`oracle_prices_handler.py::_query_chain_feeds`): identical shape — a per-feed `except Exception`
   swallow means an all-feeds-errored chain still reaches `_record_chainlink_empty`'s clean path with a fake 200. Same
   design question as Aave (classify+thread exception type, or surface per-feed exception counts).
3. **Pyth** (`oracle_prices_handler.py::_fetch_pyth_prices`/`_fetch_pyth_prices_at_timestamp`): DIFFERENT — the real
   HTTP status IS already in local scope at the fetch call site (`_hermes_latest_get` returns `resp.status` directly)
   but is discarded on the clean-empty `record_zero_rows` path, which falls through to the generic synthesized 200.
   Concrete correctness wrinkle: `_fetch_pyth_prices_at_timestamp` returns `[]` (not an error) on a genuine Hermes 404
   ("no data at this timestamp") — that flows to the same clean-empty path, so the synthesized `http_status=200` is
   provably wrong in that specific case (real status was 404). This one is bounded/CODE-eligible, not a design question
   — purely a threading exercise (widen the two functions' return signature to also carry the resolved `http_status`,
   thread it into `build_fetch_evidence(http_status=..., source="pyth_hermes")` at the `_emit_pyth_manifest` call site),
   no new exception-narrowing needed.

## Why it matters

Items 1-2 are a real (if minor) honest-absence fidelity gap: an all-calls-errored aggregate shard is currently
indistinguishable from a genuinely-empty one in the manifest. Item 3 is a provable factual inaccuracy in already-fetched
data (a real 404 recorded as a fake 200), not just an imprecision — same class of gap the source doc's
`governance_adapter.py` correctness fix (item 1) closed for the subgraph family. None are urgent (all three are dormant
unless the underlying family goes fully dark for a day, or a Hermes-404 no-data window occurs), which is why this stays
P3.

## Recommended decision

- [ ] [CODE] P3. Classify + thread the caught exception type (transport `HTTPError` w/ real status vs JSON-RPC
      `Web3RPCError`/`ContractLogicError` vs connection/timeout) into `fetch_evidence` for Aave's per-reserve RPC
      swallow (`_aave_oracle_collection.py`) and Chainlink's per-feed swallow
      (`oracle_prices_handler.py::_query_chain_feeds`). Per D63 ruling (2026-08-22): classify+thread — mirrors the
      shipped Pyth `http_status` pattern (market-tick-data-service@480e76dd) and reuses existing machinery.
      (repo: market-tick-data-service)
- [x] [CODE] P2. **Thread Pyth's already-in-hand HTTP status into the clean-empty path** (market-tick-data-service):
      widen `_fetch_pyth_prices`/`_fetch_pyth_prices_at_timestamp`'s return signature to also carry the resolved
      `http_status` (200 on the normal empty-after-filter path, 404 on the Hermes no-data-at-timestamp case), and thread
      it into `_emit_pyth_manifest`'s `record_zero_rows` call via
      `build_fetch_evidence(http_status=..., source="pyth_hermes")` instead of falling through to the generic
      synthesized 200. **Done when**: a test proves a simulated Hermes 404 (no data at timestamp) records
      `http_status == 404` on the clean-empty path, and a genuine empty-after-filter 200 response still records
      `http_status == 200`; existing behavior otherwise unchanged. — **market-tick-data-service@480e76dd**
      (`live-defi-rollout`, verified ancestor of origin). Implemented per operator-approved option A (see Progress Log):
      the 404 signal folds into `_collect_pyth_rows()`'s existing boolean return slot rather than widening
      `_emit_pyth_manifest`/`process` (both were already at their exact 900-line-file/50-line-method QG caps — any
      net-positive line addition there broke the gate; `_collect_pyth_rows()` had headroom). 62/62 tests green, QG
      sentinel `480e76dd7…` == HEAD, quickmerge Pass 2 landed + ancestry-verified.

## Codex SSOTs

- `/codex/02-data/honest-absence-downstream-handling.md` (the 4-state `capture_status` contract this fidelity work sits
  inside).
- `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` (why this doc exists — migrating a prose
  deferral into a real todo per the archival ritual's step 1).

## Progress Log

- **defi_clean_path_fetch_evidence_fidelity_scope-003 dispatch (slot-6, 2026-08-09)**: filed while archiving
  `defi_clean_path_fetch_evidence_fidelity_scope_2026_07_28.md` (all 6 of its own todos done, unlocked —
  archival-eligible per the codex ritual). That doc's checkboxes 2-3 each described a genuine follow-up only in prose;
  migrated both here as real todos before the archival landed.
- **context-scout 2026-08-09**: re-scouted; fixed a wrong path (`_aave_oracle_collection.py` actually lives under
  `cli/handlers/`, not `market_interface/adapters/defi/`), swapped `/plans/active/task_template.md` for
  `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` (cited in the doc's own "Codex SSOTs" section
  but missing from context_scope), context_scope now 4 entries.
- **2026-08-09, slot-7 (dispatched todo P2 — Pyth http_status threading)**: **BLOCKED — the todo's own "no new
  exception-narrowing needed" premise is wrong; implementing it literally would introduce a live regression, not a
  fix.** Traced the full path: `record_zero_rows(fetch_evidence=...)` → `_resolve_zero_rows_reason_and_evidence`
  (`_defi_manifest.py`) resolves reason to `SOURCE_RETURNED_ZERO` for Pyth (no launch-date match) → `record_empty`
  passes the evidence to `ManifestWriter.record_empty`, which is KEYSTONE-gated: for `reason="SOURCE_RETURNED_ZERO"` it
  REQUIRES `FetchEvidence.proves_honest_absence()` (`unified_api_contracts/canonical/crosscutting/honest_coverage.py`)
  else hard-raises `UnprovenHonestAbsenceError` (only `EXPECTED_*` reasons are exempt). `proves_honest_absence()` hard-
  gates `200 <= http_status < 300` — there is NO way to pass a raw `http_status=404` through this specific path (SOURCE_
  RETURNED_ZERO) without it being rejected, regardless of `error_signal`. So threading the real Hermes 404 straight into
  `build_fetch_evidence(http_status=404, ...)` → `record_zero_rows(fetch_evidence=...)` as the todo literally describes
  would convert every genuine "Hermes has no data at this exact timestamp" case (existing, deliberate, tested behavior —
  `test_historical_404_returns_empty`, docstring "HTTP 404 from historical endpoint returns empty list (honest
  absence)") from a clean zero-row record into a crashed `process()` call. Cross-checked against
  `/codex/02-data/honest-absence-downstream-handling.md`'s own Class-2 examples (dex-swaps schema-error 404, Understat
  2019 404) — those are the OPPOSITE case (a 404 that WRONGLY got treated as clean empty, fixed by routing it to
  `record_failed`); Pyth's archive-404 is architecturally different — Hermes uses 404 to mean "no price existed at this
  specific instant," which for a point-in-time query IS a legitimate honest-absence answer, not a fetch failure, and the
  existing code/tests already encode that deliberately. The real gap the issue's summary correctly identifies (a genuine
  404 recorded as a fabricated 200) is real, but literally threading the raw status through the existing
  `SOURCE_RETURNED_ZERO` path is not a safe fix for it. **Options** (filing `/blocked`, not deciding unilaterally — this
  is a manifest-reason/downstream-analytics classification call, not a mechanical threading exercise):
  - A (recommended): for the archive-404-specifically case, call
    `recorder.record_empty(reason= "EXPECTED_KNOWN_SOURCE_GAP", ...)` DIRECTLY in `_emit_pyth_manifest` — bypassing
    `record_zero_rows`'s automatic `SOURCE_RETURNED_ZERO` reason resolution — mirroring the exact pattern this same
    function already uses one branch above for `pyth_pre_archive`. `EXPECTED_*` reasons are keystone-exempt (no
    `FetchEvidence` required), so this both avoids the crash AND correctly distinguishes "Hermes confirmed no data at
    this instant" from the routine "queried successfully, genuinely zero after IS-filter" `SOURCE_RETURNED_ZERO` case —
    arguably a MORE honest fix than the literal todo, since it changes the recorded `capture_status` reason (not just an
    evidence field) to reflect that this is a known, permanent, source-native gap shape rather than an ordinary empty
    query.
  - B: ship only the harmless half — thread `http_status=200` explicitly through the already-200-only success path (no
    behavior change, since it was already implicitly 200) — and leave the archive-404 case's `http_status=200`
    misrecording exactly as-is (defer the actual correctness fix). Minimal/safe but does not close the issue's own
    stated gap.
  - C: relax `FetchEvidence.proves_honest_absence()` in `unified_api_contracts` to accept a narrower
    source-native-confirmed-empty 4xx allowlist — a cross-repo UAC contract change, out of this task's single-repo scope
    and a bigger blast radius (affects every `SOURCE_RETURNED_ZERO` caller fleet-wide). Recommend A: smallest,
    single-repo, safe, and reuses an established pattern already in the same function. Did NOT implement any of the
    three — filing `/blocked` for the reason-classification call per the craft rule (data- correctness surprise the plan
    didn't anticipate → escalate, don't absorb). No code shipped this pass.
- **2026-08-09, slot-7 — operator answered `BLK-7eaa58e4`: option A confirmed** (route the archive-404 case through
  `record_empty(reason="EXPECTED_KNOWN_SOURCE_GAP", ...)`, keystone-exempt; explicitly rejected B — "CLAUDE.md always
  prefers the fuller solution over shipping only the harmless half" — and C — cross-repo UAC blast radius too big for a
  single-source quirk). **Implemented in market-tick-data-service** (2 commits locally,
  `fix(defi): thread Pyth Hermes archive http_status into the empty-path manifest classification` +
  `refactor(defi): fold Pyth 404-known-gap into _collect_pyth_rows's existing boolean, back within line caps`):
  `_fetch_pyth_prices`/`_fetch_pyth_prices_at_timestamp` widened to return `(rows, http_status)`; `_collect_pyth_rows`
  folds `http_status == 404` into its existing boolean return slot (renamed in spirit to "known_source_gap" — same tuple
  position, no signature change needed downstream) so `_emit_pyth_manifest` and `process()` need ZERO changes and stay
  at their pre-existing 50-line-cap / 900-line-cap ceilings (both were already AT the cap before this todo — the first
  implementation attempt threading a new `pyth_http_status` param straight into `_emit_pyth_manifest` blew both caps by
  several lines and needed reworking). 62/62 targeted unit tests pass (`test_oracle_prices_handler.py` +
  `test_cf11_swallow_remediation.py`), including 3 new tests proving the "Done when" acceptance criteria: a simulated
  Hermes 404 records `http_status == 404` (`_fetch_pyth_prices_at_timestamp` return value) and folds into
  `known_source_gap=True`; a genuine 200 keeps `known_source_gap=False`; and
  `_emit_pyth_manifest(pyth_pre_archive=True, ...)` (the shared code path both cases now route through) records
  `reason="EXPECTED_KNOWN_SOURCE_GAP"` via `record_empty`, never `record_zero_rows`. Full `quality-gates.sh` (Pass 1)
  was queued/running on this extremely-loaded shared host at compaction time — NOT yet confirmed green, NOT yet shipped
  via quickmerge. **P2 checkbox intentionally left unflipped** — `done_definition` requires "checkbox flipped in plan +
  code shipped", and code is committed locally only, not yet on `origin/live-defi-rollout`. Next session/tick: re-run
  `bash scripts/quality-gates.sh` in `market-tick-data-service`, fix anything genuinely red (the two known-baseline `⚠️`
  warnings — STEP 5.5 broad-except, STEP 5.101 empty-string-fallback — are pre-existing and not from this diff, do not
  treat as blocking), ship via `quickmerge --agent --files` once green, THEN flip this checkbox with the
  `market-tick-data-service@<sha>` evidence.
- **context-scout 2026-08-17**: populated/refreshed context_scope (4 entries)
- **context-scout 2026-08-20**: refreshed context_scope (4 entries)
- **2026-08-22 — ruling D63 (Oracle empty-path classification)**: ADOPTED-REC 2026-08-21 (autonomous-dispatch
  authority, AUTONOMOUS_AGENT_RULES rule 2): Classify+thread — mirrors the shipped Pyth http_status pattern and reuses
  existing machinery. Source: /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.
