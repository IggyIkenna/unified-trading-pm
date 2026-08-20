---
doc_type: plan
title:
  AO config env-var consolidation — split OrchestratorConfig into an env-reading operator surface + an env-free nested
  TuningDefaults, so it is unambiguous which settings the .env/.systemd can touch
summary: |
  2026-07-18 operator-session refactor of agent-orchestrator server/config.py. Today ONE OrchestratorConfig holds
  143 aliased ORCHESTRATOR_* fields, each with a default AND an env alias — but a full audit (local .env.local, the
  live planning-VM .env.local + systemd unit pulled via read-only SSM, bootstrap_vm.sh, every repo script, and all 11
  config-touching test files) shows only ~46 are ever set on any host; ~81 run on pure code defaults as
  incident-tuning escape hatches, and 20 of those are exercised ONLY by test monkeypatch.setenv. Operator decision
  (2026-07-18): make the split explicit — an env-reading class for the operator surface, and an env-FREE nested
  TuningDefaults(BaseModel) for the code-default knobs, merged into the one get_config() singleton. Verified
  empirically: a nested BaseModel field on a BaseSettings is NOT env-populated by any spelling (bare / __-delimited /
  ORCHESTRATOR_-prefixed) yet still bounds-validates. Also cleans the retired REGEN_REQUIRE_VM_MATCH still live on the
  planning VM (bootstrap already purged REGEN_DB_PATH 2026-07-17; now purges REQUIRE_VM_MATCH too, retired 2026-06-25)
  and folds in the AF-6 ENV_VARS.md residual (retired tab/<vm_id>/<slot> + "Fleet VM (epic worker)" framing). LOCAL
  track —
  operator-driven, executed interactively, never dispatched.
status: complete
nature: process
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [agent-orchestrator, config, env-vars, pydantic-settings, refactor, consolidation, tuning-defaults]
related:
  [
    /plans/archive/2026_08/ao_open_issues_consolidated_close_out_2026_07_17.md,
    /codex/06-coding-standards/config-reloader-pattern.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    ../epics/orchestrator_master.md,
  ]
created: 2026-07-18
last_updated: 2026-07-20
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 2
assigned_role: backend_engineer
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  - "operator 2026-07-18 — 'check the env-vars we use in AO … create two classes in config.py, one for the defaults set
    in the file directly and one that reads the env, so it's totally clear which are read from .env … a final settings
    _config_singleton that merges both'"
  - "operator 2026-07-18 (AskUserQuestion) — split BY ROLE (operator vs tuning); STRIP env alias from every knob not set
    on any host; FULL strip + rewire the test-coupled ones; track as a NEW local plan"
  - "Ground-truth audit this session: local .env.local; live planning-VM .env.local + orchestrator.service env via
    read-only SSM on i-0c9b283b31d6b5ca7; bootstrap_vm.sh; repo-wide assignment grep; 11 config-touching test files"
---

# AO config env-var consolidation

> **🟢 COMPLETE 2026-07-20 — ARCHIVED.** All 12 code/doc todos landed and were independently re-verified 2026-07-20:
> shas `5ad97b9`, `2d6d60b`, `c03ccce` exist and are ancestors of `origin/live-defi-rollout`; `TuningDefaults` carries
> exactly the 81 claimed fields with zero `validation_alias`; `basedpyright server/` is clean (0/0/0); the `set_tuning`
> fixture and bounds-assert patterns exist; zero `os.getenv()` anywhere in `server/` or `scripts/`. The two remaining
> items are **operator-gated prod `.env.local` actions**, not code, and are now owned by
> `ao_open_issues_consolidated_close_out_2026_07_17.md` § Phase 8.
>
> **Trap worth carrying**: the `bootstrap_vm.sh` `_remove_env` purges are GENERATOR-INERT on an already-bootstrapped
> host. `ao-self-pull.sh` only does `git merge --ff-only` + `systemctl restart` — it never re-runs an installer, so
> those purges do nothing live until `bootstrap_vm.sh` is re-run there.

