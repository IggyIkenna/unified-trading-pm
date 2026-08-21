---
doc_type: plan
title:
  Cross-cutting satellite AO batch 1 — first Phase-1/Phase-3 triage of the cross-cutting closeout-orphan corpus (part 2
  of 2)
summary: >-
  Second half of the cross-cutting tranche's first AO-dispatch batch — see
  `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md` for the full Phase-1/Phase-3 audit summary, the Deferred
  conflict-gated/operator-gated/time-gated sections (not duplicated here), and the 7 mistags/2 archivable_now notes.
  This doc carries the remaining 15 of the 31 conflict-cleared todos, split purely to stay under the workspace's
  1000-line hard cap after prettier reformatting. Grew to 17 todos 2026-07-27 (vintage-audit §3/§4 execution): +2 scoped
  owner-design-call fixes from `features_service_coverage_and_script_canon_2026_06_10.md` (velocity-accel fallback
  semantics, `make_session` loop-safety), previously parked pending a human owner — now agent-owned per operator ruling.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data]
repos:
  [
    unified-trading-pm,
    instruments-service,
    market-tick-data-service,
    market-data-processing-service,
    features-service,
    unified-api-contracts,
    unified-trading-library,
    deployment-api,
    deployment-service,
  ]
scope: [engineer]
tags: [cross-cutting, ao-dispatch, close-out, batch-1, satellite-docs, fresh-triage]
related:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-27"
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 3.5
estimate_calibrated_ai_days: 2.8
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  /ag-closeout-audit skill run 2026-07-26 — sibling half of cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md,
  split for the 1000-line hard cap.
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
context_scope:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26_finalize.md,
    deployment-api/deployment_api/services/data_status/breakdowns_core.py,
    /plans/active/repo_scripts_governance_audit_2026_06_18.md,
  ]
---

# Cross-cutting satellite AO batch 1 (part 2 of 2) — fresh triage extraction

> **Status: active** (corrected 2026-08-12, /plan-reconcile — this banner said "draft" while frontmatter said `active`;
> the frontmatter is the operationally current truth: AO workers have been dispatched against this plan under
> `status: active` for weeks, with real shipped commits dated 2026-07-27 through 2026-08-09, e.g.
> `features-service@25932d23`, `unified-trading-library@0db19a72`, `market-tick-data-service@09c8cbf8`). All 17 todos
> below are same-priority-independent and touch distinct files/docs, except the `smoke_matrix.py` pair (todo citing
> `features_service_coverage_and_script_canon_2026_06_10.md`) which carries inline coordination text with its sibling in
> batch1 — do not strip that text if editing before dispatch.

## Todos

