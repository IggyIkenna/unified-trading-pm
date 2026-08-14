---
doc_type: plan
title: GitHub Actions CI cost reduction — operator-gated followups (D2/D3/D4 decisions, verification-pending items)
summary: >-
  Open follow-up work forked from /plans/archive/2026_07/github_actions_ci_cost_reduction_2026_07_15.md per the
  2026-07-23 plan line-cap remediation triage. Carries every todo from the parent that was still open (9 total): the
  quickmerge --agent sentinel-race P0, STEP 2d assert-not-decorative + the 3-dead-workflow decisions (digest-drift-sweep
  / reconcile-release-tags / cassette-drift-check), the persist-cicd-event ledger read-modify-write race (D2), the
  bare-host bootstrap proof, the billed-notify-cost + QG-fan-out re-measurements, and the two calendar-gated billing
  re-pulls (Phase 5). Also carries the parent's full "Deferred work after 2026-07-17" operator-decision ledger, hard-won
  operational lessons, the semver-agent/release-tagging cost ruling, and "Deferred work after 2026-07-23" — everything
  an operator needs to keep deciding on, minus the fully-completed migration history (now archived at
  github_actions_self_hosted_runner_migration_2026_07_15.md) and the same-day staging-machinery-shutdown audit (forked
  to github_actions_staging_machinery_shutdown_2026_07_24.md).
status: active
nature: process
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci-cd, github-actions, cost, self-hosted-runner, workflows, spend-reduction, operator-decision]
related:
  [
    /plans/archive/2026_07/github_actions_self_hosted_runner_migration_2026_07_15.md,
    /plans/archive/2026_07/github_actions_staging_machinery_shutdown_2026_07_24.md,
    /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md,
    /plans/archive/issues/quickmerge_agent_sentinel_race_vs_own_rebase_2026_07_16.md,
    /plans/archive/issues/persist_cicd_event_ledger_read_modify_write_race_2026_07_17.md,
    /plans/archive/issues/reconcile_release_tags_dead_since_d13_git_tag_migration_2026_07_17.md,
    /plans/archive/issues/cassette_drift_check_calls_deleted_script_and_swallows_it_2026_07_17.md,
    /plans/active/issues/digest_drift_sweep_silent_noop_github_token_scope_2026_07_16.md,
    /plans/active/issues/post_cutover_silent_assumption_sweep_2026_07_23.md,
    /plans/archive/2026_07/deployment_durable_operational_data_bigquery_2026_07_21.md,
    /plans/archive/2026_08/github_actions_operator_gated_followups_progress_log_history_2026_08_03.md,
  ]
created: "2026-07-24"
last_updated: 2026-08-03 # line-cap remediation split -- extracted the 07-27/28 self-hosted-runner fan-out + final report to the archive doc above; context_scope backfilled
parent_epic: deployment_and_user_management_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 4
assigned_role: infra
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /codex/08-workflows/ci-cd-flow.md,
    /codex/07-security/self-hosted-runner-security-posture.md,
    /plans/archive/2026_07/github_actions_ci_cost_reduction_2026_07_15.md,
    /plans/active/issues/post_cutover_silent_assumption_sweep_2026_07_23.md,
    scripts/cicd/measure-billed-notify-cost.sh,
    /plans/archive/issues/cassette_drift_check_calls_deleted_script_and_swallows_it_2026_07_17.md,
  ]
source:
  - "Split from /plans/archive/2026_07/github_actions_ci_cost_reduction_2026_07_15.md per the line-cap remediation
    triage (plans/active/issues/plan_line_cap_remediation_2026_07_23.md, row 13, proposed action 2 of 3): the
    operator-gated-followups extraction (9 open todos + the full deferred-work ledger)."
drift_direction: advance-code
---

# GitHub Actions CI cost reduction — operator-gated followups

> **🟡 ACTIVE — forked 2026-07-24 from `/plans/archive/2026_07/github_actions_ci_cost_reduction_2026_07_15.md`**
> (line-cap remediation, 2026-07-23 triage, row 13 of 30). The parent's self-hosted-runner migration is DONE (37/37
> movers, zero-billed) and archived verbatim at
> [/plans/archive/2026_07/github_actions_self_hosted_runner_migration_2026_07_15.md](/plans/archive/2026_07/github_actions_self_hosted_runner_migration_2026_07_15.md)
> _(path corrected 2026-07-26: it said `plans/active/…`, which is self-contradictory with "archived" and does not exist
> — the file is in `plans/archive/2026_07/`; verified 0 open / 30 done todos there)_. This doc carries everything from
> the parent that is **still open** — 9 todos, plus the full "Deferred work" operator-decision ledger, hard-won
> operational lessons, and the two calendar-gated billing re-pulls. Content below is moved **verbatim** from the parent
> — nothing summarized or rewritten. The same-day staging-machinery-shutdown audit (Phase 6 + its two related Progress
> Log findings) is a distinct topic and lives in
> `plans/archive/2026_07/github_actions_staging_machinery_shutdown_2026_07_24.md`.

## Open todos forked from the parent plan (verbatim)

> The 9 items below are every open (unchecked) checkbox from the parent plan, moved verbatim in their original order.
> Each item's own text already carries its full context (evidence, SSOT issue-doc pointers, operator asks) — nothing was
> reworded.

- [x] ✅ [INFRA] P0. **RESOLVED — `quickmerge.sh --agent`'s sentinel-vs-own-rebase race is fixed; this item was stale
      here since 2026-07-22 (missed across ~5 subsequent na-eligibility-audit passes because they never cross-checked
      the SSOT issue doc's own `status:` field).** Full analysis (mechanism, line refs, repro, 3 candidate fixes + the
      negative test that must keep passing) lives in
      **`plans/archive/issues/quickmerge_agent_sentinel_race_vs_own_rebase_2026_07_16.md`**, whose frontmatter now reads
      `status: resolved`, `resolved_by: unified-trading-pm@e264b3c9`. One-line essence of what was fixed: STAGE 0.4
      rebases your local commits (new SHAs), then STAGE 3 demanded the `.qg_last_passed_sha` sentinel be `==` HEAD or an
      ANCESTOR of it — impossible after a rebase of your own commits, so `--agent` could never validate a sentinel it
      just wrote on a busy LDR. Operator 2026-07-16: "we will also fix the issues with quickmerge --agent" — acted on
      2026-07-22 (not the doc's own recommended fix B; an operator-decided bounded-retry alternative instead, per the
      SSOT doc's own Resolution note): STAGE 0.4's pull was extracted into a reusable function and STAGE 3's AGENT_MODE
      sentinel check now runs in a bounded retry loop (re-pull + re-run `quality-gates.sh --no-fix` + re-check on a lost
      race, up to 3 attempts with backoff) instead of hard-failing on the first loss — `unified-trading-pm@e264b3c9`
      (2026-07-22), 9 new tests, full PM `quality-gates.sh` green. The SSOT doc's own "Bonus" residual (STAGE 5's commit
      can still lose to a peer push landing between STAGE 0.4 and STAGE 5) was independently fixed later too:
      `unified-trading-pm@f93a618e6c` (2026-07-31, "add STAGE 5 no-regression guard against silent branch-reset commit
      loss"), 6 new hermetic bats tests, all 14 pre-existing quickmerge bats tests still pass. Both SHAs verified
      ancestors of `origin/live-defi-rollout`.

- [ ] [INFRA] P0. **STEP 2d — assert-not-decorative on the mover set (NEW, from this plan's own audit 2026-07-17).** **3
      of the 37 movers were long-dead silent no-ops** — `digest-drift-sweep` (never worked), `reconcile-release-tags`
      (dead since D13), `cassette-drift-check` (dead ~4 months, 52 false issues). **~8% of the audited surface was
      decorative, and NONE of it was caused by the flip** — the flip is simply what made someone read the logs. All
      three are BACKSTOPS whose healthy output and dead output are the SAME STRING (`Dispatched: 0` / `created 0 tag(s)`
      / a green job that never ran its check). **The cheapest workflow is one that does not run**:
      `reconcile-release-tags` alone burns ~48 no-op runs/day, so deleting dead glue beats moving it. Deliverable: a
      cheap recurring check that a mover's "did work" counter is not 0 on EVERY run for N days (and that "I did nothing"
      and "I could not look" are DIFFERENT exit states — the one-line assertion that would have caught all three on day
      one). Generalises `/codex/02-data/honest-absence-downstream-handling.md` from data to automation.
- [x] ✅ [INFRA] P0. **RESOLVED 2026-08-08 — rewritten to reflect the stall-alarm reality; the original "DELETE
      `reconcile-release-tags`" ask does not apply and this todo is now closed, not just deferred.** The script was
      **repurposed, not deleted**: `unified-trading-pm@6c4ee4d0c` (2026-07-23, verified ancestor of
      `origin/live-defi-rollout`) split it into two populations — legacy static-version repos still get the original
      read-version→mint-matching-tag path, while tag-derived (hatch-vcs) repos — the entire fleet today — are
      **hard-refused for minting** and instead checked for the real invariant it exists to protect ("`main` must not
      accumulate commits past the newest `v*` tag for more than `_STALL_DAYS=3`" ⇒ STALL). **Re-read the live script
      2026-08-08 (`scripts/cicd/reconcile_release_tags.py`, 581 lines) to confirm current behaviour before writing this
      rewrite, per the module docstring + `reconcile()`**: on STALL it emits a `::warning::` GH annotation, routes a
      dedup'd Slack post through the `notify-slack.yml` carrier (`_build_stall_block`/`_STALL_DEDUP_KEY`) with an
      explicit CLEARED bookend when a repo resumes tagging (`_emit_stall_clear_diff`), self-audits against an
      all-repos-unreadable false-healthy read (`FATAL` exit 1), and best-effort write-throughs the latest version↔SHA
      per repo to Firestore (`_write_firestore_release_tags`, CAS via `version_registry_store.py`) as a free-quota
      backstop for downstream tag-readers. **It is now the fleet's release-stall alarm — this is its permanent role, not
      a transitional state**, and deleting it would remove the only detector for a repeat of the 2026-06-27→07-23
      ~4-week silent tagging outage that motivated this whole todo. Codex has ruled:
      `/codex/08-workflows/ci-cd-flow.md:1004` § _"Release tag reconciler — a STALL DETECTOR, not the minter (corrected
      2026-07-25)"_; CLAUDE.md carries the matching one-liner (`reconcile_release_tags.py` = stall detector, not
      minter). The live minter is `semver-agent` on `push:[main]` (`unified-trading-pm@0b128a725`, ancestor-verified;
      fleet-rolled to 22 repos per
      [/plans/archive/2026_07/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md](/plans/archive/2026_07/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md)
      § Phase 4). **operator ruling 2026-08-08**: rewrite it to reflect the stall-alarm reality (not retire the script
      itself — the script stays and keeps running on its schedule; only this stale planning todo closes). No further
      code change needed — nothing about the script's behaviour is in question, only this todo's framing was stale.
      SSOT:
      [/plans/archive/issues/reconcile_release_tags_dead_since_d13_git_tag_migration_2026_07_17.md](/plans/archive/issues/reconcile_release_tags_dead_since_d13_git_tag_migration_2026_07_17.md)
      (banner at top).