> **Human plan — operator session executes it interactively** (`assigned_vm: NA`, never ingested). Code ships via
> `quickmerge.sh --agent --files`; each shippable unit flips its todo here in the SAME turn. A phase that touches
> `server/config.py` or its consumers commits only from a `quality-gates.sh`-green tree.

## Why

`server/config.py` = one `OrchestratorConfig(UnifiedCloudConfig)` with **143 aliased fields**. You cannot tell from the
class which settings an operator actually populates versus which are code-default escape hatches — the operator surface
and the tuning surface are visually identical, and the sprawl hides real drift (an inert retired var
`REGEN_REQUIRE_VM_MATCH=true` still live on the planning VM that no re-bootstrap cleared; several VM vars just
re-stating the code default).

**Audit result (this session):**

| Bucket                                                                                                                | Count | Meaning                 |
| --------------------------------------------------------------------------------------------------------------------- | ----- | ----------------------- |
| Operator-set (any host: VM `.env.local` / systemd / bootstrap / laptop / repo script)                                 | ~46   | genuinely `.env`-driven |
| Operator-by-nature (URL / bucket / secret-name / path / algorithm — not currently set but a NEW host must be able to) | 17    | keep env-capable        |
| Tuning knobs run on pure code default                                                                                 | 81    | → env-FREE              |
| …of those, exercised ONLY by test `monkeypatch.setenv`                                                                | 20    | need test rewiring      |

## Target design (empirically verified 2026-07-18)

```python
class TuningDefaults(BaseModel):          # pure — NEVER reads env. Bounded/validated.
    watchdog_interval_seconds: int = Field(default=60, gt=0)
    ...   # the 81 code-default knobs, grouped by subsystem

class OrchestratorConfig(UnifiedCloudConfig):   # BaseSettings — THE .env surface (~63 fields)
    model_config = SettingsConfigDict(env_file=None, ...)   # keep: reads os.environ, NOT a .env file
    vm_id: str = Field(default="", validation_alias=AliasChoices("ORCHESTRATOR_VM_ID"))
    ...   # identity / mode / paths / urls / auth-config / secret-names+URIs / buckets
          # + the knobs actually set on a host (FLEET_WORKER_CAP, REVIEW_SLOTS, PLAN_REGEN_INTERVAL…)
    tuning: TuningDefaults = TuningDefaults()    # ← the merge; get_config() exposes both
```

- `get_config().vm_id` (operator, env) stays; a moved knob becomes `get_config().tuning.watchdog_interval_seconds`.
- **Verified**: a nested `BaseModel` field resists env by every spelling (`WATCHDOG_INTERVAL_SECONDS`,
  `TUNING__WATCHDOG_INTERVAL_SECONDS`, `ORCHESTRATOR_WATCHDOG_INTERVAL_SECONDS` all ignored → 60) while `Field(gt=0)`
  still raises on 0. Env-freedom is real, not cosmetic.
- **Keep `env_file=None`** (config.py:332). "Reads the env" = reads `os.environ` that systemd/`dev.sh` populate from
  `.env.local` via `EnvironmentFile`. Having pydantic open `.env` itself would re-introduce the documented
  test-isolation bug (a stray repo-root `.env` overriding a monkeypatched default). This is a split of WHICH FIELDS, not
  of the reading mechanism.

## Codex SSOTs (read + reconcile after Phase 4)

- `/codex/06-coding-standards/config-reloader-pattern.md` — typed-config / reloader contract.
- `agent-orchestrator/docs/ENV_VARS.md` — operator reference; rewritten in Phase 4 to the two-class shape (also clears
  AF-6: retired `tab/<vm_id>/<slot>` + "Fleet VM (epic worker)" framing).

---

## Phase 0 — dead-var cleanup (zero code risk; independently valuable)

