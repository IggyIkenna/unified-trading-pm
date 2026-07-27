---
doc_type: issue
title:
  Root-cause WHY quality-gates.sh's function/class/method SIZE CHECK didn't block the 2026-07-16 sports-orchestrator
  function-size regression at commit time (migrated deferred item)
summary:
  "Migrated forward from `sports_reference_function_size_qg_regression_2026_07_16.md` (archived 2026-07-25 with 0
  remaining blocking items) — that doc's acceptance item 2 ('root-cause WHY the size gate didn't block whichever commit
  introduced this — sentinel-skip vs scoped-gate run — and note the fix/process change so future same-day sports commits
  can't silently regress this ratchet again') was explicitly confirmed STILL open 'in spirit' by its own 2026-07-23
  RE-TRIAGE, even though the underlying 3 functions were independently decomposed back under the size limit by
  `instruments-service@ac22305c` (2026-07-21) — so the symptom is fixed but the PROCESS gap (how a same-day sports
  commit regrew 3 functions past MAX_FUNCTION_LINES/MAX_METHOD_LINES without the size-check phase catching it at commit
  time) was never investigated. Low severity (P3) — this is a process/tooling-hygiene question, not a live
  data-correctness or shipping blocker; the archived source doc's own RE-TRIAGE explicitly deferred it rather than
  resolving it. Thematically adjacent to `qg_sentinel_environment_blind_2026_07_23.md` (a DIFFERENT sentinel-skip
  mechanism — ENVIRONMENT-dimension binding — surfaced 2026-07-23) but not the same root cause; that doc's fix (bind
  configuration into the sentinel hash) may or may not also explain this one, which is exactly the open question here."
status: open
nature: issue
asset_group: [sports]
stage: [meta]
repos: [instruments-service, unified-trading-pm]
scope: [engineer]
tags: [code-quality, function-size, qg-ratchet, sentinel-skip, quality-gates, sports, migrated-deferred]
related:
  - /plans/archive/issues/sports_reference_function_size_qg_regression_2026_07_16.md
  - /plans/active/issues/qg_sentinel_environment_blind_2026_07_23.md
  - /plans/archive/issues/instruments_service_codex_compliance_ceiling_drift_2026_07_20.md
  - /plans/active/sports_consolidated_closeout_2026_07_19.md
created: 2026-07-25
last_updated: 2026-07-25
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.36
assigned_role: infra
drift_direction: advance-code
resolved_by:
locked_by:
locked_since:
depends_on: []
source:
  "archival-ritual follow-up sweep 2026-07-25, migrating the one genuinely-unresolved deferred item out of
  sports_reference_function_size_qg_regression_2026_07_16.md before archiving it (per the archival ritual's 'migrate
  DEFERRED items before archiving' step) — never let real deferred work vanish silently into the archive"
---

# Root-cause the 2026-07-16 sports function-size sentinel-skip (migrated deferred item)

## Why this doc exists

`sports_reference_function_size_qg_regression_2026_07_16.md` (now archived) found 3 functions in `instruments-service`'s
`sports_reference_core.py`/`sports_reference_fixtures.py` had regrown past the `MAX_FUNCTION_LINES`/`MAX_METHOD_LINES`
size gate despite both files having been explicitly decomposed out of `FUNCTION_SIZE_EXTRA_EXCLUDES` on 2026-06-11
specifically because they were supposed to "now pass the 900-line/200-line gates directly." The symptom was fixed by
`instruments-service@ac22305c` (2026-07-21, confirmed live in a 2026-07-23 RE-TRIAGE). The MECHANISM by which a same-day
sports commit shipped this regression without the size-check phase blocking it at commit time was never investigated —
the source doc's own acceptance item 2 explicitly says so and its RE-TRIAGE confirms it "remains open in spirit."

## Original hypothesis (unconfirmed, from the source doc)

`quality-gates.sh` has a green-content-sentinel that skips the expensive TESTS+TYPE CHECK+SIZE CHECK phases when the
tree is byte-identical to the last known-green run. If the regressing sports commits (same-day candidates: `a66fc295`,
`493393c8`, `86cc71ff`, all 2026-07-16) landed via a workflow that reused a stale sentinel — or ran a `QG_SLICE`-scoped
gate that excludes phase 5 — the regression could ship silently.

## Acceptance

- [x] ✅ [SCRIPT] P3. **DONE 2026-07-26 (slot 4)** — Root-cause WHY the size gate didn't block the commits that regrew
      the 3 functions past their limits. **The original "2026-07-16 same-day candidates" hypothesis was wrong** —
      `git blame` on each function's body at the `a66fc295` discovery checkout, then direct re-measurement (same AST
      logic the gate uses: `(end_lineno - lineno + 1)` per `FunctionDef`/`AsyncFunctionDef`, method-vs-function cap by
      `ClassDef` parent) of each contributing commit's own tree, pinpoints the EXACT threshold-crossing commit per
      function — three different days, only one of which is in the original candidate list: -
      `_fetch_teams_and_standings` (200L cap): **`56aa19388`** (2026-07-13 19:44 +0100, "TEAMS/STANDINGS manifest — stop
      the live blank-league_id blanket writer"), 164L → 205L. NOT a 07-16 candidate. - `emit_empty_gaps_for_entity` (50L
      method cap): **`0d9ffabd0`** (2026-07-14 14:31 UTC), 36L → 52L (later grown further to 89L by `86cc71ff`, 07-14
      16:10, which WAS a listed candidate — but the cap was already crossed 2 hours earlier). NOT a 07-16 candidate. -
      `_write_per_fixture_entities` (200L cap): **`493393c88`** (2026-07-15 00:41 +0100, one of the 3 listed
      candidates), 173L → 225L (further grown to 253L by `a66fc295`, also a listed candidate).

      Ruled out `FUNCTION_SIZE_EXTRA_EXCLUDES` (the workaround-exclusion mechanism): `git show

0d9ffabd0:scripts/quality-gates.sh`confirms`sports_reference_core.py`/`_fixtures.py`carried NO active       exclusion entry at any of the 3 crossing commits — the only re-exclusion window was`7d56b9d6`(2026-07-20,       4-6 days AFTER these commits,`instruments_service_codex_compliance_ceiling_drift_2026_07_20.md`) through       `ac22305c`
(2026-07-21, the real decomposition fix) — a LATER, separate, already-closed episode, not the cause of the original
miss.

