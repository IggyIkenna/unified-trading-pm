---
title: Main Agent Ledger — Harsh side, daily-evolving
type: orchestration-ledger
status: active
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

# Main Agent Ledger (Harsh side)

> **The communication bus** between Harsh's main orchestrator agent (this session, slot 1) and the spawned tab agents
> (slots 2-6 today, 2026-05-11 — Model A 6-slot thematic). Daily-evolving live state — tab registry, today's status,
> recent done, open questions across plans. Workflow rules + onboarding spec live in
> [`AGENT_ONBOARDING.md`](AGENT_ONBOARDING.md) and [`../cursor-configs/CLAUDE.md`](../cursor-configs/CLAUDE.md) §
> "Daily Work-Split Process".

## Spawned tab — boot path

If Harsh just opened a fresh Claude Code (CLI in a terminal `cd .tabs/<N>/` per Option B, or VS Code window at
`.tabs/<N>/`) and pointed you at this doc with _"work on slot N, you are the implementor agent, please read the
instructions carefully"_:

1. Read [`AGENT_ONBOARDING.md`](AGENT_ONBOARDING.md) **first** — canonical reading order + communication-bus rules +
   push discipline + pre-commit check + plan-of-record curation duties. Do not skip; the orchestration mechanics live
   there.
2. Then come back here and find your **Slot N entry** below under "Today's status → Tab registry". It has: theme,
   plan-of-record paths, worktree/branch, AI-day budget, gate status, cross-tab + cross-side handshakes, and a pointer
   to today's work-split § "Slot N" for the full task brief (scope items + repos owned + collision boundaries +
   done-definition + full-execution criterion).
3. Follow the rest of the AGENT_ONBOARDING.md reading order (CLAUDE.md → per-tab-worktrees.md → plan-aware-merge-resolution.md
   → SUB_AGENT_MANDATORY_RULES.md → work-split § "Slot N" → plan-of-record).
4. Boot ack: append a one-liner to `harsh_orchestrator/pings/slot_<N>.md` (per-slot — no collision) per the AGENT_ONBOARDING.md template, then start
   work.

## Bootstrap — fresh main-agent chat

If this conversation just started — Harsh's previous main-agent chat died, ran out of context, or was reset — and you're
being asked to be the main orchestrator (slot 1):

1. Read [`AGENT_ONBOARDING.md`](AGENT_ONBOARDING.md) for the role definition + reading order (a fresh main reads the
   same docs as a spawned tab, just with different scope: orchestration not implementation).
2. Read [`../cursor-configs/CLAUDE.md`](../cursor-configs/CLAUDE.md) § "Daily Work-Split Process" + § "Per-Tab
   Worktrees" — full spec for Model A / Model B work-splits + the 3-tier worktree isolation model.
3. Read today's work-split:
   [`../plans/active/work_split_2026_05_11_harsh.md`](../plans/active/work_split_2026_05_11_harsh.md) — the 6-slot
   assignment table + cross-side handshakes + spawn prompts.
4. Run boot checklist:
   - From `unified-trading-pm/`: `git status`, `git rev-list --left-right --count HEAD...origin/live-defi-rollout`,
     `git log --oneline -5 origin/live-defi-rollout` — see local-ahead state + recent origin activity.
   - `git -C ../unified-trading-pm worktree list` — confirm slots 1-6 worktrees exist on `tab/hk/1`..`tab/hk/6`.
   - `cat harsh_orchestrator/pings/*.md` (intra-side, per-slot) + `cat harsh_orchestrator/_agent_pings.md` (transition stub) + `cat plans/active/_agent_pings.md` (cross-side) — see active pings.
   - Skim "Today's status" below for the tab registry + open questions.
5. Ack to Harsh: _"Main agent online. State: N tabs in flight, M intra-side pings, K cross-side pings, J local commits
   queued for push. Today's plan = X, Y, Z. Standing by."_

**Polling cadence**: read `harsh_orchestrator/pings/*.md` (intra-side, per-slot — see [`pings/README.md`](pings/README.md)) + the transition stub [`_agent_pings.md`](_agent_pings.md) + [`../plans/active/_agent_pings.md`](../plans/active/_agent_pings.md)
(cross-side) every **~1 min** while Harsh is active. Stretch to ~5 min when both ledgers empty for 30+ min. Empty cycles
produce no chat output (no flooding).

**Your role**: direction-setting + Q&A dispatch + plan-of-record curation + ping triage + (per Harsh's chosen merge
model 2026-05-11) fast-forward-merging implementer slot branches `tab/hk/<N>` into `live-defi-rollout` in dependency
order. **Implementation work is NOT yours** — that's spawned tabs.

## Tab numbering convention (today: 2026-05-11 Model A 6-slot thematic, per-tab worktrees)

Today's [`work_split_2026_05_11_harsh.md`](../plans/active/work_split_2026_05_11_harsh.md) uses **Model A — 6 fixed
thematic slots** (slot 1 = main orchestrator + on-call, slots 2-6 = thematic implementers). Each slot is a permanent
worktree at `${WORKSPACE_ROOT}/.tabs/<N>/` on branch `tab/hk/<N>` (machine `$USER` is `hk`; the work-split's earlier
`tab/<harsh-user>/N` / `--operator harsh` placeholders are normalised to `hk` throughout). Operator opens a fresh Claude
Code session inside the slot worktree (`cd ${WORKSPACE_ROOT}/.tabs/<N>/ && claude` — Option B; or VS Code window at
`.tabs/<N>/`) and pastes the matching spawn prompt from the work-split § "Spawn prompts". The agent reads
[`AGENT_ONBOARDING.md`](AGENT_ONBOARDING.md) → this LEDGER's Slot N entry → work-split § "Slot N" → plan-of-record.

(Earlier cycles — 2026-05-07 D1, 2026-05-08 D2 morning Model B / afternoon Model A — used the shared-working-tree model
with `Tab N` numbering and no integer-slot worktrees. Today's per-slot worktree model supersedes that per CLAUDE.md
"Per-Tab Worktrees".)

---

## Today's slot assignments

> **Per-tab worktree model** (codified 2026-05-10, see
> [`../codex/05-infrastructure/per-tab-worktrees.md`](../codex/05-infrastructure/per-tab-worktrees.md)). Each slot is a
> permanent worktree at `${WORKSPACE_ROOT}/.tabs/<N>/` on branch `tab/hk/<N>`. Slot is durable identity; theme rotates
> daily. Before reassigning a slot to a new theme, run `bash unified-trading-pm/scripts/dev/setup-tab-worktrees.sh
> --reset-slot <N>` (verify clean + rebase onto `origin/live-defi-rollout`).

**Slot count:** 6 (provisioned 2026-05-11 via `setup-tab-worktrees.sh --init --slots 6`; all on `tab/hk/1`..`tab/hk/6`
at `live-defi-rollout` tip `7fddb7e8`). Grow with `--add-slot <N>` if peak parallel work exceeds.

**Operational model (Harsh side, set 2026-05-11):** one VS Code window at the workspace root (for editor/file checks
when rarely needed); implementer agents (slots 2-6) run as `cd ${WORKSPACE_ROOT}/.tabs/<N>/ && claude` in integrated
terminals (Option B). `.tabs/**` is excluded from the root window's `files.watcherExclude` / `search.exclude` /
`files.exclude` (`.vscode/settings.json`) so the editor doesn't index the slot worktrees. **Ping ledgers are per-slot**
(`harsh_orchestrator/pings/slot_<N>.md`, one per spawned slot) so the every-slot-touches-one-file collision is gone —
slot 1 is the only reader; see [`pings/README.md`](pings/README.md). (Transition: the 2026-05-11 slots 2/3/4/6 were
spawned pointing at the old `_agent_pings.md`; slot 1 reads both during this cycle.)

