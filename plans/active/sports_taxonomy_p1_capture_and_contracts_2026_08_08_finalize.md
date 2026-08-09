---
doc_type: plan
title: Sports taxonomy P1 — finalize (reconcile source docs + release the P2/P3 gates + archive)
summary: >-
  Gated closeout for sports_taxonomy_p1_capture_and_contracts_2026_08_08.md. P1 is a batch-style phase whose todos
  resolve open items in SEVERAL source docs, so this finalize reconciles each source doc's own checkbox (not just P1's),
  checks whether reconciling left any source doc at zero open todos and therefore archivable in its own right, confirms
  the capture-outage issue docs are genuinely closed rather than assumed, and only then archives P1.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [sports, canonicalisation, finalize, archival, contracts]
related:
  [
    /plans/active/sports_taxonomy_p1_capture_and_contracts_2026_08_08.md,
    /plans/active/sports_taxonomy_p2_migration_2026_08_08.md,
    /plans/archive/issues/sports_odds_venue_enumeration_undercount_predrain_2026_07_27.md,
    /plans/active/issues/sports_features_layer_findings_sweep_2026_07_18_part3_2026_07_26.md,
  ]
created: 2026-08-08
last_updated: 2026-08-08
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.48
assigned_role: data_engineering
effort: high
supersedes:
superseded_by:
resolved_by:
drift_direction: advance-code
depends_on: [sports_taxonomy_p1_capture_and_contracts_2026_08_08]
gate_on_depends: true
sequential: true
context_scope:
  [
    /plans/active/sports_taxonomy_p1_capture_and_contracts_2026_08_08.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/02-data/sports-data-types-catalog.md,
  ]
source: >-
  task_template.md §4's finalize-plan-coverage rule — every AO-dispatched plan needs a companion gated finalize plan.
archive_exempt:
  true # temporary 2026-08-09 — bridges the one-commit gap between this flip and the very next
  # commit's git-mv archival (see Progress Log); removed once archived.
locked_by:
locked_since:
---

# Sports taxonomy P1 — finalize

> **Machine-gated** on `sports_taxonomy_p1_capture_and_contracts_2026_08_08.md`.

## Todos

