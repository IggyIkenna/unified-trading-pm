---
doc_type: issue
title: >-
  AO boot telemetry self-reports `model: "sonnet"` for DeepSeek-provider accounts — the fleet dashboard and state.db
  cannot tell which sessions actually ran on DeepSeek vs Claude
summary: >-
  Confirmed live (2026-08-06) via a read-only `state.db` query over SSM: `slots` and `activity_log.slot_boot` rows for
  workers booted under `account_id in {deepseek-v4-pro, deepseek-v4-flash}` (both registered `provider: "deepseek"` in
  `data/config/accounts.json`) still show `model: "sonnet"` — the same value a genuine Anthropic-account boot reports. A
  known, dated bug (`ao_deepseek_model_flag_misalignment_2026_08_05`, see `accounts.py::model_flag_for_provider`)
  already found that AO was passing a meaningless `--model` CLI flag to non-Anthropic spawns and fixed that — but that
  fix only suppresses the flag on spawn, it does not correct what the worker's own `/boot` call reports as `model` in
  telemetry, and the mislabeling persists a day later on real, currently-running sessions. Concretely: the
  `sports_fast_t1_recon_oom_live_capture_outage-003` task (slot 12, "backfill LAUNCHED + CONFIRMED WRITING; gate
  cleared" — see the sibling issue doc, whose "gate cleared" claim was independently found to be premature) and the
  currently-in-flight `context_scope_marker_claims_exceed_frontmatter_count-002` task (slot 6) both booted under
  `account_id: deepseek-v4-flash` while their `slot_boot` events say `model: sonnet`. Neither the FleetView dashboard
  nor a plain `state.db` query lets an operator or a reviewing agent tell, at a glance, which completed work was
  actually produced by a Claude session vs a much cheaper/weaker DeepSeek Flash session — undermining any policy
  (explicit or implicit) that scales scrutiny by model tier.
status: open
# Sanctioned bridge (archive-exempt on the flip-only commit, dropped on the archival git mv) —
# see /codex/12-agent-workflow/plan-completion-and-archival-discipline.md § archive_exempt.
archive_exempt: true
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, telemetry, model-tier, deepseek, observability, false-progress-adjacent]
related:
  [
    /plans/active/issues/sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md,
    /plans/active/issues/context_scope_marker_claims_exceed_frontmatter_count_2026_08_06.md,
  ]
created: 2026-08-06
author: interactive-session (tab 1)
priority: P2
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: infra
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source:
  [
    "discovered 2026-08-06 during an interactive audit of two other issues' worker-attribution history — read-only
    state.db query via query-ao-state-db-readonly.sh against slots + activity_log + accounts.json",
  ]
context_scope:
  [
    agent-orchestrator/server/accounts.py,
    agent-orchestrator/server/routes/slots_worker.py,
    agent-orchestrator/scripts/orchestrator/context_history_report.py,
    /codex/06-coding-standards/model-tier-selection.md,
  ]
---

# AO boot telemetry mislabels DeepSeek-provider sessions as `model: "sonnet"`

## What I found

Querying the live orchestrator's `state.db` (read-only, via `query-ao-state-db-readonly.sh`) for `activity_log`
`slot_boot` events on slots 6 and 12 around 2026-08-06:

```
{"operator": "planning", "model": "sonnet", ..., "account_id": "deepseek-v4-flash"}   # slot 12, 00:19:51
{"operator": "planning", "model": "sonnet", ..., "account_id": "deepseek-v4-pro"}     # slot 12, 00:59:12
{"operator": "planning", "model": "sonnet", ..., "account_id": "deepseek-v4-pro"}     # slot 6, 03:00:45
{"operator": "planning", "model": "sonnet", ..., "account_id": "deepseek-v4-flash"}   # slot 6, 09:38:46
```

`data/config/accounts.json` confirms both `deepseek-v4-pro` and `deepseek-v4-flash` are real, registered accounts with
`"provider": "deepseek"` (vs. `sub-a-ikenna`/`sub-e-odum2default`, real Anthropic subscription seats with no `provider`
field, defaulting to `"anthropic"` per `accounts.py::provider_for_account_id`). So these are not a naming coincidence —
the sessions genuinely ran against DeepSeek's API — yet every one of them reports `model: "sonnet"` in the same
telemetry field a real Sonnet session uses.