**Merge model — direct-to-`live-defi-rollout`, rebase-on-push (no batch-merge step):** the per-slot worktrees already
solve the foot-guns (each slot has its own `.git/index` + working tree), so the branch model stays simple. Per shippable
unit, an implementer slot does: `git fetch origin live-defi-rollout` → if incoming commits touch files this slot also
edited → STOP (flag in plan-of-record `## Open questions` 🟡 BLOCKED + ping, don't push); if incoming touches unrelated
files → `git rebase origin/live-defi-rollout` (auto-resolves non-overlapping changes) → `git push origin
tab/hk/<N>:live-defi-rollout`. Nobody does batch merges — each slot self-lands as it finishes; work is visible to all
immediately. Residual risk = rebase conflict in PM when two slots flip checkboxes in the same plan file; mitigated by
(a) only slot 1 writes PM plan/codex **bodies** — implementers flip ONLY their own plan-of-record's checkboxes with
`git add -p`; (b) the plan-aware-merge-resolution protocol auto-resolves trivial shapes (checkbox-flip / append-section)
and escalates genuine paragraph-rewrites to slot 1, never to the operator; (c) the scheduling rule — don't assign two
same-repo tasks to the same parallel wave. Slot 1's role here is PM curation + handling escalated conflicts, NOT routine
merging.

| Slot | Theme                                                                            | Plan-of-record                                                                                                                                                | AI-day | Gate status                                                                          |
| ---- | -------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ | ------------------------------------------------------------------------------------ |
| 1    | main orchestrator + on-call                                                      | (this LEDGER) + [code_freeze_migrate_backfill_sequencing_2026_05_10.md](../plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md)               | cont.  | active                                                                               |
| 2    | **features-repo consolidation Phase 4-7** (HARDEST DEADLINE 2026-05-13)           | [features_repo_consolidation_2026_05_08.md](../plans/active/features_repo_consolidation_2026_05_08.md) Phase 4-7                                              | ~5     | **READY NOW** (Phase 0-3 shipped; features-service skeleton pushed @d3d6e286)         |
| 3    | Wave3x Tracks B/C/D/E parallel                                                   | [wave3x_residual_ssots_2026_05_08.md](../plans/active/wave3x_residual_ssots_2026_05_08.md) Tracks B/C/D/E                                                     | ~5     | **READY NOW** (Track A shipped UAC@bdc84ed; Track D ANTI-SEQUENCING — before 2026-05-15) |
| 4    | bucket-name SSOT canonicalisation + per-asset-group available_at adapter wiring   | [bucket_name_ssot_canonicalisation_2026_05_10.md](../plans/active/bucket_name_ssot_canonicalisation_2026_05_10.md) + [available_at_lookahead_bias_completion_2026_05_08.md](../plans/active/available_at_lookahead_bias_completion_2026_05_08.md) Phase 1 | ~3 | PARTIAL — bucket-SSOT waits on slot 2 Phase 4; sports stamping waits on slot 3 Track E + Ikenna slot 3 Phase 0; can prep scaffolds now |
| 5    | live pipeline Phase 3-5 service wiring + Phase 13/14/15                           | [live_pipeline_mtds_mdps_features_2026_05_08.md](../plans/active/live_pipeline_mtds_mdps_features_2026_05_08.md) Phase 3-5 + 13-15                            | ~5     | GATED — Phase 3-5 impl blocked on slot 2 Phase 7 + Ikenna slot 4 design; pre-gate scaffolds OK now |
| 6    | workspace QG green sweep + codex audit pass + freeze-gate items 8 + 9             | [code_freeze_migrate_backfill_sequencing_2026_05_10.md](../plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md) freeze-gate items 8 + 9       | ~3     | READY NOW (low-urgency; value grows as slots 2-5 ship; runs all 4 days)               |

**Total active scope: ~21 AI-days across 5 thematic slots over a 4-day cycle to the 2026-05-15 Phase 1 code-freeze gate.**

The daily work-split plan (`plans/active/work_split_<YYYY_MM_DD>_harsh.md`) is the authoritative source for today's
themes; this LEDGER table mirrors it for fresh tab-agents bootstrapping outside chat scrollback. When the work-split
flips a slot to a new theme, slot 1 updates the row above + runs `--reset-slot <N>` before the new theme begins.

---

## Today's status (2026-05-11 — Model A 6-slot, Phase 1 code-freeze push)

### Tab registry

#### Slot 1 — `harsh-main-orchestrator` 🟢 ONLINE — infra bootstrap done; Wave 1 spawn ready

- **Status (2026-05-11)**: per-tab worktree infra provisioned (6 slots, `tab/hk/1`..`tab/hk/6`, all at `7fddb7e8`).
  `.vscode/settings.json` `.tabs/**` watcher-exclude applied (freeze fix). LEDGER refreshed to today's 6-slot
  assignments. Ledger sweep done — `harsh_orchestrator/_agent_pings.md` cleared of stale 2026-05-08 entries; cross-side
  `plans/active/_agent_pings.md` reviewed (Ikenna-side INFO pings, no Harsh-side action pending).
- **Worktree**: `.tabs/1/` on branch `tab/hk/1`.
- **Scope (per work-split § "Slot 1")**:
  - **P0**. Daily ledger sweep at start + every 4-6h: read both ping ledgers, triage 🟡 BLOCKED Qs >24h, ack STARTED
    pings, verify DONE pings.
  - **P0**. Cross-side coordination: route Harsh slot 2 (features-consolidation Phase 7 ship) cross-side ping when it
    lands → Ikenna slot 4 unblocks live-pipeline implementation.
  - **P0**. Workspace QG sweep coordination: when slot 6 ships any QG-green checkpoint, validate Phase 1 gate item 8 +
    escalate failure attribution per CLAUDE.md "QG failure attribution".
  - **P0** (merge-model 2026-05-11): NOT routine merging — implementers self-land directly to `live-defi-rollout`
    (rebase-on-push). Slot 1's duty is handling *escalated* PM rebase conflicts (paragraph-rewrite shape) via the
    plan-aware-merge-resolution protocol + enforcing the scheduling rule (no two same-repo tasks in one wave).
  - **P1**. Stale work-split sweep: ✅ DONE (by extra-hands @PM`6093b8c5`) — `work_split_2026_05_08_{harsh,ikenna}.md`
    moved `plans/active/` → `plans/archive/`; carryover items already rolled into today's split.
  - **P1**. Operator Q&A dispatch: route 🟡 BLOCKED Qs from slots 2-6 to operator chat; route decisions back to
    plan-of-record `## Open questions` sections.
- **Plan-of-record**: this LEDGER + [`../plans/active/work_split_2026_05_11_harsh.md`](../plans/active/work_split_2026_05_11_harsh.md)
  + [`../plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md`](../plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md).
- **Repos owned (collision boundary)**: `unified-trading-pm/plans/active/work_split_2026_05_11_harsh.md` +
  `unified-trading-pm/harsh_orchestrator/*` + `unified-trading-pm/plans/active/_agent_pings.md` (cross-side curation).
  Does NOT touch UAC / UTL / service repos.
- **Doing now**: standing by for Wave 1 spawn (slots 2 + 3 from terminal). Polling both ping ledgers ~1 min while
  operator active.

#### Slot 2 — `harsh-features-consolidation-tab` 🟢 IN FLIGHT — `features_service_qg_cleanup_2026_05_11.md` Phase 1.2 (session 3, fan-out): STARTED 2026-05-11 11:05 UTC; all 4 QG-check FPs resolved (skip nothing); re-ran QG → 16 real violation categories; launched 3 background sub-agents A/B/C partitioned per-FAMILY (pathspec commits, master pushes after verify); Phase 1.2e (row e ~38 schema-prov → UAC) split — group-1 mandatory + proceeds, group-2 gated on **Q3** ✅ ANSWERED (move-to-UAC default except `HealthResponse`+`_WeatherRow`; surfaced to operator + cross-side). Phase 1.1 ✅; Q1/Q1.3/Q2 all ✅

- **Status (2026-05-11, latest)**: Q1 ✅ RESOLVED — operator approved (a) spawn `features_service_qg_cleanup_2026_05_11.md`
  (created by slot 1; Phase 1 = QG-codex cleanup the proper way / no per-package-ignore; Phase 2 = full parity run
  blocked_by `code_freeze` Phase 3 backfills; Phase 3 = F9 org transfer P2 non-blocking) + (b) Phase 4.6/6 in the parent
  `**DEFERRED → features_service_qg_cleanup_2026_05_11.md**` + (c) F9 non-blocking. **Slot 2's next move**: take
  `features_service_qg_cleanup_2026_05_11.md` Phase 1. features-consolidation is ~done for the work-split (Phase 7 ✅;
  residual = the cleanup plan; none of it gates the May-23 cutover). Pointer in `slot_2.md` `[main → slot 2]`.
- **Earlier status (2026-05-11)**: 🟢 IN FLIGHT — STARTED ack received (PM@`917ec9d6`; the agent wrote `11:35 UTC` but the
  machine clock is IST so that's actually ~`06:05 UTC` — AGENT_ONBOARDING.md § "Boot ack template" now mandates
  `date -u` for ping timestamps); booting/fanning-out on features_repo_consolidation Phase 4. Phase 0-3 already shipped per prior cycle: Phase 0 pre-audit @PM`1de574b4` (1286 lines /
  11 ext imports + 51 string refs); Phase 1A UAC `FeatureFamily` enum @`7f63ca3`; Phase 1B UTL `ManifestWriter
  feature_family` kwarg @`c16cef3`; Phase 2 + Phase 3 first wave done (features-service skeleton @`d3d6e286` pushed to
  `IggyIkenna/features-service` `live-defi-rollout`; workspace-manifest registered line 880).
- **Theme**: features-repo consolidation Phase 4-7 (Phase 4 import rewrite → Phase 5 cross-family helper lift to UTL →
  Phase 6 pyproject + test consolidation → Phase 7 single deployable + 8 child repos archived, DEADLINE 2026-05-13).
  P1 Phase 8 manifest migration; P2 Phase 9 Health-API/live-mode flavors (deferred per plan body).
- **Plan-of-record**: [`../plans/active/features_repo_consolidation_2026_05_08.md`](../plans/active/features_repo_consolidation_2026_05_08.md).
  Sequencing umbrella served: [`code_freeze_migrate_backfill_sequencing_2026_05_10.md`](../plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md).
- **Worktree**: `.tabs/2/` on branch `tab/hk/2`.
- **AI-day budget**: ~5. **Deadline**: Phase 7 by 2026-05-13.
- **Read-first**: CLAUDE.md § "ARCHITECTURE 2026-05-08 — Live pipeline" + § "Shard-granularity SSOT" ([UAC]/[UTL]/
  [per-service] discipline) + § "Post-Plan-Phase Codex Audit" + § "Citadel-Grade Planning § 6 Downstream Consumer
  Updates" (workspace-grep audit table required) + the Phase 0 pre-audit manifest @PM`1de574b4`.
- **Sub-agent fan-out (within slot 2 worktree — share its `.git/index`, so pre-commit check + `git add -p` mandatory)**:
  4 parallel at boot — (1) Phase 4 import rewrite (mechanical; pre-audit lists exact 11+51 sites), (2) Phase 5
  cross-family helper lift to UTL (~5 helpers: watermark+grace fan-in, available_at stamping, LookaheadBiasError gate,
  NaN write-gate, ManifestFreshnessCache adoption), (3) Phase 6 pyproject unification + test consolidation (parallel
  with Phase 5), (4) Phase 7 archive coordination (deprecation banners + workspace-manifest registration).
- **Repos owned**: 8 features-* services → `features-service` (consolidated) + `unified-trading-library` (cross-family
  helper lifts — `feature_*` subdirs; coordinate with slot 3's `availability_stamping/` + slot 4) + `workspace-manifest.json`
  + PM (plan flips + codex SSOT updates).
- **Collision risk**: vs Ikenna slot 4 (imports consolidated features-service for Phase 5 contract types — **hard sync**:
  ship Phase 7 ASAP + cross-side ping); vs Harsh slot 5 (cannot start Phase 3-5 impl until Phase 7 — slot 5 preps
  scaffolds while gated); vs Harsh slot 4 (per-family `config.py` paths — slot 4 waits for Phase 4 to stabilise); vs
  Harsh slot 3 Track D (audits 8 features-* repos mid-consolidation — recommend Track D audits the consolidated state
  after Phase 4 ships, or archived snapshots).
- **Cross-side ping MANDATORY** when Phase 7 lands (features-service deployable; 8 child repos archived) so Ikenna slot 4
  can promote live-pipeline Phase 4-5 design to implementation.
- **Done-definition + full-execution criterion**: see work-split § "Slot 2" — Phase 4 grep shows zero references to old
  per-repo paths; Phase 5 helpers in UTL with tests; Phase 6 done; Phase 7 `cd features-service && bash scripts/quality-gates.sh`
  green + all 5 asset_groups' calculators import + run + `pip install -e ../features-service` succeeds; cross-side ping
  posted.
- **Full task brief**: [`../plans/active/work_split_2026_05_11_harsh.md`](../plans/active/work_split_2026_05_11_harsh.md)
  § "Slot 2 — Features-repo consolidation Phase 4-7".

#### Slot 3 — `harsh-wave3x-tab` ✅ DONE — all 5 Wave3x tracks shipped (A-UTL/B/C/D-audit/E); FREE for reassignment

- **Status (2026-05-11, latest)**: ✅ **DONE all 5 Wave3x tracks** (PM@`553e57c4` + `1f55b265`): A-UTL+B classifier
  extensions UTL@`3fbc6b3` + UAC@`7c8b5ad`; C `reconcile_legacy_blank_to_typed_reason.py` + 5-manifest dry-run
  instruments-service@`485c57b`; D audit (findings doc + P0 bugs escalated [P0-1/P0-2 shipped by slot 6], case-D impl
  deferred post-cutover, `EXPECTED_KNOWN_SOURCE_GAP` → Ikenna slot 5); E 3 stamping helpers + codex UTL@`2ab3685`.
  PM plan flips + DONE-2026-05-11 block + deferred-work scoreboard. Track E features-sports wire-in deferred to slot 4
  + Ikenna slot 3. **Going quiet — slot 3 is FREE for reassignment** (candidates: slot-5-adjacent pre-gate prep, or a
  new item, or stay idle — operator's load-balance call).
- **Earlier status (2026-05-11)**: 🟢 IN FLIGHT. **Track D ✅** — zero-activity-bar adapter audit complete; anti-seq verdict =
  NO new manifest schema dimension forced (the 2026-05-15 freeze gate is NOT blocked by Track D); findings filed in
  [`../plans/active/issues/wave3x_track_d_findings_2026_05_11.md`](../plans/active/issues/wave3x_track_d_findings_2026_05_11.md)
  (1 candidate new `EmptyConfirmedReason` `EXPECTED_KNOWN_SOURCE_GAP` → Ikenna slot 5 decision, cross-side-pinged; case-D
  *implementation* = substantial deferred work, recommend defer post-cutover / Wave 3.M; + 3 P0 bugs surfaced — see
  slot-6 entry + Open questions below). **Track B ✅** — UAC sports SSOTs (`UNDERSTAT_COVERED_LEAGUES` + `TRANSFER_WINDOWS`
  + footystats season bounds) shipped UAC@`e5d82a15`-area, 3 checkboxes flipped. **Continuing: Track C** (legacy-blank →
  typed-reason reconciler) **+ Track E** (sports stamping cascade). Track A shipped UAC@`bdc84ed`. **Re-scope note from
  Track D D3**: the sports per-fixture-bundle case-D work belongs in instruments-service, not MTDS — flagged for the
  wave3x plan owner.
- **Theme**: Wave3x Tracks B/C/D/E parallel — (B) sports per-source SSOTs `UNDERSTAT_COVERED_LEAGUES` + `TRANSFER_WINDOWS`
  + footystats season bounds (UAC `canonical/sports/`); (C) `reconcile_legacy_blank_to_typed_reason.py` reconciler for
  instruments-service; (D) **ANTI-SEQUENCING CRITICAL** zero-activity-bar adapter audit across MTDS, MDPS, 8 features-*
  services — if it finds a new shard atom dimension or new error reason needed, forces a second migration walk → MUST
  complete before the 2026-05-15 freeze; (E) sports per-source stamping helpers `stamp_available_at_lineups` / `_injuries`
  / `_post_match_cascade` / `_odds` (UTL `availability_stamping/` — folded into available_at Phase 1, coordinate with
  Ikenna slot 3). P1 Track A UTL wire (half-day + session-hours from UAC@bdc84ed).
- **Plan-of-record**: [`../plans/active/wave3x_residual_ssots_2026_05_08.md`](../plans/active/wave3x_residual_ssots_2026_05_08.md).
  Sequencing umbrella: [`code_freeze_migrate_backfill_sequencing_2026_05_10.md`](../plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md).
- **Worktree**: `.tabs/3/` on branch `tab/hk/3`.
- **AI-day budget**: ~5.
- **Read-first**: CLAUDE.md § "Sports source coverage windows" + § "Honest absence vs fake placeholders" + §
  "Four-category empty-output decision" + § "available_at is per-row, write-time, equal to live-pipeline-arrival" + §
  "Grep-Then-Read, Not Grep-Then-Conclude" (Track D audit must read consumer code + check runtime-resolved patterns) +
  Wave3x plan body.
- **Sub-agent fan-out**: 5 parallel at boot (one per Track A-UTL / B / C / D / E). Track D especially benefits from
  ~10-12 sub-sub-agents (one per service repo) for the read-only audit pass. **Sequencing**: Track D audit of the 8
  features-* repos should run AFTER slot 2's Phase 4 import rewrite (or on archived snapshots) — coordinate via slot 1.
- **Repos owned**: `unified-api-contracts` (Tracks A+B SSOTs) + `unified-trading-library` (Tracks A+E stamping +
  Track C reconciler infra — `availability_stamping/` + reconciler module; distinct from slot 2's `feature_*` subdirs)
  + `instruments-service` (Track C reconciler script — new file) + MTDS / MDPS / 8 features-* (Track D audit — read-only,
  finding-only).
- **Collision risk**: vs Ikenna slot 3 (Track E folds into available_at Phase 1 — distinct files within `availability_stamping/`;
  surgical `git add -p`); vs Harsh slot 2 (Track D audits repos mid-consolidation — see sequencing note above).
- **Track D escalation**: if the audit finds a new shard atom dimension OR new error reason needed → escalate to slot 1
  + Ikenna slot 5 IMMEDIATELY (they decide whether it lands in v8 schema via Ikenna slot 2 or is deferred post-cutover).
- **Done-definition + full-execution criterion**: see work-split § "Slot 3" — Track B 3 SSOTs + tests + CLAUDE.md
  sports-section cross-refs; Track C reconciler dry-run on production manifest maps 100% of blank-reason rows to typed
  reasons; Track D findings doc `plans/active/issues/wave3x_track_d_findings_2026_05_11.md` with per-adapter A/B/C/D
  classification; Track E 4 stamping helpers + tests integrated by Ikenna slot 3.
- **Full task brief**: [`../plans/active/work_split_2026_05_11_harsh.md`](../plans/active/work_split_2026_05_11_harsh.md)
  § "Slot 3 — Wave3x Tracks B/C/D/E parallel".

#### Slot 4 — `harsh-bucket-and-adapter-tab` 🟢 IN FLIGHT (multi-session) — SCOPE NARROWED to the bucket-name SSOT ((b+); the available_at P1 absorbed by `ikenna-available-at-tab` per operator "harsh agent is stale"). Session 1 ✅: Phase 0b (@deployment-svc`a7eba4f`+@UTL`2118b1e`) + Done-def #2 L2 config.py migration (@features-svc`8f03ceeb`) + sports-adapter stamping (@MTDS`c186ecb` — todo flipped `[x]` + 4 design Qs resolved by Ikenna) + PM`f5b7da56`. **Phase 0i ✅ = ap-northeast-1**. **Session 2 (2026-05-11)**: Phase 0e ✅ shipped (@`ecb47b6c` — env-tier the Group-A kinds; all env-tiered names verified to fit the 63-char limit) — but surfaced **Q5** (🟡 needs Ikenna): `features-cross-instrument`/`features-multi-timeframe` bucket names OVERFLOW 63 chars when combined with `-{ag}-{env}-{pid/account}` (AWS `unified-trading-features-cross-instrument-prediction-staging-{12-digit}` ≈ 73, even `...-cefi-prod-...` ≈ 64); 4 options listed (alias/drop-prefix/env-less/asymmetric) — bucket-naming SSOT call = Ikenna's per work-split; routed cross-side. Slot 4 proceeding on the unblocked work (Done-def #3 + the env-less-GCP-entries DeFi-raw-first sub-todo); ONLY the cross-instrument/multi-timeframe config.py bucket-defaults item waits on Q5. Next session: Done-def #3 (legacy `get_bucket_name`/`BUCKET_PREFIXES` delegate, UTL) + the env-less-GCP-entries sub-todo + Done-def #5/#6 + 0f/0g/0h; Phase 0c/0d (provision+migrate) = code_freeze Phase 2.6 (2026-05-15→05-19). v8 schema cols + `EXPECTED_KNOWN_SOURCE_GAP` available from UAC root for Phase 0c.

- **Status (2026-05-11, latest)**: ⚪ no-gate prep DONE, agent gone quiet (cleanly). Shipped: parity-test extension
  UTL@`e8dc6e3` (bucket_naming features-*/sports/tradfi/prediction coverage + fixed `test_workspace_yaml_has_gcp_aws_parity`,
  RED since 2026-05-08); plan-flips PM@`59e92b18`; full 4-layer pre-audit manifest + per-layer migration recipe + QG STEP
  5.69 design; the **P0 FINDING** that `cloud-providers.yaml` features-* entries carry a `${DEPLOYMENT_ENV}` tier the GCP
  buckets DON'T have (naive config.py→`resolve_bucket_name` migration would re-create the first-write-failure bug — Q4,
  surfaced to operator + cross-side-pinged Ikenna); sports-adapter audit `issues/mtds_sports_available_at_wiring_2026_05_11.md`
  (PM@`7c088961`/`e1f20f01`); DONE block + deferred-work scoreboard. **Q1/Q2/Q3 answered by slot 1** (A1 keep resolver
  in UTL — work-split paste corrected; A2 slot-2-Phase-4 gate clear, proceed after Q4; A3 STEP 5.69). **Resume on**: Q4
  answered (operator/Ikenna — recommend (a) match yaml to reality) → Phase 0 + L2 config.py migration; slot-3 Track E ships
  → wire sports stamping into MTDS.
- **Worktree note (2026-05-11)**: slot 4's `unified-trading-system-ui` worktree was left in a broken half-checkout
  state (3075 dirty files, `locked`) by the killed `--init` during the freeze incident. Fixed: removed the broken
  worktree, re-added on `tab/hk/4`, ran `--reset-slot 4` → all slot-4 repos rebased clean onto `origin/live-defi-rollout`.
  Slot 4 is now spawnable normally.
- **Theme**: bucket-name SSOT canonicalisation (yaml = canonical per plan; collapse the per-family `config.py` + UTL
  resolver duplicates → `bucket_naming.resolve_bucket_name()`; workspace QG step for inline `f"gs://{bucket}/..."`;
  yaml-vs-resolver parity test; plan-flip audit table) + per-asset-group available_at adapter wiring (sports adapter
  stamping — wire slot 3 Track E's UTL helpers into MTDS sports adapters; CeFi already shipped MTDS@`4a00bd5`).
- **Plan-of-record**: [`../plans/active/bucket_name_ssot_canonicalisation_2026_05_10.md`](../plans/active/bucket_name_ssot_canonicalisation_2026_05_10.md)
  + [`../plans/active/available_at_lookahead_bias_completion_2026_05_08.md`](../plans/active/available_at_lookahead_bias_completion_2026_05_08.md) Phase 1 per-adapter halves.
- **Worktree**: `.tabs/4/` on branch `tab/hk/4`. **AI-day budget**: ~3.
- **Gate**: bucket-name SSOT migration runs AFTER slot 2 Phase 4 import rewrite stabilises (per-family `config.py`
  paths) — or against the consolidated state. Sports adapter stamping WAITS on (a) slot 3 Track E ship (UTL helpers),
  (b) Ikenna slot 3 Phase 0 ship (bar boundary contract). While gated: prep test scaffolds + the mechanical 3-layer
  collapse plan.
- **Read-first**: CLAUDE.md "Bucket-name SSOT" memory + § "available_at is per-row" + § "Plans Run To Actual Completion"
  (bucket-SSOT triple-drift incident, 2026-05-08 Tab 4 close-out — there are THREE current SSOT layers: yaml + per-family
  config.py + UTL resolver; yaml is canonical, collapse the other two; audit each call site before deletion).
- **Sub-agent fan-out**: 2 parallel — (1) bucket-name SSOT migration, (2) sports adapter stamping wiring (gated).
- **Repos owned**: `unified-trading-library` (`cloud_interface.bucket_naming` resolver — exists; SSOT = `cloud-providers.yaml`) + `unified-trading-library` (QG step) + `features-service`
  (per-family config.py — coordinate paths with slot 2) + `deployment-service` (setup-buckets.sh) + `market-tick-data-service`
  (sports adapter stamping) + PM (plan flips + audit table).
- **Full task brief**: [`../plans/active/work_split_2026_05_11_harsh.md`](../plans/active/work_split_2026_05_11_harsh.md)
  § "Slot 4 — Bucket-name SSOT + per-asset-group available_at adapter wiring".

#### Slot 5 — `harsh-live-pipeline-impl-tab` ⚪ QUEUED — GATED (pre-gate scaffolds now; activate on slot 2 Phase 7 + Ikenna slot 4 design)

- **Theme**: live-pipeline Phase 3-5 service wiring (Phase 3 MTDS websocket rollout per asset_group; Phase 4 MDPS
  streaming aggregation; Phase 5 features-service asset-scoped streaming) + Phase 13/14/15 (VM launchers + watchdog dict
  updates + codex SSOT updates + QG sweep + smoke — likely next-cycle).
- **Plan-of-record**: [`../plans/active/live_pipeline_mtds_mdps_features_2026_05_08.md`](../plans/active/live_pipeline_mtds_mdps_features_2026_05_08.md) Phases 3-5 + 13-15.
- **Worktree**: `.tabs/5/` on branch `tab/hk/5`. **AI-day budget**: ~5.
- **Gate**: Phase 3-5 IMPLEMENTATION blocked until BOTH (a) Harsh slot 2 ships features-consolidation Phase 7 AND
  (b) Ikenna slot 4 ships Phase 4-5 design-ahead commits. PRE-GATE work now: read live-pipeline design docs + Ikenna's
  UTL stubs as they ship; prep MTDS websocket integration scaffolds (Phase 3) + MDPS streaming consumer hooks (Phase 4)
  + features-service per-asset-group flavors (Phase 5) + test scaffolds + integration fixtures. POST-GATE: 5 parallel
  implementers (one per asset_group).
- **Read-first**: CLAUDE.md § "ARCHITECTURE 2026-05-08 — Live pipeline" + § "Per-VM shard isolation" + § "VM launcher
  script SSOT" + § "VM Naming Convention" + live-pipeline plan body.
- **Repos owned**: `market-tick-data-service` (Phase 3) + `market-data-processing-service` (Phase 4) + `features-service`
  (Phase 5 — coordinate paths with slot 2) + `deployment-service/scripts/vm/` (Phase 13) + `vm_zombie_watchdog.py`
  (dict updates) + PM (codex SSOTs + plan flips).
- **Collision risk**: vs Harsh slot 2 (Phase 5 consumers in the repo slot 2 is consolidating — wait for Phase 7); vs
  Harsh slot 6 (Phase 15 QG sweep shared scope — coordinate which slot owns the final run).
- **Full task brief**: [`../plans/active/work_split_2026_05_11_harsh.md`](../plans/active/work_split_2026_05_11_harsh.md)
  § "Slot 5 — Live pipeline Phase 3-5 service wiring".
- **SCOPE UPDATE 2026-05-11 — P0-2 MDPS surgery NO LONGER slot 5's**: Ikenna's slot 8 (`ikenna-slot8-p0-2-surgery`,
  PM `6c2b7170`..`bf18c6db` + DONE block `5b3ea34d` in `writegate_honest_coverage_endtoend_2026_05_06.md`) shipped P0-2
  steps 1-4 + 6 (`mdps@d717c59`/`93883b7`/`2f163c1` + the step-4 enum finalize + step-6 branch delete). Only step 5
  (`output_schemas.py` OHLCV nullability flip) remains — OUT-OF-SCOPE / owned by `hard_schema_enforcement_2026_05_08.md`
  (itself blocked by `tradfi_master_2026_05_07` futures-expiry). So when slot 5 activates: do NOT redo P0-2; Phase 4 is
  just the MDPS service-wiring per the work-split. Detail in `pings/slot_5.md` `[main → slot 5]` 2026-05-11.

#### Slot 6 — `harsh-workspace-qg-tab` 🟢 IN FLIGHT — codex audit ✅ + QG baseline ✅ + Track-D P0-1/2/3 ✅; raised items F3 + slot-worktree-QG-bug ✅ RESOLVED by operator 2026-05-11 (PM`39ab61e5`); back to freeze-gate-8/9 + phantom-audit cadence

- **Status (2026-05-11, latest)**: Track-D P0 batch ✅ DONE — **P0-1** `market-tick-data-service@3da026d` (4 `record_empty`
  callsites get `reason="SOURCE_RETURNED_ZERO"` + `except (LegacyBlankErrorReasonError, UnknownEmptyConfirmedReasonError):
  raise` before the swallowing `except`; ruff-clean + 12 sentinel tests pass); **P0-2 slot-6 half** PM@`a4512ed3` (QG
  STEP 5.67 — `check_banned_placeholder_methods.py` + `banned_placeholder_methods_baseline.yaml`; AST-walk for the
  banned NaN-placeholder / bypass-`record_captured` patterns; baseline-aware shrinking ratchet — 8 known MDPS
  occurrences are pending_removal WARNINGS, new ones fail CI; the P0-2 *code* fixes stay writegate Phase 2.A + slot 5);
  **P0-3** commodity phantom-row classified + captured + owner-routed (slot 5 + writegate; the fix is features-service =
  slot-2 territory; no separate issue doc). Phantom audit (P1) deferred to a GCE same-region VM (laptop run impractical
  — cross-region listing 18× slower); 2026-05-04 baseline (354 residual) stands. **Flagged to slot 1**: `bash
  scripts/quality-gates.sh` from a slot worktree resolves the wrong repo root (runs PM's tests when PM is a sibling
  worktree) — affects every slot's pre-push QG; issue doc `plans/active/issues/slot_worktree_qg_repo_root_resolution_2026_05_11.md`,
  cross-side-pinged Ikenna. Now: back to freeze-gate-8/9 (validate slot-2-to-5 shippable units) + the phantom-audit
  cadence; standing by for the Ikenna-slot-2 writegate-v8-schema cross-side handshake.
- **Earlier status (2026-05-11)**: 🟢 IN FLIGHT. Done so far: codex SSOT audit pass (freeze-gate-9 inventory: 25 plans / 91
  codex docs / 58 present / 33 pending; F2 → routed to slot 2; F3 v8-schema-owner ambiguity → cross-side-pinged Ikenna;
  see [`../plans/active/issues/codex_audit_2026_05_11.md`](../plans/active/issues/codex_audit_2026_05_11.md)) + QG static
  baseline (ruff 20/22 clean — features-service 13×I001 mid-consolidation-churn by slot 2; SIT 4×C901 pre-existing; 0
  bare `# type: ignore`; see [`../plans/active/issues/qg_sweep_2026_05_11.md`](../plans/active/issues/qg_sweep_2026_05_11.md)).
  Migrated to per-slot ping log `harsh_orchestrator/pings/slot_6.md`. Full `quality-gates.sh` sweep deferred days 2-4
  (slot worktrees have no per-repo `.venv`).
- **ADDED SCOPE (2026-05-11, per operator direction)** — Track-D P0-bug fixes (Track D audit by slot 3 surfaced them,
  fixes in sight): **P0-1** MTDS honest-coverage sentinel silent-abort (`orchestrator.py:2671/2808/2849` +
  `rebuild_prediction_manifest.py:351` `record_empty(row_key=...)` missing `reason=` → `LegacyBlankErrorReasonError`
  swallowed by the wrapping `except` → no `empty_confirmed`/`attempted_failed` rows for CeFi/sports on zero-data shards;
  fix = pass `reason="SOURCE_RETURNED_ZERO"` / calendar `EXPECTED_*`, stop swallowing the exception); **P0-2 QG-gate half**
  = add an AST/grep QG STEP flagging banned NaN-placeholder / bypass-`record_captured` patterns (`_create_empty_output` /
  `_handle_empty_tick_data` / `_create_full_day_empty_output` / `_create_closed_market_candle` /
  `_maybe_write_vix_gap_placeholder` / direct `upload_bytes` candle writes) — the P0-2 *code* fixes (delete legacy
  `orchestration_writer.py:328 _write_candles`, fix `tradfi/ohlcv_passthrough.py`, flip `output_schemas.py` OHLCV
  nullability, resolve the triple-SSOT) are writegate Phase 2.A + Harsh slot 5, NOT slot 6; **P0-3** `commodity` phantom-row
  → investigate in the P1 phantom-audit pass. Source: [`../plans/active/issues/wave3x_track_d_findings_2026_05_11.md`](../plans/active/issues/wave3x_track_d_findings_2026_05_11.md).
  Full brief: work-split § "Slot 6" (updated 2026-05-11).
- **Theme**: workspace QG green sweep (UAC + UTL + every service repo; basedpyright clean; no `# type: ignore` masking
  architectural violations — run after each slot ships a shippable unit, validate) + codex SSOT audit pass per CLAUDE.md
  "Post-Plan-Phase Codex Audit" HARD RULE + freeze-gate items 8 + 9 of `code_freeze_migrate_backfill_sequencing_2026_05_10.md`
  + P1 phantom audit (`instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group all --dry-run` —
  ensure the 354 residual phantoms from 2026-05-04 baseline haven't grown).
- **Plan-of-record**: [`../plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md`](../plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md) freeze-gate items 8 + 9.
- **Worktree**: `.tabs/6/` on branch `tab/hk/6`. **AI-day budget**: ~3.
- **Read-first**: CLAUDE.md § "Post-Plan-Phase Codex Audit" + § "QG failure attribution" + § "Manifest phantom audit" +
  § "CI Verification After Every Push" + § "Findings Triage Discipline" temporary exception (QG-failure findings on
  someone else's code during the cleanup window are EXEMPT from case-3/4/5 documentation — bulk-cleaned).
- **Repos owned**: read-only across UAC + UTL + every service repo + codex docs. Issue docs filed in `plans/active/issues/`
  for any failure attribution.
- **Full task brief**: [`../plans/active/work_split_2026_05_11_harsh.md`](../plans/active/work_split_2026_05_11_harsh.md)
  § "Slot 6 — Workspace QG green sweep + codex audit pass".

### 🟢 Booted slots

- **Slot 1** (this session) — online (orchestrator, runs in the main clone, not `.tabs/1/`).
- **Slot 2** `harsh-features-consolidation-tab` — 🟢 IN FLIGHT; `features_service_qg_cleanup` Phase 1.2 session 3 (3-sub-agent fan-out A/B/C per-family); 16 real violation categories; Phase 1.2e group-1 proceeds, group-2 = Q3 ✅ answered (move-to-UAC default except HealthResponse/_WeatherRow); all 4 QG-check FPs resolved.
- **Slot 3** `harsh-wave3x-tab` — ✅ DONE (all 5 Wave3x tracks A-UTL/B/C/D-audit/E shipped; FREE for reassignment).
- **Slot 4** `harsh-bucket-and-adapter-tab` — 🟢 IN FLIGHT (bucket-SSOT canonical layer = yaml decided; PARTIAL GATE on the rest).
- **Slot 5** `harsh-live-pipeline-impl-tab` — ⚪ QUEUED; hold ~1 day (gated on slot 2 Phase 7 *deployable* + Ikenna slot 4 design). `--reset-slot 5` before spawn.
- **Slot 6** `harsh-workspace-qg-tab` — 🟢 IN FLIGHT (codex audit + QG baseline ✅; Track-D P0-1/2/3 ✅; back to freeze-gate-8/9 + phantom-audit cadence; flagged the slot-worktree-QG-repo-root bug).

### ⚪ Main agent (this session) doing now — POST-COMPACT RESUME SNAPSHOT (2026-05-11 10:30 UTC)

> **If you're a post-compact / fresh main-agent session reading this**: you ARE slot 1 (Harsh-side orchestrator). A
> cron loop (job `e97acdd7`, every 5 min, session-only) fires "Orchestrator poll (Harsh side, slot 1)..." prompts —
> on each fire: `cd unified-trading-pm; git fetch; if incoming, git pull --rebase`; check `harsh_orchestrator/pings/slot_2..6.md`
> + `harsh_orchestrator/_agent_pings.md` + `plans/active/_agent_pings.md` for new activity; handle (a) new blocker Q →
> answer A1 in the slot's plan-of-record `## Open questions` + `[main → slot N]` ping + commit+push; (b) new STARTED →
> flip the slot's LEDGER entry to 🟢 IN FLIGHT; (c) new DONE/shipped-unit → verify + flip LEDGER + note in `slot_6.md`
> there's a unit to QG-validate; (d) Ikenna cross-side ping answering a pending item → relay to the affected slot +
> flip LEDGER; (e) case-5 BIG finding → surface to operator in chat; (f) nothing new → terse one-liner. `date -u` for
> timestamps (machine clock is IST). Conditional-push (fetch + rebase-on-reject; don't pipe `git push` through `tail`).
> Don't reassign slot 3 (operator directive). Operator may say "stop" → omit further loop handling (loop ends when
> the session ends anyway).

**State as of 2026-05-11 10:30 UTC:**
- **All cross-side decisions resolved** — Q4→(b)→(b+) full env-aware bucket arch; AWS region = ap-northeast-1; `EXPECTED_KNOWN_SOURCE_GAP` enum (Phase 1, shipped UAC root); F3 v8-schema-owner = `manifest_schema_final_gate_2026_05_09.md` (v8 slice (b) shipped @UAC`174f401`+`d938a69`); Q1.1/Q1.2/Q1.3/Q2 (4 features-svc QG-check FPs) all fixed; slot-worktree-QG-repo-root bug → `per_agent_worktrees` Phase 4.5; defi_master Q1 all 3 approved (#3 → Ikenna slot 5; #4 ASTER shipped UAC`77666c8`); slot-4 sports-stamping asks resolved. **No open blocker Qs.**
- **Slots**: 1 = this (orchestrator, loop active). 2 `harsh-features-consolidation-tab` = 🟢 IN FLIGHT (resumed 2026-05-11 11:05 UTC) — `features_service_qg_cleanup` Phase 1.2 session 3, 3-sub-agent fan-out (A/B/C per-family); 16 real violation categories; Phase 1.2e group-1 proceeds, group-2 = Q3 ✅ answered. 3 `harsh-wave3x-tab` = ✅ DONE all 5 tracks; idle (NOT reassigning per operator); Track-D case-D impl deferred post-cutover (Wave 3.M follow-up TBD). 4 `harsh-bucket-and-adapter-tab` = 🟢 IN FLIGHT (session 2, 2026-05-11) — bucket-name SSOT: Phase 0e ✅ @`ecb47b6c`; **Q5** (cross-instrument/multi-timeframe 63-char overflow) 🟡 routed to Ikenna; proceeding on Done-def #3 + env-less-GCP-entries sub-todo (only the xinstr/mtf config bucket-defaults item waits on Q5); Phase 0c/0d = code_freeze Phase 2.6; scope = bucket-SSOT only; Phase 0i ✅ = ap-northeast-1. 5 `harsh-live-pipeline-impl-tab` = not spawned / gated (on Ikenna's live-pipeline Phase 4-5 design; features-consolidation Phase 7 ✅ met). **P0-2 MDPS surgery is now DONE by Ikenna slot 8** (PM `6c2b7170`..`bf18c6db`; only step 5 = `output_schemas.py` nullability remains, owned by `hard_schema_enforcement`) — slot 5 should NOT redo P0-2; see `slot_5.md` `[main → slot 5]` 2026-05-11. 6 `harsh-workspace-qg-tab` = `/compact`+continue'd ~2026-05-11 10:30 UTC — resuming: re-run freeze-gate-9 codex re-check now that v8 slice (b) landed + QG-validate slot-4/slot-2 shippable units; freeze-gate-8/9 + phantom-audit cadence.
- **Harsh-side-unassigned carry-forward**: defi_988 remainder ~1,335 rows (#5 LINEA/BSC `lending-indices-handler` routing config + the VM launches) — flagged to operator; low priority.
- **Merge/op model** (set 2026-05-11): one VS Code window at root + implementer agents via `cd .tabs/<N>/ && claude` (Option B); `.tabs/**` excluded from `.vscode/settings.json` watcher; per-slot ping files `harsh_orchestrator/pings/slot_<N>.md` (bidirectional — `[main → slot N]` channel; transition stub `_agent_pings.md`); direct-to-`live-defi-rollout` rebase-on-push (no batch merge); only slot 1 writes PM plan/codex bodies, implementers flip their own checkboxes with `git add -p`.

### ❓ Open questions across active plans (operator decisions pending)

_(2026-05-11) `defi_master_2026_05_07.md` Q1 ✅ RESOLVED by Ikenna — defi_988 backfill (~13,632 rows of DeFi data reclamation) is unblocked: #4 ASTER chain genesis on BSC ✅ shipped UAC`77666c8`; #5 LINEA/BSC `lending-indices-handler` routing config authorized (still to land); #3 PROTOCOL_LAUNCH_DATES tightening authorized-in-principle (needs per-protocol date research for ~30 pairs). **NOT on any current Harsh slot** (the 2026-05-08 `vm-ops-tab` that owned it is retired; today's slot 4 is a different theme) — carry-forward / spin-up candidate; flagged to operator._


| Slot | Plan | Q | Status | Action needed |
| --- | --- | --- | --- | --- |
| 3 | `issues/wave3x_track_d_findings_2026_05_11.md` | `EXPECTED_KNOWN_SOURCE_GAP` enum + case-D impl deferral. | ✅ RESOLVED 2026-05-11 (operator, Ikenna PM`39ab61e5`): enum ✅ APPROVED Phase 1 (lands in `manifest_schema_final_gate_2026_05_09.md`); case-D impl ✅ deferred post-cutover (Wave 3.M follow-up plan TBD; sports half re-scopes to instruments-service — Harsh-side follow-up, slot 3 not reassigned). | — (closed; Wave-3.M-plan creation = next-cycle follow-up) |
| 6 | `issues/codex_audit_2026_05_11.md` Q1 (F3) | v8-schema-owner ambiguity. | ✅ RESOLVED 2026-05-11 (operator, Ikenna PM`39ab61e5`): option (b) — `manifest_schema_final_gate_2026_05_09.md` canonical; writegate slice (b) Phase 5.2 SUPERSEDED; `code_freeze` updated; A1 in codex_audit Q1. | — (closed) |
| 2 | `features_service_qg_cleanup_2026_05_11.md` Q1.1/Q1.2/Q1.3/Q2 (4 QG-check FPs) | `cli/` print / `scripts/` schema-provenance / `unified_api_contracts.internal` deep-import / docstring-import false flags. | ✅ ALL RESOLVED — Q1.1 ✅ + Q1.2 ✅ (Harsh slot 1, PM`2cacb0eb`); Q1.3 ✅ (Ikenna, PM`d2a553ed` — base-service.sh deep-import whitelist); Q2 ✅ (Ikenna, PM`0407eb1a` — imports-inside-functions → AST). | — (closed; slot 2 proceeds Phase 1.2 full-throttle on the real-violation rows). |
| 2 / Ikenna | `features_service_qg_cleanup_2026_05_11.md` Q1 (3 sub-Qs) | 3 codex-compliance categories are QG-check false positives: (1) `print()` in `cli/`; (2) schema-provenance flags `scripts/` (CLAUDE.md says "(scripts/ excluded)"); (3) `unified_api_contracts.internal` flagged as deep-import (it's a sanctioned facade). | ✅ ANSWERED by slot 1 (all 3 confirmed FPs; slot 2 skips those rows in Phase 1.2); QG-check fixes cross-side-pinged Ikenna (3 small PM-template edits + rollout) | Ikenna: 3 QG-check fixes (or Harsh slot 1 does the PM edits + Ikenna runs rollout — operator's call). Not blocking — slot 2 has real-violation work meanwhile. |
| 4 | `bucket_name_ssot_canonicalisation_2026_05_10.md` Q4 (P0) | env-tier in bucket names vs flat provisioned buckets. | ✅ RESOLVED 2026-05-11 → operator extended to **(b+)** full env-aware bucket architecture (env tier on ALL kinds incl. Group-A; sync script; region pinning; env-aware VM launchers; pipeline_mode in PATH not name). Ikenna landed all cascading edits PM`2d6b131c` (bucket_name_ssot Phase 0a-0i + code_freeze GAP-2.4.B-I + aws_migration banner + work_split slot 4 scope + ikenna work_split slot 5 anti-seq + 4 codex banners + CLAUDE.md). My PM`7be8593a` (b) version is banner-superseded. | Slot 4 picks up the (b+) brief (re-bootstrap ping sent); region-pin Q (0i) to operator pending; otherwise no operator decision needed. |
| 2 | `features_repo_consolidation_2026_05_08.md` Q1 | Phase 4.6 (consolidated-repo QG green) BLOCKED on ~17 codex-compliance + function/file-size violations carried over from the 8 source repos without their per-file ignores (proper fix = a multi-day cleanup workstream, not per-package-ignore restoration); Phase 6 full byte-for-byte parity RUN never ran (needs a 7-day live-data window); F9 org-naming (features-service under `CosmicTrader` not `IggyIkenna` — operator-confirmed-temporary). NONE of it gates the May-23 cutover per the plan's own assessment; Phase 7 (8 repos archived) IS done. | 🟡 BLOCKED — needs operator triage on scope | Recommend: (a) spin a `features_service_qg_cleanup_<date>.md` successor plan owning 4.6 + Phase 6 full parity run + F9; (b) annotate Phase 4.6 + Phase 6 `**DEFERRED → successor**`; (c) treat features-consolidation as ~done for the work-split (residual = QG-cleanup + parity-run, neither gating cutover). Operator confirm? |

### ✅ Done today (2026-05-11)

| Repo               | Sha / change | Slot  | What                                                                                          |
| ------------------ | ------------ | ----- | --------------------------------------------------------------------------------------------- |
| (workspace root)   | `.vscode/settings.json` | 1 | Added `**/.tabs/**` to `files.watcherExclude` / `search.exclude` / `files.exclude` — freeze fix. _Loose local file, not committed to any repo._ |
| unified-trading-pm | `0244af36`+`6bfa9a42`+(this) | 1 | LEDGER + work-split refreshed to 2026-05-11 6-slot; `tab/<harsh-user>/N` → `tab/hk/N`; AGENT_ONBOARDING worktree-aware (new merge model); work-split spawn prompts slimmed to self-contained per-slot pointers; `_agent_pings.md` swept; slot 2+3 flipped IN FLIGHT. |
| unified-trading-pm | `1d6c9d61` | (Ikenna) | `cleanup-empty-dirs.py` workspace housekeeping utility (operator-confirmed, pushed). |
| unified-trading-system-ui | `bb2bd32a` | 1 | Untracked stray `.pyc` removed (operator-confirmed, pushed). |
| (worktree fix)     | n/a          | 1     | Slot 4's `unified-trading-system-ui` worktree was broken (3075 dirty, `locked`) by the killed `--init` — removed + re-added on `tab/hk/4` + `--reset-slot 4` → all slot-4 repos clean on `origin/live-defi-rollout`. Slot 4 spawnable. |
| unified-trading-pm | `7a871894` | 1 | Per-slot ping files (`harsh_orchestrator/pings/slot_<N>.md`) — kill the every-slot-touches-one-file collision; `_agent_pings.md` → redirect stub; AGENT_ONBOARDING + LEDGER + work-split spawn prompts + CLAUDE.md "Ping ledger bifurcation" updated. |
| unified-trading-pm | (this commit) | 1 | Slots 4+6 flipped IN FLIGHT; slot 3 Track D ✅ + B ✅ + escalation cross-side-pinged Ikenna (EXPECTED_KNOWN_SOURCE_GAP + F3 v8-owner + P0-2 MDPS heads-up); slot 6 Track-D P0 fixes added to scope; slot 2 Phase 4.6-blocked + Q1 surfaced; Open-questions table populated. |
| unified-api-contracts | (slot 3) | 3 | Wave3x Track B UAC sports SSOTs (`UNDERSTAT_COVERED_LEAGUES` + `TRANSFER_WINDOWS` + footystats season bounds) shipped + 3 checkboxes flipped (PM@`e5d82a15`-area). |
| unified-trading-pm | (slot 4) | 4 | bucket-name SSOT — canonical layer decided = yaml; parity-test todo flipped; pre-audit manifest added (PM@`59e92b18`). |
| unified-trading-pm | (slot 6) | 6 | codex SSOT audit pass (freeze-gate-9 inventory + F2/F3) + QG static baseline; 2 issue docs filed (`codex_audit_2026_05_11.md` + `qg_sweep_2026_05_11.md`) (PM@`04ed9203`+`e8cbe46b`). |
| market-tick-data-service / unified-trading-pm | (slot 6) | 6 | Track-D P0-1 fix MTDS@`3da026d` (record_empty reason= + loud manifest-contract exceptions); P0-2 QG STEP 5.67 PM@`a4512ed3` (banned-placeholder-method AST-walk, baseline-ratchet); P0-3 commodity phantom-row classified + owner-routed. |
| unified-api-contracts / unified-trading-library / instruments-service | (slot 3) | 3 | Wave3x ALL DONE — Track A-UTL+B classifier extensions UTL@`3fbc6b3`+UAC@`7c8b5ad`; Track C reconciler `reconcile_legacy_blank_to_typed_reason.py` instruments-service@`485c57b`; Track D audit (findings doc); Track E 3 stamping helpers UTL@`2ab3685` (PM flips @`553e57c4`+`1f55b265`). |
| deployment-svc/UTL/features-svc/MTDS/PM | (slot 4) | 4 | (b+) session 1: Phase 0b cloud-providers.yaml @deployment-svc`a7eba4f` + parity-test @UTL`2118b1e`; Done-def #2 L2 config.py migration @features-svc`8f03ceeb`; sports-adapter `available_at` stamping @MTDS`c186ecb`; PM`f5b7da56` flips/scoreboard. |
| (operator + Ikenna) | `78fd7070` | — | AWS region ratified = `ap-northeast-1` (b+ Phase 0i resolved; zero-cost — DeFi buckets already there; matched-region with GCP asia-northeast1). Master plan readiness column refresh. |
| harsh_orchestrator + plans | (this commit) | 1 | Ikenna available_at re-task batch acked (PM`b7e5bb6c`..`c761ff68`): sports-stamping Phase-1 todo flipped citing slot 4's MTDS`c186ecb` + 4 design Qs resolved; `ikenna-available-at-tab` absorbed slot 4's available_at P1 (per operator "harsh agent is stale") → slot 4 scope narrowed to bucket-name SSOT; defi #3 → Ikenna slot 5. `[main → slot 4]` + cross-side ack + LEDGER. |
| harsh_orchestrator + plans | (this commit) | 1 | v8 manifest schema slice (b) Phase 1.A/B/C shipped (Ikenna slot 6, UAC`174f401`+`d938a69`, PM`b0069ca3`) — relayed to Harsh slot 6 + cross-side ack. The handshake Harsh slot 6 was standing by for. |
| harsh_orchestrator + plans | (this commit) | 1 | defi_master Q1 ✅ resolved by Ikenna (3 priorities approved; #4 ASTER genesis UAC`77666c8`; defi_988 ~13,632 rows unblocked) — noted as unassigned carry-forward + cross-side ack (clarified today's slot 4 ≠ old vm-ops-tab) + flagged to operator. |
| harsh_orchestrator + plans | (this commit) | 1 | Q1.3 (4th of 4 QG-check FPs) ✅ FIXED by Ikenna @PM`d2a553ed` (base-service.sh deep-import whitelist `unified_api_contracts.internal`) — relayed to slot 2 (full-throttle on real-violation rows now) + flipped cleanup-plan A1 + LEDGER; cross-side ack. ALL 4 QG-check FPs resolved (Q1.1/Q1.2 Harsh slot 1, Q1.3/Q2 Ikenna). |
| harsh_orchestrator + plans | (this commit) | 1 | Q2 (4th QG-check FP) ✅ FIXED by Ikenna @PM`0407eb1a` (imports-inside-functions → AST) — relayed to slot 2 + flipped in cleanup-plan A2 + LEDGER; cross-side ack. All 4 QG-check FPs now: Q1.1/Q1.2 ✅ (Harsh slot 1), Q2 ✅ (Ikenna), Q1.3 pending-on-slot-2. |
| harsh_orchestrator + plans | (this commit) | 1 | Relayed Phase-0i resolution + session-1 ack to slot 4 (`[main → slot 4]`); cross-side-pinged Ikenna slot 3 (flip sports-stamping todo + answer 2 design Qs in mtds_sports_available_at_wiring); flagged slot-4 shippable units to slot 6; LEDGER. |
| harsh_orchestrator + plans | (this commit) | 1 | Ack'd Ikenna's 5 operator-decisions (PM`39ab61e5`): F3 ✅ option (b) (manifest_schema_final_gate canonical); EXPECTED_KNOWN_SOURCE_GAP ✅ Phase 1; P0-2 MDPS ✅ Phase 1 → routing ack'd (slot 5 = MDPS code fixes / slot 6's QG-AST-gate half already done @a4512ed3); case-D ✅ deferred post-cutover (Wave 3.M TBD); slot-worktree-QG-bug ✅ → per_agent_worktrees Phase 4.5. `[main → slot 5]` (P0-2 brief) + `[main → slot 6]` (resolutions) + wave3x_residual_ssots case-D note + LEDGER. |
| (extra-hands) | `6093b8c5` | — | Stale work-splits `work_split_2026_05_08_{harsh,ikenna}.md` archived `active/`→`archive/` (slot-1 P1 carryover, done by extra-hands); + banner audit + AWS region brief. |
| harsh_orchestrator + plans | (this commit) | 1 | (b)→(b+) supersession ack'd (Ikenna PM`2d6b131c`); slot-4 re-bootstrap `[main → slot 4]` ping ((b+) ~10-13 AI-day brief); slot-2 Phase 1.2 partial verified + Q2 (4th QG-check FP) ACKED → cross-side-pinged Ikenna; LEDGER slot 4 + slot 2 updated. |
| unified-trading-pm | `2cacb0eb`+(this) | 1 | Q1.1 + Q1.2 QG-check FP fixes (operator OK'd): `base-service.sh` print()-check excludes `**/cli/main.py`/`**/cli/_shim.py`/`**/__main__.py`; `check_schema_provenance.py` excludes `scripts/` (CLAUDE.md). Both PM-only, no rollout. Q1.3 (`unified_api_contracts.internal` deep-import flag) — offending check not found; routed back to slot 2 for the exact step output. `[main → slot 2]` + cross-side ping + A1 updated. |
| unified-trading-pm | (this commit) | 1 | Deconflict cross-side ping — Ikenna's Q4=(b)-propagation todo overlaps the Harsh-side half I already shipped @PM`7be8593a`; pinged him to rebase + reconcile/skip those (bucket_name_ssot Q4, code_freeze 2.6, work_split_harsh slot 4, slot-4 ping done by Harsh; his half = ikenna work-split slot 5 anti-seq, aws_migration AWS-side, codex docs, CLAUDE.md key rule). |
| unified-trading-pm | (this commit) | 1 | Q4 ✅ RESOLVED = (b) (Ikenna): bucket_name_ssot Q4 updated; code_freeze Phase 2.6 added (env-tiered bucket provisioning + data migration); `[main → slot 4]` ping — both slot-4 halves now actionable; LEDGER status. |
| unified-trading-pm | (this commit) | 1 | slot 2 Q1 (3 QG-check FPs) ANSWERED in `features_service_qg_cleanup` § Open questions; 3 QG-check fixes cross-side-pinged Ikenna; `[main → slot 4]` ping — Track E shipped so slot 4 can resume its sports-stamping half independent of Q4; LEDGER status. |
| unified-trading-pm + (workspace .tabs/) | (this commit) | 1 | Track D doc P0-1 owner pointer fixed (shipped by slot 6, not slot 5); filed `issues/slot_worktree_qg_repo_root_resolution_2026_05_11.md` + cross-side-pinged Ikenna; `.code-workspace` backfilled into all 6 slots (Ikenna action item); LEDGER slot 3 ✅ DONE + slot 6 status. |
| unified-trading-pm | (this commit) | 1 | NEW `features_service_qg_cleanup_2026_05_11.md` (QG-codex cleanup + full parity run [blocked_by code_freeze Phase 3] + F9 transfer; owner slot 2); slot 2 Q1 ✅ RESOLVED (A1 in features_repo_consolidation); Phase 4.6/6 annotated DEFERRED→successor; per-slot ping file bidirectional (`[main → slot N]` channel — README + AGENT_ONBOARDING + spawn prompts + CLAUDE.md updated). |
| features-service / UTL / unified-trading-pm | (slot 2) | 2 | features-svc Phase 4.1-4.5 verified + shipped (test files `c11cafcd`; UTL facade re-exports `e7975fe`; import-rewrite `a308a273` → 0 deep-import violations); Phase 7 checkbox flipped `[x]` (8 repos archived); F2 no-op / F6 Option C / F7 N/A confirmed (PM@`9d91b2f4`). |

_(Implementer slot DONE blocks land in each slot's plan-of-record body; this table is the cross-slot index.)_

---

## Daily reset (each morning)

Per CLAUDE.md "Daily Work-Split Process" § "Daily reset (each morning)" — see that section for the full protocol. In
short:

1. Fetch + summarise incoming commits (don't auto-pull).
2. Re-read yesterday's work-split + this ledger's "Today's status" + `harsh_orchestrator/pings/*.md` + cross-side `plans/active/_agent_pings.md` for overnight pings.
3. Daily ledger sweep — remove ✅ RESOLVED Q&As >24h old; verify no stale 🟡 BLOCKED >24h.
4. Draft today's work-split items (carryover + new emergence). Confirm `--init` slot count covers the day's themes.
5. Slot-reset sweep — for every slot whose theme changed from yesterday, `setup-tab-worktrees.sh --reset-slot <N>`.
6. Mirror today's slot↔theme table into this LEDGER's "Today's slot assignments".
7. Report to operator: "Today's plan = X, Y, Z. N items / M AI-days. Ping ledgers have K open. Local commits queued: J."
8. Wait for operator direction.

## Historical log

### 2026-05-08 (D2 — Model B morning 12 tabs / Model A afternoon 5 tabs)

5-tab afternoon cycle: 13 commits across 4 repos. Tab 1 instruments-live Predictions Phase 1 (`instruments-service@98bb167`
+ `b904785`) + plan-flip `7343b93`; Q1 resolved (manifest-layer re-bundling by canonical_question_group). Tab 2
features-consolidation Phase 0 pre-audit @`1de574b4` + Phase 1A UAC `FeatureFamily` @`7f63ca3` + Phase 1B UTL kwarg
@`c16cef3` + Phase 2A evidence `0c8800b8` + features-service skeleton @`1f2bc16` (later pushed @`d3d6e286`). Tab 3
deployment-UI Phase A foundation 5/5 (UAC@`ba94d05` LifecycleClass+CloudTarget+EnvironmentTier 43 tests; codex
deployment-ui-architecture.md @`ebe5cc09`; batch-live-symmetry UX section @`eb8a96ca`; vm_zombie_watchdog VmPrefixSpec
migration; plan-flips `4d6f2731`). Tab 4 vm-ops cefi sweeps #16-#40 + filed `issues/mdps_tradfi_silent_partial_drain_2026_05_08.md`
+ `971c7a1f`. Tab 5 mechanical-refactor: launcher_consolidation followup + data_status tests Wave 1+2 (119 tests) +
mtds_per_instrument chain axis + api_football flattening removal + cme_polymarket Phase 1. Morning Model B (12 tabs):
all ✅ DONE — folded into [`../plans/archive/work_split_2026_05_07.md`](../plans/archive/work_split_2026_05_07.md).
The data-loss event (Tab 5 `pull --rebase` auto-stash on shared dirty tree clobbered Tab 4 + main WIP, ~11:35-11:43 UTC)
drove the git HARD RULE + ultimately the per-tab worktree model. `work_split_2026_05_08_harsh.md` not yet archived
(slot 1 P1 carryover).

### 2026-05-10 (PM-side governance + Ikenna flotilla 290 commits)

PM-only governance hygiene sweep (13 commits: archived operator_decisions_2026_05_08 + 7 resolved issue docs + alerting
Q1 back-flip + manifest_v7 SUPERSEDED banner + launcher_consolidation flips). Ikenna's parallel-agent flotilla landed
~290 PM commits May 8→11 (271 docs / 10 feat / 7 fix / 2 chore): per-agent worktrees infra (4 feat); 3 new DeFi/audit
plans (`defi_catalogue_chain_primitives` / `defi_simulation_realism` / `cross_asset_group_catalogue_audit`); QG STEP
5.65 AST-walk removed-symbol detection; Telegram CI alert hardening; features-service consolidation Phase 7 closure.
Plus `mtds-utl-completion-tab` shipped UTL@`ef47c81b` `record_captured_from_counts` + MTDS@`a2f8d80` prediction bundle
finalize + MTDS@`4a00bd5` cefi available_at per-row stamping.

### 2026-05-07 (D1)

Folded into [`../plans/archive/work_split_2026_05_07.md`](../plans/archive/work_split_2026_05_07.md).

---

## Plan filename convention reminder

Use `.md` paths (no `.plan.md` segment) when referencing files in `plans/active/` or `plans/epics/`. `plans/archive/` +
`plans/ai/` continue to use `.plan.md` (frozen historical state). This LEDGER uses the `.md` paths consistently.

## Cross-references

- **Today's work-split**: [`../plans/active/work_split_2026_05_11_harsh.md`](../plans/active/work_split_2026_05_11_harsh.md)
  (6-slot assignment + cross-side handshakes + spawn prompts).
- **Companion (Ikenna side)**: [`../plans/active/work_split_2026_05_11_ikenna.md`](../plans/active/work_split_2026_05_11_ikenna.md).
- **Workflow rules + spawn-prompt template**: [`AGENT_ONBOARDING.md`](AGENT_ONBOARDING.md) (read first by spawned tabs).
- **Per-tab worktree model**: [`../codex/05-infrastructure/per-tab-worktrees.md`](../codex/05-infrastructure/per-tab-worktrees.md)
  + [`../codex/05-infrastructure/plan-aware-merge-resolution.md`](../codex/05-infrastructure/plan-aware-merge-resolution.md).
- **Workspace coding standards + Daily Work-Split Process spec**: [`../cursor-configs/CLAUDE.md`](../cursor-configs/CLAUDE.md).
- **Active pings**: [`harsh_orchestrator/pings/`](pings/) (intra-side, per-slot — see [`pings/README.md`](pings/README.md)) + [`_agent_pings.md`](_agent_pings.md) (transition stub) + [`../plans/active/_agent_pings.md`](../plans/active/_agent_pings.md) (cross-side).
- **Master plan**: [`../plans/active/master_to_live_defi_2026_05_23.md`](../plans/active/master_to_live_defi_2026_05_23.md).
- **Sequencing umbrella this cycle**: [`../plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md`](../plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md).
- **Spawned 2026-05-11**: [`../plans/active/features_service_qg_cleanup_2026_05_11.md`](../plans/active/features_service_qg_cleanup_2026_05_11.md) (successor for `features_repo_consolidation` Phase 4.6 + Phase 6 + F9; owner = slot 2).
- **Findings Triage Discipline**: CLAUDE.md § "Findings Triage Discipline (HARD RULE)".
- **Push discipline (conditional rule)**: CLAUDE.md § "CI Verification After Every Push (HARD RULE)" + "Daily Work-Split
  Process" § "Conditional push (the multi-agent safety valve)".