- [x] ✅ [REVIEW] P0. **RESOLVED 2026-08-08 — consolidated 20→1, root cause diagnosed, fix specified (not yet
      shipped).** **operator ruling 2026-08-08** (full execution evidence in this same entry below —
      `github_actions_operator_gated_followups_2026_07_17.md`): consolidate the 20 open issues down to 1, archive the
      rest, fix the 2 real schema mismatches (Balancer pools / Deribit ticker), then retire the last remaining issue
      once the fix lands. **Executed live via `gh issue close`/`gh issue comment` against
      `IggyIkenna/unified-api-contracts`**: closed 19 duplicates (#641, #660, #672, #683, #698, #713, #720, #729, #736,
      #758, #778, #791, #814, #825, #827, #843, #850, #862, #870) as dup-of-#880 (not false-positives — each is
      annotated as a correct daily detection of the same real condition); kept **#880** (2026-08-08, newest) as the
      single live tracking issue, verified via
      `gh issue list --repo IggyIkenna/unified-api-contracts --search '"[Cassette Drift]" in:title' --state open` →
      exactly 1 open. **Root-cause investigation (posted in full on #880, not repeated here) answers the operator's
      option (ii) — the matching-lottery question — for both cassettes, and the answer is NEITHER is a live API schema
      change**: (1) Balancer `pools.yaml` — the cassette records a real GraphQL envelope
      `{"data": {"poolGetPools": [...]}}`; `BalancerPoolsResponse` correctly models the _unwrapped_ inner shape (how
      production code actually consumes it), but `detect_cassette_drift.py::_validate_cassette` validates the raw
      still-wrapped body — a **checker bug** (no GraphQL-envelope unwrap, unlike `test_vcr_replay.py`'s own
      `response_path="data"` handling for its tracked endpoints). (2) Deribit `ticker.yaml` — the cassette's recorded
      request is actually `GET .../public/get_instruments?currency=BTC&kind=future&expired=false`, **not**
      `public/ticker` — the file is mis-recorded/misnamed. `DeribitTickerResponse.result` correctly expects a single
      object (a real ticker response); the recorded payload is the `get_instruments` list, which
      `DeribitInstrumentsResponse`/`DeribitGetInstrumentsResponse` already model correctly. FINDING #4's venue-scoped
      matcher worked correctly here (picked the one Deribit model whose name contains "ticker") — the cassette content
      itself is what's wrong. **Exact fix specified on #880, ready to apply — NOT shipped this session** (this session
      is scoped to editing `unified-trading-pm` only, not `unified-api-contracts`): (a) Balancer — add a targeted
      GraphQL-envelope retry-unwrap in `_validate_cassette` (mirrors `test_vcr_replay.py`'s `response_path` handling,
      generalizes beyond just Balancer); (b) Deribit — re-record `ticker.yaml` against the real
      `GET https://www.deribit.com/api/v2/public/ticker?instrument_name=BTC-PERPETUAL` (public, no auth needed),
      replacing the mis-recorded `get_instruments` payload. **#880 stays open** until that fix lands in
      `unified-api-contracts` and the check is green for a few consecutive runs — then close it as resolved-by-fix; do
      not re-open the archived 19. **Ikenna's original cassette-count verification (operator 2026-07-17) is superseded**
      by this session's live re-count (20 open, now 1). SSOT:
      `plans/archive/issues/cassette_drift_check_calls_deleted_script_and_swallows_it_2026_07_17.md`.

- [x] ✅ [REVIEW] P0. **OPERATOR CALL (D2) — event ledger loses rows; fix-vs-accept.** **ANSWERED 2026-08-02**
      (`ci_satellite_ao_dispatch_batch1-027`). WHO READS IT: SSOT's 2026-07-21 Resolution already answered this (this
      doc's D2 entry missed it) — re-confirmed live via a fresh grep-then-READ across all repos. **Consumer, measured**:
      `deployment-api/_repo_ci_alerts.py::_read_ledgers_sync()` prefix-walks `cicd/events/` (line 412) → feeds
      `repo_ci.py`/`unified_alerts.py`/`health_overview.py`; `unified_alerts.py` backs `GET /api/alerts`, consumed by
      `deployment-ui/src/pages/Alerts.tsx`. (`unified-trading-system-ui`'s `GitHubWorkflowEvent` copy is a TS type-gen
      mirror, not a real consumer.) Real prefix-walk consumer ⇒ Option 1 was free, and **already shipped**
      (`unified-trading-pm@4cbf2006d`, confirmed on origin) — one never-overwritten object/event replaces the race.
      **EVENTS ledger race resolved in practice.** Audit-only, no write-path touched. (Incidental sibling-ledger finding
      filed separately — see `ci_satellite_ao_dispatch_batch1_2026_07_26.md` Progress Log.) SSOT:
      `plans/archive/issues/persist_cicd_event_ledger_read_modify_write_race_2026_07_17.md`.

- [ ] [VERIFY] P0. **PROVE the bootstrap on a bare host** — ⏳ **PARTIAL** (unified-trading-pm@80f00684a). ✅
      **Container leg DONE**: bare `ubuntu:24.04` → EXIT=0, all 10 tools resolve; found + fixed the `sudo` assumption.
      Reproduce:
      `docker run --rm -v "$PWD/bootstrap-ci-host.sh:/b.sh:ro" ubuntu:24.04 bash -c 'useradd -m -s /bin/bash ubuntu; bash /b.sh'`.
      ❌ **STILL UNPROVEN — a container structurally cannot exercise these:** IMDS / EC2 instance role · GCP ADC
      (interactive; STEP 2b's trim depends on runner-user ADC) · **systemd — so `setup-glue-runners.sh install` (units,
      slice, refresh timer) is UNTESTED end-to-end** · actual runner registration against GitHub. **Do NOT tick this off
      the container pass**; it closes only when a real bare VM runs it. The upcoming planning-VM deploy proves the
      systemd/registration legs; the bare-VM leg stays open until we genuinely rebuild a host.

- [x] ✅ [VERIFY] P0. **Use `scripts/cicd/measure-billed-notify-cost.sh`** (promoted out of a scratchpad 2026-07-16 — it
      is what produced this plan's notify-slack numbers, and the measurement took THREE attempts to get right: skipped
      jobs are not billed, and a throttled API call silently counts as 0). After 3–5 days, re-measure PM's billed
      minutes (ledger); confirm the moved workflows bill
      ~$0 and the VM absorbed the load without contention (slice
      `MemoryCurrent` < 8G, orchestrator load unaffected). **DONE 2026-08-09 (slot 31)** via
      `ci_satellite_ao_dispatch_batch1_2026_07_26.md`'s `[VERIFY] P1` todo: `DAYS=23 scripts/cicd/measure-billed-notify-cost.sh`
      measured `DEDUP_BILLED_23D=2019` (~$12/23d
      dedup-only subtotal) across `sit-debounce-trigger`=778, `branch-health`=447, `escalate-to-orchestrator`=356,
      `ci-health`=275, `cloud-build-failure-watcher`=97, `cascade-qg-ordering`=63, `ruleset-drift-alert`=3.
      **Superseding finding**: the deeper premise (self-hosted glue absorbing load, hence the `MemoryCurrent`/contention
      half of this done-when) is moot — the self-hosted glue deployment was retired (51 orphaned units archived
      2026-08-08T13:05Z, per `/plans/archive/issues/ao_observability_and_deploy_hygiene_gaps_2026_08_08.md`) and PM's
      workflows were separately reverted to `ubuntu-latest`
      (`/plans/archive/2026_08/self_hosted_runner_public_repo_revert_2026_08_05.md` todo 24) — PM is now public, so
      GH-hosted billing is unmetered, $0 for a different reason than self-hosting. Not credentials-blocked; moot, not
      unreachable. Re-measure fresh only if the glue deployment is ever actually completed.

- [x] ✅ [VERIFY] P0. **DONE 2026-08-09 (slot-28)** — representative QG run ~10 billed min (features-service PR run,
      real /jobs pull); identical-tree sentinel skip ~5% (PM, 1/20) / 0% (features-service, 0/20). Full numbers: batch4
      todo 9 Progress Log.

### Phase 5 — Prove the savings

- [x] ✅ [VERIFY] P0. **DONE 2026-08-09 (slot-28)** — fleet run-rate ~$1065/mo (Jul1-15 baseline) → ~$382/mo (Aug1-8),
      -64.2%, lands the ~$300-400/mo target; the +47% non-PM masking has resolved (non-PM now -68.5%). Full numbers:
      batch4 todo 9 Progress Log.

---

## Deferred work after 2026-07-17

STEP 2 is **DONE (37/37 movers on the pool, zero-billed, verified)**. Everything below is what remains, why it is not
done, and what the next session should NOT re-derive.

**STEP 2c is COMPLETE (`a6057ea36` converted → observed green on main → `0c845f930` deleted, 2026-07-17).** The persist
minute-minimum is gone from all 22 callers (~$117/mo); `ci-status-update` measured `billable: {}` end-to-end on main
(runs 29579499315, 29579977224). Finding ②'s rule still governs any FUTURE edit of `action.yml`: _edit the manifest →
prove on ONE caller → only then fan out._

### ⛔ OPERATOR DECISIONS — 4 open, nothing below them moves without these