**Mechanism**: NOT a `QG_SLICE`-scoped run (all 3 are full feature/bugfix commits with real test suites, no scoping
evidence), NOT the exclusion workaround (ruled out above). `0d9ffabd0`'s own commit message claims "Quality gates: 134s,
sentinel written" — i.e. the agent's local Pass-1 run reportedly passed and wrote a green sentinel, YET direct
re-measurement of that EXACT commit's tree shows a genuine 52L>50L violation with no exclusion in effect. Re-running the
identical check logic in isolation against the extracted file DOES correctly flag the violation — so this is not a bug
in the AST size-measurement logic itself. The gap is most consistent with either (a) the committed tree differing from
whatever tree the agent's local QG run actually verified (edits made after the Pass-1 run, before commit, that should
have invalidated the content-sentinel but evidently didn't block `quickmerge --agent`), or (b) a live,
not-yet-reproduced bug in the sentinel comparison itself. Distinguishing (a) from (b) needs a LIVE reproduction
(deliberately grow a function past cap, run the real Pass-1→commit→quickmerge-agent sequence, and see whether the
mismatch is actually caught) — filed as a follow-up todo below rather than attempted here, since the historical
`.qg_content_sentinel` artifacts from these 2026-07-13/14/15 commits are local, uncommitted, and long gone; nothing in
the historical record can further disambiguate (a) vs (b) without a fresh repro.

- [x] ✅ [SCRIPT] P3. **DONE 2026-07-26 (slot 4)** — **Verdict: does NOT subsume this gap; needs its own fix.**
      `qg_sentinel_environment_blind_2026_07_23.md`'s planned fix binds `ENVIRONMENT` (dev/prod) into the sentinel hash
      — but the function/class/method size check is a pure Python AST measurement with zero `ENVIRONMENT` dependency (no
      bucket resolution, no cloud config, nothing environment-sensitive in the check logic read at
      `scripts/quality-gates-base/base-service.sh:1352-1373`). Binding `ENVIRONMENT` into the sentinel would not change
      whether this specific class of miss (a size violation slipping past a sentinel that reportedly passed) recurs —
      the two are orthogonal dimensions of the same underlying weakness (a content-hash sentinel is only as trustworthy
      as the guarantee that the verified tree byte-for-byte equals the committed tree), but fixing the ENVIRONMENT
      dimension does nothing for the size-check dimension. Filed as its own follow-up (see below); not marking this doc
      `resolved` since the live-reproduction follow-up is still open.

## Follow-up todos