- [x] [SCRIPT] P1. ✅ **Purge retired `ORCHESTRATOR_REGEN_REQUIRE_VM_MATCH` on re-bootstrap** —
      agent-orchestrator@5ad97b9. CORRECTION to the original framing: on READING `bootstrap_vm.sh` (not just grepping),
      it already `_remove_env`s `REGEN_DB_PATH` (line 722, since 2026-07-17) and `REQUIRE_VM_MATCH` appeared only in
      COMMENTS — so bootstrap did not "write both." The real gap: no matching purge for `REQUIRE_VM_MATCH`, so a
      re-bootstrap never cleared the live VM's inert `REGEN_REQUIRE_VM_MATCH=true` (retired 2026-06-25, D8). Fix: added
      `_remove_env     ORCHESTRATOR_REGEN_REQUIRE_VM_MATCH` beside the DB_PATH purge + dropped two stale comments
      (retired `tab/<VM_ID>/<slot>` framing; the `REQUIRE_VM_MATCH=true` EXTRA_ENV example). `bash -n` clean.
- ➡️ **MIGRATED 2026-07-20 → `ao_open_issues_consolidated_close_out_2026_07_17.md` § Phase 8. NOT done; not owned
  here.** Original item, for the record: [SCRIPT] P2. **Remove the dead `ORCHESTRATOR_REGEN_REQUIRE_VM_MATCH=true` from
  the live planning-VM `.env.local`** — live on the VM (confirmed via SSM) but the field no longer exists (silently
  ignored via config `extra="ignore"`). Two ways: a re-bootstrap now purges it (agent-orchestrator@5ad97b9), OR an SSM
  `sed -i` backup-first + clean restart. Operator-gated: touches prod env. **BLOCKED-OPERATOR-DECISION** (no rush —
  inert no-op today).
- [x] [DOC] P2. ✅ **Recorded the redundant-to-default VM vars** — agent-orchestrator@c03ccce. ENV_VARS.md now has a
      "Redundant on the live VM (safe to remove)" section for `WATCHDOG_DAILY_CAP=50`, `SNAPSHOT_INTERVAL_SECONDS=1800`,
      `WORKER_HOST=local`, `REGEN_PRUNE_STALE=true` (documented, not silently changed on prod).

## Phase 1 — split the class (config.py only)

- [x] [BACKEND] P1. ✅ **Added `TuningDefaults(BaseModel)` + moved the 81 tuning fields** — agent-orchestrator@2d6d60b.
      Same defaults/bounds/`BoolEnvTrue/False` coercers/docstrings, `validation_alias` dropped, grouped by subsystem.
      DEVIATION: the two `_blank_*_loop` blank-coercer validators were NOT kept — env-free makes a blank string
      unreachable, so they were dead code; removed them (a bare `default=` handles unset). Every field default + bound
      verified to round-trip vs the pre-split snapshot (0 mismatches).
- [x] [BACKEND] P1. ✅ **Added `tuning: TuningDefaults = Field(default_factory=TuningDefaults)`** —
      agent-orchestrator@2d6d60b. 81 fields deleted from OrchestratorConfig; the 63 operator fields keep their env
      aliases.
- [x] [BACKEND] P1. ✅ **Updated in-file resolvers** — agent-orchestrator@2d6d60b. `main_loop_seconds()` /
      `review_loop_seconds()` now read `get_config().tuning.*`; `review_slot_ids()` / `fleet_worker_cap()` stay
      operator. Empirically verified nested `tuning` is env-FREE (bare / `__` / `ORCHESTRATOR_`-prefixed all ignored)
      yet bounds-validates.

## Phase 2 — rewire consumer call sites (~60 reads across server/)

- [x] [BACKEND] P1. ✅ **Rewrote every `get_config().<tuning>` → `get_config().tuning.<tuning>`** —
      agent-orchestrator@2d6d60b. 85 reads across 26 server modules (3 receiver styles: `get_config().x`,
      `config.get_config().x`, `cfg`/`_CFG` bindings), scripted + receiver-aware; grep-verified 0 unprefixed moved-field
      reads remain.
- [x] [BACKEND] P1. ✅ **basedpyright + import-smoke** — agent-orchestrator@2d6d60b. All server modules import (0
      failures); `basedpyright server/` clean; `get_config().tuning.watchdog_interval_seconds` resolves.

## Phase 3 — rewire the 20 test-coupled knobs (11 test files)