- [x] ✅ [REVIEW] P1. **Reconcile every SOURCE doc P1 resolved, re-verifying each cited commit exists.** P1 is a
      batch-style phase: its todos close open items in
      `/plans/archive/issues/sports_odds_venue_enumeration_undercount_predrain_2026_07_27.md` (the 19-vs-21 unmapped
      bookmaker classification, resolved mechanically by retiring the split),
      `/plans/active/issues/sports_features_layer_findings_sweep_2026_07_18_part3_2026_07_26.md` (the codex rename/split
      process rule), and the two capture-outage docs (`mtds_sports_odds_api_force_fetch_no_parquet_2026_08_01.md`,
      `sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md`). Flip each source doc's OWN checkbox with evidence —
      do not trust a source doc's copy of an evidence line. **Done when**: every named source doc's checkbox is flipped
      and each cited commit is confirmed via `git log`. — **RECONCILED 2026-08-09 (slot 23, review)**, read all four
      source docs in full (not the P1 copy) + independently verified every cited commit via `git cat-file -e`/`git show`
      in its own repo (none trusted from P1's citation alone): 1.
      `sports_odds_venue_enumeration_undercount_predrain_2026_07_27.md` — **already fully closed + archived**: both its
      own todos are `[x]`, `status: resolved`, archived 2026-08-08 citing this same
      `/plans/active/sports_taxonomy_p1_capture_and_contracts_2026_08_08.md` as the plan that superseded its ask. The
      mechanical resolution P1 claims (retire the exchange_odds/fixed_odds split) cites `unified-api-contracts@56f20ad0`
      — verified present (`git cat-file -e` + `git show --stat`, commit message matches the claimed content exactly:
      `derive_sports_odds_instrument_type()`, makes the 19-vs-21 count moot). No action needed — the doc's own checkbox
      was already flipped before P1 was authored. 2.
      `sports_features_layer_findings_sweep_2026_07_18_part3_2026_07_26.md` — **the SPECIFIC item P1 claims is already
      `[x]`**: the `[PROCESS] P1` "entity rename/split MUST enumerate consumers" todo (§ R) is checked, citing
      `/codex/02-data/entity-rename-and-split-consumer-migration-rule.md` — confirmed the file exists and was authored
      in the plan-authoring commit `unified-trading-pm@6860859a5` (matches the todo's own citation). This 943-line doc's
      `status` stays `open` — it carries MANY other open `[ ]` items (§ R's "audit every other stale-entity consumer", §
      U's residual-league decisions) that are explicitly owned by `sports_consolidated_closeout_2026_07_19.md` Tracks
      E/F, NOT by P1 — correctly untouched, not P1's scope. 3.
      `mtds_sports_odds_api_force_fetch_no_parquet_2026_08_01.md` — P1's Block A todo-1 cites this as background reading
      only ("may already carry the answer"), never claims to resolve it. Confirmed: this doc diagnoses a DIFFERENT,
      unrelated failure (the `pipeline_e2e_check.py` force-fetch tool hitting an upstream `the-odds-api.com`
      401/quota-exhaustion on 2026-08-01) — 4 of 5 todos are `[x]` with the shipped fix
      `market-tick-data-service@bc269b51` verified present; the sole remaining `- [ ] [OPERATOR] P2` is a genuine
      credential/billing ask, correctly left open and untouched by P1. No overlap with P1's actual root cause. 4.
      `sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md` — this IS the doc P1's diagnosis relied on ("Full
      root cause already in `sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md`; confirmed live and
      code-level"). Verified that claim holds: read the full code-level trace (future-date-guard removal exposing an
      unscoped 30-league fetch, OOM-before-manifest-write crash-loop) and independently confirmed every commit P1's
      diagnosis + this doc's own fix chain cites exists — `market-tick-data-service@410d7569` (future-date-guard
      exemption, the exposing change), `deployment-service@4e0e03d` (`--league` scoping fix),
      `market-tick-data-service@afa8eaec` (pre-flight source-scoping fix), `unified-trading-library@2e072fbf` (top-level
      freshness-skip demotion), and `market-tick-data-service@fc704195` (the root-fixed + re-strengthened
      `_asset_group_for_venue` test P1's own weakened-test sweep cites). This 1019-line doc's `status` stays `open` — it
      carries its OWN still-live, independent operational chain (live-verify todos for the pre-flight fix, a 5-day
      historical backfill whose "gate cleared" claim was self-caught-and-reverted as premature 2026-08-06, and an
      unresolved `[DATA] P2` vendor-verify-first decision) that is about restoring FULL coverage for the specific
      2026-07-27..08-02 gap window — a distinct, still-in-progress task from P1's contract-only scope, correctly left
      untouched (P1's own Block A todo-2 separately re-measured live capture as healthy for day=2026-08-07, which is
      corroborating, not duplicate, evidence).

      **Net**: no false-done claims found in any of the four source docs; every commit P1 or its sources cite resolves
                                              to a real, verifiable commit in the correct repo. Nothing needed flipping beyond this todo itself — the two
                                              capture-outage docs' remaining open items are legitimately out of P1's scope and must stay open until their own
                                              (unrelated, already-tracked) chains finish.

- [x] ✅ [REVIEW] P1. **Check whether reconciling left any source doc at zero open todos**, and if so run the same
      6-step archival ritual on it — a finalize that closes only its own plan while leaving a now-fully-done source doc
      live is the exact omission that caused a real `run_hygiene_sweep.sh --ci` hard-fail (10 violations). **Done
      when**: each source doc is either still open with todos, or archived. — **VERIFIED 2026-08-09 (slot 9, review)**,
      counted `- [     ]` open todos directly in each of the four source docs (not trusted from the prior todo's prose):
      `sports_odds_venue_enumeration_undercount_predrain_2026_07_27.md` — 0 open, `status: resolved` — but this doc was
      **already archived to `plans/archive/issues/` on 2026-08-08**, before P1 was authored (confirmed by its own path +
      the prior todo's citation), so there is no live doc left to archive here.
      `sports_features_layer_findings_sweep_2026_07_18_part3_2026_07_26.md` — 2 open todos remain (§ U residual-league
      decisions), `status: open`. `mtds_sports_odds_api_force_fetch_no_parquet_2026_08_01.md` — 1 open todo remains (the
      `[OPERATOR] P2` credential ask), `status: open`. `sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md` — 4
      open todos remain (its own live operational chain), `status: open`. **Net**: reconciling did not leave any
      currently-live source doc at zero open todos — none qualifies for the 6-step archival ritual right now.
- [x] ✅ [REVIEW] P1. **Confirm capture is STILL live, not merely restored once.** P1's Block A proves a single day;
      this re-checks that raw sports capture has continued writing for the full window since, and that the new staleness
      guard actually fires on a synthetic frozen-source day. A guard that was never observed firing is not a guard. —
      **VERIFIED + BUG FOUND + FIXED 2026-08-09 (slot 32, review)**. (1) **Capture still live**: manifest
      (`instruments-store-sports-prd-...`) shows real non-empty `capture_status=captured` trades rows continuing every
      day since P1's single-day proof — 2026-08-05 (17 shards/592 rows), 06 (17/592), 07 (225/9154, P1's day), 08
      (1237/75570), 09-partial (397/36019 so far) — plus GCS parquet object counts climbing the same days (225 → 1237 →
      397-so-far). Not the outage's silent-zero pattern. (2) **Staleness guard: DOES fire, but was BROKEN — firing
      unconditionally regardless of true capture health, not "never observed firing."** Live Cloud Run logs
      (`uts-prod-market-data-processing-service-t1-recon`) show it firing twice, 2026-08-09T01:03:16Z and 03:03:26Z:
      `SPORTS staleness guard: refusing derived output for sports/2026-08-08 — MTDS manifest has no     capture_status=captured row for SPORTS/2026-08-08 ...`
      — despite 2026-08-08 having 1237 real captured trades rows (confirmed above). Root cause:
      `check_sports_raw_source_captured` (Block A todo-3, `market-data-processing-service@41cdb702d`) resolved the
      bucket via `_resolve_upstream_bucket("SPORTS")`, which returns the RAW `market-data-tick-sports-*` bucket — but
      SPORTS' canonical availability manifest lives in the SEPARATE `instruments-store-sports-*` bucket (documented
      carve-out, `market-tick-data-service`'s `_manifest_bucket.py::_resolve_manifest_bucket`, since the 2026-06-07
      sports-manifest-canonicalisation fix). The raw-tick bucket's own manifest index has only 5 stale `empty_confirmed`
      placeholder rows for trades — it NEVER carries real captured rows for SPORTS — so the guard was unconditionally
      refusing odds_snapshot/odds_movement/odds_horizon_bucket derivation, live in production, since it shipped
      2026-08-08. All 9 original unit tests mocked `_resolve_upstream_bucket` directly and never caught this. **Fixed**:
      `market-data-processing-service@631fc4594` — guard now resolves `instruments-store-sports` directly (mirrors the
      MTDS carve-out pattern); added a regression test asserting the correct bucket kind/asset_group. QG: ✅ ALL QUALITY
      GATES PASSED, 10/10 unit tests green (was 9, +1 regression). Verified `631fc4594` is an ancestor of
      `origin/live-defi-rollout`.
- [x] ✅ [REVIEW] P1. **Re-verify the already-archived exchange/fixed-odds fork pair still resolves.** Both
      `sports_closeout_exchange_fixed_odds_fork_2026_07_25.md` and its finalize sibling were marked `superseded` and
      **archived to `plans/archive/2026_08/` on 2026-08-08** in the same commit that authored this chain — the parent
      because the operator retired the instrument_type split it exists to implement, the sibling because a
      `gate_on_depends` finalize whose parent went terminal can never fire. Three active-corpus referrers were repathed
      at the time. This todo only re-checks that no NEW referrer has since been authored against the old `plans/active/`
      path (a real risk while this chain is in flight). **Done when**: a corpus-wide grep for either slug shows every
      referrer resolving to the archived location. — verified 2026-08-09:
      `grep -rn     "/plans/active/sports_closeout_exchange_fixed_odds_fork" plans/active/` returns zero hits (also
      checked codex/, scripts/); the only frontmatter path-reference outside the archived pair itself
      (`sports_consolidated_closeout_2026_07_19.md`) already cites `/plans/archive/2026_08/…`. Every other match across
      the corpus is a bare-filename historical-narrative mention (Progress Log prose), not a resolvable path citation.
      No new referrer has been authored against the stale active path.
- [x] ✅ [REVIEW] P2. **Confirm the P2 and P3 gates can legitimately release.** Both declare `gate_on_depends: true` on
      P1. Verify the contracts they assume actually exist in UAC (venue/executable split, single lowercase `odds`,
      `horizon` axis, retired `markets`/`outcomes`/`settlements`) rather than relying on P1's checkbox state alone.
      **Done when**: each assumed contract is confirmed present in the shipped UAC, or a blocking gap is filed as a
      `- [ ]` todo. — **VERIFIED 2026-08-09 (slot 23, review)**. Confirmed all 4 assumed contracts are genuinely live in
      shipped `unified-api-contracts`, independent of P1's own checkbox prose — cited SHAs verified present + ancestors
      of `origin/live-defi-rollout` (`git cat-file -e` + `git merge-base --is-ancestor`), then re-derived each contract
      by importing the live code in the repo's own `.venv` (not re-reading the commit message): 1. **venue/executable
      split** (`05a709fd`) — `venue_adapter_keys.is_venue_executable()` exists and is exported from
      `registry/__init__.py`; `VENUES_BY_ASSET_GROUP["sports"]` (31 venues) contains neither `ODDS_API` nor `FOOTYSTATS`
      (both correctly demoted to source-only). 2. **single lowercase `odds`** (`b2c5197d5`) — imported
      `SPORTS_ODDS_DATA_TYPE_CANONICAL_FORM` + `canonical_sports_odds_data_type()` from `league_data.py`:
      `{'trades': 'odds', 'ODDS': 'odds', 'odds': 'odds'}`, both `'trades'` and `'ODDS'` resolve to `'odds'` live. 3.
      **`horizon` axis** (`685b288a`) — imported `SPORTS_HORIZONS`
      (`['T-24h','T-18h','T-12h','T-6h','T-4h','T-2h',        'T-1h','T-10m','T-0']`) + `is_valid_horizon()` from
      `market_data_categories.py`, both live and callable. 4. **retired `markets`/`outcomes`/`settlements`**
      (`975f0191`) — imported `DATA_TYPES_BY_ASSET_GROUP["sports"]` live: all three tokens absent.

      Cross-checked against the LIVE AO gate mechanism itself (`GET /api/backlog`), not just the plan file: every
                          currently-queued `sports_taxonomy_p2_migration-*` task's `blocked_reason` cites only the SECOND gate
                          (`sports_af_full_entity_completion_2026_08_03` prereqs) — none cite P1 or an upstream-open-todos reason on P1
                          anymore, confirming the `gate_on_depends` on P1 has ALREADY mechanically released. Same for
                          `sports_taxonomy_p3_consumers-*`: the still-queued tasks are gated on unrelated `auto_unpark__*` prerequisites and
                          a fleet cooldown, not on P1. Also confirmed P1's own plan file has ZERO remaining `- [ ]` todos and
                          `status: active` / unlocked (`locked_by:` empty) — the gate's source-of-truth is genuinely fully done, not a
                          false-done checkbox. **Net**: no blocking gap. Both gates release legitimately.

- [x] ✅ [DOC] P2. **Archive `sports_taxonomy_p1_capture_and_contracts_2026_08_08.md`** via the standard 6-step ritual,
      including the codex-alignment check (P1 CREATES codex docs — the rename/split process rule — and SUPERSEDES
      `sports-data-types-catalog.md`, so this is a real check, not a no-op), the corpus-wide referrer-path fixup for the
      plan slug, and archiving this finalize doc alongside it in the same commit. **Done when**: the plan is in
      `plans/archive/2026_08/`, every referrer resolves, and this doc is archived with it. — **DONE 2026-08-09
      (data_engineering, slot 15)**. Codex-alignment check found 2 genuinely stale claims in
      `/codex/02-data/sports-data-types-catalog.md` ("P1 todo still in flight" for the BETFAIR operator-group parent,
      and "being retired in P1 (todo in flight)" for the exchange_odds/fixed_odds split) — both P1 todos were actually
      done; corrected both to cite the landed commits. Added a fleet-wide pointer to
      `/codex/02-data/entity-rename-and-split-consumer-migration-rule.md` in CLAUDE.md § "Working on DATA / manifest /
      pipeline?" (was created by P1 but never indexed there). Corpus-wide referrer-path fixup: repathed 6 active
      `plans/active/**` docs + 2 `codex/02-data/*.md` docs (8 files, 11 leading-slash `/plans/active/...` citations of
      this plan) to point at its post-move archive location; left already-archived docs' historical citations untouched
      (frozen-at-archival-time precedent, confirmed via
      `sports_closeout_exchange_fixed_odds_fork_2026_07_25_finalize.md`'s own un-repathed cross-reference to its
      already-archived parent). `plans/active/INDEX.md` regenerated post-move. Both docs archived to
      `plans/archive/2026_08/` in a separate commit from this checkbox flip (never combine flip + `git mv`, per this
      ritual's own SSOT) — bridged this checkbox-flip commit past `check_archive_candidates.sh`'s new `--only` precommit
      mode (added 2026-08-09, the same day, with no exemption for the standard flip-then-mv two-commit shape) via a
      temporary `archive_exempt: true`, removed in the archival commit; filed the gap as its own follow-up (see Progress
      Log).

## Progress Log

- **2026-08-08** — Authored alongside the parent per the finalize-plan-coverage rule.
- **2026-08-09** — Todo 4 (re-verify the archived exchange/fixed-odds fork pair) done. Corpus-wide grep for
  `/plans/active/sports_closeout_exchange_fixed_odds_fork` returns zero hits anywhere in `plans/active/`, `codex/`, or
  `scripts/`. The one active-corpus frontmatter path-citation of the pair (`sports_consolidated_closeout_2026_07_19.md`)
  already points at `/plans/archive/2026_08/sports_closeout_exchange_fixed_odds_fork_2026_07_25.md`. Every remaining
  corpus match is a bare-filename mention inside Progress Log prose (historical narrative, not a live path reference).
  Conclusion: no new referrer has been authored against the stale active path since the 2026-08-08 archival.

- **2026-08-09 (slot 23, review)** — Todo 5 (confirm the P2/P3 gates can legitimately release) done. Independently
  verified all 4 UAC contracts P2/P3 assume (venue/executable split, single lowercase `odds`, `horizon` axis, retired
  `markets`/`outcomes`/`settlements`) by importing the live shipped code, not re-reading P1's checkbox prose. Also
  cross-checked the live AO gate mechanism via `GET /api/backlog`: no queued P2/P3 task cites P1 as a blocking reason
  anymore, confirming the machine gate already released correctly. No blocking gap found — nothing to file.

- **2026-08-09 (data_engineering, slot 15)** — Todo 6 (archive P1 via the 6-step ritual) done. Codex-alignment check (a
  real check per this todo's own text, not a no-op) found 2 genuinely stale "still in flight" claims in
  `/codex/02-data/sports-data-types-catalog.md` for todos that were actually landed — corrected both to cite the landed
  commits (`unified-api-contracts@49e83239` BETFAIR operator-group parent; `unified-api-contracts@56f20ad0`
  exchange_odds/fixed_odds derivation). Also found the rename/split rule's own codex doc had never been indexed in
  CLAUDE.md's domain map despite being a fleet-wide HARD RULE, not sports-specific — added a one-line pointer under §
  "Working on DATA / manifest / pipeline?" (CLAUDE.md was 39730/40960 bytes; landed at 40012, still under the
  QG-enforced 40KB cap). Corpus-wide referrer-path fixup: grepped the whole corpus for the leading-slash exact path
  citation (per the workspace's cross-reference convention, not bare-filename prose mentions) and found 11 citations
  across 8 active-corpus files (6 `plans/active/**`, 2 `codex/02-data/*.md`) plus citations inside already-archived
  `plans/archive/**` docs and this finalize doc's own self-references — repathed only the 11 active-corpus citations to
  this plan's post-move archive location, left the archived-doc and self-reference citations frozen (matches the
  established precedent that an already-archived doc's cross-references are not retroactively repathed when their target
  later archives — confirmed against `sports_closeout_exchange_fixed_odds_fork_2026_07_25_finalize.md`, which still
  cites its own already-archived parent's original active path). Added archived banners + `status: complete` to both P1
  and this finalize doc. Regenerated `plans/active/INDEX.md` post-move. Both docs moved to `plans/archive/2026_08/` in a
  commit separate from this checkbox flip (never combine flip + `git mv`, per this ritual's own SSOT).