| ID     | Decision                                                                            | Recommendation + why                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| ------ | ----------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **D1** | ✅ **DECIDED 2026-07-17** — operator delegated; checkout kept, `@main` pin rejected | Finding ② made pre-main testability non-negotiable; ~1s sparse checkout on our own runner = $0. Rollout executed same day (`a6057ea36`); STEP 2b's no-checkout clause amended to sparse-checkout.                                                                                                                                                                                                                                                                                                                                                                                                                               |
| **D2** | **Event ledger loses rows** — fix vs accept                                         | ✅ **RESOLVED 2026-08-02** — consumer confirmed: `deployment-api/_repo_ci_alerts.py::_read_ledgers_sync()` prefix-walks `cicd/events/`, feeding `unified_alerts.py`/`repo_ci.py`/`health_overview.py` → `deployment-ui`'s Alerts page. Option 1 (one-object-per-event) already shipped, `unified-trading-pm@4cbf2006d` (confirmed ancestor of `origin/live-defi-rollout`). SSOT: `plans/archive/issues/persist_cicd_event_ledger_read_modify_write_race_2026_07_17.md`.                                                                                                                                                         |
| **D3** | **The 3 dead workflows** — operator wants to review first (2026-07-17)              | **`reconcile-release-tags` RESOLVED 2026-08-08** — repurposed into the fleet's release-stall alarm (see the retired-todo entry above), not deleted; its part of D3 is closed. **CORRECTED 2026-08-12 (/plan-reconcile)**: `digest-drift-sweep` is 3-of-4 FIXED (2026-07-26, per its own SSOT `issues/digest_drift_sweep_silent_noop_github_token_scope_2026_07_16.md`'s banner) — the token bug + silent-failure hardening + dispatch cap all shipped. Only recommendation 1 (investigate the dormant `update-dependency-version.yml` primary cascade) is still open, and **STEP 2d is still held** on that one remaining item. |
| **D4** | ✅ **RESOLVED 2026-08-08** — close 52 false issues? fix the UAC matching?           | Not false positives — 20 real recurring issues, consolidated to 1 (#880), root cause diagnosed (checker/cassette bug, not live schema drift), fix specified pending shipment in `unified-api-contracts`. See the matching planning todo above.                                                                                                                                                                                                                                                                                                                                                                                  |

### Not done — blocked on nobody, real work

| #   | Item                                                                                | State                                                                                                                                                                                                                                                                                                                                                                                                                              |
| --- | ----------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | ~~A2 — content-gate dedup~~                                                         | ✅ **SHIPPED + PROVEN 2026-07-17** — see the A2 todo's evidence block (c535ec087; alerting-service runs 29584946980 MISS+save / 29585163847 22s HIT+skip). [A2 todo now archived in `github_actions_self_hosted_runner_migration_2026_07_15.md`.]                                                                                                                                                                                  |
| 2   | ~~A1 — docs-only fast-path~~                                                        | ✅ **SHIPPED 2026-07-17** — see the A1 todo's evidence block (e5b22fddc, PR #1124; fleet template rollout deferred to batch with A5). [A1 todo now archived in `github_actions_self_hosted_runner_migration_2026_07_15.md`.]                                                                                                                                                                                                       |
| 3   | ~~A5 — collapse the QG fan-out~~                                                    | ✅ **DONE 2026-07-17** — measured 23 repos then collapsed to `[tests, checks]` (1bb13bfb2, PR #1126; live proof in its own run).                                                                                                                                                                                                                                                                                                   |
| 4   | ~~Security-posture codex doc~~                                                      | ✅ **DONE 2026-07-17** — `/codex/07-security/self-hosted-runner-security-posture.md`.                                                                                                                                                                                                                                                                                                                                              |
| 5   | ~~Cron cadence · debounce~~                                                         | ✅ **DONE 2026-07-17** — 5 health/backstop crons hourly (3 are HOSTED watchers = real $); debounce CLOSED not-worth-it (warm slot ~2-5s @ $0; CAS risk).                                                                                                                                                                                                                                                                           |
| 13  | Clean up the 91 pre-existing broken doc references in `doc_reference_baseline.yaml` | **NEW 2026-07-22, P3, nobody's blocking it, just not prioritized.** Real dead links (mostly `related:`/`referenced_by:` pointing at docs that were renamed or never existed at the stated path), NOT the routine archived-plan noise (that's already discounted). Fix a batch, re-run `python3 scripts/plan-hygiene/check_frontmatter_schema.py --update-doc-ref-baseline`, commit the shrunk baseline — never hand-edit the YAML. |

### Cannot be done yet — waiting, NOT neglected

| #   | Item                                                               | Blocked on                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| --- | ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 6   | ~~Re-measure billed minutes (`measure-billed-notify-cost.sh`)~~    | ✅ **RESOLVED 2026-08-09** — see the `[VERIFY] P0` item above, now flipped `[x]`. `DEDUP_BILLED_23D=2019` (~$12/23d); self-hosted-glue premise moot (retired), PM reverted to `ubuntu-latest` (public repo, unmetered).                                                                                                                                                                                                                                                                                       |
| 7   | Two-week billing-ledger comparison vs the Phase-0 baseline         | the calendar — earliest **~2026-07-31**.                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| 8   | **Bootstrap on a bare host** (`PARTIAL`)                           | a genuine VM rebuild — systemd / IMDS / GCP ADC / runner registration **structurally cannot** run in a container.                                                                                                                                                                                                                                                                                                                                                                                             |
| 14  | ~~**Verify `ldr-docs-gate`'s hourly `schedule:` actually fires**~~ | ✅ **RECONCILED 2026-08-09 (`ci_satellite_ao_dispatch_batch6_finalize` todo 1) — already done, stale row.** **CONFIRMED FIRING** via `ci_satellite_ao_dispatch_batch1_2026_07_26.md`'s `[VERIFY] P2` todo, DONE 2026-07-26 (slot 6): `gh run list -R IggyIkenna/unified-trading-pm --workflow=ldr-docs-gate.yml --limit 20` showed 20 consecutive `event=schedule` runs, all `conclusion=success`, spanning 2026-07-26T03:02:59Z–23:19:47Z. This row was simply never flipped after that verification landed. |

### Operator-owned — do not start

| #   | Item                                       | Note                                                                                                                                                                                           |
| --- | ------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 9   | ~~`quickmerge.sh --agent` sentinel race~~  | ✅ **RESOLVED 2026-07-22/31** — see the matching `[x]` todo above (`unified-trading-pm@e264b3c9` + `@f93a618e6c`). No longer operator-owned; row kept struck-through for the historical trail. |
| 10  | MTDS promote PR #601 blocked on QG failure | From the 2026-07-17 #ci-failures triage (operator: "we will take care of the … repos later"). Real, current, NOT this plan's: market-tick-data-service's own QG fails on its promote path.     |
| 11  | `deployment-api` Cloud Builds failing      | Same triage: 3+ failures/24h (e.g. build `8b581721` at `deployment-api@8c7811f`). Recurring, outside this plan.                                                                                |
| 12  | `branch-health` PROMOTION-LAG alert noise  | ~24 of 79 #ci-failures messages/24h are this one warning re-firing; a genuinely stuck `system-integration-tests` LDR→main (~4 days) hides inside it. Overlaps the Phase-3 cadence/alert todo.  |

### Findings parked for later — do NOT re-investigate, they are fully written up

| Issue doc                                                              | One-line verdict                                                                                                                                                                                                                                                                                                                                                                                                 |
| ---------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `digest_drift_sweep_silent_noop_github_token_scope_2026_07_16`         | Never worked (PM-scoped token). Fixing it dispatches to **15 of 16 repos** — measured, re-runnable via `scripts/propagation/simulate-digest-drift-sweep.sh`. **The 15 is a SYMPTOM: the primary cascade has also been dormant since 2026-06-28.** Answer that first.                                                                                                                                             |
| `reconcile_release_tags_dead_since_d13_git_tag_migration_2026_07_17`   | **RESOLVED 2026-08-08 — repurposed, not deleted.** The original "DELETE, do not fix" verdict here was superseded 2026-07-23 by `unified-trading-pm@6c4ee4d0c`: the script now splits tag-derived (hard-refused for minting, STALL-checked) vs legacy static-version (original mint path) repos, and is the fleet's release-stall alarm. See the retired planning todo above for the full re-confirmed behaviour. |
| `d13_orphaned_version_readers_and_manifest_drift_2026_07_17`           | D13 migrated SOME version-readers. `sync-manifest-versions.py` still reads the deleted field; `versions{}` lags the tags for 9/24 repos; `assert_version_coherence.py` exits 1 with 24 violations while QG passes EXIT=0.                                                                                                                                                                                        |
| `cassette_drift_check_calls_deleted_script_and_swallows_it_2026_07_17` | **FIXED + FLIPPED.** Residual: the UAC detector's model-matching is a lottery (finding #4) + 52 false issues to close (finding #5).                                                                                                                                                                                                                                                                              |
| `persist_cicd_event_ledger_read_modify_write_race_2026_07_17`          | ✅ **RESOLVED 2026-08-02 (D2).** Consumer found (`deployment-api/_repo_ci_alerts.py::_read_ledgers_sync()`); Option 1 fix shipped, `unified-trading-pm@4cbf2006d`, confirmed ancestor of `origin/live-defi-rollout`. See D2 row above.                                                                                                                                                                           |

### Hard-won context the next session should inherit rather than rediscover

- **Evidence shape**: a run-level `runner_name` is MEANINGLESS for a cross-boundary workflow — a glue job + a hosted
  KEEP-D/MOVE-C job in one run is BY DESIGN. **Always read per-JOB.** (I truncated that column once and was ~1 minute
  from reporting "5 workflows silently failed to move".)
- **Billing**: `/timing.billable.total_ms` **UNDER-REPORTS — it returns 0 for jobs that plainly ran.** GitHub bills a
  **1-minute minimum PER JOB**, so COUNT JOBS, never ms. `billable: {}` (no UBUNTU key at all) is the real zero.
- **Never `2>/dev/null` a measurement.** `gh api` has no `--arg` flag; swallowing that error rendered a broken query as
  a clean "0 runs overnight" — the literal `curl -sf || echo ""` bug this plan documented, committed by me a day later.
  Also: `gh api --paginate --jq '[...]'` emits **one array PER PAGE**, so `jq length` counts only the first.
- **Cron delivery measured ~80-90%**, NOT the ~37% in CLAUDE.md's throttle note (hourly crons landed 9/10; `*/30` landed
  16/20). Re-check that figure before tuning any cooldown to it.
- **The security invariant is the TRIGGER AUDIT, not the private flag** — visibility is a settings toggle; "no
  self-hosted workflow carries a `pull_request` trigger" is a property of the workflows and survives it. Re-run it
  before adding such a trigger to any self-hosted workflow. **It is one command — a rule with no command is a rule that
  gets skipped, so here it is** (expect ZERO output; any line is a workflow that would run PR-authored code on our VM):
  ```bash
  grep -lE '^\s*runs-on: \[self-hosted' .github/workflows/*.yml \
    | xargs grep -lE '^\s*(pull_request|pull_request_target):'
  ```
- **A composite action gets NOTHING ambient from the repo — only what the caller explicitly hands it.** GitHub withholds
  **both `secrets` and `vars`** so an untrusted third-party action cannot read org/repo values without an explicit
  opt-in. The docs state the `secrets` half and are SILENT on `vars`; the silence is not permission.
  `actions/runner#2551`.
- **Composite-action manifest errors are NOT containable.** Validation happens at LOAD, before any step runs, so
  `continue-on-error` on every step buys you nothing — a bad `action.yml` fails the CALLER's real job. With 22 callers
  that is 22 simultaneous failures. **Edit the manifest → prove on ONE caller → only then fan out.**