- [x] [TEST] P1. ✅ **Rewired the 20 test-coupled knobs off `setenv`** — agent-orchestrator@2d6d60b. Added a
      `set_tuning` conftest fixture (sets on the live `get_config().tuning`); behavior tests use it, bounds/env-parse
      tests became `TuningDefaults(<field>=<bad>)` construction asserts (the moot "blank→default via env" cases
      deleted). 12 files touched (test_config, test_autospawn, test_tmux_nudge_retry, test_agent_silence, + 8 more).
- [x] [TEST] P1. ✅ **Full suite green** — agent-orchestrator@2d6d60b. `bash scripts/quality-gates.sh` PASSED: 1366
      passed / 1 skipped, dashboard tsc + vitest (94) green, ruff + basedpyright clean.

## Phase 4 — docs

- [x] [DOC] P1. ✅ **Rewrote `docs/ENV_VARS.md` to the two-class shape** — agent-orchestrator@c03ccce. Documents the
      operator surface (env-read) vs `config.tuning` (env-free, edit+redeploy), replacing the "~80 remaining knobs /
      grep config.py" note. Cleared AF-6: dropped `tab/<vm_id>/<slot>`, "Fleet VM (epic worker)", and the
      `ORCHESTRATOR_OPERATOR = tab branch operator` framing for the single-VM `planning` reality.
- [x] [DOC] P2. ✅ **Codex reconcile — nothing to change** — checked
      `/codex/06-coding-standards/config-reloader-pattern.md`: 0 grep hits for `OrchestratorConfig` / "every knob" /
      `tuning`; its single "orchestrator" mention is about crash telemetry, not config structure. The nested split
      invalidates no claim there.

## Phase 5 — ship + verify

- [x] [BACKEND] P1. ✅ **Shipped each phase via `quickmerge.sh --agent --files`** from a QG-green tree, flipping todos
      in the same turn: Phase 0 ao@5ad97b9, Phases 1-3 ao@2d6d60b, Phase 4 ao@c03ccce. All landed on LDR, ahead=0.
- ➡️ **MIGRATED 2026-07-20 → `ao_open_issues_consolidated_close_out_2026_07_17.md` § Phase 8. NOT done; not owned
  here.** Original item, for the record: [SCRIPT] P2. **(operator-gated) apply the Phase-0 P2 VM `.env.local` cleanup**
  once code is live + `ao-self-pull` has the new config; verify `curl localhost:8765/api/mode` + a clean restart via
  SSM.

---

## Appendix A — the 81 tuning fields (→ env-free `TuningDefaults`; ‡ = test-coupled, needs Phase 3 rewire)

agent_message_max_redeliveries, autospawn_cooldown_seconds‡, autospawn_five_hour_pct_ceiling‡,
autospawn_interval_seconds‡, autospawn_weekly_pct_ceiling‡, blocked_reconcile_interval_seconds, boot_grace_seconds,
boot_read_confirm, ci_reconcile_cooldown_seconds, ci_reconcile_max_per_tick, context_burn_hours‡, context_burn_kill,
context_burn_min_compactions, context_burn_min_pct‡, context_compact_force_after_seconds, context_compact_guidance_pct,
context_lifecycle_enabled, context_recycle_compactions, context_recycle_hours, creds_env_poll_interval_seconds,
creds_prefix, daily_summary_enabled‡, daily_summary_interval_seconds, dispatch_ack_timeout_seconds, done_require_clean‡,
done_require_origin, done_require_plan_flip‡, failover_heartbeat_threshold_seconds, failover_interval_seconds,
ff_cron_stale_secs, gh_rate_clear_margin, gh_rate_interval_seconds, head_backward_canary_interval_seconds,
high_affinity_spill_after_seconds‡, kick_escalation_threshold, liveness_interval_seconds, main_agent_cooldown_seconds,
main_agent_interval_seconds, main_agent_stale_grace_hours, main_loop_seconds_value‡, mcp_backtest_timeout_secs,
nudge_attempts‡, nudge_retry_backoff_s‡, one_shot_stale_grace_minutes, orphaned_task_reclaim_grace_seconds,
paste_settle_s‡, pm_repo_path, prereq_block_release_seconds‡, rate_limit_min_cooldown_s, repo_health_interval_seconds,
reporter_stale_secs, respawn_debounce_minutes, resume_compact_first_context_pct, resume_fresh_context_pct,
resume_max_attempts, review_heartbeat_timeout_override‡, review_loop_seconds_value‡, run_volume_interval_seconds,
run_volume_top_n, slot_message_max_redeliveries‡, slot_skip_ttl_hours, spawn_heartbeat_timeout_seconds, spawn_timeout_s,
stuck_threshold_minutes, tmux_prune_interval_seconds, usage_tui_reconcile_pct, vm_stale_threshold_secs,
watchdog_cooldown_seconds, watchdog_flap_slot_threshold, watchdog_flap_window_seconds, watchdog_heartbeat_resume_max,
watchdog_heartbeat_timeout‡, watchdog_idle_session_ticks, watchdog_interval_seconds‡, watchdog_nudge_after_ticks,
watchdog_nudge_daily_cap, watchdog_nudge_grace_seconds, watchdog_nudge_text, watchdog_session_gone_grace_seconds,
watchdog_stuck_ticks, watchdog_zombie_grace_seconds