- [x] ✅ [SCRIPT] P3. **PARTIALLY ANSWERED 2026-07-26 (slot 7) via an unplanned live repro — not the deliberate
      scratch-branch repro this todo originally asked for, but a real, same-session, twice-repeated natural occurrence
      that answers the open question directly: the miss is real and reproducible on THIS shared host, not a one-time
      historical artifact.** Working `instruments-service` under `cross_cutting_satellite_ao_dispatch_batch1-012` +
      `instruments_service_qg_red_function_size_sports_reference-001` in the same session: (1) ran a full
      `bash scripts/quality-gates.sh` (no scoping flags) on a tree where
      `sports_reference.py:_fetch_sports_reference_data` was ALREADY 206L (>200 cap, confirmed via direct AST
      re-measurement using the exact same logic + exclude-list as `base-service.sh:1352-1373`) — the run printed
      `✅ ALL QUALITY GATES PASSED` and wrote a fresh `.qg_last_passed_sha` matching HEAD; ran it a SECOND time minutes
      later (same tree, same violation) — same "ALL QUALITY GATES PASSED" result. (2) Separately, my own earlier commit
      (`instruments-service@9c203ce1`, threading `available_at=` into 4 `process_write.py` callsites) pushed that file
      from exactly 900 to 904 lines (`MAX_FILE_LINES` cap) — confirmed via `git show <parent>:<path> | wc -l` = 900 vs
      current = 904 — yet the SAME two full quality-gates.sh runs that followed (verifying an unrelated `--asset-group`
      bucket-resolution fix) both reported "ALL QUALITY GATES PASSED" with a fresh sentinel each time, never flagging
      the file-size violation either. Both violations were independently confirmed via a from-scratch direct
      AST/line-count re-implementation of the checks (not trusting the script's own report) before and after my fixes,
      so this is not a false trigger — the checks WOULD fire under a correct run, and this session's real runs did not
      fire them. **What this does NOT answer**: whether it's (a) the sentinel/content-cache mechanism vs (b) some other
      skip path — a live diagnostic instrumenting `base-service.sh` itself (e.g. temporarily echoing `$_SIZE_FILES`
      count + a checksum right before the check block, across a repeat run) is still needed to pin the exact mechanism;
      this session's evidence proves WHETHER it recurs (yes, twice, unprompted) but not precisely HOW. Downgrading from
      "needs a deliberate repro" to "needs instrumentation of a MEASURED recurrence" — the original scratch-branch repro
      is still valuable if the instrumentation approach doesn't pin it, so leaving this open rather than fully resolved.
- [ ] [SCRIPT] P2. Instrument `scripts/quality-gates-base/base-service.sh`'s size-check block (~line 1335-1373) with a
      temporary diagnostic (echo `$_SIZE_FILES` count + whether `.qg_content_sentinel`/`.qg_last_passed_sha` existed and
      matched BEFORE this run started) on the NEXT real occurrence of "ALL QUALITY GATES PASSED" despite a known live
      oversized function/file (reproducible right now on any instruments-service checkout with `sports_reference.py`'s
      current state — check first, it may already be fixed by the time this runs) — pin whether it's the
      content-sentinel fast-path, a stale cached `$_SIZE_FILES` variable, or something else entirely. Escalate to P0 if
      confirmed as a live sentinel bug (silently green-lights real 900L+/200L+ violations fleet-wide) rather than a
      one-off. Repo: instruments-service + unified-trading-pm (shared `base-service.sh`).

## Progress Log

- 2026-07-26 (slot 4): Root-caused via `git blame` + direct AST re-measurement (same logic as `base-service.sh`'s
  phase-5 check) of each contributing commit's exact tree state, rather than trusting the source doc's "same-day 07-16
  candidates" hypothesis. Found the actual threshold-crossing commits are `56aa19388` (07-13), `0d9ffabd0` (07-14),
  `493393c88` (07-15) — 3 different days, only one a listed candidate. Ruled out the `FUNCTION_SIZE_EXTRA_EXCLUDES`
  workaround directly (checked the exclusion list's exact content at each crossing commit — no active exclusion; the
  only re-exclusion window was `7d56b9d6`/2026-07-20, a later, separate, already-resolved episode). Confirmed
  `qg_sentinel_environment_blind_2026_07_23.md`'s fix does not subsume this (orthogonal dimension — the size check has
  no ENVIRONMENT dependency). Both acceptance items flipped with the full evidence trail; filed a live-reproduction
  follow-up since the historical sentinel state can no longer be inspected and a definitive tooling-bug-vs-workflow-gap
  verdict needs a fresh repro.
- 2026-07-26 (slot 7): Unprompted, natural repro of the exact same class TWICE in one session on instruments-service —
  `sports_reference.py` sitting at a live 206L (>200 cap) function AND, separately, my own commit pushing
  `process_write.py` from 900→904L (>900 file cap) — both survived 2+ full `quality-gates.sh` runs reporting "ALL
  QUALITY GATES PASSED" with a fresh sentinel each time (confirmed via independent from-scratch AST re-measurement
  before/after fixing both). Downgraded the open follow-up from "needs a deliberate scratch-branch repro" to "needs live
  instrumentation of a measured recurrence" (added as a new P2 todo) since the recurrence itself is no longer in
  question — only the precise mechanism (content-sentinel fast-path vs something else) is. Both real violations are now
  fixed in my own working tree (instruments-service, uncommitted pending a currently-running full QG confirmation) — not
  a duplicate finding, this doc's existing scope already covers it; flagging severity: this may be a live,
  currently-active fleet-wide gap letting real 900L+/200L+ violations merge silently, not a historical-only artifact.
  verdict needs a fresh repro.