`accounts.py::model_flag_for_provider` (with the `ao_deepseek_model_flag_misalignment_2026_08_05` fix cited inline)
already documents the adjacent, earlier-discovered half of this: "only the ONE fresh-spawn['s `--model`] flag ... was
actually running deepseek-v4-pro the whole time" — i.e. AO used to pass an Anthropic model flag to a DeepSeek spawn,
which the DeepSeek backend silently ignored. The fix suppresses that flag for non-`anthropic` providers. But
`slots_worker.py`'s `/boot` handler (`routes/slots_worker.py:294-341`) just persists whatever `req.model` the worker's
own boot call self-reports, with no cross-check against `provider_for_account_id(req.account_id)` — so the worker-side
boot script apparently still labels itself "sonnet" regardless of which account/provider it's actually running under,
and nothing on the server side catches the mismatch.

## Why it matters

- The FleetView dashboard (and anyone reading `state.db` directly, including a reviewing agent) has no reliable signal
  for "was this task's output produced by Claude Sonnet or DeepSeek Flash/Pro" — the one field that should answer that
  (`model`) is wrong for every DeepSeek-provider session sampled.
- This surfaced while auditing two OTHER issues in this workspace (`sports_fast_t1_recon_oom_live_capture_outage`'s
  prematurely-cleared backfill-coverage gate, and `context_scope_marker_claims_exceed_frontmatter_count`'s soft-false
  restoration claim) — both pieces of work in question ran under `deepseek-v4-flash`, not Sonnet. Whether DeepSeek
  Flash's involvement is causally related to those quality gaps is NOT established here (that would need a controlled
  comparison, out of scope for this issue) — but the fleet currently has no way to even ask that question, because the
  telemetry that would let someone correlate "which model produced this" is wrong at the source.

## Todos

- [x] ✅ [SCRIPT] P2. In `routes/slots_worker.py`'s `/boot` handler, cross-check `req.model` against
      `provider_for_account_id(req.account_id)` (`accounts.py`) — for a non-`anthropic` provider, either (a) overwrite
      the stored `model` with the account's real `variant` (e.g. `deepseek-v4-flash` → `model: "deepseek-flash"`), or
      (b) reject a self-reported `model` that doesn't match the account's provider with a 4xx, forcing the boot script
      to report accurately. Pick whichever keeps `slot_boot` telemetry queryable without a join back to `accounts.json`
      — a human/agent reading `activity_log` alone should be able to tell the real model. Done when: a unit test boots a
      `deepseek-v4-flash` account and asserts the persisted `SlotRow.model` / `slot_boot.details_json.model` is NOT
      `"sonnet"`. — agent-orchestrator@eb6a763: added `effective_model_for_telemetry()` (accounts.py), wired into
      `boot_slot()`'s upsert_slot + slot_boot activity-log call (slots_worker.py); 7 new unit tests in
      `tests/test_boot_deepseek_model_telemetry.py` cover deepseek-flash/pro/no-variant + anthropic-preserved +
      unknown-account regression; full quality-gates.sh green (2614 passed).
- [x] ✅ [DOC] P3. Once fixed, backfill-correct the FleetView dashboard's badge rendering (and any other consumer of
      `SlotRow.model`, e.g. `context_history_report.py`'s `--group-by model`) to show the real value — check whether any
      of them special-case the string `"sonnet"` in a way that would break once this field starts reporting DeepSeek
      variants. — agent-orchestrator (no code change): `ModelBadge` in `layout.tsx` already checks
      `provider === "deepseek"` and renders `deepseekVariant`, never the `model` string, for DeepSeek slots;
      `context_history_report.py` uses passthrough `ep.model or "unknown"` for `--group-by model`; `utils.ts`
      `modelBadgeClass`/`MODEL_RANK` operate on the role registry (`RoleModel`) not slot telemetry; zero
      `model === "sonnet"` conditional comparisons found in dashboard TS files. No breaking consumers — the eb6a763 fix
      is safe to ship without dashboard changes (slot-9, 2026-08-08).
- [x] ✅ [SCRIPT] P3. **PATTERN CONFIRMED (slot-13, 2026-08-10)** — the SAME self-report-without-cross-check pattern
      EXISTS for `effort`/`thinking`. `slots_worker.py:320-321` stores `effort=req.effort, thinking=req.thinking`
      directly from the worker's `/boot` self-report with no provider-aware cross-check; `slot_boot` activity event
      (lines 354-355) logs them identically. A companion gap in the spawn path: `--effort` and `--max-thinking-tokens`
      CLI flags are NOT provider-gated (`tmux_spawn.py:_append_model_flags` only gates `--effort` on Haiku, not on
      non-Anthropic providers) — unlike `--model`, which `model_flag_for_provider()` suppresses for non-Anthropic
      spawns. Impact: lower severity than the `model` mislabel (effort/thinking are reasoning knobs, not identity), but
      telemetry is equally misleading for non-Anthropic sessions and spawn flags are wasted/possibly erroneous.
      Follow-up fix tracked as new todo 4. — agent-orchestrator@(audit-only, no code change).