> **Judgment call to review:** `pm_repo_path` (a deployment path) is listed as tuning because no host sets it; if a
> non-standard PM-clone layout should be env-settable, promote it back to the operator class. Flag any other Appendix-A
> field you would rather keep env-capable BEFORE Phase 1.

## Appendix B — the 63 operator fields (stay env-reading; env aliases intact)

Identity/topology: vm_id, vm_role, operator, host_label, standalone_override, use_private_urls, worker_host,
vm_registry_path, service_name. Mode/state paths: mode_raw, db_path_override, state_json_override, backlog_override,
accounts_override, backends_override, users_json_path, claude_accounts_dir_override. URLs: public_url, dashboard_url,
server_url_value, cors_origins, mcp_data_status_base_url. Auth-config + secret NAMES/URIs: allow_anonymous,
jwt_algorithm, internal_alg, jwt_secret_gcs, internal_secret_gcs, google_cloud_project, telegram_bot_token_secret,
telegram_chat_id, gh_app_ci_poller_app_id/installation_id/ private_key_file. Buckets: orchestrator_gcs_bucket,
orchestrator_s3_bucket, creds_s3_bucket, creds_gcs_bucket. Deploy toggles + host-set knobs: autospawn_enabled,
worker_watchdog_enabled, escalation_watchdog_enabled, usage_tui_reconcile_enabled, failover_enabled,
watchdog_nudge_enabled, notify_work_picked_up, allow_port_conflict, fleet_worker_cap_override, review_slots_raw,
plan_regen_interval_seconds, snapshot_interval_seconds, sqlite_backup_every_n_ticks, ci_reconcile_interval_seconds,
usage_poll_interval_minutes, regen_prune_stale, watchdog_daily_cap, autospawn_min_free_disk_pct, worker_memory_max,
worker_memory_swap_max, workspace_root, slot_branch, agents_dir_override, claude_config_base, gh_owner,
run_volume_repos.

> **Also unchanged (not config fields):** the raw-secret env reads at the security boundary — `ORCHESTRATOR_JWT_SECRET`,
> `ORCHESTRATOR_INTERNAL_SECRET`, `TELEGRAM_BOT_TOKEN`, `AGENT_ORCHESTRATOR_SLACK_WEBHOOK`,
> `GH_APP_CI_POLLER_PRIVATE_KEY`, and the ES256 `ORCHESTRATOR_INTERNAL_{PUBLIC,PRIVATE}_KEY_GCS` (via
> `auth.py::_load_internal_*_key`). These stay direct `os.environ` reads by design and are NOT in either class.

---

## Progress Log

