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
status: active
nature: process
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [agent-orchestrator, config, env-vars, pydantic-settings, refactor, consolidation, tuning-defaults]
related:
  [
    ao_open_issues_consolidated_close_out_2026_07_17.md,
    ../codex/06-coding-standards/config-reloader-pattern.md,
    ../codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    ../epics/orchestrator_master.md,
  ]
created: 2026-07-18
last_updated: 2026-07-18
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

- `codex/06-coding-standards/config-reloader-pattern.md` — typed-config / reloader contract.
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
- [ ] [SCRIPT] P2. **Remove the dead `ORCHESTRATOR_REGEN_REQUIRE_VM_MATCH=true` from the live planning-VM `.env.local`**
      — live on the VM (confirmed via SSM) but the field no longer exists (silently ignored via config
      `extra="ignore"`). Two ways: a re-bootstrap now purges it (agent-orchestrator@5ad97b9), OR an SSM `sed -i`
      backup-first + clean restart. Operator-gated: touches prod env. **BLOCKED-OPERATOR-DECISION** (no rush — inert
      no-op today).
- [ ] [DOC] P2. **Trim redundant-to-default VM vars** — note (do not necessarily delete) `WATCHDOG_DAILY_CAP=50`,
      `SNAPSHOT_INTERVAL_SECONDS=1800`, `WORKER_HOST=local`, `REGEN_PRUNE_STALE=true` on the VM just re-state code
      defaults. Record in ENV_VARS.md "redundant, safe to remove" rather than silently changing prod.

## Phase 1 — split the class (config.py only)

- [ ] [BACKEND] P1. **Add `TuningDefaults(BaseModel)` + move the 81 tuning fields** (see Appendix A) verbatim — same
      defaults, same `gt/ge/le` bounds, same `BoolEnvTrue/False` coercers, same docstrings — but DROP each
      `validation_alias`. Group by subsystem with section headers. Keep the 4 `field_validator`s that belong to moved
      fields (`_blank_main_loop`, `_blank_review_loop`) on TuningDefaults.
- [ ] [BACKEND] P1. **Add `tuning: TuningDefaults = TuningDefaults()` to OrchestratorConfig** and delete the 81 moved
      fields from it. Leave the 63 operator fields (Appendix B) exactly as they are (env aliases intact).
- [ ] [BACKEND] P1. **Update the in-file resolver fns** that read moved knobs (`main_loop_seconds()`,
      `review_loop_seconds()`, `review_slot_ids()` stays operator, etc.) to read `get_config().tuning.<field>`; keep the
      module-level `DEFAULT_*` constants as the single default source referenced by TuningDefaults.

## Phase 2 — rewire consumer call sites (~60 reads across server/)

- [ ] [BACKEND] P1. **Rewrite every `get_config().<tuning_field>` → `get_config().tuning.<tuning_field>`** across
      `server/` (Appendix A is the exact field set; ~60 single-line edits, most one-per-module). Grep-verify zero
      `get_config().<moved>` remain outside `tuning.`.
- [ ] [BACKEND] P1. **`basedpyright` + import-smoke** —
      `python -c "from server.config import get_config; c=get_config(); c.tuning.watchdog_interval_seconds"` resolves;
      no attribute errors.

## Phase 3 — rewire the 20 test-coupled knobs (11 test files)

- [ ] [TEST] P1. **Switch `monkeypatch.setenv("ORCHESTRATOR_<moved>", …)` → direct injection** for the 20 test-coupled
      fields (Appendix A ‡). Pattern: `object.__setattr__(get_config().tuning, "<field>", <val>)` after
      `reset_config()`, or build a `TuningDefaults(<field>=…)` and patch it on. Delete env-PARSING tests that only
      asserted "blank→default / bad→raise via env" (moot once env-free); replace coverage with a
      `TuningDefaults(<field>=<bad>)` bounds test where the behavior still matters.
- [ ] [TEST] P1. **Full suite green** — `bash scripts/quality-gates.sh` (agent-orchestrator) passes; no skipped/xfailed
      config tests.

## Phase 4 — docs

- [ ] [DOC] P1. **Rewrite `docs/ENV_VARS.md` to the two-class shape** — the operator surface = the env-reading class
      (what you populate per host); a short "everything else is `config.tuning`, edit-and-redeploy, not env" note
      replacing the "~80 remaining knobs / grep config.py" section. Clears AF-6: remove `tab/<vm_id>/<slot>`, "Fleet VM
      (epic worker)", `ORCHESTRATOR_OPERATOR = tab branch operator" framing → single-VM `planning` reality.
- [ ] [DOC] P2. **Codex reconcile** — check `codex/06-coding-standards/config-reloader-pattern.md` for any "every knob
      is a field on OrchestratorConfig" claim that the nested split invalidates; update to name the two classes.

## Phase 5 — ship + verify

- [ ] [BACKEND] P1. **Ship each phase via `quickmerge.sh --agent --files`** from a QG-green tree; flip the phase's todos
      here in the same turn with `<repo>@<sha>` evidence.
- [ ] [SCRIPT] P2. **(operator-gated) apply the Phase-0 P2 VM `.env.local` cleanup** once code is live + `ao-self-pull`
      has the new config; verify `curl localhost:8765/api/mode` + a clean restart via SSM.

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