- [x] ✅ [SCRIPT] P3. **NEW (slot-13 audit, 2026-08-10).** Fix the effort/thinking cross-check gap found by todo 3's
      audit: either (a) add `effective_effort_for_telemetry()` / `effective_thinking_for_telemetry()` to `accounts.py`
      mirroring `effective_model_for_telemetry()`, storing a provider-aware value (e.g. `null` or the provider's own
      reasoning-tier label for non-Anthropic) in `SlotRow` + `slot_boot` activity events, AND/OR (b) provider-gate the
      `--effort` and `--max-thinking-tokens` CLI flags in `tmux_spawn.py:_append_model_flags()` the same way
      `model_flag_for_provider()` already suppresses `--model` — currently `--effort high` and
      `--max-thinking-tokens 31999` are passed to DeepSeek spawns where they are at best ignored and at worst could
      cause API errors. Done when: a unit test boots a `deepseek-v4-flash` account and asserts the persisted
      `SlotRow.effort`/`SlotRow.thinking` are provider-corrected (NOT raw Anthropic labels), and non-Anthropic spawns
      omit `--effort`/`--max-thinking-tokens` from the CLI flags. (repo: agent-orchestrator) — RECOVERY NOTE (main
      2026-08-10): this todo is already implemented as orphan commit `cf9eef3` (slot-11, `agent-orchestrator`, "fix(ao):
      provider-gate effort/thinking telemetry + spawn flags for non-Anthropic", 2026-08-10 08:56) — 1 ahead of origin
      and unshipped. Recover it (`git -C <tabs>/11/agent-orchestrator show cf9eef3`), verify against this done-when,
      ship via quickmerge — do NOT re-author it. — agent-orchestrator@70281b1: recovered orphan commit `cf9eef3`
      byte-faithful (cherry-pick onto LDR HEAD; change set identical — 13 files, 273+/8−; only delta = preserved HEAD's
      `running_checkout_sha` import in tmux_spawn.py); both done-when assertions covered by
      `test_deepseek_flash_boot_stores_none_effort_thinking_not_anthropic_labels` (SlotRow.effort/thinking → None, not
      `"high"`/`"on"`) + `test_non_anthropic_spawn_omits_effort_and_thinking_flags` (non-Anthropic spawns omit
      `--effort`/`--max-thinking-tokens`); full quality-gates.sh green (3156 passed). Companion test-isolation fix at
      `7a1016f` (patch `capture_pane` in the two `switch_main_*` resume tests — env-dependent flake on the shared host
      where the live `orch-agent-main` pane reads ~92% context and dropped the resume target; stacks on top of the
      already-landed `425a779` `_main_context_saturated_pct` patch). (slot-29, 2026-08-10).

## Progress Log

- **na-eligibility-audit 2026-08-06 (governance-sweep reclassification pass)**: RECLASSIFY,
  `assigned_vm: NA -> planning`. Freshly-filed doc, never previously assessed by any audit — purely a bounded
  engineering bug fix (cross- check `req.model` against `provider_for_account_id` in `slots_worker.py`'s `/boot`
  handler, stated unit-test done-when) plus two worker-determinable follow-on todos. No operator gate, no
  design/judgment call, no hard-rule veto. Conflict-check cleared (no overlapping claim in
  `parent_epic: orchestrator_master`).

- **context-scout 2026-08-07**: populated/refreshed context_scope (4 entries). Dropped
  `agent-orchestrator/data/config/accounts.json` — real on the live deployed server but gitignored, so it never resolves
  in a fresh repo checkout (only `data/config/accounts.mock.json` is committed); `server/accounts.py` already covers the
  same `AccountDef`/provider schema this doc's finding depends on. Added
  `agent-orchestrator/scripts/orchestrator/context_history_report.py`, the exact consumer the open `[DOC] P3` todo names
  (`--group-by model`).
- **Operator ruling 2026-08-07 (interactive session, via consolidated NA-blocker-digest audit)**: `asset_group` mistag
  RULED — Option B/C combined ("make it correct"). Retagged `[infrastructure]` → `[ao]` directly (finding 19,
  `ag_closeout_audit_infra_parked_2026_08_07.md`, 3rd confirmed instance of the same pattern). Sibling doc
  `ao_self_pull_wedged_by_main_inbox_untracked_file_2026_07_30.md` (finding 6) retagged in the same pass; the
  authoring-time default fix (Option C) tracked separately.
- **2026-08-08 (slot-9, infra, todo -002)**: Audited all consumers of `SlotRow.model` for hardcoded `"sonnet"`
  special-cases. Finding: NO breaking consumers. `ModelBadge` (`layout.tsx:3927-3928`) already checks
  `provider === "deepseek"` and renders `deepseekVariant` — the `model` string is not used for DeepSeek slots.
  `context_history_report.py` lines 328/332 use `ep.model or "unknown"` passthrough — will correctly group by
  `"deepseek-flash"` once eb6a763 lands. `utils.ts` `modelBadgeClass`/`MODEL_RANK` reference
  `RoleModel = "opus"|"sonnet"|"haiku"` which is the role-registry type (static per role config), not slot telemetry.
  Zero `model === "sonnet"` conditional comparisons in dashboard TS. No code changes needed; todo -002 closed.
- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (4 entries), still accurate.
- **slot-13 2026-08-10 (infra, todo -003, `ao_deepseek_provider_model_telemetry_mislabeled-003`)**: Audited whether the
  same self-report-without-cross-check pattern exists for `effort`/`thinking` as the already-fixed `model` (todo 1,
  `eb6a763` → `effective_model_for_telemetry()`). **Finding: PATTERN CONFIRMED for both fields, plus a companion gap in
  the spawn path.**

  **Telemetry gap** (`slots_worker.py:320-321`, `354-355`): `effort` and `thinking` are stored directly from
  `req.effort`/`req.thinking` in the `/boot` handler (both `upsert_slot` and `slot_boot` activity event) with no
  provider-aware cross-check — identical to the `model` mislabel before `effective_model_for_telemetry()`. A
  `deepseek-v4-flash` session shows `effort: "high"`, `thinking: "on"` in telemetry — Anthropic-specific labels with no
  defined meaning on DeepSeek.

  **Spawn-path gap** (`tmux_spawn.py:_append_model_flags:1426-1432`): `--effort` is only Haiku-gated
  (`model_supports_effort`), NOT provider-gated; `--max-thinking-tokens 31999` is only gated by the `thinking` boolean.
  Unlike `--model` (suppressed by `model_flag_for_provider()` for non-Anthropic), these Anthropic-specific reasoning
  flags are still passed to DeepSeek spawns — at best silently ignored, at worst causing API errors depending on the
  compatibility layer.

  **Severity assessment**: lower than the `model` mislabel (reasoning knobs, not identity), but the same class of bug:
  Anthropic-specific concepts applied to non-Anthropic providers with no cross-check. A `needs_respawn()` at a task
  boundary comparing effort-ladder indices of two DeepSeek sessions is comparing meaningless values. Read context_scope
  files (`accounts.py`, `slots_worker.py`, `model_tier.py`, `tmux_spawn.py:_append_model_flags`). No code change made
  (audit-only). Filed follow-up fix as new todo 4 (provider-corrected telemetry + provider-gated CLI flags, same
  `effective_*_for_telemetry()` pattern as the `model` fix). Checkbox flipped; Progress Log entry written.

- **slot-29 2026-08-10 (infra, todo -004, `ao_deepseek_provider_model_telemetry_mislabeled-004`)**: RECOVERED + SHIPPED
  the already-implemented orphan commit `cf9eef3` per the RECOVERY NOTE (did NOT re-author). Cherry-picked the exact
  commit byte-faithful onto LDR HEAD (only delta vs the original: preserved HEAD's `running_checkout_sha` import after a
  trivial tmux_spawn.py import conflict). Recovered change set = 13 files, 273+/8−: `effective_effort_for_telemetry()` /
  `effective_thinking_for_telemetry()` in `accounts.py` (non-Anthropic → `None`), wired into `boot_slot()`'s
  `upsert_slot` + `slot_boot` event; `_build_claude_flags()` provider-gates `--effort`/`--max-thinking-tokens`
  (Anthropic-only), `provider` threaded through all 17 `spawn`/`spawn_named` call sites. Shipped as
  `agent-orchestrator@70281b1` (+ `7a1016f` for the companion test-isolation fix) via quickmerge after full
  `quality-gates.sh` green (3156 passed). QG initially FAILED on 2 pre-existing env-dependent tests
  (`test_switch_main_account_resumes_with_stored_session`, `test_switch_main_model_resumes_and_writes_sonnet_default`) —
  verified PRE-EXISTING at base HEAD via a clean worktree (byte-identical failure): both read the LIVE `orch-agent-main`
  tmux pane through the unpached `_main_context_saturated_pct()` fallback (~92% context on this host → resume dropped →
  `assert None == 'sess-abc'`). Fixed the determinism gap by patching `capture_pane` in both tests (4a131ed/7a1016f),
  which stacks on top of the concurrently-landed `425a779` `_main_context_saturated_pct` patch from another slot. Both
  done-when assertions covered by `test_deepseek_flash_boot_stores_none_effort_thinking_not_anthropic_labels`
  - `test_non_anthropic_spawn_omits_effort_and_thinking_flags`. Checkbox flipped; Progress Log entry written.