**2026-07-18 (authoring)** — plan created from the operator's env-var-consolidation request. Design chosen + verified
(nested `TuningDefaults(BaseModel)` is env-free by empirical probe; `env_file=None` retained). Full ground-truth audit
completed: local `.env.local`, live planning-VM `.env.local` + `orchestrator.service` env (read-only SSM on
i-0c9b283b31d6b5ca7), `bootstrap_vm.sh`, repo-wide `ORCHESTRATOR_*=` grep, and 11 config-touching test files.
Classification: 63 operator / 81 tuning (20 test-coupled). Two DEAD vars found still written by bootstrap + live VM
(`REGEN_DB_PATH`, `REGEN_REQUIRE_VM_MATCH`). Folds in AF-6 (ENV_VARS.md residual) from
`ao_open_issues_consolidated_close_out_2026_07_17.md`. No code shipped yet.

**2026-07-18 (execution — Phases 0-5 code complete)** — all code + docs shipped, every phase QG-green:

- **Phase 0** ao@5ad97b9 — bootstrap now purges the retired `REGEN_REQUIRE_VM_MATCH` on re-bootstrap (correction: it
  already purged `REGEN_DB_PATH`; the gap was only REQUIRE_VM_MATCH) + stale-comment cleanup.
- **Phases 1-3** ao@2d6d60b — `TuningDefaults` env-free split (81 knobs moved, verified round-trip + env-free), 85
  call-site rewires across 26 modules, 20 test-coupled knobs rewired onto a `set_tuning` conftest fixture + direct
  `TuningDefaults` bounds asserts. QG: **1366 passed / 1 skipped**, dashboard green, ruff + basedpyright clean.
  Deviation: dropped the two dead `_blank_*_loop` blank-coercers (env-free makes them unreachable).
- **Phase 4** ao@c03ccce — ENV_VARS.md rewritten to the two-class shape, AF-6 residual cleared; codex config-reloader
  doc checked (nothing to reconcile).

Measurement/design notes for a fresh session: (1) pydantic-settings makes a bare `BaseModel` field inherited into a
`BaseSettings` read env by BARE name — that's WHY tuning had to be a NESTED sub-model, not a mixin (empirically shown).
(2) QG basedpyright EXCLUDES `tests/` (`include=["server"]`) and ruff `tests/*` ignores F401/F841/F811 — so test-file
IDE diagnostics are non-gating; only runtime test-pass + `server/` lint/types gate. (3) tuning knobs are read at
call-time, so `set_tuning` on the live singleton survives until the next `reset_config()`.

**2026-07-18 (follow-on — config-default reconciliation, ao@955f5f5)** — operator reviewed the operator-surface fields
and adjusted defaults to match host reality; three fail-safe/security calls made:

- `worker_watchdog_enabled` + `autospawn_enabled` — kept default **OFF** (fail-safe). A self-healing loop that acts on
  the live fleet must never run on a fresh/demo/test backend by accident; the VM opts in explicitly. (A brief flip to
  default-ON was reverted.)
- `plan_regen_interval_seconds` default **1800 → 600**; the VM keeps its explicit `300` (5-min) override — a legitimate
  per-host choice, not drift.
- `allow_anonymous` — kept default **True** (dev-open). Flipping to False risks locking a fresh local/demo backend out
  of its own dashboard; the only exposed host (the VM) is already explicitly `false`.
- `resume_fresh_context_pct` 95 → 90 (tuning). No prod-VM env change needed — every host that wants a non-default
  already sets it explicitly.

## Deferred work after 2026-07-18

| Item                                                                                                                                       | State / why deferred                                                                                                                                                                                | Blocked on            |
| ------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------- |
| Phase 0 P2 / Phase 5 P2 — remove dead `REGEN_REQUIRE_VM_MATCH` + trim the redundant-to-default vars from the LIVE planning-VM `.env.local` | Operator-owned — touches prod env. Inert no-op today (config `extra="ignore"` ignores it), so no urgency. A re-bootstrap now clears REQUIRE_VM_MATCH; or SSM `sed -i` backup-first + clean restart. | **operator decision** |

Recommended NEXT: nothing here is blocking — the refactor is functionally complete and live-safe. The only open items
are the operator-gated prod-env tidy-ups above; do them opportunistically on the next VM re-bootstrap.