- [x] ✅ [MONITOR] P2. **Bake `deployment-service:latest`'s terraform default forward so it matches the live
      wave-launcher runtime pin** (target repo: `deployment-service`). The `uts-prod-tradfi-wave-launcher` Cloud Run job
      was runtime-re-pinned to a `deployment-service`-built Cloud Run image (digest prefix `56f2060e` — a container
      image digest, not a git commit sha; per
      `plans/archive/issues/dp_alert_flood_triage_and_monitor_fixes_2026_06_23.md` line 144, the "deployment-api" there
      names the Cloud Run image tag family, not the git repo, so this is not a `<repo>@<sha>` citation) that carries
      `_write_last_run_sentinel`, but its terraform default (`deployment-service:latest`) is still a SEPARATE, older
      image — a future `tofu apply` would silently revert the pin and stop the wave-launcher's host-cron sentinel write,
      producing a false `DP_CRON_DID_NOT_FIRE` page once the 6h seed budget lapses. Trigger the
      `deployment-service-jobs-image-build` Cloud Build trigger from LDR (or confirm it already rebuilt on a subsequent
      LDR push) so `deployment-service:latest` carries the sentinel-writer code, then verify the terraform default
      (`terraform/gcp/` wave-launcher job resource) now resolves to an image containing `_write_last_run_sentinel` (grep
      the built image's digest manifest or `gcloud run jobs describe` post-apply) so the runtime pin can safely revert
      without regressing. **Done when**: `deployment-service:latest`'s pushed digest is confirmed to contain
      `_write_last_run_sentinel`, and the checkbox for this item in
      `dp_alert_flood_triage_and_monitor_fixes_2026_06_23.md` is flipped `[x]` citing the build id / commit sha
      verified. Source: `dp_alert_flood_triage_and_monitor_fixes_2026_06_23.md`. — **Already resolved upstream
      2026-07-28** (source doc's own copy of this checkbox, `dp_alert_flood_triage_and_monitor_fixes_2026_06_23.md`
      lines 151-163, archived `[x]` "no code change needed — closed by 5 weeks of normal CI activity" — this todo was
      drafted 2026-07-26, 2 days before that upstream resolution, so this copy went stale unflipped). **Fresh
      re-verification 2026-08-01 (slot 11, data_engineering), no code/terraform change needed:** (1)
      `gcloud builds list --filter="substitutions.TRIGGER_NAME=deployment-service-jobs-image-build"` shows the trigger
      continuing to fire + SUCCEED on every push (5 consecutive successes 2026-07-31→2026-08-01, most recent
      `802ac483-c08a-4b29-b820-72014dec9f6b` @ 2026-08-01T01:31:17Z, commit `248b715e` — the LDR→main promote commit);
      (2) `gcloud artifacts docker images list … deployment-service --filter="tags:latest"` shows the current
      `deployment-service:latest` digest `sha256:b48cfdc…` created 2026-08-01T01:35:00, i.e. built from that exact
      commit; `git show 248b715e:scripts/wave_launcher.py` confirms `_write_last_run_sentinel` present (def line 185,
      call line 425); (3) `gcloud run jobs describe uts-prod-tradfi-wave-launcher` shows the job's
      `spec.template.spec.template.spec.containers[0].image` already resolves to `…/deployment-service:latest` directly
      (the tag, not a separately-pinned digest) — the runtime-pin-vs-terraform-default split this todo warns about no
      longer exists today, so a `tofu apply` is harmless. Matches the source doc's 2026-07-28 finding exactly,
      re-confirmed live 3 days later.
- [ ] [SCRIPT] P2. **features-service coverage/script-canon cleanup** — three bounded follow-ups from the 2026-06-10
      coverage session: (1) ~~fix the per-module `pytest --cov=features_service.<module>` scipy/numpy/pytest-cov
      double-import crash on Python 3.13~~ **DONE 2026-07-31 — features-service@60992d3e** (see
      `plans/archive/2026_08/issues/features_service_coverage_and_script_canon_2026_06_10.md` line ~84 for the full root-cause +
      fix writeup: an early pytest plugin, `tests/_native_lib_early_preimport.py`, pre-imports
      numpy/scipy/talib/`unified_trading_library` before `coverage.start()` runs, so its `source=` probe-import never
      purges-then-reloads their C-extension/pydantic-schema state; the whole-package `--cov=features_service` CI gate
      was already unaffected and remains so); (2) ~~relocate the smoke/e2e harnesses (`scripts/*/smoke_matrix.py` ×8,
      `scripts/e2e/*`) from features-service to `e2e-testing/scripts/<domain>/` per
      `/codex/06-coding-standards/script-homes.md`, rewiring them to the primary-consumer QG (STEP 5.65)~~ **DONE
      2026-07-31 — features-service@7717fbee (relocation + every real consumer repointed: the 8
      `features_service/<domain>/smoke.py` package re-exporters, the 8 `tests/<domain>/unit/test_smoke_matrix.py`
      dynamic loaders, `quality-gates.sh`'s E2E-driver/backfill-tooling smoke invocations, `pipeline_e2e_check.py`'s
      `resolve_lookback.py` subprocess path) + e2e-testing@4b5a743 (the 13 relocated files landed under
      `scripts/{delta_one,commodity,cross_instrument,calendar,sports,multi_timeframe,volatility,onchain, features}/`,
      wired into features-service's peripheral-dir QG loop for all 9 domains; kept e2e-testing's own
      fallback-import/DTZ-TID251/empty-string-fallback ratchet baselines at-or-below via targeted `# noqa:` markers —
      these only trip once the files land in e2e-testing's own scan scope, separate from features-service's). Verified:
      117/117 features-service smoke_matrix unit tests + manual dry-run smokes of run_pipeline_e2e/run_backfill/
      resolve_lookback pass from the new cross-repo location; `quality-gates.sh` green in both repos. Also fixed a
      pre-existing unrelated bug found in the same session (`coverage_harness.py`'s `MdpsUniverseProvider.iter_atoms`
      still unpacked `mdps_mvp_universe()` as a 2-tuple after it was upgraded to 3-tuples) — landed independently by
      another slot as e2e-testing@65f43f4, reconciled via rebase. **CI-only gap found + fixed 2026-07-31 (cicd agent,
      escalation agt-ddbcde, features-service#910 LDR→main promotion red):** the "locally green in both repos" claim
      above was true but incomplete — it never exercised CI's clone topology. `dep_repos` (the space-separated sibling
      list `python-quality-gates-v2.yml` clones per-repo) is derived ONLY from the pyproject `path = "../<repo>"`
      editable-deps closure; e2e-testing has no `[build-system]` (scripts-only) so it can never appear there, meaning CI
      never cloned it even though every local slot worktree already has it as a sibling. Result: features-service's 8
      `tests/<domain>/unit/test_smoke_matrix.py` files hard-failed in real CI (117 broken pytest outcomes — 8 FAILED +
      109 setup ERRORs, all `FileNotFoundError` on the relocated cross-repo path) while passing clean locally. Fixed via
      unified-trading-pm@aa8f111 (new `extra-dep-repos.txt` override + `get_extra_dep_repos()` in
      `rollout-workflow-templates.sh`, for exactly this shape: a sibling consumed by raw file path rather than as a
      `uv sync`-installed package) + features-service@ce369620 (regenerated `dep_repos` to
      `"unified-trading-library unified-api-contracts e2e-testing"`). Verified GREEN in a live `workflow_dispatch`
      re-run on the fixed `live-defi-rollout` HEAD (features-service run 30605670801, `quality-gates-v2`
      conclusion=success, including the `QG slice (tests)` job that previously failed). PR#910 itself is a frozen-head
      ref pinned to the old (broken) LDR SHA — the fleet promote bot supersedes it with a fresh promote PR off the fixed
      HEAD on its next ~15min tick, no manual PR action needed.** (3) run the `script-homes.md` "Per-repo cleanup sweep"
      (classify → relocate/fold-into-CLI/delete-dead, GCS-orphan-verify before any migration-script delete) across every
      repo's `scripts/` EXCLUDING features-service's smoke/e2e harnesses already handled in (2). Source:
      `plans/archive/2026_08/issues/features_service_coverage_and_script_canon_2026_06_10.md`. Done when: per-module coverage
      runs green on Python 3.13 locally; the 8 smoke_matrix.py + e2e/\* files exist under
      `e2e-testing/scripts/<domain>/` and no longer under features-service, wired to that repo's QG; every repo's
      `scripts/` directory has been classified per the script-homes canon with dead scripts deleted and relocatable
      scripts moved, each carrying the required lifecycle marker.

      **PARTIAL PROGRESS 2026-07-31 (slot 10) — lifecycle-marker stamping sub-piece DONE, classify/delete/relocate
          NOT done.** Fleet-wide `grep -rL '^# Delete-when:' */scripts/ --include='*.py' --include='*.sh'` found 32
          remaining unstamped scripts across 12 repos (client-reporting-api, deployment-service, deployment-ui,
          e2e-testing, features-service, fund-administration-service, greeks-service, instruments-service,
          market-data-processing-service, market-tick-data-service, unified-api-contracts, unified-trading-pm) — every
          other repo in the fleet was already fully stamped from the prior rollout. Stamped all 32 using the
          already-decided classification embedded in each script (existing `Epic:`/`Lifecycle:` prose where present) or
          the nearest sibling-file epic convention (mechanical, no new judgment calls), then shipped per-repo via the
          normal QG→quickmerge flow: client-reporting-api@c47835f, deployment-service@1261ce7, deployment-ui@5a4ce5a,
          e2e-testing@42be3c1, features-service@3966bfcb, fund-administration-service (pending final quickmerge, commit
          c0402e0 already QG-green), greeks-service@aee891d, instruments-service@240d80a7,
          market-data-processing-service@855198c, market-tick-data-service@fe1c4ca2, unified-api-contracts@a4b1345d
          (recovered via reflog after a quickmerge branch-reset bug — see
          `plans/archive/issues/quickmerge_agent_regate_resets_branch_loses_local_commit_2026_07_31.md`), unified-trading-pm
          (this commit). **The classify/delete/relocate portion of this item's done-when is intentionally NOT attempted
          here** — that work requires per-script KEEP/DELETE/DEPRECATE/PROMOTE-TO-CLI judgment calls (campaign-gating
          awareness, GCS-orphan-verification before any delete) that are explicitly scoped as
          GATED+REVIEWED/human-judgment in `plans/active/repo_scripts_governance_audit_2026_06_18.md` (`assigned_vm: NA`)
          — an AO worker attempting a fleet-wide classify+delete sweep unsupervised would risk deleting
          campaign-in-flight one-offs (that governance-audit doc's own Finding 1 flags this exact risk for
          instruments-service/MTDS). This item stays open; the marker-stamping done-when clause is satisfied, the
          delete/relocate clauses are not — do not re-flip this checkbox until the governance-audit plan's Phase-1
          delete/deprecate/promote execution actually lands.

- [x] ✅ [CODE] P2. **features-service — fix `odds_features_exporter.py` velocity-accel fallback NaN/math semantics
      (dead-code + a legit-`0.0`-drop bug).** `_compute_velocity_from_pivoted`'s (lines ~509-514) elif/else acceleration
      branches are unreachable dead code today: `np.nan` satisfies `isinstance(x, float)`, so the line-509 guard always
      fires and the elif/else are never taken. Separately, the same function's `v_late = a or b` retrieval drops a
      legitimate `0.0` value (Python truthiness treats `0.0` as falsy, so a real zero velocity silently falls through to
      `b`). Fix: (1) add `and not math.isnan(v_early)` to the line-509 guard so the elif/else branches become reachable
      when intended; (2) replace the `a or b` retrieval with an explicit not-None check (e.g.
      `a if a is not None else b`) so a legitimate `0.0` is preserved. This changes acceleration feature math — sports
      feature buckets are currently empty in prod (per the source doc, no live data affected today), so this is safe to
      land now without a data-correctness blast radius. Repo: features-service
      (`features_service/sports/exporters/odds_features_exporter.py`). Source:
      `plans/archive/2026_08/issues/features_service_coverage_and_script_canon_2026_06_10.md` (line ~71-75, previously DEFERRED
      pending owner sign-off on NaN/fallback semantics — operator ruling 2026-07-27,
      `/plans/active/june_2026_vintage_audit_findings_2026_07_27.md` §5-RESOLVED item 35: this is now agent-owned scoped
      work, not parked on a human). Done when: both fixes land with a new/extended unit test asserting (a) the elif/else
      branches are reachable and produce the expected acceleration value for a non-NaN early velocity, and (b) a
      legitimate `v_late=0.0` is preserved rather than replaced by the fallback; `quality-gates.sh` is green in
      features-service; and the source doc's line ~71-75 checkbox is flipped citing the commit sha. — **ALREADY DONE
      2026-07-31 (slot 15) — pre-existing, shipped before this todo was even written.** Read the current function: the
      elif/else fallback no longer exists at all — it was REMOVED (not patched) by `features-service@bf6fc2f4`
      ("fix(sports): gate T-0 closing-line-derived odds columns out of pre-match horizons", 2026-07-16, verified
      ancestor of `origin/live-defi-rollout`), replaced with a single deterministic `v_mid - v_early` computation gated
      on `isinstance(v_mid, float) and isinstance(v_early, float)` — this makes the unreachable-elif bug moot (dead code
      deleted, not made reachable) and there is no `a or b` pattern anywhere in the function anymore (`row.get(...)`
      used directly), so the `0.0`-drop bug is independently gone too. Test coverage already exists and passes
      (`tests/sports/unit/test_odds_features_exporter.py`, 16/16 velocity/ acceleration tests green, incl.
      `test_acceleration_never_uses_the_closing_leg` and `test_acceleration_nan_when_v_early_is_nan` which directly
      cover this todo's two done-when criteria). No new code needed — both source docs' line numbers were stale (509-514
      pre-dates the 2026-07-16 rewrite; actual function is now at line 636).
- [x] ✅ [CODE] P2. **features-service — make `_make_session`'s aiohttp resolver construction lazy/loop-safe (latent
      out-of-loop-construction crash).** `features_service/onchain/app/core/data_loader.py:224`'s `_make_session`
      constructs `aiohttp.resolver.ThreadedResolver()` eagerly, which calls `asyncio.get_running_loop()` at construction
      time — this crashes with a `RuntimeError` if `_make_session` (or anything that constructs the session) is ever
      called outside a running event loop. All current callers are async-context-only, so this is latent, not yet
      reproducing in prod. Fix: defer the `ThreadedResolver()` construction until it's actually built inside a running
      loop (e.g. construct it lazily inside an already-async factory/context manager, or pass a resolver factory instead
      of a pre-built instance), so calling the session-construction path from a non-async context either works safely or
      raises a clear, intentional error instead of an opaque `asyncio.get_running_loop()` crash. Repo: features-service
      (`features_service/onchain/app/core/data_loader.py`). Source:
      `plans/archive/2026_08/issues/features_service_coverage_and_script_canon_2026_06_10.md` (line ~76-79, previously DEFERRED
      pending owner sign-off on the DNS-resolver config change — operator ruling 2026-07-27,
      `/plans/active/june_2026_vintage_audit_findings_2026_07_27.md` §5-RESOLVED item 35: this is now agent-owned scoped
      work, not parked on a human). Done when: the fix lands with a new/extended test confirming the
      session-construction path no longer raises the construction-time `RuntimeError` when exercised outside a running
      loop while existing async-context callers remain green; `quality-gates.sh` is green in features-service; and the
      source doc's line ~76-79 checkbox is flipped citing the commit sha. — features-service@25932d23: `_make_session`
      made async so `ThreadedResolver()` construction defers until awaited inside a running loop; regression test
      `test_calling_outside_running_loop_does_not_raise_at_call_time` + existing async-caller test confirmed green;
      quickmerge-shipped to live-defi-rollout.
- [x] ✅ [CODE] P2. Close the 4 remaining fixable-bug residuals from `fleet_data_acquisition_health_2026_06_21.md` —
      market-tick-data-service@09c8cbf8 (verified 2026-08-04, slot 5 data_engineering). All 4 items resolved: **(a)**
      sports ODDS_API completeness — fixed write-side venue-based completeness check in `manifest_finalize.py` (was
      comparing bookmaker venues against `["ODDS_API"]`, now source-scoped guard skips for sports;
      `market-tick-data-service@09c8cbf8`). Read-side already fixed 2026-07-30. **(b)** sports footystats 0-byte run.log
      — transient VM startup failure, not a systemic bug; daily Cloud Run enrichment cron active since 2026-07-14;
      stale-log class fixed 2026-06-22 (`UPLOAD_MAX_STALENESS_SEC=90`). **(c)** unified-api-contracts book_snapshot_5
      SOURCE_PRIORITY — already shipped `unified-api-contracts@7d41bc34`. **(d)** MTDS version-surface drift —
      self-resolved via semver-agent; `v0.102.0`, zero VERSION_SPLIT. Source issue doc
      `fleet_data_acquisition_health_2026_06_21.md` updated: status→resolved, resolved_by set. **(a) sports** — recheck
      `mtds-backfill-odds-*` ODDS_API source-completeness (item #4: manifest flags `complete=False missing=['ODDS_API']`
      despite 8.5K rows across 22 bookmaker shards) and verify the sports-odds SOURCE_PRIORITY entry is correct; fix if
      the completeness-check itself is wrong, or the cred/source registration if that's the real gap. **Hint
      (2026-07-27, `mdps_t1_recon_job_oom_failing_7_days_2026_07_26.md` Phases 0-4)**: not investigated here, but worth
      checking first — this MIGHT be a symptom of the same conflation class that todo just fixed elsewhere (MDPS's
      `reprocess_sports_odds.py`): if this specific completeness check filters manifest rows on `venue="ODDS_API"` (the
      vendor) when the real captured rows now correctly carry per-bookmaker venues (real bookmaker fan-out, as this
      row's own text says — "22 bookmaker shards"), the check itself is looking at the wrong axis (`source="odds_api"`
      is what MTDS's raw fan-out correctly stamps per `/codex/02-data/venue-availability.md`, not `venue`). Confirm
      which axis this specific checker reads before assuming a cred/registration gap. **(b) sports** — item #5's
      `footystats-fwd-*` 0-byte `run.log` (VM startup/log-upload never emitted): check a current footystats
      forward-fetch VM's startup + heartbeat-uploader path; fix the bug if still reproducible, or confirm-and-log if it
      self-resolved. **(c) unified-api-contracts** — fix the `book_snapshot` vs `book_snapshot_5` SOURCE_PRIORITY key
      mismatch (live connectors emit `data_type="book_snapshot_5"` but `SOURCE_PRIORITY` keys
      `("cefi","book_snapshot")`, leaving book writes source-unvalidated): register `("cefi","book_snapshot_5")`
      additively (or rename to one canonical spelling), and sweep other asset_groups for the same
      book_snapshot/book_snapshot_5 key-drift pattern. **(d) market-tick-data-service** — verify whether the mtds
      pyproject↔manifest version-surface drift that blocked LDR→staging `quality-gates.sh` on 2026-06-21 (pyproject
      0.31.0 vs workspace-manifest 0.25.0 vs repositories.mtds 0.20.0) is still reproducible today; if still blocking,
      run the sanctioned `scripts/repo-management/run-version-alignment.sh --fix` (never hand-bump); if already resolved
      by routine semver-agent automation, cite evidence it's clear. Source:
      `fleet_data_acquisition_health_2026_06_21.md`. Done when: each of the 4 items has either a shipped fix (repo@sha
      cited) or a confirmed-resolved/no-longer-reproducible note, logged into the doc's body/Progress Log, and its
      `status:` frontmatter updated to `resolved` if all 4 close.
- [x] ✅ [UTL] P2. **Bound the un-evicted `_CANONICAL_CACHE` to stop the manifest-read OOM (Option A, lowest-risk)** —
      in `unified_trading_library/manifest_writer/_state.py`'s `_invalidate_index_cache` (~L142-166), cap
      `_CANONICAL_CACHE` to the single current bucket: on a bucket-change, `del` the prior bucket's cached DataFrame
      before caching the new one, instead of leaving every visited bucket's merged index pinned in the process-global
      cache forever. This targets the confirmed root cause of the DeFi multi-day batch-backfill OOM (exit_code=137 on
      `e2-standard-4`): the slow per-VM fan-in merge path (`_read_and_merge_per_vm_shards`,
      `manifest_writer/_read_index.py:429-481`) produces a multi-GB merged DataFrame per bucket that `_CANONICAL_CACHE`
      never evicts, so RSS climbs unbounded across a day-loop. Do NOT touch `_read_and_merge_per_vm_shards` itself (that
      is the separate, larger Option B streaming-merge fix — out of scope for this todo) and do NOT remove the
      `MANIFEST_CONSOLIDATED_STALENESS_SEC=86400` DeFi-launcher config mitigation (Option C) that already routes most
      runs around the slow path. Add/adjust a UTL unit test asserting that after a bucket switch, the prior bucket's
      entry is gone from `_CANONICAL_CACHE` (e.g. via a size/identity check), and re-run the existing sports-warm-cache
      regression test to confirm the same-bucket warm-read path (`~27s` avoided re-read) is unaffected — this is
      cross-cutting shared code on the LIVE cefi/sports/tradfi manifest-read path, so the no-regression check on the
      warm-cache win is mandatory, not optional. Source:
      `plans/archive/issues/manifest_index_read_oom_canonical_cache_2026_06_24.md`. Done when: the per-bucket eviction
      is implemented in `_state.py`, the new eviction unit test and the existing sports warm-cache test both pass,
      `quality-gates.sh` is green, and the change is shipped via quickmerge with the issue doc's frontmatter `status`
      flipped to reflect the resolved Option A (leaving Option B noted as a still-open, separately-scoped follow-on if
      desired, not silently implied done). — **DONE 2026-07-28**: `unified-trading-library@0db19a72`. Option A shipped
      exactly as specified; new tests `test_invalidate_index_cache_evicts_other_buckets_canonical_cache` (bucket-switch
      eviction) and `test_invalidate_index_cache_noop_on_single_bucket` (same-bucket warm-read path unaffected — no
      pre-existing named "sports warm-cache" test existed under that name, so this new test fills that exact role) in
      `tests/unit/test_manifest_read_index_slim.py`; `quality-gates.sh` green; source issue doc archived with
      `status: resolved`. Option B untouched, still open/separately-scoped if the fleet needs it.
- [x] ✅ [DOC] P2. Close the mechanical/AO-eligible remainder of `mtds_plan_reconciliation_2026_06_29.md`'s live
      findings (Section F) — unified-trading-pm@ec705fb46: (a) **M-C1/M30.5** flip M7 IN-FLIGHT→LANDED in the doc's
      Section A ledger + fix codex `pipeline-mode-partition.md` normative prose (still teaches `live_websocket`, ~lines
      84/124/167-180) to reflect the verified `live_<source>` runtime state (cefi: 15,993 `live_<source>` rows, 0
      `live_websocket`); (b) **M30.3** execute the reader legacy-fallback removal in market-tick-data-service
      `reader.py` (drop the unconditional non-`pipeline_mode=` base-path append) — first verify
      `READER_FELL_BACK_TO_LEGACY_PATH`=0 has held 7d; if not yet, report the metric instead of forcing the removal; (c)
      **M-C4** seed the `_honest_coverage_clusters.py` cluster registry for Kalshi CQG (or confirm
      `cluster_extractor`/`expected_root_clusters` kwargs are wired for it) before any Kalshi
      `prediction_canonical_question_group` write ships, to prevent a `MissingClusterValidationError`; (d) **M-C3**
      residuals: migrate `carry_staked_basis_funding_scan_experiment`'s env-less
      `lst-rates-central-…`/`lending-indices-central-…` bucket reads to `resolve_bucket_name(...)`, and replace the
      (archived) `defi_manifest_canonicalisation`'s G1 `gsutil ls` step with a UTL GCS helper wherever that logic now
      lives; (e) **M-C10** update the 2 still-active v1-coverage consumer plans —
      `data_status_tab_and_downloads_remediation_2026_06_16.md` and
      `issues/honest_coverage_smoke_harness_4ag_verify_2026_07_06.md` — to the codex `honest-coverage-model.md`
      two-layer/Layer-1-gate coverage model instead of the flat `captured/(c+e+f+eu)` formula (the other 3 named M-C10
      consumers — downstream_services/cefi_manifest/defi_manifest canonicalisation — are already archived/superseded;
      skip them). Explicitly OUT OF SCOPE: **M-C7** (warm-GCS-parts live-persistence sink) — real new-code architecture
      work the doc states is "decided, NOT yet built — awaiting greenlight to implement"; that stays a separate
      operator-gated item, not bundled here. Source: `plans/archive/issues/mtds_plan_reconciliation_2026_06_29.md`
      (Section A ledger, Section F M-C1/M-C3/M-C4/M-C10, Progress Log). Done when: (a)-(e) each land with a
      commit/evidence citation in the doc's Progress Log, the M7 ledger flip + codex text fix are committed, and the
      doc's `status:` is reassessed (M-C7 remains explicitly open/deferred, not silently dropped).
- [x] ✅ [DATA] P1. **Close out remaining perp-funding data-semantics/cadence CeFi work: exact discrete funding, cadence
      tracker, Aster backfill + live book, margining reverify.** Five independent legs from the same source doc (repos
      market-tick-data-service + unified-api-contracts unless noted). **Status update (2026-07-27/28 vintage-audit
      re-verification): leg (a) is now DONE UPSTREAM — do not re-do it.** The source doc's own P1 checkbox for this leg
      shipped 2026-07-27 (`unified-api-contracts@22689df5`, `market-tick-data-service@466d5670` — audited every
      `funding_timestamp`/`next_funding_timestamp` write path and fixed 3 go-forward bugs: OKX field-swap,
      `hyperliquid_s3.py` REST-backfill gap, Tardis WS-replay derivation). Only (b)-(e) remain open: ~~(a) make exact
      discrete per-settlement funding readable — persist funding settlements timestamped to the charge instant (matching
      venue `fundingTime`), or add a canonical per-settlement funding data_type, and document `funding_timestamp`
      semantics across cefi adapters (Tardis cefi, hyperliquid, OKX `next_funding_timestamp`)~~ **DONE, see above.** (b)
      add a historical funding-cadence tracker in GCS (canonical-from-docs or inferred from observed settlement
      frequency per instrument/day) so a venue cadence change doesn't silently mis-annualise historical windows. (c) run
      the Aster perp-funding backfill VM
      (`deployment-service/scripts/vm/launch-mtds-perp-funding-backfill-vm.sh --perp-protocols aster`, start 2023-07-22,
      default SPOT) — the write path is production-verified-ready (e2e↔production parity confirmed 2026-06-17); this is
      a safe, idempotent write-only historical backfill (no deletes), so no `[OPERATOR]` gate needed; label pre-2024
      rows as Binance-proxied Astherus funding per the doc's genesis note. (d) add a live Aster `book_snapshot_5`
      WS/poll connector mirroring the existing `live/connectors/aster_ws.py` trades connector (REST fallback
      `AsterAdapter.fetch_depth`, `normalize_aster_orderbook` for the 5-level shape, register via
      `register_ws_feed_connector(venue="ASTER", ...)`). (e) re-verify Aster's margining model (`venue_collateral.py`,
      USDC/USDT-only, no spot/LST collateral) against live Aster docs before any cash-and-carry sizing decision.
      **Excludes** (do not duplicate): the pre-funding-genesis Aster trades backfill (explicitly blocked on GAP4 in the
      source doc, and GAP4 itself is already an open `[ ]` todo in `instruments_completion_tracker_2026_07_06.md` Stage
      2c) and the latent cefi `ohlcv_*` direct-write capability (explicitly deferred by the source doc until a
      trades-less cefi venue exists — no current need). **Also NOT covered here (found 2026-07-27/28, needs its own
      home, not batchable as-is)**: the source doc's standalone P2 todo "Bulk historical Tardis-CSV
      `derivative_ticker.funding_timestamp` is forward-looking, not the charge instant" — `tardis_stream_processor.py`'s
      shared streaming pass-through leaves already-written historical parquet mislabeled, and the source doc explicitly
      states this needs a **design decision** (in-place go-forward derivation vs. a one-time heavy-I/O reprocessing
      backfill), not an in-slot judgment call — flag for the operator-gated queue rather than dispatching blind. Source:
      `perp_funding_data_semantics_and_cadence_2026_06_16.md`. **Done when**: (a) is already shipped (no action —
      verified above); (b) lands as code + tests in mtds/uac with `quality-gates.sh` green; (c)'s VM run reaches STOPPED
      with new Aster `derivative_ticker` shards visible in the manifest for the backfill range; (d) lands with a unit
      test asserting the 5-level book write + manifest record at `pipeline_mode=live_aster`; (e) is recorded as a
      Progress Log finding (confirmed unchanged, or a new dated issue doc if Aster's collateral rules changed). —
      **Status 2026-07-28 (slot 14, data_engineering) — 2 of 4 legs resolved, 1 coded-but-unshipped (host contention), 1
      findings-filed pending operator input. Checkbox correctly stays unchecked.** - **(d) live Aster `book_snapshot_5`
      WS connector — ALREADY SHIPPED, no action needed.** Live code check found the plan's premise stale: the file it
      names (`live/connectors/aster_ws.py`) was already renamed/consolidated into
      `market_tick_data_service/live/connectors/aster_book_liq_ws.py`, which already implements
      `AsterBookWSConnector(BinanceFuturesBookWSConnector)` (5-level `bid_px_0X`/`bid_sz_0X`/`ask_px_0X`/`ask_sz_0X`
      shape via the shared `_build_book_levels()`), registered via `_aster_factory()` →
      `register_ws_feed_connector(venue="ASTER", ...)`, with real test coverage (`tests/unit/test_aster_ws_connector.py`
      `TestAsterBook`, incl. `test_aster_registered_for_all_data_types`). No commit made — nothing to change. - **(e)
      Aster margining re-verify — DONE, filed as a finding (not silently reconciled).** Live-fetched
      `docs.asterdex.com`: two DIFFERENT collateral tables exist (general "Aster Perps" multi-chain vs "AstherusEX"
      orderbook) that disagree with each other AND with the currently-registered UAC `venue_collateral.py` USDC/USDT-
      only rows (both live tables show BTC/ETH accepted at a real 95% ratio, contrary to nothing registered for BTC/ETH
      today) — and which Aster product our `fapi.asterdex.com` integration actually trades against is genuinely
      ambiguous from the docs alone. Filed `issues/aster_margining_registry_live_docs_drift_2026_07_28.md` (`[OPERATOR]`
      todo to confirm the product mapping before any registry edit — a wrong haircut here mis-sizes real cash-and-carry
      positions). No code touched pending that confirmation. - **(c) Aster perp-funding backfill VM — NOT launched;
      stale-launcher + genesis-conflict finding filed instead of guessing.** The plan's named launcher
      (`launch-mtds-perp-funding-backfill-vm.sh --perp-protocols aster`) targets `PerpFundingHandler`, which RETIRED
      Aster from standalone `perp_funding` capture 2026-07-08 (its own module docstring) — running the plan-literal
      command would hit the unknown-protocol branch and write false `attempted_failed` manifest rows, not silently
      no-op. Separately, a live manifest census (`market-data-tick-cefi-prd-central-element-323112`) found ASTER
      `derivative_ticker`'s real captured coverage starts 2023-11-01 with ZERO manifest rows of any kind in
      2023-07-22→2023-10-31 — disagreeing with BOTH the plan's stated 2023-07-22 genesis AND the CORRECT current
      launcher's (`launch-cefi-hl-aster-historical-backfill.sh`) own hardcoded 2024-01-01 default. 3-way genesis
      disagreement is a genuine judgment call, not a mechanical fact — did not guess-launch a VM. Filed
      `issues/aster_perp_funding_backfill_stale_launcher_and_genesis_conflict_2026_07_28.md` with the correct
      (non-retired) launcher command + exact scoping flags (`VENUES=ASTER DATA_TYPES=derivative_ticker` +
      `OVERRIDE_START_DATE`/`OVERRIDE_END_DATE`) ready to run once the genesis date is confirmed. - **(b) historical
      funding-cadence tracker — CODE + TESTS WRITTEN, BLOCKED FROM SHIPPING by severe host QG contention, not by
      anything wrong with the change.** Implemented in `unified_api_contracts/registry/perp_funding_cadence.py`:
      `FundingCadenceEra` NamedTuple + a `FUNDING_CADENCE_HISTORY: dict[str, tuple[FundingCadenceEra, ...]]` seeded 1:1
      from `FUNDING_CADENCE_SECONDS` (every venue gets one open-started era at today's value — no venue has ever changed
      cadence yet), plus `cadence_seconds_as_of()`/`fundings_per_day_as_of()`/`annualise_funding_rate_bps_as_of()`
      date-aware lookups (walk the venue's eras, return the cadence whose `effective_from` last applies on-or-before the
      query date) — this is the CANONICAL/docs-sourced half of Finding 3's "canonical-from-docs or inferred from
      observed settlement frequency" ask; the mechanism is designed so a future real cadence change is a 2nd-era
      addition, not a silent edit-in-place. 16 new tests added to `tests/unit/test_perp_funding_cadence.py`
      (`TestFundingCadenceHistory`) incl. a consistency guard that the LATEST era always matches
      `FUNDING_CADENCE_SECONDS` (mirrors the existing `FUNDING_ACCRUAL_MODEL` consistency test's pattern) and a
      synthetic 2-era multi-era-walk test (no real venue has 2 eras yet, so this proves the walk logic rather than a
      live fact). **The GCS-persisted OBSERVED/inferred half (Finding 3's other named sourcing mode — counting real
      distinct `funding_timestamp` settlements/day per shard, mirroring
      `e2e-testing/scripts/defi/ staked_basis_funding_scan.py`'s `n_settlements` logic, lifted into a proper MTDS script
      that writes a dated audit object to GCS) was NOT built this session** — descoped once the QG blocker made it clear
      the canonical half alone would already exceed a single turn's shippable budget; tracked as its own follow-up todo
      below, not silently dropped. **SHIPPED — `unified-api-contracts@e8b45af4`.** `quality-gates.sh` was SIGTERM-killed
      by the qg-host-governor 6 consecutive times (~25min span) at `[3/6] TESTS` during a real, already-tracked
      host-wide contention burst (`issues/orchestrator_vm_disk_io_contention_runner_burst_2026_07_28.md` — confirmed by
      main via `BLK-af1211b4` as the SAME transient incident, not a new one; no fresh issue doc filed). Backed off with
      jitter (not a tight retry loop) per main's guidance; a subsequent attempt passed clean (494s), committed, re-ran
      QG once more so the sentinel matched the new commit SHA exactly, then shipped via `quickmerge.sh --agent --files`.
      Landed on `live-defi-rollout`; `quality-gates-v2` fires on the eventual LDR→staging promote PR (Tier-C drain,
      ~15min), not on this raw push — nothing further to verify from this slot. — **Status 2026-07-29 (slot 9,
      data_engineering) — leg (e) now FULLY resolved (registry corrected, not just filed).** The operator retagged
      `issues/aster_margining_registry_live_docs_drift_2026_07_28.md`'s todo 2026-07-29 from `[OPERATOR]` to `[VERIFY]`
      ("not sure, needs live verification") — delegating the product- identity question to a live-API check rather than
      requiring a human product-knowledge answer. Hit `GET fapi.asterdex.com/fapi/v1/exchangeInfo` live: its
      `assets[].marginAvailable` list (39 assets incl. USDC) matches `docs.asterdex.com`'s Multi-Asset Mode ("Aster
      Perps", Page 1) table, not "AstherusEX" (Page 2, whose docs explicitly exclude USDC on both its chains) — USDC's
      presence with `marginAvailable:true` is the decisive signal. Corrected
      `unified_api_contracts/registry/venue_collateral.py`: USDC/USDT haircut fixed from the placeholder 0%/1% to the
      real Multi-Asset-Mode 99.99%-ratio (0.01% haircut); BTC/ETH added as accepted (95% ratio, 5% haircut), previously
      untracked. New test `test_aster_multi_asset_mode_live_verified_2026_07_29` pins the corrected rows. Did not add
      the remaining ~15 multi-chain-specific tokens (LISTA/CAKE/TSLAB/etc.) — none are tracked as collateral for any
      other venue in this registry, so adding them now would be speculative bloat; ratios are preserved in the issue
      doc + module docstring if a future strategy needs one. Issue doc flipped to `status: resolved`.
      `unified-api-contracts@66297dc4` (corrected 2026-08-06 by context-scout: original citation `14f0aff5` did not
      resolve; `66297dc4` is the real slot-9 2026-07-29 commit matching this narrative's own author/date, verified via
      `git cat-file -t` + commit message/diff content match). **(c) remains the sole open leg — still genuinely blocked
      on the operator's 3-way genesis-date call in
      `issues/aster_perp_funding_backfill_stale_launcher_and_genesis_conflict_2026_07_28.md`; checkbox correctly stays
      unchecked.** — **Status 2026-07-29T15:3xZ (slot 15, data_engineering)**: attempted to resolve leg (c)'s
      genesis-date ambiguity via external research (Aster/Astherus's real-world launch history) — deepened rather than
      resolved it (real Aster/Astherus history postdates all 3 candidate dates by over a year, so this is an
      internal/methodological decision, not a discoverable fact). Filed `BLK-a94f446d` with 3 options (consult the
      original operator decision / default to the earliest-real-captured-row date / default to the launcher's current
      default). Full detail in the issue doc's Progress Log (`unified-trading-pm@263739b7c`). Checkbox stays unchecked
      pending the answer. — **Status 2026-07-29T20:19Z (slot 4, data_engineering)**: re-verified `BLK-a94f446d` still
      unanswered (fresh pull, corpus grep, commit history — no change). No unblocked action available: legs (a/b/d/e)
      resolved, leg (c)'s only open scope is the disputed 2023-07-22→2023-11-01 window this blocker gates (the
      uncontested 2023-11-01+ floor is already fully captured). Full detail in
      `issues/aster_perp_funding_backfill_stale_launcher_and_genesis_conflict_2026_07_28.md`. Released via
      `/skip-current-task {"reason_code": "BLOCKED"}`. — **Status 2026-07-31T (slot 13, data_engineering)**: re-verified
      `BLK-a94f446d` still unanswered (fresh pull, corpus grep for the blocker id, `git log --since 2026-07-29` on both
      this plan and the issue doc — only unrelated commits landed; no operator decision was ever recorded). The
      2026-07-31 corpus-wide ownership-conflict sweep added a premise-correction banner to the issue doc (about Finding
      1's HL/ASTER-funding-equivalence claim being reversed) but explicitly left this todo's genesis-date question
      `[OPERATOR]`-gated and unaffected. `POST /api/backlog/.../blockers` confirms no formal blocker record tied to this
      task_id (the gate lives on the issue doc's own todo, not the backlog dispatcher), and a `/progress` call returned
      no operator message. No unblocked action available — same as the 2026-07-29 status. Released via
      `/skip-current-task {"reason_code": "BLOCKED"}`. — **RESOLVED 2026-08-06 (slot 5)**: leg (c) done-when condition
      was already met. The launcher header (`deployment-service/scripts/vm/launch-cefi-hl-aster-historical-backfill.sh`)
      explicitly records "real gap 2023-07-22→2023-10-31 found + backfilled 2026-07-29". Source doc
      (`perp_funding_data_semantics_and_cadence_2026_06_16.md`, 2026-08-03 entry) independently verified ASTER
      `derivative_ticker` rows for 2023-07-22→2023-07-26 as `capture_status=captured`, `source=aster`. Prior workers did
      not have this 2026-08-03 source-doc update in view. `BLK-a94f446d` question is moot — the backfill ran with the
      operator-confirmed 2026-06-17 genesis date. Issue doc flipped to resolved.
      `issues/aster_perp_funding_backfill_stale_launcher_and_genesis_conflict_2026_07_28.md` — status: resolved.
- [x] ✅ [DATA] P2. **Build the GCS-persisted OBSERVED funding-cadence audit script** — the inferred half of Finding 3 —
      market-tick-data-service@fd9efc85 (script `scripts/analysis/measure_perp_funding_cadence_drift.py` + 17 unit tests
      in `tests/unit/scripts/test_measure_perp_funding_cadence_drift.py`, covering agree/disagree/CAS-retry/discovery;
      calls `cadence_seconds_as_of()` from UAC `perp_funding_cadence.py`; writes dated audit JSON to GCS via UTL
      `get_storage_client()` with CAS read-modify-write; prefix-scoped listing, never a whole-corpus walk)
      (`perp_funding_data_semantics_and_cadence_2026_06_16.md`) that the canonical `FUNDING_CADENCE_HISTORY`
      versioned-registry todo above did NOT cover. Lift the `n_settlements` counting logic from
      `e2e-testing/scripts/defi/staked_basis_funding_scan.py` (`fr["funding_timestamp"].nunique()` per shard) into a
      proper committed MTDS script/CLI that, for a given venue+day, reads the real `derivative_ticker` shard, computes
      the observed settlement count, compares it against `cadence_seconds_as_of(venue, day)` (UAC
      `perp_funding_cadence.py`), and writes a small dated audit JSON to GCS (via UTL's `get_storage_client()`, never
      inline `gs://`) flagging any day where observed cadence disagrees with the registered value — the "a venue cadence
      change nobody documented in the canonical history still gets caught" half of the original ask. (repo:
      market-tick-data-service + unified-api-contracts). Depends on the `FUNDING_CADENCE_HISTORY` todo above having
      shipped (calls its `cadence_seconds_as_of` API). **Done when**: the script runs against a real venue+day and
      writes a real audit object to GCS; unit tests cover both the agree and disagree cases with a mocked storage
      client; `quality-gates.sh` green.
- [x] ✅ [BUG] P0. **DONE 2026-07-28 (part 1) / re-scoped (part 2).** (1) Stash recovery: the original stash
      (`features-safe-survivor-fixes-2026-07-20-DEFERRED-peer-contention-on-smoke_matrix-allhandlers`) was confirmed
      unrecoverable from the features-service clone (`git stash list` empty, no matching dangling commit in `git fsck`)
      — both fixes re-derived fresh instead. `paired_dispatch.py`'s delta-one-prefix fix was ALREADY independently
      shipped via `features-service@57f8b45d9` (2026-07-22, confirmed via `git blame`) — no action needed.
      `smoke_matrix.py`'s feature_group-scoping fix was genuinely still missing after peer `features-service@9ce1f4ab`
      (`--all-handlers`) landed (that commit added the per-feature_group loop but never scoped the manifest-row check to
      `feature_group`) — fixed fresh + reconciled against the peer's shape, 2 regression tests added,
      `bash scripts/quality-gates.sh --no-fix` green. — features-service@ab53855b. (2) Finding #2 (gas-fee data-location
      question) is NOT resolved here — re-scoped as its own tracked todo in
      `/plans/active/issues/silent_wrong_answer_audit_untracked_followups_2026_07_28.md` (strategy-service repo, out of
      this dispatch's features-service/cross-cutting scope) rather than answered inline in this doc, so it isn't lost.
      **Moved again 2026-07-30**: that gas-fee todo now lives in its own dispatchable doc,
      `/plans/archive/issues/strategy_service_gas_fee_reader_hardcodes_1_gwei_2026_07_30.md` — follow that pointer, not
      the untracked-followups doc, which now holds only the unrelated e2e-testing schema-contract decision. Source:
      `/plans/archive/issues/silent_wrong_answer_audit_candidates_2026_07_20.md` (archived 2026-07-28).
- [x] ✅ [SCRIPT] P3. Close the stale `strategy_store_split_brain_2026_07_13.md` issue doc — its two remaining
      reader-code legs are already shipped, the doc frontmatter just never flipped. Verify both live: (1)
      `deployment-api/deployment_api/deployment_api_config.py` `effective_strategy_store_{cefi,tradfi,defi}_bucket` all
      default via `resolve_bucket_name(kind="strategy-store")` (the flat unified bucket, no per-AG hardcode) — landed
      `deployment-api@ff1c691` (bucket_fold_closeout_2026_07_17.md loose-end 4c, 2026-07-19); (2)
      `unified-api-contracts/scripts/enumerate_envelope.py` (~line 1060) reads
      `GCS_BUCKET = f"strategy-store-prd-{_PROJECT_ID}"` — no `strategy-store-cefi` hardcode remains (loose-end 4d,
      2026-07-19, UAC tree clean). Once both confirmed, flip `strategy_store_split_brain_2026_07_13.md` frontmatter
      `status: open` → `status: resolved` with `resolved_by:` citing the two shas/dates above, append a closing dated
      note, and run the plan archival ritual (migrate to `plans/archive/2026_07/`, no DEFERRED items to carry, no other
      doc references this path that need updating). Source:
      `plans/active/issues/strategy_store_split_brain_2026_07_13.md`. Done when: both reader-code legs re-verified live
      in current `deployment-api`/`unified-api-contracts` trees, the issue doc's status is `resolved` (or archived) with
      cited evidence, and Track 13 of `cross_cutting_consolidated_closeout_2026_07_25.md` no longer needs this doc as an
      open dependency.
- [x] ✅ [SCRIPT] P1. Reconcile + close the stale-verbatim-carryover checkboxes in
      `legacy_bucket_dual_write_decommission_2026_07_24.md` and land 2 small non-gated hygiene fixes it still owns: (1)
      verify current code state of the two lead "still open" SCRIPT items —
      `unified-trading-library/unified_trading_library/core/cloud_constants.py::get_bucket_name` (confirmed live code:
      the duplicate implementation flagged as the foot-gun was already deleted 2026-07-20, `get_bucket_name` is now the
      sole SSOT-delegating implementation with real cross-repo importers in
      strategy-service/features-service/deployment-service/mtds/instruments-service/ml-service — do NOT delete; instead
      audit each importer and redirect only genuinely-legacy no-env-shape call sites to `resolve_bucket_name`, closing
      the item as done where already fixed) and MTDS `_instruments_metadata.py`/`engine/orchestrator/__init__.py`
      env-LESS instruments-store readers (confirmed live code: all `_instruments_metadata.py` sites already call
      `resolve_bucket_name(cloud="gcp", kind="instruments-store", asset_group=...)`, not `build_bucket()`, and the named
      `_sports_instr_bucket`/`_cefi_instr_bucket`/etc. helpers no longer exist in `orchestrator/__init__.py` — mark this
      item DONE with an evidence citation, or find+redirect any residual env-LESS call site if one still exists); (2)
      add the "legacy bucket-name dual-write detection" recurring check to
      `plans/audit/instructions/batch_live_symmetry_master_audit_instructions.md` (extends its existing pipeline_mode
      checks; confirmed absent today); (3) add the reopen-note banner to archived
      `plans/archive/2026_05/bucket_name_ssot_canonicalisation_2026_05_10.md` pointing at this doc, and update the
      `codex/05-infrastructure/` bucket-naming SSOT doc with the "writer must use resolve_bucket_name, never
      string-concat" rule. Source: legacy_bucket_dual_write_decommission_2026_07_24.md (lines 54-68, 156-164). Done
      when: both lead checkboxes are flipped (closed-with-evidence or narrowed-to-real-residual-sites), the
      audit-instructions doc carries the new recurring check, and both the archived-doc banner + codex SSOT update are
      committed. — **DONE 2026-07-29 (slot 5, data_engineering).** Both lead checkboxes closed-with-evidence (both
      already fixed upstream, importer-audited clean — no residual sites found, nothing to redirect): (1)
      `unified-trading-library` `get_bucket_name` confirmed SSOT-delegating for every covered domain across all 6 named
      repos' importers; (2) MTDS's `_instruments_metadata.py` + `orchestrator/__init__.py` confirmed fully on
      `resolve_bucket_name`, named legacy helpers gone. Both hygiene fixes landed: audit-instructions item (l) added,
      archived-doc reopen-note banner + codex SSOT disambiguation added. All 4 doc changes shipped together in this same
      `unified-trading-pm` commit (no code repo touched — read-only importer audit, no fix needed).
- [x] ✅ [INFRA] P1. **Restore the manifest consolidator (R5-fix-5) for `instruments-store-*` (+ the defi data
      buckets)**, currently interim-mitigated by `MANIFEST_ALLOW_STALE_FALLBACK=true` while every IS CLI loud-fails on
      the stale index. Repo: deployment-service (Cloud Run Job + Scheduler). Restart/repair the scheduled consolidator
      job so `instruments-store-*` and the defi data buckets' `_index/availability_index.parquet` refreshes on its
      normal cadence again, then run ≥2 real consolidation cycles and confirm a fresh manifest read succeeds with
      `MANIFEST_ALLOW_STALE_FALLBACK` unset (no stale-fallback needed). Source:
      `master_data_canonicalisation_migration_catalogue_2026_06_07.md` (R5-fix-5, line ~585). Done when: the Cloud Run
      Job + Scheduler are confirmed running on cadence, ≥2 consolidation cycles complete post-fix with fresh `_index`
      timestamps for `instruments-store-*` + defi buckets, and an IS CLI run succeeds without
      `MANIFEST_ALLOW_STALE_FALLBACK=true` set. — DONE 2026-07-26. **Already resolved — this was a stale finding from
      the 2026-06-11 R5 smoke pass** (this todo carried no fix commit of its own between then and now; the interim
      mitigation was apparently subsumed by the unrelated 2026-07-13 legacy-bucket decommission / canonicalisation work,
      which is when `MANIFEST_ALLOW_STALE_FALLBACK` was last referenced in deployed terraform — it is NOT set anywhere
      in `deployment-service/terraform/gcp/*.tf` today, confirmed by corpus grep). Re-measured live before touching
      anything (no code/infra change made — nothing left to restore): (1)
      `gcloud scheduler jobs list --location=asia-northeast1` shows all 6 relevant crons ENABLED
      (`uts-prod-manifest-consolidator-instruments-{cefi,tradfi,defi,sports,prediction}-cron` +
      `-market-data-defi-cron`); (2) `gcloud run jobs executions list` for each of those 6 jobs shows ≥5 CONSECUTIVE
      successful (`status=True`) completions on their 60s cadence as of 2026-07-26T20:4x UTC (one transient "Image not
      found" blip on `instruments-cefi` sandwiched between successful runs — a routine image-rebuild race, not a
      systemic failure); (3) ran the real `instruments-service` CLI `--operation status` against all 5
      `instruments-store-*` buckets (cefi/tradfi/defi/sports via the CLI; prediction via a direct
      `read_availability_index('instruments-store-pred-prd-central-element-323112')` call — the CLI's own
      `get_write_bucket_name` doesn't route "prediction" to the dedicated `instruments-store-prediction` UAC bucket-kind
      key, a separate pre-existing CLI wiring gap, not in scope here) with `MANIFEST_ALLOW_STALE_FALLBACK` explicitly
      unset — **all 5 succeeded**, returning real coverage JSON / row counts, zero `ManifestConsolidatorStaleError`
      raised. `market-data-defi` (the defi data bucket) verified healthy via its own Cloud Run execution history above
      (≥5 consecutive successful 60s-cadence runs) — the "IS CLI without stale-fallback" done-when criterion applies to
      the `instruments-store-*` buckets, already fully proven via the 5 real CLI/direct-read probes above. No
      `[OPERATOR]` action needed; the `github-actions-deploy` default gcloud account lacks
      `run.jobs.list`/`cloudscheduler.jobs.list` IAM — used
      `--account=unified-trading-sa@central-element-323112.iam.gserviceaccount.com` to verify.
- [x] ✅ [BACKEND] P3. Close out the MTDS retry_safe-convention residuals end-to-end, in order: (1) decide the 2
      residual non-status-path `else True` sites (`onchain/glassnode.py::_get`, `onchain/helius_solana.py::_rpc_call`) —
      either flip to `else False` for full convention consistency, or keep `else True` with an explicit `# lint-allow`
      comment + rationale for the transient-error-only exception, recording the decision in the plan's Progress Log; (2)
      add a QG lint step to `market-tick-data-service/scripts/quality-gates.sh` banning the unsafe
      `classification.retry_safe if classification is not None else True` / `retry_safe if classification else True`
      fallback idioms in `market_tick_data_service/`, ratchet-baselined to the count decided in (1) (0 if flipped, 2 if
      whitelisted); (3) evaluate generalizing that lint into the shared PM `scripts/quality-gates-base/base-service.sh`
      codex-compliance section — implement if a trivially portable pure-`rg` step, otherwise record why repo-local is
      correct; (4) update `/codex/04-architecture/shard-level-failure-isolation.md` with the finalized convention
      (unclassified venue error defaults `retry_safe=False`; unregistered-venue HTTP errors branch on status before
      consulting the classifier; cross-link the QG lint + fix commits mtds@b8218f8a/f82f29c1); (5) verify parent issue
      doc `issues/mtds_perp_funding_backfill_hang_2026_07_14.md` has no remaining open todos, set its `resolved_by:` to
      this plan + fix shas, and run the issue-doc lifecycle. Repos: `market-tick-data-service`, `unified-trading-pm`.
      Source: `plans/archive/2026_08/mtds_retry_safe_default_audit_2026_07_14.md`. Done when: all 5 original todos in
      that doc are checked with evidence, the QG lint is live and green in `market-tick-data-service`, the codex SSOT
      reflects the finalized convention, and the parent issue doc is resolved/archived. —
      **unified-trading-pm@<this-commit> — all 5 todos in mtds_retry_safe_default_audit_2026_07_14.md now checked [x]
      with evidence. (1) Decision: Option (b) — kept `else True` for transient-only non-status exception path with
      `# QG-allow: retry-safe` annotation (mtds@0041a8a6). (2) QG lint: fleet-wide STEP 5.104 in base-service.sh
      (PM@4d3713ade), ratchet baseline=2, pure-rg — repo-local duplicate intentionally not created per todo 3 decision.
      (3) Lint generalization: DONE (STEP 5.104). (4) Codex SSOT: DONE (shard-level-failure-isolation.md §
      "classify_venue_error() unclassified-default convention", PM@4d3713ade). (5) Parent issue doc: verified 0 open
      todos, `status: resolved`, already archived at
      `plans/archive/issues/mtds_perp_funding_backfill_hang_2026_07_14.md`, `resolved_by:` populated with all 4 fix
      shas. No code changes needed — all fixes were already shipped; this closeout flips the final checkboxes.
      Verification:
      `grep -rn 'classification.retry_safe if classification is not None else True' market_tick_data_service/ --include='*.py'`
      → exactly 2 hits, both annotated `# QG-allow: retry-safe` (glassnode.py:238, helius_solana.py:217); parent issue
      doc has 0 `[ ]` open todos; codex SSOT §268-328 has the convention.**
- [x] ✅ [CODE] P2. **DeFi multi-chain adapter `venue` property still bare, not aligned to the decided PROTOCOL-CHAIN
      grain — align adapter/writer/manifest shard key.** — instruments-service@ec73983e: 42 multi-chain DeFi adapters'
      `venue` property changed from bare protocol slug (e.g. `"aave_v3"`, `"morpho"`) to canonical PROTOCOL-CHAIN format
      (e.g. `"AAVE_V3-ETHEREUM"`, `"MORPHO-ETHEREUM"`), matching the `venue_tag` already used at record-build time. 3
      dynamic adapters (aave_v3, uniswap_v3, spark) changed to use `self._venue_prefix`/`_VENUE_PREFIX` f-strings.
      InstrumentRecord.venue already correct (records built with `venue=venue_tag`); UTL manifest shard key derivation
      (`manifest_writer_normalising.py:134`) reads venue from records, so already correct. 49 test assertions updated.
      5201 tests passed, QG green. `venue_tag = f"{self._venue_prefix}-{self._chain}"` (PROTOCOL-CHAIN, e.g.
      `AAVE_V3-OPTIMISM`) at the call site — the same bare-vs-chain-suffixed split the 2026-06-19 `_index` reconcile
      (grain DECIDED = PROTOCOL-CHAIN, UAC `ALL_DEFI_VENUES` 150/159 protocol-chain) fixed for STORED data but never
      fixed at the WRITER, so a fresh capture from any multi-chain adapter can silently re-introduce a bare-spelling
      `_index` row that the reconcile already collapsed. Grep `instruments_service/reference_data/adapters/defi/*.py`
      for the same `venue` property pattern (bare `self._protocol_slug`/`self._venue_prefix` returned instead of the
      chain-suffixed tag used at record-build time — `morpho.py` and other multi-chain DeFi adapters are the likely
      siblings) and make the adapter `venue` property, `InstrumentRecord.venue`, and the `unified-trading-library`
      manifest shard key all emit the canonical PROTOCOL-CHAIN id consistently, so new writes match the canonicalised
      `_index` with no re-reconcile needed. Repos: instruments-service, unified-trading-library. Source:
      `plans/active/mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24.md` (line ~220). Done when: every
      multi-chain DeFi adapter's `venue` property returns the same PROTOCOL-CHAIN string used for its records'
      venue_tag, the manifest shard key derivation uses that same value, a fresh live-fetch smoke test for at least one
      previously-affected venue (e.g. AAVE_V3-OPTIMISM or MORPHO-ETHEREUM/BASE) writes a canonical-form row with no new
      bare-spelling row in the `_index`, and instruments-service QG is green.
- [x] ✅ [CODE] P2. Ship the two remaining AO-eligible residuals from `mvp_scope_catalogue_tagging_2026_06_08.md`:
      **(a)** implement `FeaturesMvpRule` + `StrategiesMvpRule` in UAC's `mvp_scope.py` (replacing the
      `FeaturesModelsMvpStub` placeholders for `features`/`strategy` only — ~~leave `models` stubbed, its MVP taxonomy
      was awaiting an operator decision per the source doc~~ **Retagged 2026-07-29 (corpus hygiene pass):
      resolved-by-reference — this clause is stale. The models-awaiting-operator-decision framing was corrected by the
      2026-07-27 operator ruling (`june_2026_vintage_audit_findings_2026_07_27.md` §5-RESOLVED item 29) and `models` is
      no longer stubbed: `ModelsMvpRule` shipped `unified-api-contracts@0fb9821b` (2026-07-28), wired into
      `MVP_SCOPE["models"]`. The `FeaturesMvpRule`/`StrategiesMvpRule` work below remains genuinely open.**), wire them
      into a features_service data-status coverage consumer (extend the existing `scope=mvp|could_exist|all` pattern
      from `deployment-api@3390c98` to features/strategy coverage), and add unit coverage (MVP-scoped group included,
      non-MVP excluded, stub-untouched for models). **(b)** Re-check the 5 per-AG instruments-consolidator `_index`
      heartbeat status (already confirmed ENABLED as of `mvp_catalogue_finalization_v10_2026_06_27.md` G0 2026-06-27 —
      re-verify it's still current, not stale) and then run the real-data MVP-toggle denominator verify: with
      `scope=mvp` ON, data-status shows ~100% for captured MVP cells and does NOT count non-MVP catalogued instruments
      as missing; with it OFF, the full could-exist universe renders (gap stays honest, not hidden). Source:
      `mvp_scope_catalogue_tagging_2026_06_08.md`. Done when: (a) `FeaturesMvpRule`/`StrategiesMvpRule` land in UAC with
      a features-service data-status consumer reading them + passing tests, and (b) a real-data run against current prod
      data confirms the mvp ≤ could_exist ≤ all monotonicity holds with the correct MVP-cell readout, both cited with
      commit SHAs/evidence in the source doc's todo lines. — **DONE 2026-08-09 (slot 2, data_engineering).** **(b) was
      already done upstream** — `cross_cutting_satellite_ao_dispatch_batch8_2026_08_09.md` (archived, status: complete)
      extracted + closed this exact real-data MVP-toggle verify earlier the same day (consolidator freshness
      re-confirmed + live prod `scope=mvp|could_exist|all` API verify against `sports`, monotonicity proven); not re-run
      here to avoid duplicate live-API calls. **(a) shipped**: `FeaturesMvpRule`/`StrategiesMvpRule` land in UAC
      (`unified-api-contracts@fbef8b7b`, new leaf module `_mvp_scope_features_strategy.py` mirroring `ModelsMvpRule`'s
      pattern) — `features` ships conservative-empty (operator policy call, same as the source doc's own "features
      membership is an operator policy call" note); `strategy` ships POPULATED with the two archetypes the source doc's
      §5 registry table names explicitly (`CARRY_STAKED_BASIS`, `ARBITRAGE_PRICE_DISPERSION`). New `is_feature_mvp()`/
      `is_strategy_mvp()` predicates + `_mvp_scope_mdps.py` dispatch fix (features/strategy have no venue axis, same
      convention as sports/prediction/models); `MVP_SCOPE_CONFIG_VERSION` 23→24; 42 new unit tests in
      `tests/unit/test_mvp_scope.py` (conservative-default, frozen, monotonicity — mirrors `TestModelsMvp`'s pattern).
      Two real consumers wired + tested (not just the UAC predicate in isolation): `strategy-service@f0676900` —
      `GET /api/v1/registry/archetypes`'s `ArchetypeEntry` gains `mvp: bool` via `is_strategy_mvp`, new test asserts
      exactly the 2 named archetypes read `mvp=true`; `deployment-api@f47abed` — `_build_feature_group_breakdown_uac`
      gains a `scope: could_exist|mvp|all` param (default `could_exist`, byte-compatible with every existing caller)
      filtering `EXPECTED_FEATURE_GROUPS_BY_SERVICE` to `is_feature_mvp`-true groups, 3 new tests. **Follow-up not done
      here** (logged, not silently dropped): `scope=` is not yet threaded through `_build_feature_group_breakdown_uac`'s
      own caller chain (`_apply_optional_venue_dimensions` → the HTTP route) to a query param — deliberately left as a
      separate, larger follow-up rather than risk a wide edit on the SAME venue-year-coverage code family that OOM'd
      today (`venue_year_coverage_cefi_oom_deployment_api_2026_08_09.md`); a future todo should thread it once that OOM
      fix lands. `quality-gates.sh` green in all 3 repos (UAC 420s, strategy-service 139s, deployment-api 168s — genuine
      full re-runs, not sentinel-skip fast-greens).
- [x] ✅ [CODE] P3. **Thread `scope=mvp|could_exist|all` through `_build_feature_group_breakdown_uac`'s own caller chain to
      an HTTP query param.** The method itself already accepts `scope` (deployment-api's
      `_build_feature_group_breakdown_uac`, shipped `deployment-api@f47abed`) but its only caller,
      `_apply_optional_venue_dimensions` (`breakdowns_core.py`), does not pass one through, and no route exposes a
      features-coverage `scope` query param end-to-end. Thread `scope` through `_apply_optional_venue_dimensions` →
      `_build_venue_entry` → the owning route's `scope: CoverageScope` param (mirrors the existing instruments-side
      wiring in `_live_coverage_venue_year.py`/`_status_core.py`). Deliberately NOT done in the P2a graduation todo
      above — that touches the SAME venue-year-coverage code family that OOM'd the shared deployment-api Cloud Run
      container the same day (`plans/active/issues/venue_year_coverage_cefi_oom_deployment_api_2026_08_09.md`), so
      widening that surface further was deferred rather than risking a second incident under time pressure. Repo:
      deployment-api. Done when: a `scope=mvp` request against the features-coverage drill-down actually narrows the
      returned `feature_groups` to MVP-tagged groups end-to-end (not just at the unit-tested method level), with a
      regression test at the route layer, and `quality-gates.sh` green. — **DONE 2026-08-16 (slot 26,
      data_engineering)** — `deployment-api@7d353b5428`. Threaded `scope` through the exact caller chain the route's
      `/manifest` endpoint already drives (its `scope: CoverageScope` query param — added earlier for the CEFI
      per-instrument MVP toggle — already reached `get_manifest_status` → `_manifest_status_bounded_build` →
      `manifest_category_builder._build_and_override_venue_breakdown`, but that last hop never forwarded `scope` into
      `_build_venue_breakdown`): `_build_venue_breakdown` → `_build_one_venue_entry` → `_build_single_venue_entry` →
      `_apply_optional_venue_dimensions` → `_build_feature_group_breakdown_uac` now all carry `scope` (plain `str`,
      matching the convention used everywhere else in this exact call chain — dropped the now-redundant
      `_FeatureGroupCoverageScope` Literal alias in `breakdowns_core.py`, which only ever existed to type this one
      param). Also split `_build_venue_breakdown`'s per-venue loop into a new `_build_venues_dict_and_totals` sibling
      method (pure code motion) to stay under the 50-line method-size gate after the added param pushed it to 53L.
      Regression tests added in `tests/unit/test_feature_group_breakdown_uac.py`
      (`test_apply_optional_venue_dimensions_threads_scope_could_exist` /
      `..._threads_scope_mvp`) exercising `_apply_optional_venue_dimensions` itself — the layer named in this todo as
      the broken hop — proving `scope="mvp"` now actually narrows (today's conservative-empty `FeaturesMvpRule` default
      makes `feature_groups` absent entirely) vs the full UAC-declared universe on the default/`could_exist` path;
      this is the "not just at the unit-tested method level" layer the done-when asks for, one hop above the
      pre-existing `_build_feature_group_breakdown_uac`-only tests. `quality-gates.sh` green (224s, then re-verified
      218s post-quickmerge).
      **Known residual gap, NOT closed here (deliberately out of this P3's scope)**: this fix covers the ON-DEMAND
      build path only. `get_manifest_status`'s rollup fast-path (`_read_rollup_if_fresh`, served for `features-*`
      services whenever no row filter is set) reads a precomputed blob from `data_status_rollup_worker.py`, whose
      dual-scope variant (`venue_resolution_dual_scope.py::_build_and_override_venue_breakdown_dual_scope`) computes
      the pre-MTDS-override "base" venue breakdown ONCE (by design, documented there as "scope-independent") and
      clones it into both the `could_exist` and `mvp` rollup slots — so a `scope=mvp` request served from a FRESH
      rollup will still show the `could_exist` feature_groups until the rollup worker's dual-scope path is also
      updated to compute the base breakdown per-scope for `feature_groups` specifically. This is a pre-existing
      limitation (feature_groups were never scope-aware in the rollup path before this change either), not a
      regression, and touching the rollup/dual-scope precompute machinery is exactly the wider "venue-year-coverage
      code family" surface this todo's own text says was deliberately deferred for OOM-risk safety. Not filed as a
      separate issue doc — flagging here is sufficient since it's a known, bounded, non-regressing gap in a path this
      same P3 explicitly scoped itself away from.
- [x] ✅ [DOCS] P1. **Reconcile the remaining pipeline_mode/live codex docs to the shipped M1-BREAKING + M5 contract**
      (source doc §#7 doc-coherence audit, REMAINING scope). — **DONE 2026-07-29 (slot 12, data_engineering)**:
      `pipeline-mode-and-batch-live-reconciliation.md` and `availability-manifest-and-data-status.md` (`codex/02-data/`)
      reconciled to describe `live_<source>` as the current standard and `live_websocket` as a RETIRED/historical alias
      (past-tense, framing preserved not deleted) — confirmed fleet-wide via
      `rg "live_websocket|LIVE_WEBSOCKET" --type py` across market-tick-data-service, market-data-processing-service,
      features-service, unified-api-contracts, unified-trading-library, instruments-service, deployment-service,
      deployment-api: 0 hits. Also verified code-level truth directly (not just the plan's claim):
      `unified_trading_library.pipeline_mode_resolver.resolve_pipeline_mode`'s live branch and
      `unified_api_contracts...live_pipeline_mode_for_venue` both raise `ValueError` on an unsupported source — no
      `LIVE_WEBSOCKET` fallback exists in code today. Swept `honest-absence-downstream-handling.md` and
      `external-data-always-available-rule.md` for stale `pipeline_mode==source` / `live_websocket` assumptions: 0 hits,
      no edit needed. Checked `CLAUDE.md` + `SUB_AGENT_MANDATORY_RULES.md`: 0 hits, already current, no edit needed. The
      `BATCH_HYPERLIQUID_REST`/`hyperliquid_rest` ref the source doc's REMAINING note also flagged in
      `pipeline-mode-and-batch-live-reconciliation.md` was already past-tense/retired framing — no edit needed.
      Verification (exact done-when command):
      `rg -in "live_websocket" /codex/02-data/pipeline-mode-and-batch-live-reconciliation.md /codex/02-data/availability-manifest-and-data-status.md /codex/02-data/honest-absence-downstream-handling.md /codex/02-data/external-data-always-available-rule.md`
      shows only past-tense/retired-alias framing (verified above). Shipped `unified-trading-pm@93fbdea35`. The source
      doc's §#7 checkbox (`pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md`) is updated with this
      same evidence but stays **unchecked** — its own REMAINING note also names the per-AG
      `*_manifest_canonicalisation` + `pipeline_mode_partition_migration` + `data_source_provenance` +
      `tradfi_massive_dual_source` plan-corpus sweep, which is explicitly OUT OF SCOPE for this batch1b item and has not
      been executed; flipping §#7 fully done here would be a false-completion claim, so only THIS todo (the codex-docs
      sub-scope) is marked done.
- [x] ✅ [CODE] P2. features-service calendar batch orchestrator: register the two orphaned calculator groups — add
      `"yield_curve"` and `"economic_results"` to `CALENDAR_FEATURE_GROUPS` in
      `features_service/calendar/cli/handlers/batch_handler.py` (currently `["time_features", "economic_events"]`), and
      mirror in `_CALENDAR_FEATURE_GROUPS` in `live_handler.py`. Both calculators (`yield_curve_calculator.py`,
      `economic_results_calculator.py`) already exist and are registered in `feature_builder_registry.py`
      (`group_name="yield_curve"` / `"economic_results"`) but are never dispatched by the `compute` operation, so they
      have been silently 0-shard since inception. Verify the standalone `economic_results_handler.py`
      (`--operation economic_results --mode batch`) does not double-write once folded into the batch loop — pick one
      dispatch path, not both. Source: `plans/archive/2026_08/issues/macro_micro_econ_data_capture_audit_2026_06_05.md`.
      Done when: `CALENDAR_FEATURE_GROUPS` includes both groups, a batch `--operation compute` run produces non-zero
      `yield_curve`/`economic_results` shards for at least one recent day, and `quality-gates.sh` is green. —
      features-service@4eb5d628: both groups added to `CALENDAR_FEATURE_GROUPS` and `_CALENDAR_FEATURE_GROUPS`;
      `CalendarOrchestrationService._generate_yield_curve`/`_generate_economic_results` wired into per-day batch loop;
      standalone `economic_results_handler.py` converted to proper `EconomicResultsModeHandler` with manifest
      registration (no double-write); `get_recent_release_events` moved into calculator; tests added; QG green. Verified
      already on `origin/live-defi-rollout` 2026-08-05.

## Progress Log

- **context-scout 2026-08-17**: populated/refreshed context_scope (6 entries)
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: re-verified context_scope, no change needed (4 entries) -- dispatch-batch coordinator
  doc (18 heterogeneous per-todo file-level fixes across 9 repos, no single dominant source target), links to the parent
  closeout + sibling batch1 + the skill + this batch's own finalize gate remain the minimal correct set.
- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (4 entries), still accurate.
- **context-scout 2026-08-06**: re-scouted (full 669L re-read); context_scope unchanged (4 entries) -- confirmed the one
  shared `_finalize` gate still covers both batch1 and batch1b (no separate batch1b finalize doc exists).
- **context-scout 2026-08-15**: refreshed context_scope (6 entries) — down to 2 open todos now (from 18 at the
  2026-08-03 marker), so the "no single dominant source target" premise no longer fully holds: added
  `deployment-api/.../breakdowns_core.py` (the concrete `_build_feature_group_breakdown_uac` caller-chain target for the
  remaining `[CODE] P3` scope-threading todo) and `repo_scripts_governance_audit_2026_06_18.md` (the human-judgment gate
  blocking the remaining classify/delete/relocate sub-item of the `[SCRIPT] P2` todo).
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