- **MEASUREMENT TRAPS hit this session (same family as the `--arg`/`2>/dev/null` ones above):**
  - **A compound background command reports the LAST command's exit code, not your tool's.**
    `qg.sh > log; echo "EXIT=$?"; tail log` → the harness reported **exit 0** for `tail` while QG's real status was in
    the log. Always print and read an explicit `EXIT=` marker.
  - **The Bash tool's own ceiling is 10 min (600000ms max).** Wrapping a longer job in `timeout 900` does NOT help — the
    harness SIGKILLs it first and you get a bare **137** that looks like OOM. PM's full QG exceeds 10 min ⇒ it MUST run
    `run_in_background`. (Checked: 69 GB free, no competing QG — it was never resource pressure.)
  - **`grep -rl 'self-hosted, glue'` counts your own COMMENTS.** The flip comment contains both `glue-writer` and
    `runs-on: ubuntu-latest` as literal strings, so file counts came out 37/22 and did not reconcile against 56. Anchor
    to `^\s*runs-on:` or you are measuring your own prose.
  - **A hand-wavy doc summary is an INFERENCE.** When you ask for a verbatim quote and get prose ("X appears in multiple
    keys that…"), you did not get an answer. **Search the error string first** — it is faster and it is ground truth.
- **Reading Slack directly**: `scripts/dev/slack-read-channel.py [channel] [hours]` (operator-directed 2026-07-17; auth
  = Secret Manager `SLACK_ALERTS_READER_BOT_TOKEN`, resolved in-process, never on disk). Trap it encodes: carrier posts
  keep the real content in Block Kit `blocks` — the `text` field is only the ":x: CRITICAL — <workflow>" headline, so
  grepping `text` tells you nothing about WHAT failed.
- **Session working-state (2026-07-17, slot 1)**: STEP 2c/2b work was done in a git WORKTREE of the slot-1 clone at the
  session scratchpad (`git worktree list` in `.tabs/1/unified-trading-pm` shows it; local branch `tmp/step2c-rollout`,
  fully pushed). If the scratchpad is gone, clean the stale registration with `git worktree prune` +
  `git branch -D tmp/step2c-rollout` — everything it held is on `origin/live-defi-rollout`. The worktree pattern itself
  is the documented way to work while the slot clone carries someone's live WIP.
- **5-day post-migration system check (2026-07-22)** — operator asked "is everything working, did anything break due to
  our migration?". Findings, evidence-first via `gh run list`/`gh api .../jobs`/`.../logs` (not Slack — this session's
  gcloud ADC needed an interactive reauth this tool couldn't do, so live Slack alert-volume re-verification was skipped;
  GH Actions run data is authoritative and sufficient on its own):
  - **`ldr-docs-gate` (shipped 2026-07-17 as the frontmatter backstop) had NEVER completed a single run** — 39/40
    sampled runs over 5 days show `cancelled`, 0 ever reached a verdict. Root cause:
    `concurrency: cancel-in-progress: true` on a static group name, racing against LDR's real push cadence (a new
    doc/plan push lands every few minutes fleet-wide, faster than this sub-minute check finishes) — every run got
    pre-empted by the next push before it could report anything. The backstop has been silently inert this whole time.
    **FIXED live this session**: `cancel-in-progress: false` (queue instead of cancel — self-hosted + sub-minute jobs
    make queuing free) → `unified-trading-pm@efdeb6f41`.
  - **CORRECTION #2 (real root cause, found only after the operator pushed back on my "resource limitation" theory
    2026-07-22 — that theory was WRONG, and the pushback was right)**: after the concurrency fix, runs were STILL 100%
    cancelled/stuck-queued (total population re-checked via `gh api .../runs?per_page=1` → `total_count: 1200`, not the
    40 I'd sampled earlier via a capped `--limit`; 1198 cancelled, 0 succeeded, 0 failed, ever — cross-checked against
    1402 real commits touching `plans/`/`codex/` in the same window, so the trigger itself was firing correctly). I
    first blamed shared self-hosted runner-pool CPU contention. Measured locally: the check itself runs in **2.04s** for
    the full 1670-doc corpus — nowhere near slow enough to explain a 90+-minute queue wait, and other `glue`-pool
    workflows (`cloud-build-router`, `change-freeze-check`, etc.) were completing in seconds in the EXACT same window a
    `ldr-docs-gate` job sat queued with `runner_name:""` — ruling out pool saturation outright (a saturated pool would
    starve everything, not one specific workflow). The actual cause: `runs-on: [self-hosted, Linux, X64, glue]` requires
    4 labels, but `scripts/self-hosted-runners/glue-runner-run.sh:190` registers every JIT-ephemeral runner in this pool
    with only `["self-hosted","glue"]` — no `Linux`/`X64` ever advertised. Label matching is a strict subset test, so a
    job needing all 4 can **never** match any runner in the pool — not eventually, structurally never.
    `ldr-docs-gate.yml` was the ONLY one of 36 workflows using this pool that specified the 4-label form; the other 35
    all correctly use the 2-label form matching the actual registration. **FIXED**: `runs-on: [self-hosted, glue]` →
    `unified-trading-pm@078c85dc3`. This is the REAL fix; the earlier concurrency change was necessary (a run that DID
    match a runner would otherwise still get killed by the next push) but was not sufficient on its own, and my "fixed"
    claim in the entry above was premature.
  - **LIVE PROOF (2026-07-22, same session)**: the very next `plans/**` push (this commit) triggered run `29910893758` —
    but it stayed `pending` with no job created, because the DEAD run from 08:36 (`29904643698`, created under the
    pre-fix 4-label config, which could never match a runner) was still sitting unresolved in the concurrency group and
    — since it was never cancelled by any of the ~15 pushes since — was silently jamming the whole queue behind it.
    Manually cancelled it (`gh api -X POST .../runs/29904643698/cancel`); the queue immediately unblocked and
    `29910893758` ran and completed in **12 seconds** (10:11:57→10:12:09) on `glue-ip-172-31-5-118-5`, conclusion
    `success`, `notify-broken-docs` correctly `skipped` (green verdict). First real completion in this workflow's 5-day
    existence. Three bugs total, now all fixed: (1) `cancel-in-progress:true` killing in-flight runs (`efdeb6f41`), (2)
    the labels mismatch preventing any match at all (`078c85dc3`), (3) an unresolvable zombie run parked in the
    concurrency queue with nothing to clear it (manually cancelled, no code fix needed — a genuinely dead run just needs
    cancelling once; it can't recur since (2) means no future run can get stuck the same way).
  - **Operator's 4 follow-on improvements (2026-07-22, now unblocked — the gate is confirmed working)**: (1) switch
    trigger from per-push (~240/day measured) to an hourly cron — per-push was never the right model for a check whose
    failure mode (a broken doc sitting undetected a bit longer) is low-consequence; (2) scope
    `check_frontmatter_schema.py` to just the changed files (`git diff --name-only`) instead of the bare/full-corpus
    call — the script already supports `[file ...]` args, `ldr-docs-gate.yml` just never used them; (3) add an
    existence-only check for frontmatter-referenced doc paths (`related`/`supersedes`/`parent_epic`) — confirmed via
    reading `docspec.py` that NO such check exists today (`related`-type fields are untyped `"free_list"`, never
    resolved against the filesystem); (4) Slack alert + optional AO-escalator dispatch on red, same as today just on the
    new cadence. None of these implemented yet — correctly gated on proving the actual fix works first.
  - **CORRECTION (caught when the operator asked "what is this test and should we bump it to 2s?")**: I initially
    reported UTL's `test_manifest_completeness.py::TestF1PerfGuard` (a perf-guard on `compute_completeness_fraction()`,
    added alongside the 16.7x `80d2497e` filter-then-build/memoize optimization, asserting a 1.2M-row completeness
    lookup stays fast so a revert to the old O(n) full-scan gets caught) as a **still-open** regression needing an
    operator decision on its budget. That was wrong — I hadn't checked failure timestamps against the fix's landing
    time. **It was already fixed by another agent BEFORE this system check started**: `unified-trading-library@9081e51c`
    (authored 2026-07-21T02:09:30Z, already on `live-defi-rollout`) bumped the budget 0.5s → **3.0s** for exactly this
    reason (docstring cites the same shared-host contention: "consistently measured 0.57–0.70s… ~4× headroom over the
    worst observed CI time… a revert… exceeds it by 3.5×"). Re-checked all 9 "F1 build" failures in the original sample
    — **every one is dated 2026-07-20T19:26Z–2026-07-21T01:35Z, i.e. before the 02:09Z fix**; every UTL failure _after_
    the fix (6 of them, through 2026-07-21T23:20Z) was the unrelated pip-audit/CVE issue, not F1PerfGuard; and the last
    15 UTL runs (through 2026-07-22T07:49Z) are all green. **Zero recurrences since the fix landed — already resolved,
    no operator decision needed, do not re-open or lower the budget.**
  - **Coincidental, NOT migration-caused, already fixed by others**: instruments-service's
    `TestWriteVenueCanonicalPartition` tests hit `pytest_socket.SocketConnectBlockedError` on `169.254.169.254` for a
    few hours today. Traced (via a dedicated sub-agent, `instruments-service` git history) to a same-day refactor
    (`a9be6ce9`, 03:20 UTC) that changed `_write_venue` to build its own real `get_data_sink()` instead of using the
    test's mocked sink, without updating the test's mocks — would have failed identically on a GitHub-hosted runner
    (pytest-socket's `--allow-hosts` is the same either way). Two slots raced a fix within ~50 min
    (`4ca56889`/`14a1548f`, reconciled `a74e0c46`); HEAD is clean.
  - **Real, currently-live, fleet-wide, but NOT migration-caused**: a freshly-disclosed CVE pair in `pyasn1==0.6.3`
    (CVE-2026-59885, CVE-2026-59886) is failing the pip-audit gate (part of the merged `checks` leg / Codex compliance)
    on every repo that depends on it — confirmed red on unified-trading-library, features-service, and alerting-service
    (instruments-service likely too). This predates and is unrelated to the CI-cost work; it needs a version bump/pin or
    a documented waiver. Not actioned here (out of this plan's scope) — flagged to the operator.
  - **Everything else sampled** (instruments-service hardcoded-test-project-ID / function-size / DeFi-citation-baseline
    / UAC-adapter-registration-drift failures; the single `Escalate to Orchestrator` failure on a
    `gh pr edit --add-label` call hitting GitHub's deprecated `projectCards` GraphQL field) is pre-existing/organic
    fleet churn, unrelated to A1/A2/A5/STEP2b/notify-slack/prek/cron-cadence — each caught correctly by gates that were
    unchanged by this plan's work.
  - **Verdict for the operator**: the CI-cost-reduction changes themselves (A1/A2/A5/STEP2b/alert-dedup/cron-cadence)
    are running clean — PM's own `quality-gates-v2` is 157 success / 12 failure / 31 cancelled (cancelled =
    concurrency-superseded, benign) over 5 days, and none of the fleet failures trace back to those specific changes.
    The one thing that WAS broken because of this plan's work (`ldr-docs-gate`) took two fix attempts — see the two
    CORRECTION entries above — and is now fixed pending live confirmation on the next real doc push. The F1PerfGuard
    finding above was itself later corrected too: it turned out to already be fixed by another agent before this check
    started, not an open regression.
- **`ldr-docs-gate` 4 operator-suggested improvements — SHIPPED 2026-07-22** (`unified-trading-pm@0349d1d15` +
  `51ce7c394`, same session as the LIVE PROOF above):
  1. Trigger switched `push` → `schedule: "0 * * * *"` + `workflow_dispatch` — cuts this workflow's own contribution to
     shared glue-runner load from ~240/day to 24/day.
  2. Full-corpus scan (not diff-since-last-push) KEPT deliberately — measured 2.04s for the whole 1670-doc corpus, so
     scoping buys negligible performance and doesn't map cleanly onto a periodic model anyway. What per-push attribution
     gave is recovered via a per-violating-file `git log -1` lookup instead — MORE precise than `head_commit` once
     hourly batching means several commits land between checks.
  3. New `docspec.validate_doc_references()`: existence-only check for frontmatter fields that reference other docs by
     relative path (`related`, `codex_ssots`, `supersedes`, `depends_on`, etc.), skipping bare slugs/prose by design
     (only entries containing `/` and ending `.md`/`.mdc`, no whitespace). Measured against the live corpus: 336 raw
     hits → 244 were references to a plan later completed+archived (a normal lifecycle event, now discounted via a
     `plans/archive/**` basename fallback) → 91 genuine dead links remain, seeded into
     `scripts/plan-hygiene/doc_reference_baseline.yaml` (same shrinking-ratchet convention as
     `defi_address_citation_baseline.yaml`) so the check gates NEW breakage only, not day-one pre-existing debt.
     Verified live: injecting a synthetic broken reference correctly failed with a
     `(NEW — not in doc_reference_baseline.yaml)` marker; reverted clean; `--update-doc-ref-baseline` confirmed
     idempotent (zero-diff re-run).
  4. On red, in addition to the existing Slack page, now ALSO dispatches `wall_type: plan_health` to
     `escalate-to-orchestrator.yml` (the SAME already-built resolver `plan-health-agent.yml`'s PR-gate uses —
     `server/plan_health.py` + `agents/plan-health.md`) via `pr_number: 0` (non-PR-scoped, sanctioned by that workflow's
     own contract), so a worker actually attempts the fix instead of only paging a human.
  - **NOT YET VERIFIED**: the `schedule:` trigger resolves against the repo's DEFAULT branch (`main`), which still had
    the pre-fix workflow file at commit time. Tried a direct push of just this one file to `main` — correctly REJECTED
    by branch protection (PR + required `quality-gates-v2` check, no exception; my assumption that the
    `.github/**`-direct-push carve-out meant a literal git-push bypass was WRONG for this repo's actual GitHub ruleset).
    It will reach `main` via the existing LDR→main auto-promote cycle (`ldr-to-main-promote(-fleet).yml`, `*/15`,
    v2-gated auto-merge) — new todo below to confirm the cron actually fires once that lands.
- **LESSON (2026-07-22): never pipe a secret value into visible tool output while inspecting the VM.** Twice this
  session — once reading the Slack bot token from Secret Manager to test auth, once running `ps aux`/`systemctl status`
  on the glue-runner cgroup (which embeds each JIT-ephemeral runner's registration token as a `--jitconfig` base64 CLI
  arg) — a live token landed in plaintext in tool output/the conversation transcript. Neither was written to a file
  (checked: no token-shaped string anywhere in this session's scratchpad), but both were avoidable: check a secret's
  exit code / length instead of `head -c`'ing its value, and never dump a bare `ps aux`/`systemctl status` on this
  specific cgroup — pipe through `ps -o pid,etimes,cmd | cut -c1-80` or grep for the process NAME only.

- **2026-07-23 — 1-week interim billing check (operator ask: "did the migration pay off?").** NOT the scheduled two-week
  Phase-5 re-pull below — an informal 1-week checkpoint, live-pulled from the same Enhanced-Billing ledger
  (`github-billing-token` → `GET /users/IggyIkenna/settings/billing/usage?year=2026&month=7`, 1,283 line items, 100%
  `product=actions`, token shredded from scratchpad immediately after the pull). Method: pre = Jul 1–15 (the plan's own
  Phase-0 baseline window); post = Jul 17–22 (6 full days — the first clean days after BOTH STEP 2, 37/37 movers, and
  STEP 2c, the composite-action conversion, landed 2026-07-17); Jul 16 excluded as the deploy/transition day (only 10/38
  flipped, canary testing in progress, spend that day was actually the month's 2nd-highest); Jul 23 excluded as a
  partial day (pulled mid-session).
  - **PM (the only repo STEP 2 touched) — real, measured win**: **$16.89/day → $10.94/day, -35.3%**
    (-$5.96/day;
    run-rate ~$513/mo → ~$333/mo, ~**$181/mo saved** if sustained;
    ~$36 actually saved over the 6 clean post-migration
    days). Against the tighter immediately-prior week (Jul 8–15 = $24.74/day,
    since spend was ramping into mid-July — see the Jul 13/14 spike that triggered this whole plan) the drop reads
    steeper: -55.8%, ~$420/mo run-rate. Report both; the true number is baseline-sensitive and the 2-week re-pull will
    tighten it.
  - **Fleet-wide total did NOT drop** — $35.51/day → $38.37/day (**+8.1%**), nowhere near the plan's own
    "~$1,000/mo →
    ~$300–400/mo" target. Root cause, isolated by repo: **every non-PM repo rose**,
    $18.61/day → $27.44/day (**+47%**, ~$566/mo → ~$834/mo run-rate) — and STEP 2 touched **zero** non-PM workflows, so
    this is not the migration backfiring. Per-day trace shows several repos (features-service, agent-orchestrator,
    deployment-api, market-tick-data-service) were already elevated on Jul 14–16, _before_ migration — a fleet-wide
    activity ramp this plan didn't touch, now masking PM's real saving in the naive fleet total. Not investigated
    further (out of this plan's scope) — worth a look if it doesn't revert on its own by the 2-week re-pull.
  - **Data-quality note**: this pull's Jul 1–15 fleet total
    ($532.58) is ~10% above the plan's originally-recorded
    baseline ($485, frontmatter `source:`) — Enhanced-Billing
    appears to backfill/revise a few days after the fact (the original was pulled ~Jul 15/16, before the period closed).
    Use this session's $532.58/$16.89-per-day-PM as the more complete Phase-0 reference going forward.
  - **Verdict**: PM's piece of the plan is working as designed, in the right direction, at roughly 36–100% of the item-1
    estimate ($400–500/mo) depending which baseline you trust — genuine progress, not yet provable as the full plan
    target, and invisible in a naive fleet-total check because of unrelated fleet growth. Don't re-derive this by hand
    next time — the pull command + math above is reusable verbatim for the scheduled 2-week comparison.

- **2026-07-23 (session end) — LESSONS worth more than the state.** Recorded because each cost real time today and none
  of it is inferable from the diffs:
  1. **I stated two things before verifying them, and both were materially wrong.** (a) Published
     "~$180–195/mo of
     staging waste, all GitHub-hosted" — PM's four drivers were ALREADY self-hosted since STEP 2 (in this plan's own
     MOVE list, which I failed to re-read); real figure ~$166/mo,
     ~97% of it in the two templates that CANNOT be self-hosted. (b) Repeated a sub-agent's "transient xdist flake"
     diagnosis — it was deterministic and concealed a P1 gate-bypass. **Rule: a sub-agent's DIAGNOSIS is a hypothesis,
     not a finding. Re-run the check yourself before it reaches a doc or the operator.**
  2. **`billable={}` (absence of the `UBUNTU` key) is the honest self-hosted check on this account.** `/timing`'s
     `total_ms` reads 0 for HOSTED jobs too — it proves nothing on its own. This is what made the wrong cost figure look
     plausible.
  3. **PM's LDR is too busy for the documented sentinel-race workaround alone.** The known P0 workaround (chain
     `quality-gates.sh --no-fix && quickmerge.sh` in one shell) was NOT sufficient — PM takes a push roughly every ~2
     min while its gate takes ~4, so the commit always arrived stale (failed 3×, drift of 3 → 1 → 1 commits). What
     worked: a bounded `for i in 1..5; pull --rebase --autostash; quickmerge; break-if-clean` loop — landed on
     attempt 2. Use the loop on PM; a single retry is not enough. NEVER `SKIP_BRANCH_DRIFT` (human-only).
  4. **Derive fleet-rollout order topologically from `workspace-manifest.json`, don't discover it by failure.**
     Yesterday's rollout blocked repo-by-repo on quickmerge's dep-audit. Today, computing dependency layers up front
     (Layer 1 `deployment-ui`/`unified-api-contracts`/`unified-trading-system-ui` → L2 `unified-trading-library` → L3 17
     repos → L4 `deployment-api`/`e2e-testing` → L5 `system-integration-tests`) let batches of 5-6 run cleanly in
     parallel. The one-liner that produces it is in the session transcript's audit step; re-derive with a topological
     sort over `repositories.<repo>.dependencies`.
  5. **gitleaks false-positives on ordinary prose — and the trap is RECURSIVE.** The `generic-api-key` rule blocked a
     `docs(plans):` commit twice today. Trigger shape (described, deliberately NOT reproduced here, see why below): a
     frontmatter line where the word "key" is followed by a comma and then a slash-joined token pair — gitleaks reads
     that token as a secret assigned to the "key". The recursion: my FIRST fix reworded the frontmatter, but then
     writing THIS lesson quoted the original string verbatim, which re-triggered the identical block on the very commit
     carrying the lesson. **So: describe such a trigger, never quote it.** Also: do NOT add a gitleaks suppression for a
     doc, and do not assume a gitleaks failure means you leaked something — read the `Finding:` line first, it prints
     the matched context.
  6. **Rejected approach, so it isn't re-walked:** self-hosting the two staging fleet templates to make them free. Not
     possible — all 8 runners are registered to `unified-trading-pm` ONLY (fleet repos measure 0;
     `orgs/IggyIkenna/ actions/runners` → 404, personal account, no org pool). Flipping their `runs-on` would hang all
     24 rendered copies. This is the plan's existing **KEEP-T** class, re-confirmed by measurement.

---

## Cost ruling 2026-07-23 — semver-agent stays DEAD; minting moves to the PM reconciler (option B)

Investigating the dead fleet release tagging (`plans/active/issues/post_cutover_silent_assumption_sweep_2026_07_23.md`
F2) surfaced a decision that belongs to THIS plan, because it is a spend decision, not a repair.

**Root cause of the tagging outage was not a bug — it was an orphaning.** `semver-agent.yml` triggers on
`push: [staging]`; the 2026-06-27 cutover made staging dormant, so the only thing that mints `v*` tags simply stopped
firing (last runs UTL 2026-06-28 / UAC 2026-06-27, matching each repo's newest tag exactly). Measured impact: **22
repos, 26–29 days, ~2,490 unreleased commits.**

**Reviving it was built, proven, and then REVERTED — on cost and noise:**

| axis         | measured                                                                                                                         |
| ------------ | -------------------------------------------------------------------------------------------------------------------------------- |
| GHA cost     | `ubuntu-latest` (unmovable — self-hosted runners are PM-only, no org pool), ~~178 runs/day, 1-min billing minimum ⇒ **~~$32/mo** |
| commit noise | **733 PM `chore(manifest)` commits in 30 days — ~24/day, peak 84/day**, into the merge-driver file every slot rebases on         |

~$32/mo is a **~19% add-back** against this plan's ~$166/mo baseline, which is why it was rejected here rather than
treated as a straightforward fix. **Option B** puts minting in `reconcile_release_tags.py`, already scheduled `*/30` in
PM on **self-hosted runners (\$0)**, with ONE batched manifest commit per run instead of one per bump — same versions
and rollback capability, no new billable runs, no commit storm.

**Reverted, verified clean:** `unified-api-contracts@d9ff488b`, `unified-trading-library@df89ac54`,
`unified-trading-api@6987074`. The proven template is recoverable from the pre-revert shas cited in the issue doc.

**KEPT deliberately** (zero cost, zero noise, independent of the minter design):

- the release-stall **detector** in `reconcile_release_tags.py` — converts a silent 4-week outage into a `::warning::`
  naming the repos and their staleness (this is what measured the numbers above);
- `publish-package.yml` **fail-closed on `0.0.0.dev0`** + `fetch-depth: 0` (a shallow checkout has no tags, so hatch-vcs
  emitted a sentinel version — that wheel is in AR from 2026-07-03);
- `unified-trading-library@08b4d89a` — the `:VERSION` Docker tag is no longer re-pointed at new content.

**Lesson for this plan's cost model:** "revive the dead thing" is not automatically the right fix. The measurement that
mattered here was not whether it works, but what it costs per month and how many commits/day it generates — and both
were knowable before writing any code. Measure the running cost of a mechanism BEFORE restoring it.

## Deferred work after 2026-07-23

| #   | Item                                                                   | State / why deferred                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | Blocked on               |
| --- | ---------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------ |
| 1   | **Trading kill-switch is a no-op** (`halt-order-flow` has no listener) | **OPERATOR-OWNED.** Verified first-hand: execution-service has only a `dependency-update` listener; 204 reads as success; the code's own comment predicts a 404 that never comes. Touches live trading behaviour — not started.                                                                                                                                                                                                                                                                                                                                                                                                                  | Operator ruling          |
| 2   | ~~**Fleet release tagging dead since 2026-06-27**~~                    | **STALE — RESOLVED 2026-07-25, this table row was never updated.** CLAUDE.md already records `semver-agent` "retargeted off `staging`" to `push:[main]` (2026-07-25). Spot-checked live 2026-07-27: `Semver Agent` firing 100%-success on `push` in features-service/agent-orchestrator/instruments-service/unified-api-contracts (21-22 runs/3d each); fresh `v*` tags landed 2026-07-25/26/27 in all four (e.g. `unified-api-contracts` jumped a 30-day-stale `v0.72.0`@06-27 straight to `v0.73.0`@07-27). Do not re-derive or re-fix — it's working. Still `KEEP-T` (github-hosted, ~$32/mo fleet-wide, accepted cost per the ruling below). | Resolved, needs no owner |
| 3   | **QG sentinel is environment-blind**                                   | **NOT DONE.** Gate-bypass: a standalone (prod-default) gate pass writes a sentinel that quickmerge (dev-mode) then honours, skipping the failing suite.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | Operator picks fix split |
| 4   | `staging_versions` dep-gate fix                                        | **BLOCKED — do not action independently.** Its premise was inverted by finding F2; `staging_versions` tracks the real git tag, `versions` does not.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | Item 2                   |
| 5   | ~~Codex staging re-entry procedure + stale branch-model sections~~     | ✅ **RECONCILED 2026-08-09 (`ci_satellite_ao_dispatch_batch6_finalize` todo 1) — already done, stale row.** **DONE 2026-07-26** via `ci_satellite_ao_dispatch_batch1_2026_07_26.md`'s combined `[DOC] P2` todo — `unified-trading-pm@97970974e` (verified ancestor of `origin/live-defi-rollout`). All four staging-as-canonical narrative sites corrected to the LDR→main-direct model; added the "Staging re-entry procedure" section (manifest flip + disabled-triggers table + default-branch schedule gotcha); corrected the stale "WARN-default" line.                                                                                     | Resolved, needs no owner |
| 6   | 4 orphan dispatches · 4 dead listeners · ~873 vacuous cron runs/wk     | **NOT DONE, P2.** All catalogued with file:line in the sweep issue. `digest-drift-sweep` is the only one costing real money (never converges, fans out to `ubuntu-latest`).                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | Nobody                   |
| 7   | Two-week billing re-pull vs the Phase-0 baseline                       | **CANNOT BE DONE YET** — needs elapsed time. Earliest ~2026-07-31. Method + exact commands are in the 2026-07-23 billing entry above; re-run verbatim.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | The calendar             |

**#2 (release tagging) is now RESOLVED** (see the corrected row above) — it is no longer the recommended next item. #1
is more severe but is explicitly the operator's call (still not started). SSOT for 1/5/6:
`plans/active/issues/post_cutover_silent_assumption_sweep_2026_07_23.md`.

**Recommended NEXT item (added 2026-07-27, operator ask: "how do we cut fleet GHA spend another 50%?"): Phase 7 below.**
A live billing pull + run-mix sample (not a re-read of stale numbers) shows the 2026-07-15/17 self-hosted migration's
~35-56% win is real but PM-only — **100% of every non-PM repo's spend is still plain GitHub-hosted `Actions Linux`**,
which is why the fleet total never dropped (`$35.51/day → $38.37/day`, masked by unrelated non-PM growth the parent plan
already flagged and never followed up on). Non-PM is now 62% of fleet spend and growing (features-service/
agent-orchestrator up 180-230% vs the Jul01-15 baseline).

## Phase 7 — Fleet-wide self-hosted-runner rollout (NEW 2026-07-27)

> **Evidence**: live Enhanced-Billing pull (`github-billing-token`, same method as the 2026-07-23 entry above), Jul23-26
> per-repo/per-SKU breakdown: PM $14.25/day (win partly eroded from the $10.94 post-migration figure); non-PM $23.09/day
> across 24 repos, **every single line item is `Actions Linux`** (zero self-hosted offload outside PM). Run-mix sample
> (`gh api .../actions/runs`, last 3 days) on the two fastest-growing repos shows the SAME categories of thin glue/
> dispatch workflow PM already proved movable — `main-backmerge-to-ldr` (~13/day), `image-build-gate` (~15/day),
> `Semver Agent` (~7/day), `update-dependency-version` (~7/day) — all still hosted, structurally, because **all 8
> self-hosted runners are registered to `unified-trading-pm` only** (`orgs/IggyIkenna/actions/runners` → 404, personal
> account, no org-level pool — the exact `KEEP-T`/`KEEP-R` blocker the original migration doc already found and
> correctly left alone rather than hanging 24 repos). **`quality-gates-v2`'s real pull_request-triggered
> pytest/lint/typecheck job is explicitly OUT of scope** — it stays hosted per the existing security ADR (no self-hosted
> runner may carry a `pull_request` trigger) and touching it is not part of this phase.

> **Expected savings — measured, NOT the ~35-56% PM got.** Pulled real per-JOB billed minutes
> (`gh api .../actions/runs/{id}/jobs`, counting jobs not `/timing.total_ms` — the same trap the 2026-07-17 session
> already documented) for one `quality-gates-v2` run and one `image-build-gate` run on features-service:
> `quality-gates-v2` bills **~14 min/run** (`content sentinel` 1 + `QG slice (checks)` 3 + `QG slice (tests)` 9 + rollup
> 1 — ALL of it inside the SAME pull_request-triggered workflow file, so none of it is separable from the security
> boundary; the 5 conditional glue jobs in that file were `skipped`/unbilled on this run). `image-build-gate` bills **~2
> min/run**. `main-backmerge-to-ldr` bills **~1 min/run**. At measured daily run-rates (~43-49/day quality-gates-v2,
> ~15-17/day image-build-gate, ~13-15/day main-backmerge-to-ldr, plus smaller items), the confidently **movable** glue
> (`main-backmerge-to-ldr` + `update-dependency-version` + `version-registry-notify` + `major-bump-issue-handler` — all
> push/repository_dispatch/issue_comment triggered, none `pull_request`) is only **~4-5% of one busy repo's total billed
> minutes**; `image-build-gate` (~9%) is a SEPARATE, larger pool. **`image-build-gate`'s security review is now DONE
> (2026-07-27), not open** — read the actual reusable (`unified-trading-pm/.github/workflows/image-build-validate.yml`):
> it `actions/checkout`s **PM's own repo, never the calling repo's PR code**; the real Docker build already happens on
> **GCP Cloud Build / AWS CodeBuild**, triggered via `gcloud builds triggers run --substitutions=...` with the PR's
> commit SHA passed as a plain string (not templated into the shell — `branch`/`commit_sha` flow through `env:`
> indirection, the safe GitHub-recommended pattern, not `${{ }}` interpolated directly into `run:`). **Verdict: safe to
> self-host once a runner exists for the calling repo** — its `pull_request` trigger doesn't carry the risk
> `quality-gates-v2` does, because it never executes the calling repo's code at all; the only blocker is the same
> runner-registration gap as everything else in this phase. **quality-gates-v2's real test/lint job alone is ~90%+ of a
> plain service repo's billed minutes** — far higher than PM's own ~18-20% pre-migration share, because service repos
> don't run PM's extra automation (`ci-status-consolidator`, `cloud-build-router`, monitors, etc.) that diluted PM's own
> quality-gates-v2 share. **Net read: Phase 7 (main-backmerge/update-dependency-version/etc. + now image-build-gate)
> plausibly nets ~13-14% off each non-PM repo's own spend** (~8-9% off the fleet total) — real and worth doing, but the
> 50% target is NOT reachable through this lever alone. Getting there needs the real-test-compute lever below (P3).

> **Operator decision (NEW 2026-07-27) — is moving `quality-gates-v2` itself off hosted runners worth the security
> tradeoff?** This is where the actual 50%+ lives (it's ~90%+ of a service repo's spend), and it is explicitly NOT
> recommended casually. GitHub-hosted runners for `pull_request` are ephemeral, single-use, zero-ambient-credential
> sandboxes destroyed after each job; this workspace's self-hosted runners carry AMBIENT GCP/AWS credentials on a
> persistent host (that's why they're useful for the glue jobs). Running the real pytest suite there means a compromised
> transitive PyPI dependency (`uv sync` resolves the PR's own lockfile — no malicious human required) or an autonomous
> agent writing something dangerous into a test file (elevated risk here specifically, given how much agent-driven code
> churn this workspace has vs. a small human team) executes WITH that host's real cloud access, and one bad run poisons
> the box for every other repo/job sharing it. Doing this "safely" means building fully ephemeral, zero-ambient-
> credential, per-job sandboxes (torn down after every run) — a real infra project shared by all ~25 repos, not a
> `runs-on:` flip; one misconfiguration reopens the hole fleet-wide. **Not started, not recommended by default** — this
> needs an explicit operator call, weighing the real $ upside against a real security posture change. **This is not a
> hypothetical: verified live 2026-07-27 that the actual ambient identity on this host is account-wide
> S3/RDS/ECS/DynamoDB `*FullAccess` plus a `self-manage-own-policies` privilege-escalation primitive (any process on the
> box can attach `AdministratorAccess` to itself) — filed as its own P0, see
> `/plans/archive/issues/orchestrator_vm_aws_role_overprivileged_self_escalating_2026_07_27.md`. This is a pre-existing
> exposure for every self-hosted CI job running there TODAY, not created by moving quality-gates-v2 — but it means the
> "ambient credentials" risk above is not theoretical, and fixing the IAM scope (that issue's own recommendation) is a
> prerequisite to this decision looking any different than "full AWS account compromise on one bad test run."**

- [x] ✅ **DONE 2026-07-27 — fleet-wide MOVE/KEEP audit, all 24 non-PM repos, verified live.** Ran
      `classify-glue-workflows.sh` via its existing `WF_DIR` override against every repo in `workspace-manifest.json`
      (not a re-derivation — the script needed zero code changes, it already supports pointing at any repo's
      `.github/workflows/`). Every repo resolved cleanly (no hangs, no missing dirs). **Result: 178 MOVE-classified
      workflow files across the 24 repos** (per-repo range 6-9, consistently matching the fleet-template MOVE set
      already named in this doc: `main-backmerge-to-ldr`, `major-bump-issue-handler`, `request-major-bump`,
      `semver-agent`, `staging-backmerge-to-ldr`, `update-dependency-version`, `version-registry-notify`, plus a handful
      of repo-owned extras per repo). KEEP counts (3-8/repo) are consistently
      `quality-gates-v2`/`image-build-gate`/`staging-lock-check` (pull_request-triggered) plus repo-specific
      `KEEP-U`/`KEEP*` entries. Full per-repo breakdown in "## Phase 7 fleet audit — per-repo breakdown" at the bottom
      of this doc — do not re-run this audit, read that table instead. **Still blocked on the runner-registration
      finding immediately below before any of these 178 can actually move.**
- [x] ✅ **RESIZED 2026-07-27 — `i-0c9b283b31d6b5ca7` is now `m8i.4xlarge` (16 vCPU / 64GB), up from `m8i.2xlarge` (8
      vCPU / 32GB).** Operator decision: double both CPU and RAM (matches the dual-purpose framing below — this was
      never purely a GHA-savings call). Executed via a NEW canonical procedure, NOT an opportunistic mid-session stop:
      `agent-orchestrator/scripts/orchestrator/clean-restart-vm.sh     i-0c9b283b31d6b5ca7 m8i.4xlarge 900` —
      checkpoints every `orch-slot-*`/`orch-agent-main` tmux session (injects `/pre-compact`, polls each pane for the
      skill's own "Safe to compact" verdict, up to a 15-minute budget) BEFORE stopping, so in-flight git work gets
      committed+pushed first rather than silently lost. Real run: 16 sessions found, 3 checkpointed inside the window
      (slot-1, slot-9, slot-15), 13 timed out and were restarted anyway per the 15-min cap (their uncommitted
      conversational state was lost — expected, not a bug; only uncommitted GIT state was ever at risk, and none of
      those 13 had walked off a cliff mid-commit). Post-resize verified live: `nproc`→16, `free -m`→63255MB total
      (~61.8GiB, matching the 64GB nominal spec), `orchestrator.service` active, EIP `13.113.200.22` unaffected (a real
      allocated Elastic IP, confirmed before stopping — survives stop/start). **This script is now the canonical way to
      restart this VM for ANY reason**, not just this resize — use it instead of a bare `aws ec2 stop-instances`/reboot
      from now on. Financial framing (unchanged from the analysis below, now moot as a blocker): the narrow
      "GHA-savings-only" verdict said this doesn't pencil out; the operator's dual-purpose framing (fixes the
      orchestrator's own chronic ~5x CPU oversubscription for interactive/autonomous slots, independent of CI, plus the
      GHA ceiling, plus likely-faster self-hosted `quality-gates-v2` wall-clock) is why it was approved anyway — see
      both framings preserved below for the reasoning trail.
- [x] ✅ **Byproduct fix, same session — the AO dashboard's live RAM number was never actually wrong.** Investigated the
      operator's "RAM number reads too low" report: `agent-orchestrator/server/host_resources.py` correctly reads
      `/proc/meminfo` on the host and reported ~30.8GB out of the (pre-resize) real ~31.5GB total — accurate. The actual
      bug was several OTHER files stating this exact host was already `m8i.4xlarge`/64GB
      (`orchestrator_vm_registry.yaml`, `orchestrator.service`'s `MemoryHigh=48G`/`MemoryMax=56G` comment+values,
      `apply_resource_limits.sh`, a terraform comment, a launcher default, several codex docs) — a stale assumption from
      before an earlier undocumented downsize to `m8i.2xlarge`. The resize above makes those files true again rather
      than needing a correction; verified `orchestrator_vm_registry.yaml`'s `instance_type: m8i.4xlarge` entry is now
      accurate. No code fix was needed in the live dashboard path.
- [ ] [INFRA] P2. **RULED 2026-07-28 (retagged from `[OPERATOR]`) — scheduled, not blocked: operator has already
      self-provisioned 2 of the additional Claude account credentials personally; that's enough for now, do NOT
      provision more immediately.** Raising slot concurrency 12→16 needs 4 more Claude account credentials total, a
      separate real cost/logistics item from the VM resize (which is done). `bootstrap_vm.sh --slots N` only provisions
      worktree directories; each slot still needs a real underlying account
      (`ORCHESTRATOR_ACCOUNTS`/`data/config/accounts.json`, account-rotation logic in
      `agent-orchestrator/server/autospawn.py`). Operator expects the remaining accounts to free up within hours-to-
      days of 2026-07-28. **Do not re-raise this before ~2026-08-02** — revisit then: if the operator has freed up the
      remaining credentials, wire them in and raise concurrency to 16; if not yet, re-check again rather than
      provisioning anything without the operator's own account action. In the meantime, continue running on the current
      (lower) concurrency — this is not a blocker for any other work.
- [x] ✅ **DONE 2026-08-09 (`ci_satellite_ao_dispatch_batch5_2026_08_02.md` todo 2, slot 11) — measured, WITHIN BAND, no
      re-escalation.** `bq query` on `central-element-323112.deployment_operational_data.resource_samples`
      (`vm_name='planning'`, `service='agent-orchestrator'` — the only values resolving to this host): **avg_cpu_pct =
      50.6%** (min 16.7%, p95 85.6%, max 95.1%, 171 samples) — **within the 50-70% band**, real burst headroom, neither
      failure mode. Caveat: pipeline data for this VM only starts 2026-08-08 03:14:43 (verified no earlier rows in a
      35-day back-check), so the window is ~29.5h, not multi-day — the verdict is unambiguous regardless. Per the
      done-condition, no re-escalation warranted. Original text preserved below for record.
  - **Retagged from `[OPERATOR]` (2026-07-28 gate-cleanup pass)** — this is a measurable fact-check, not an operator
    judgment call: run the verification directly against the durable BigQuery `resource_samples` pipeline (below) over a
    sustained window, compute the average utilization, and report it against the operator's pre-stated band. **No
    further human judgment required unless the measured result falls outside that band** — at which point re-escalate
    with the number. (tracked as `ci_satellite_ao_dispatch_batch4_2026_07_31.md` Deferred D4-3, picked up as
    `ci_satellite_ao_dispatch_batch5_2026_08_02.md` todo [VERIFY] P2 ~line 163; both status: active, open/dispatchable
    now, not yet completed. **Corrected 2026-08-07 (na-eligibility-audit)**: previously said "both status: draft, not
    yet dispatched" — both are `status: active`) **Post-scale verification, now that the resize IS done (2026-07-27).**
    Watch the rolling utilization for a sustained window over the coming days — target ~50-70% average with burst
    headroom; NOT 30-40% (over-provisioned, give some back) and NOT pinned 90%+ again (under-provisioned, the resize
    didn't fix it). The durable BigQuery `resource_samples` pipeline (below) now exists to answer this with real data
    once the bridge cron is retired in favour of it — do not judge this off a single point-in-time SSM check.

              **Phase 7's scope (thin push/repository_dispatch glue only —
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              main-backmerge-to-ldr, image-build-gate's polling wrapper, update-dependency-version, etc.) is still fine to add
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              here** — none of it is CPU-heavy. A dedicated, appropriately-sized runner host (separate from the orchestrator
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              box) would be needed before any CPU-heavy workload could safely self-host, which is its own cost to weigh against
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              the savings.

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      **⚠️ That CPU-heavy boundary has already been crossed for ≥9 repos, and there's now real measured
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      contention evidence (2026-07-27, ~23:20 UTC).** `python-quality-gates-v2.yml`'s `qg-slices` job (the
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      REAL pytest/typecheck/lint compute, not glue) takes a `self_hosted_runner_labels` input — default empty
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      → `ubuntu-latest`, but grep across the fleet shows agent-orchestrator, execution-service,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      deployment-service, batch-live-reconciliation-service, e2e-testing, ml-service, strategy-service,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      greeks-service, and instruments-service have ALL already opted in (`self_hosted_runner_labels` set in
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      their own `quality-gates-v2.yml` caller). Every one of these repos' "glue" runners
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      (`glue-ip-172-31-5-118-{1,2}`) resolve to the SAME physical host as the orchestrator VM itself
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      (`i-0c9b283b31d6b5ca7`, confirmed via `aws ec2 describe-instances --filters
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      Name=private-ip-address,Values=172.31.5.118`) — i.e. real pytest/typecheck compute for ≥9 repos is now
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      running on the exact box that also hosts the AO dispatch system and every interactive/autonomous agent
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      slot. Measured just now: CPU is NOT the bottleneck (CloudWatch `CPUUtilization` over the last 2h:
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      23-58% avg, 26-64% max — well within the 50-70% target range above) but the attached `gp3` EBS volume
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      (`vol-0b4f0237fa0f5cd0f`, 500GB @ baseline 3000 IOPS / 125 MB/s — never upsized alongside the CPU/RAM
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      resize) shows a SUSTAINED `VolumeQueueLength` of ~2.5-2.9 for the full 2-hour window checked, not a
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      spike — consistent with the real symptoms observed same-day: a deployment-service QG job that normally
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      takes minutes was still `in_progress` after 77+ minutes (well inside its generous 135m timeout, so it
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      may still complete, but that's degraded, not healthy), plus the independently-root-caused
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      `SETUPTOOLS_SCM_SUBPROCESS_TIMEOUT` git-status-timeout fix already landed in this same workflow file
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      today for the identical contention signature on execution-service. **This reads as disk I/O
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      provisioning, not CPU provisioning, being the actual constraint** — the CPU/RAM resize earlier today
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      addressed a real problem but not this one; an EBS `iops`/`throughput` bump on `vol-0b4f0237fa0f5cd0f`
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      (a live, non-disruptive `gp3` modify-volume operation) is the more targeted fix to actually try before
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      reaching for the heavier "dedicated separate runner host" option this todo already named. Not actioned
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      — operator-level shared-host capacity/cost decision, same class as the CPU/RAM resize itself.

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      **This corroborates, and is a smaller-magnitude AFTER-picture of,**
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      `plans/active/issues/orchestrator_vm_disk_io_contention_runner_burst_2026_07_28.md` — the SAME Phase-7
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      runner-registration burst drove this exact box to 66→93% iowait / load-avg 74→119 / swap growing / disk
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      90% full a few hours earlier (with the operator's OWN interactive AO slot-workers observed in D-state
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      alongside the runner processes), which is why `glue-2` was disabled across all 23 newly-registered
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      pools as an immediate mitigation. The `VolumeQueueLength` ~2.5-2.9 measured here is the RESIDUAL level
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      AFTER that halving — not the raw pre-mitigation severity — so the fact meaningful queueing is still
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      sustained post-mitigation is itself evidence this is a real steady-state capacity gap, not just burst
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      noise that self-resolves. See that doc for the fuller live diagnosis and the still-open P1/P2 follow-up
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      verification todos (confirm iowait actually eased, re-attempt the runners still showing
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      `total_count: 0`, and the longer-term glue-2-disabled-or-not capacity-planning call).

- [x] ✅ **DONE 2026-07-27 — `setup-glue-runners.sh` multi-tenancy fix, shipped + verified live
      (`unified-trading-pm@30872b269` + 2 same-day follow-ups `ab418de3a`/`dafa68ec4`).** Implemented the `POOL_TAG`
      parameterization exactly as scoped: `ENV_FILE`/`RUNNER_BASE` + all six systemd unit names/paths now derive from
      `POOL_TAG` (default empty ⇒ verified BYTE-IDENTICAL to every pre-existing installed unit — diffed locally against
      the checked-in templates before shipping). Unit-file CONTENT (not just filenames) needed substitution too, exactly
      as this todo predicted — `render_unit()` (sed-based) replaces `/opt/github-glue-runners`,
      `/etc/github-glue-runner.env`, `Slice=github-glue-runner.slice`, and (found live, not in the original scoping)
      `Unit=github-glue-slot-refresh.service` (the slot-refresh timer's explicit pairing line) +
      `RuntimeDirectory=github-glue-runner`/`GH_TOKEN_FILE`/ `GLUE_GCLOUD_CONFIG` (previously unset on 2 of 6 units,
      silently defaulting to PM's shared paths — harmless with one pool, load-bearing with two). Two more REAL bugs
      surfaced only by actually running a fresh install (not caught by reading the script): (1) the WIF cred-config
      write failed EPERM on a genuinely fresh `RUNNER_BASE` (root:root 0755) — pre-created the file first, same pattern
      already used for `repo.refreshed-at`; (2) `runner_path()` (used by `preflight`) read the checked-in template's
      literal PATH regardless of `POOL_TAG`, giving a false-positive python3/uv check against PM's already-built venv.
      Both fixed same session, both verified.
- [x] ✅ **DONE 2026-07-27 — agent-orchestrator canary runner pool live + verified healthy, PM's pool unaffected.**
      `setup-glue-runners.sh POOL_TAG=ao OWNER=IggyIkenna REPO=agent-orchestrator GLUE_COUNT=2 WRITER_COUNT=1     GH_TOKEN_SECRET=GH_PAT install`
      on `i-0c9b283b31d6b5ca7` — 2 glue + 1 writer, all `active running`, all `online` via `gh api .../actions/runners`
      (`glue-ip-172-31-5-118-1/-2`, `writer-ip-172-31-5-118-1`). PM's original 8-runner pool re-verified `status`
      immediately after — all 8 still `active running`/`online`, completely untouched.
- [x] ✅ **DONE 2026-07-27 — Phase 7 canary: 8 glue workflows flipped to self-hosted for agent-orchestrator, 2 live
      triggers verified green +
      $0 billed.** The 7 fleet-templated MOVE workflows (main-backmerge-to-ldr,
      major-bump-issue-handler + its Slack-failure job, request-major-bump + its Slack-failure job,
      staging-backmerge-to-ldr, update-dependency-version + its Slack-failure job, version-registry-notify,
      semver-agent) edited in the SHARED templates + rolled out via `rollout-workflow-templates.sh --repo
      agent-orchestrator --template <name>` (scoped to this ONE repo, not the other 23 — confirmed via dry-run first).
      Plus `deploy-dashboard.yml` (agent-orchestrator-owned, no shared template) hand-edited directly.
      `detect_template_drift.py --workflows` correctly flagged the resulting 23-repos-not-yet-rolled-out drift;
      baselined via `--baseline-write-allow-additions` (140 entries, `unified-trading-pm@b6c4d0fb1980d85f23859dcfa0107594fa5ff2b5`) as the documented,
      intentional, TEMPORARY canary-phase state — ratchet down as each repo gets its own runner + rollout. Live
      verification: triggered `main-backmerge-to-ldr` (run 30296962972, 13s) and `staging-backmerge-to-ldr` (run
      30297012634, 11s) via `gh workflow run`, both green; `gh api .../jobs/<id>` confirms `runner_name:
      glue-ip-172-31-5-118-1`, `labels: [self-hosted, glue]`; `gh api .../timing` confirms `billable: {}` ($0).
- [x] ✅ **DONE 2026-07-27 — quality-gates-v2 canary: the REAL pytest/lint/typecheck job (qg-slices) verified running on
      self-hosted infra, green,
      $0 billed.** This is the operator's actual "migrate the expensive CI job" ask (Phase
      7 above is the thin-glue 90%-is-NOT-this remainder). Cannot be a blanket `runs-on:` flip in the shared reusable
      workflow (`unified-trading-pm/.github/workflows/python-quality-gates-v2.yml`) — it is called via `uses:` by ALL 24
      non-PM repos, and only PM + agent-orchestrator have a self-hosted pool; a global flip would hang every other
      repo's promotion gate waiting for a runner that never appears. Fix: added an opt-in `self_hosted_runner_labels`
      `workflow_call` input (default `''` ⇒ `ubuntu-latest`, byte-identical for every caller that doesn't pass it —
      `unified-trading-pm@5058dca8`, actionlint-clean), touching ONLY the `qg-slices` matrix job (the ~90%+-of-billed-
      minutes one per this doc's own measurement above) — the file's other thin glue jobs (content-gate,
      supersede-check, etc.) are untouched, separate scope. **Verified the default path is unaffected first**:
      deployment-api's quality-gates-v2 (run 30297826469, doesn't pass the new input) ran green on `ubuntu-latest` as
      always. Then agent-orchestrator's own `quality-gates-v2.yml` got a clearly-commented, deliberate, TEMPORARY
      hand-set `self_hosted_runner_labels: '["self-hosted","glue"]'` override (`agent-orchestrator@7ce642afb52f2fe26e1c1f34c6ed3f47b6d9b325`+push) —
      **run 30298445269: `QG slice (checks)` + `QG slice (tests)` both `conclusion: success`**, `runner_name:
      glue-ip-172-31-5-118-1`/`-2`, `labels: [self-hosted, glue]`, `billable: {}` ($0).
      The known P0 ambient-AWS- overprivilege finding
      (`/plans/archive/issues/orchestrator_vm_aws_role_overprivileged_self_escalating_2026_07_27.md`) remains UNRESOLVED
      and now has real (not hypothetical) exposure surface via this one repo's test runs — flagged, not fixed, per the
      operator's explicit override of the prior security deferral.
- [x] [INFRA] P1. **Fan out Phase 7 + the quality-gates-v2 self-host flip from the now-fully-verified agent-orchestrator
      canary to the remaining 23 repos.** Per-repo: register a `POOL_TAG=<repo-slug>` runner pool (capacity-plan against
      the 16 vCPU box — agent-orchestrator's canary used 2 glue + 1 writer; 23× that is NOT a straight multiply, size
      down for low-traffic repos), roll out the 7 already-edited templates via
      `rollout-workflow-templates.sh --repo <name>`, add its own `quality-gates-v2.yml` override (ideally replacing the
      hand-set canary pattern with a real per-repo templated substitution — a new `rollout-workflow-templates.sh`
      placeholder + allowlist, not 23 more hand-edits), verify a live trigger, ratchet the drift baseline down as each
      repo lands. — **✅ DONE 2026-07-27/28; closed 2026-07-30 by `/na-eligibility-audit ci` as STALE.** This doc's own
      dated "Final report" below supersedes the original "NOT started / paused for an operator scope-pacing" wording:
      pacing resolved (staged, 2-at-a-time), 23 pools registered + `online`, templates rolled, allowlist applied, live
      triggers verified, drift baseline seeded (`unified-trading-pm@b6c4d0fb1980d85f23859dcfa0107594fa5ff2b5`), closing
      _"All 24 non-PM repos in this fan-out are now fully shipped."_ **Caveat, not glossed**: `deployment-ui` was later
      reverted to `runs-on: ubuntu-latest` under host contention — the fan-out landed, that one repo's flip did not
      stick.
- [x] ✅ [VERIFY] P2. **DONE 2026-08-09 (slot-28)** — agent-orchestrator (first-flipped) `Actions Linux`
      $13.87/day→$3.78/day (-73%), no new billed line added; residual is the still-hosted quality-gates-v2 test job (out
      of scope, security ADR). Full numbers: batch4 todo 9 Progress Log.
- [x] ✅ [VERIFY] P2. **DONE 2026-08-09 (slot-28)** — fleet $37.35/day (Jul23-26) → $12.72/day (Aug1-8), -65.9%; non-PM
      -74.7%. Confirms the fleet-total target has now moved. Full numbers: batch4 todo 9 Progress Log. been
      `status: active` since creation)
- [x] ✅ **DONE 2026-07-28 — root-caused features-service's `quality-gates-v2` ~15-16×/day `workflow_dispatch` firing
      (was the (a) half of the P3 REVIEW below).** Traced to
      `unified-trading-pm/scripts/repo-management/ldr_ci_monitor.py` (hourly `ldr-ci-monitor.yml`): it conditionally
      re-dispatches `quality-gates-v2` against the LDR ref only when the LDR tip has moved since the last dispatch (the
      script's own docstring names this the deliberate anti-waste guard against "the unconditional-x24-repos Actions
      waste that got [caused] the [2026-06-11] billing wall"). Pulled features-service's actual dispatch history
      (`gh api .../workflows/quality-gates-v2.yml/runs?event=workflow_dispatch`): head SHA differs on almost every
      dispatch — this repo just has unusually high commit velocity, not a stuck/red LDR triggering the unconditional
      RED-repo re-check path. **Verdict: working as intended, not waste. No action needed.**
- [x] ✅ **EXTRACTED 2026-08-03 to its own issue doc** —
      `plans/active/issues/test_impact_selective_execution_design_2026_08_03.md`. Both the P3 "this is the actual path
      to 50%, not Phase 7" framing note and the P2 "scope a design (design only, no implementation)" todo
      (operator-approved 2026-07-28) moved there verbatim, plus the design itself is now written (safety guarantee,
      mapping mechanism grounded in real repo facts — dynamic-dispatch adapter registries, conftest.py-tree fixture
      coupling, manifest-driven tests — the fallback rule, and a 3-layer self-test / shadow-mode validation plan). Still
      gated on operator review before any implementation todo is authorized — this plan was at its 1000-line hard cap,
      so the open review-gate + follow-up todos now live in the new doc, not here.
- [ ] [REVIEW] P3. Longer-horizon alternative to per-repo runner registration, NOT recommended to start now: migrating
      the personal-account repos (`IggyIkenna/*`) into a GitHub organization to unlock a shared org-level runner group
      (free on GitHub's org tier — no Team/Enterprise upgrade needed for runner groups themselves). This would let ONE
      runner pool serve all repos instead of per-repo registration, but repo-ownership transfer risks breaking anything
      keyed to the literal `IggyIkenna/<repo>` slug (webhooks, PAT scopes, package-registry references, deploy keys) and
      should only be considered if per-repo runner management becomes unwieldy as the fleet grows.

## Phase 7 fleet audit — per-repo breakdown (2026-07-27)

`classify-glue-workflows.sh` run via its existing `WF_DIR` override against every repo in `workspace-manifest.json`
(zero code changes needed) — 178 MOVE / 108 KEEP across 24 repos, all resolved cleanly:

| Repo                              | MOVE | KEEP | Repo                      | MOVE | KEEP |
| --------------------------------- | ---- | ---- | ------------------------- | ---- | ---- |
| alerting-service                  | 7    | 4    | ml-service                | 7    | 3    |
| batch-live-reconciliation-service | 7    | 4    | strategy-service          | 8    | 4    |
| client-reporting-api              | 7    | 4    | system-integration-tests  | 8    | 7    |
| deployment-api                    | 7    | 4    | trading-agent-service     | 7    | 4    |
| deployment-service                | 7    | 4    | unified-api-contracts     | 8    | 8    |
| execution-service                 | 7    | 6    | unified-trading-library   | 8    | 4    |
| features-service                  | 9    | 5    | unified-trading-api       | 7    | 3    |
| fund-administration-service       | 9    | 3    | unified-trading-system-ui | 9    | 7    |
| greeks-service                    | 7    | 3    | deployment-ui             | 6    | 5    |
| ibkr-gateway-infra                | 7    | 4    | e2e-testing               | 7    | 3    |
| instruments-service               | 7    | 6    | agent-orchestrator        | 8    | 4    |
| market-data-processing-service    | 7    | 5    | market-tick-data-service  | 7    | 5    |

> **Line-cap remediation (2026-08-03)**: the "Progress Log (fan-out to the remaining 23 repos, 2026-07-27/28,
> `/autonomous`)" section and the "Final report" section (both fully closed — "all 24 non-PM repos... fully shipped —
> zero remaining items") were extracted verbatim to
> `/plans/archive/2026_08/github_actions_operator_gated_followups_progress_log_history_2026_08_03.md` to bring this doc
> back under the 1000-line hard cap.

## Progress Log — 2026-07-28 evening (`/autonomous`, deployment-ui migration + shared-box I/O fix + AO dashboard)

Full narrative + evidence lives in `/plans/active/issues/orchestrator_vm_disk_io_contention_runner_burst_2026_07_28.md`
(updated same session) — this entry is the pointer + terse status per plan-vs-issue-doc SSOT direction.

- ✅ `deployment-ui@22df17f`+`210e4c4` — real test/lint job moved to self-hosted `[self-hosted, glue]` (operator
  explicit go-ahead on the security tradeoff), timeout bumped 10→25min after a live regression (see issue doc).
- ✅ Root-caused + fixed the shared box's actual bottleneck: `vol-0b4f0237fa0f5cd0f` (gp3) was running AT its
  provisioned 8,000 IOPS/500 MB/s ceiling continuously (measured `iostat`, not inferred). Live `aws ec2 modify-volume` →
  16,000 IOPS/1,000 MB/s, no downtime. Corrects an overclaim in this plan's own "Final report" above
  ("IOPS/throughput/size all bumped" — only size was; iops/throughput is fixed NOW, not that session).
- ✅ `agent-orchestrator@<see repo log>` — Host Resources dashboard now surfaces `iowait_percent` + load average (4th
  tile, own colour thresholds), closing the exact blind-spot this incident exposed (CPU% read moderate while the box was
  66-93% iowait). Full test coverage both sides, `quality-gates.sh` green before ship.
- ✅ **DONE — `deployment-ui` PR #440 chain resolved end-to-end, verified on `main`.** Two more fixes landed on LDR from
  a separate `escalate-to-orchestrator` responder (`a1d58d8` typecheck timeout). Self-hosted still failed under host
  contention even at the bumped budgets (confirmed via `iostat`/`uptime`: not a config problem, the host genuinely
  couldn't complete the work) — reverted `deployment-ui` to `runs-on: ubuntu-latest` (temporary, same precedented fix
  `fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md` already proved on
  `strategy-service`/`execution-service`), verified green in 3m45s on a real hosted runner. The shared VM then went
  fully unreachable (SSH + SSM `ConnectionLost`) — waited for genuine recovery (~35min) rather than intervening on
  shared infra another process owned; confirmed recovered via SSM, re-triggered the promote sweep. Last blocker was
  `sit-gate/fleet-green` (a real fleet-wide SIT signal, not a per-repo check) churning through several
  cancelled/superseded runs during the post-outage activity burst — no manual fix needed, it cleared on its own. Stale
  PR #440 → superseded by fresh `#441` (`promote/deployment-ui/5c658c43bf62`) → **merged to `main` 22:07:53 UTC**,
  independently verified by reading `ui-quality-gates-v2.yml` back off `main` (`runs-on: ubuntu-latest` confirmed
  present). Loop terminates here — success criteria met, nothing left to pick up on this thread.

## na-eligibility-audit verdict

**na-eligibility-audit 2026-07-30** (tranche `ci`, autonomous): KEEP-NA, one stale item closed — the Phase-7 fan-out
todo closed against this doc's own Final report. The other 16 are operator-gated (D2/D3/D4 rulings, the bare-VM
bootstrap leg, 2 calendar-gated billing re-pulls, slot-concurrency pending operator account provisioning, org-migration
marked NOT-recommended) or claimed by ci dispatch batch 1 / batch 2. **na-eligibility-audit 2026-08-01**: re-confirmed
KEEP-NA, stale-items — 15/16 still operator-gated, 1 annotated tracked-elsewhere.

**na-eligibility-audit 2026-08-03** (tranche `ci`, autonomous, `agt-4acc10`): KEEP-NA, mixed — re-read all 13 open items
end-to-end. 8 stay KEEP-NA valid unchanged (sentinel race, STEP 2d/D3, SUPERSEDED-banner deletion, cassette-drift D4,
bare-VM bootstrap, slot-concurrency-16 pending operator credentials, org-migration NOT-recommended). Item
"`measure-billed-notify-cost.sh`" stays KEEP-NA-STALE with its existing citation to
`ci_satellite_ao_dispatch_batch1_ 2026_07_26.md` (active, still accurate, no fix needed). 5 items (representative-QG-run
job-minutes, two-week billing ledger re-pull, BigQuery `resource_samples` utilization, both Enhanced-Billing re-pulls)
were already independently extracted into `ci_satellite_ao_dispatch_batch4_2026_07_31.md` todo 9 / Deferred D4-3 (picked
up by `ci_satellite_ao_dispatch_batch5_2026_08_02.md`) but this doc carried no back-citation — added one to each item
above (both batches are `status: draft`, not yet dispatched, so no reclassification; flipping this doc directly would
open a competing dispatch path). No RECLASSIFY, no ARCHIVE. Cross-cutting note: batch4 (2026-07-31) and batch5
(2026-08-02) are both still un-activated drafts holding most of this doc's calendar-gated follow-on work — an
operator/workflow activation decision, out of this audit's scope.

## Progress Log

- **context-scout 2026-08-03**: re-verified context_scope, no change needed (5 entries).
- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (5 entries), still accurate.

**na-eligibility-audit 2026-08-06**: KEEP-NA, valid — mixed operator-gated items, SUPERSEDED banners, credential-gated
work

- **context-scout 2026-08-07**: refreshed context_scope (5 -> 6 entries) — added
  `/plans/archive/issues/cassette_drift_check_calls_deleted_script_and_swallows_it_2026_07_17.md`, the SSOT for the
  cassette-drift-check operator-decision item that was substantively corrected 2026-08-06 (18 real open drift issues
  found, not false positives — a live unresolved P0). Other 5 entries re-verified and still resolve.
  **na-eligibility-audit 2026-08-07** (tranche `ci`, autonomous, `agt-cbbd1f`): KEEP-NA, stale citations fixed — all 13
  open items re-verified genuinely operator-/design-gated (7 valid) or already tracked in an active
  `assigned_vm: planning` doc (6, cited but the citations wrongly said "status: draft, not yet dispatched" for the
  `ci_satellite_ao_dispatch_batch4_2026_07_31.md`/`batch5_2026_08_02.md` items — both are `status: active` and have been
  since creation). Corrected the wording at all 5 affected citation points (5 items; the batch1 citation was already
  accurate) so a future reader doesn't wrongly think these need re-extraction. No `assigned_vm` change — flipping this
  doc would create a live duplicate-dispatch path against batch4/batch5, which already own this work.

**round5-ci-question-resolution 2026-08-08**: closed 1 stale item — the `quickmerge.sh --agent` sentinel-race todo (head
of "Open todos forked from the parent plan") and its matching "Operator-owned" table row 9 were both flipped to
resolved. This was raised as a round-5 operator-question candidate ("should quickmerge's own sentinel-race be fixed now,
and how?"); investigation found the SSOT issue doc
(`plans/archive/issues/quickmerge_agent_sentinel_race_vs_own_rebase_2026_07_16.md`) already carries `status: resolved` /
`resolved_by: unified-trading-pm@e264b3c9` (2026-07-22), and the doc's own noted residual (STAGE 5 losing to a peer
push) was independently fixed later at `unified-trading-pm@f93a618e6c` (2026-07-31) — both SHAs verified ancestors of
`origin/live-defi-rollout`. No new decision made; this doc was simply never caught up to the SSOT doc's own resolution
across ~5 prior na-eligibility-audit passes that classified it "KEEP-NA valid" without re-checking the SSOT's
frontmatter. No `assigned_vm` change (doc has other genuinely open operator-gated items). **na-eligibility-audit
2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid — 7th+ consecutive pass, unchanged. Re-read all 10 open items
against today's 9 operator-Q&A precedents (IAM self-service, D16 carve, S5.1 tiering, context_scope default,
escalation-N days, reversibility-qualified deletes, Option-B retirement, AWS lower-stakes, sibling-precedent
self-service) — none apply. STEP 2d stays blocked on the digest-drift-sweep dormant-cascade investigation (itself
open-ended, unchanged); the bare-host bootstrap leg stays structurally blocked (needs a real VM, not a container); the 4
VERIFY billing/utilization items stay KEEP-NA-STALE (already tracked in
`ci_satellite_ao_dispatch_batch4_2026_07_31.md`/`batch5_2026_08_02.md`, both active); the slot-concurrency item is
cross-tranche (`ao`, not `ci`) per batch6's own same-day finding, out of scope here; the org-migration REVIEW stays
explicitly not-recommended. No `assigned_vm` change.

- **2026-08-09 (slot-28, review→cicd craft) — 4-item billing sweep, all 4 gates now real, real numbers (live
  Enhanced-Billing pull, `github-billing-token`, July+August 2026, `netAmount` per-item, token shredded post-pull; not
  `/timing.total_ms`).** (1) Phase-5 two-week+ re-pull: fleet $35.51/day (Jul1-15 baseline) → $12.72/day (Aug1-8),
  -64.2%, run-rate ~$1065/mo→~$382/mo — **lands the
  ~~$300-400/mo target**; the 2026-07-23 +47% non-PM masking has
  reversed (non-PM now -68.5%, PM -59.4%). (2) Representative QG run (features-service, real `/jobs` pull): ~10 billed
  min/PR-run (content-sentinel 1 + QG-checks 3 + QG-tests 5 + rollup 1); identical-tree sentinel skip rate (real
  `content-sentinel HIT` vs `MISS` log-count, not the always-both-present source echo) — PM 1/20 (~5%), features-service
  0/20 (promote-PR flow always touches code, so 0% is expected there). (3) agent-orchestrator (first-flipped canary)
  `Actions Linux`: $13.87/day
  (Jul20-26) →
  $3.78/day (Aug1-8), -73%, no new billed SKU line added; residual is the
  still-hosted `quality-gates-v2` pytest job (explicitly out of scope, security ADR — self-hosted runners never carry
  `pull_request`). (4) Full fleet re-pull vs Jul23-26: $37.35/day
  → $12.72/day, -65.9% (non-PM -74.7%) — the number the
  original "~$1,000/mo→~~$300-400/mo" target was about, now
  moved. All 4 checkboxes above flipped; full evidence + methodology in `ci_satellite_ao_dispatch_batch4_2026_07_31.md`
  todo 9's own Progress Log.

**`ci_satellite_ao_dispatch_batch5_2026_08_02.md` todo 2, 2026-08-09 (slot 11) — both remaining items closed.** (1)
BigQuery `resource_samples` utilization: measured avg_cpu_pct=50.6%, within the 50-70% band — full detail on the flipped
checkbox at ~line 685. (2) Test-impact design scoping: MOOT, already `[x]` at ~line 861 (extracted 2026-08-03, now fully
shipped as `test_impact_fleet_wide_measurement_and_rollout_2026_08_03.md`) — no fresh design needed.

**round-9 sweep, 2026-08-09**: KEEP-NA, valid, unchanged from round7 — no round-9 new-facts apply.
**na-eligibility-audit 2026-08-10** (ci tranche, autonomous, dispatch agt-74eff9) [body-hash:058d1b97f5f905f2]: KEEP-NA,
valid — Full read (1001 lines, both pages) + grep confirm 4 open todos, matching phase0=4. (1) line 106 STEP 2d
assert-not-decorative: doc's own D3 table row states 'digest-drift-sweep still unfixed and STEP 2d is still held for it
(its design depends on this remaining undecided item)' -- dependency-blocked on the still-open
/plans/active/issues/digest_drift_sweep_silent_noop_github_token_scope_2026_07_16.md investigation. (2) line 188
bare-host bootstrap PROVE: container leg done, IMDS/EC2-role + GCP ADC (doc flags this leg 'interactive') + systemd +
real GH runner registration 'structurally cannot' run in a container -- tied to 'the upcoming planning-VM deploy,' a
genuine host rebuild.
