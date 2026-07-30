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
last_updated: 2026-07-30
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
- [x] ✅ [SCRIPT] P2. **DONE 2026-07-30 (slot 2) — ROOT CAUSE DEFINITIVELY PINNED, and it is NEITHER of the two
      candidate mechanisms.** Instrumented `scripts/quality-gates-base/base-service.sh` at 4 points (sentinel-state echo
      right after the sentinel-hit block ~L722; `$_SIZE_FILES` count + `V` echo right after the `find` assignment
      ~L1429; `SVIOL`/`FSIZES` non-empty + `V` echo right after the size checks ~L1471; final `V` vs
      `CODEX_MAX_VIOLATIONS` verdict echo ~L2168), then ran a REAL, full, unscoped `bash scripts/quality-gates.sh` on
      instruments-service against the LIVE reproducible violation (`sports_reference_fixtures.py` at 914L, >900
      `MAX_FILE_LINES`, confirmed via direct AST/byte-newline re-measurement before running — not excluded in
      `FUNCTION_SIZE_EXTRA_EXCLUDES`). Diagnostic output (full run log preserved in this session's evidence):

      ```
                      QG_SIZE_DIAG: sentinel_file_existed=yes sha_sentinel_existed=yes sentinel_hit=false content_hash=a44890b01405... stored_hash=b440d7799da5...
                      QG_SIZE_DIAG: _SIZE_FILES count=55 pwd=.../instruments-service V_before_size_checks=1
                      ❌ Files exceed 900 lines:  ./instruments_service/engine/orchestrator/sports_reference_fixtures.py: 914 L
                      ❌ Function/class/method size exceeded:  ./instruments_service/engine/orchestrator/process.py:99:process_instruments(): 205L
                      QG_SIZE_DIAG: SVIOL_nonempty=yes FSIZES_nonempty=yes V_after_size_checks=3
                      QG_SIZE_DIAG: final_V=3 CODEX_MAX_VIOLATIONS=3 verdict=WARN_WITHIN_TOLERANCE
                      ⚠️  Codex compliance: 3 violations (within tolerance of 3)
                      ✅ ALL QUALITY GATES PASSED (112s)
                      ```

                      **(a) Content-sentinel fast-path — RULED OUT, conclusively.** `sentinel_hit=false` (my own edit to
                      `base-service.sh` changed the gate-script content hash — the sentinel hash includes the gate script itself, per
                      `_qg_content_hash()` L100 — which invalidated any prior sentinel and forced a genuine full run). This was NOT a
                      skipped-heavy-phases run; TESTS + TYPE CHECK both ran. The violation was STILL missed as a fail. **(b) Stale
                      `$_SIZE_FILES` — RULED OUT.** `_SIZE_FILES count=55` (correctly enumerated, `sports_reference_fixtures.py`
                      included) and BOTH `SVIOL` (the 914L file) and `FSIZES` (a NEW regression: `process.py:process_instructions()`
                      regrew to 205L — the exact function that was decomposed from 1,931L on 2026-06-11 to justify ratcheting
                      `CODEX_MAX_VIOLATIONS` 4→3) were correctly populated non-empty. The size-check AST/byte-count logic itself has
                      ZERO bug — it detected both violations exactly as designed.

                      **(c) ACTUAL root cause — the `CODEX_MAX_VIOLATIONS` static tolerance ceiling (base-service.sh L2168-2176)
                      masks NEW violations with headroom freed by OTHER, unrelated violation classes shrinking.**
                      `_max_v=${CODEX_MAX_VIOLATIONS:-0}`; the verdict is `V > _max_v → FAIL`, `0 < V <= _max_v → WARN (logged, gate
                      still passes)`, `V == 0 → PASS`. instruments-service sets `CODEX_MAX_VIOLATIONS=3`
                      (`instruments-service/scripts/quality-gates.sh:233`), explicitly comment-justified on 2026-06-11 as "Remaining 3
                      classes: os.getenv/os.environ, bare `pip install uv`, broad `except Exception:`" — i.e. the ceiling was sized
                      assuming the size-violation class stayed at 0 forever. In THIS run, `os.getenv`/`pip install uv` had ALSO since
                      cleared (only "broad except Exception" remained, contributing `V=1`), so 2 full slots of headroom existed —
                      exactly enough to silently absorb the 2 BRAND-NEW size violations (`V: 1→3`) without crossing `_max_v=3`. The
                      ceiling is a single AGGREGATE count across every violation class, with no per-class floor/ceiling and no
                      awareness that "0 size violations" was a load-bearing precondition of its own value — so it structurally cannot
                      distinguish "3 pre-approved legacy debt items" from "1 pre-approved item + 2 fresh regressions of a class the
                      ceiling assumed was permanently cleared." This is a LIVE, currently-active gap (not a one-off, not historical) —
                      confirmed via a real, non-scoped, non-sentinel-hit run, moments before filing this update. Escalating per the
                      todo's own criterion ("silently green-lights real 900L+/200L+ violations fleet-wide"): a fleet scan
                      (`grep CODEX_MAX_VIOLATIONS=` across every repo's `scripts/quality-gates.sh`) found **9 repos exposed to this
                      exact class**: `deployment-api` (5), `strategy-service` (4), `execution-service` (3), `instruments-service` (3),
                      `unified-api-contracts` (2), `batch-live-reconciliation-service` / `deployment-service` / `ibkr-gateway-infra` /
                      `market-data-processing-service` (1 each) — any of these can have a genuine NEW size (or other codex-checked)
                      violation silently pass as long as some OTHER pre-existing violation class in that repo has since shrunk. P0
                      follow-up filed below with the concrete fix direction. Diagnostic instrumentation fully REVERTED after capture
                      (`git diff` on `base-service.sh` clean) — it was fleet-shared code and the diagnostic was explicitly temporary.
                      Live regressions found in instruments-service (the 914L file + the 205L function) are NOT fixed by this todo
                      (out of scope for a tooling-diagnostic task on a different repo's domain code) — filed as their own todo below.

- [ ] [SCRIPT] P0. Fix `CODEX_MAX_VIOLATIONS` aggregate-tolerance masking (base-service.sh L2166-2176,
      `unified-trading-pm`): a size (file/function/method/class) violation must NEVER be absorbable by tolerance
      headroom freed by an unrelated violation class shrinking — confirmed live 2026-07-30, see evidence above.
      Recommended direction: move the file-size + function/class/method-size checks (`SVIOL`/`FSIZES`, currently
      L1417-1471) into the existing ZERO-TOLERANCE hard-gate aggregation pattern already used for fallback-imports/
      DTZ/TID251/citations (see `_V_PRE_RATCHET` at L2188 + its surrounding comment: "Hard gates get ZERO codex
      tolerance — they carry their own per-repo baselines inside the checkers") instead of the shared `V`/
      `CODEX_MAX_VIOLATIONS` aggregate counter. Each repo with a live size baseline keeps its OWN explicit allow-list
      (`FUNCTION_SIZE_EXTRA_EXCLUDES`, already the sanctioned per-repo escape hatch) rather than an opaque shared
      numeric ceiling that can't tell which class regressed. Repo: unified-trading-pm (shared `base-service.sh` —
      touches all 9 exposed repos' effective gate behavior, but the fix is one file).
- [ ] [SCRIPT] P1. Decompose the two live size regressions this investigation surfaced in instruments-service (both
      currently masked by the `CODEX_MAX_VIOLATIONS=3` gap above, so `quality-gates.sh` reports green despite these):
      (1) `instruments_service/engine/orchestrator/sports_reference_fixtures.py` at 914L (>900 `MAX_FILE_LINES`) — split
      out a sibling module per the pattern used for the 2026-07-21 decomposition of the same file's earlier regrowth
      (see `instruments_service_codex_compliance_ceiling_drift_2026_07_20.md`, archived). (2)
      `instruments_service/engine/orchestrator/process.py:99` `process_instructions()` at 205L (>200
      `MAX_FUNCTION_LINES`) — this is a REGROWTH of the exact function decomposed from 1,931L on 2026-06-11 (the
      decomposition that originally justified ratcheting `CODEX_MAX_VIOLATIONS` 4→3); extract named helpers per that
      same precedent. After both are fixed, `CODEX_MAX_VIOLATIONS` can likely ratchet down further (verify actual `V`
      afterward, don't guess). Repo: instruments-service.

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
- 2026-07-30 (slot 2): Instrumented `base-service.sh` (4 diagnostic echo points), ran a REAL full non-scoped
  `quality-gates.sh` on instruments-service against the live 914L `sports_reference_fixtures.py` violation (still
  reproducible — check first for stale docs was right to include, it hadn't been fixed). Definitively RULED OUT both
  candidate mechanisms: sentinel_hit=false (my base-service.sh edit invalidated any prior sentinel, forcing a genuine
  full run — TESTS+TYPECHECK both ran) and `$_SIZE_FILES`/`SVIOL`/`FSIZES` all correctly populated (the AST/size-check
  logic itself is bug-free). PINNED the actual mechanism: `CODEX_MAX_VIOLATIONS=3` (instruments-service) is a single
  AGGREGATE tolerance ceiling across every codex-violation class; two OTHER pre-existing classes (`os.getenv`,
  `pip install uv`) had independently cleared since the 2026-06-11 ratchet, freeing exactly enough headroom to absorb 2
  brand-new size violations (the known 914L file + a newly-discovered regression: `process.py:process_instructions()`
  regrew to 205L — ironically the SAME function whose 2026-06-11 decomposition originally justified the ceiling) without
  crossing the ceiling, producing a WARN instead of a FAIL. Confirmed fleet-wide exposure: 9 repos carry a nonzero
  `CODEX_MAX_VIOLATIONS`. Reverted all diagnostic instrumentation (fleet-shared file; `git diff` clean). Filed a P0
  follow-up (fix the aggregate-masking design) + a P1 follow-up (fix the 2 live instruments-service regressions this
  investigation surfaced) — both out of scope to fix inline here (cross-repo, needs their own review). All 4 acceptance
  items + follow-ups in this doc's original scope are now resolved; the 2 new follow-ups are fresh work items, not
  reopenings.
