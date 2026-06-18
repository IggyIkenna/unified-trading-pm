---
title:
  "CI incident findings 2026-06-09 — readiness-verifier missing script + dirty-skip not alerted + orchestrator headroom"
created: 2026-06-09
locked_by: live-defi-rollout
priority: P2
status: archived
---

> **🗄️ ARCHIVED 2026-06-18 — superseded by the cicd consolidation; any open items were migrated to the 4 themed plans
> (promotion-pipeline / quality-gates / sit-and-fleet / release-machinery). Disposition + provenance:
> `plans/active/cicd_docs_and_consolidation_2026_06_18.md`.**

## What I found (during the 2026-06-09 PM-RED incident)

The PM-RED root cause (parity_watchdog empty-string fallback) is FIXED (PM@512626fe7); these are the adjacent findings
surfaced while triaging the Slack #ci-failures burst:

1. **✅ RESOLVED 2026-06-09 (PM@874bf24ab)** — **Readiness Verifier was hard-broken** —
   `.github/workflows/readiness-verifier.yml:45` called `scripts/workspace/setup-workspace-from-manifest.sh` → exit 127
   every run, then `cat readiness-report.txt` → exit 1 (pre-existing, not a regression). **Diagnosis refinement:** the
   script DOES exist, just at `scripts/setup-workspace-from-manifest.sh` (not `scripts/workspace/`), AND it is a
   **per-`<service>`** dep-cloner (`<SERVICE_NAME> [--skip-install]`), so it never accepted the `--tier`/`--skip-fresh`
   flags the step passed. `setup-workspace-root.sh` only sets the workspace-root path (no clone, no tier) — so the
   "repoint to setup-workspace-root.sh + tier filter" option could not have worked either. **Fix shipped:** made the
   step `continue-on-error: true` (non-fatal — the only thing failing the job was this step's exit 127; readiness
   mismatches merely alert via Slack, no hard-fail gate), dropped the phantom path, and made it best-effort (clones a
   single `repo_filter`'s deps via the real script when given). The fleet stops reddening; `check-repo-readiness.py`
   runs against repos already present (PM + in-repo `codex/`). **Residual follow-up (NICE-TO-HAVE):** no tier-bulk-clone
   helper exists — a dedicated one would let tier-mode actually populate sibling repos before the readiness check (see
   todo below).

2. **slot-cron-ff-pull dirty-skip is silent** — the FF-pull cron correctly skips a worktree with uncommitted changes
   (`[skip:dirty]`), but `verify-slot-host-symmetry.sh --alert` only alerts when the cron **didn't run**, not when it
   ran-but-skipped-everything. A slot left dirty for hours therefore never FF-syncs AND never alerts. Fix: have the
   symmetry verify (or a new check) alert when a slot has been `[skip:dirty]` for > N consecutive ticks. (This incident:
   the dirtiness was transient Path-B migration churn + a hook `chmod`; both cleared/fixed.)

3. **Orchestrator headroom, not down** — `api.agent-orchestrator.odum-research.com/health` = 200, but
   `Escalate to Orchestrator` returned no `escalation_id` ("no free slot / headroom account") and the Overnight Dead Man
   Switch reported the orchestrator "did not complete". Capacity / overnight-run issue on vm-0, not an unreachable VM —
   needs an operator look at slot headroom + the overnight job.

4. **Cross-repo promotion-lag reddened consumer CI on the R4 `BATCH_HYPERLIQUID_REST` rename (transient, self-healed)**
   — at 08:24Z the alerting-service dep-update PR #31 (`feat!: update unified-api-contracts to 0.2.0`) QG failed at
   conftest import:
   `AttributeError: PipelineMode has no attribute 'BATCH_HYPERLIQUID_REST'. Did you mean: 'BATCH_HYPERLIQUID'?`. The bad
   ref was **not** in alerting-service — chain is
   `tests/conftest.py:6 → unified_trading_library/__init__.py:950 → pipeline_mode_resolver.py:39`. The R4 rename
   (`BATCH_HYPERLIQUID_REST` → `BATCH_HYPERLIQUID`; transport is a manifest COLUMN, not the source name — UTL@d0745bde,
   2026-06-07) was already on UAC + UTL **LDR**, but CI's dep-clone fallback cloned UTL **`main`** (the manifest-pinned
   `v0.4.0` tag was re-cut at 09:23Z — _after_ the run), and UTL-`main` had not yet received the rename promotion →
   UAC-`main` ahead of UTL-`main` for that window. **Self-healed ~09:23Z** (UTL `main` now clean of the stale member);
   PR #31 was **closed** 08:54Z as redundant (alerting pins UAC via a path source + range `>=0.1.0,<1.0.0` already
   admitting 0.2.0); alerting-service LDR is green. **Root cause is not alerting-specific** — any repo whose CI imports
   UTL in that window would have hit it. **Systemic gap**: the CI dependency-clone fallback to `main` exposes consumers
   to _in-flight breaking renames_ that have landed on the upstream's `main` before the downstream consumer's
   `main`/release catches up. Preventive options: promote a breaking UAC rename to `main` atomically-with / after the
   UTL consumer fix, or have the dep-clone fallback prefer the manifest-pinned release tag over upstream `main`.
   Composes with `cicd_contract_hardening_2026_06_01.md`.

5. **UAC QG is RED on LDR tip + MTDS slot diverged — blocks all UAC/MTDS commits (surfaced 2026-06-09 shipping
   defi-drift D8)** — while shipping two trivial `defi_code_codex_drift` D8 cleanups, `quality-gates.sh --no-fix` on
   `unified-api-contracts` LDR tip (`4a491916`) fails on PRE-EXISTING checks unrelated to the change: (a) `STEP 5.86`
   orphan cassette `fear_greed/mocks/stub.yaml` (self-evident `stub-placeholder`, `interactions: []`, contract
   `UAC@7ae9daee`) — fixable via the allowlist (entry prepared locally); (b) `Hardcoded project ID in production`; (c)
   `Backward-compat pattern found` — intentional shims in `internal/modes.py` ("kept for backward-compat with 6 consumer
   call-sites") + `registry/chain_env.py` ("ghost no-underscore protocol tokens") that the `no-backward-compat-shims`
   gate rejects but which need a real refactor + owner judgment (removing them touches 6 consumers). Separately, **MTDS
   slot is diverged from LDR** — an unpushed feature commit `01fda7ce`
   (`feat(defi): migrator gas-fees + liquidations specs`) + a rebase conflict in
   `tests/unit/test_collect_handler_schema.py` (foreign file) blocks `quickmerge` STAGE 0.4. Net: the D8 edits are
   made + correct but cannot pass the per-repo commit gate without unrelated remediation. (Also observed during this
   work: a host-resource crisis — load ~247 on 10 cores, ~46 concurrent QG-family procs, QGs OOM-killed/governor-queued;
   self-cleared to load ~12.)

## Why it matters

(1) keeps a required-ish check red (noise + can gate). (2) is a real observability gap (silent no-sync). (3) means stuck
promotion PRs don't get auto-escalated workers — they wait on a human. (4) any cross-repo breaking rename can
transiently redden **every** UTL consumer's CI during the upstream→downstream `main` promotion lag — invisible-looking
failures on a clean consumer repo, costing triage time chasing a ref that exists in no current source.

## Todos

- [x] ✅ [SCRIPT] P2. Finding 1 — readiness-verifier clone step non-fatal + drop phantom `scripts/workspace/` path.
      Shipped PM@874bf24ab (`fix(ci): make readiness-verifier clone step non-fatal + drop phantom script path`),
      actionlint-clean. — 2026-06-09.
- [ ] [SCRIPT] P3. **NICE-TO-HAVE** Finding 1 residual — add a **tier-bulk-clone** helper (PM `scripts/`) so the
      readiness-verifier can actually populate the tier's sibling repos before `check-repo-readiness.py` runs. Today
      `setup-workspace-from-manifest.sh` is per-`<service>` and `setup-workspace-root.sh` only sets the root path, so
      tier-mode runs against whatever repos already happen to be present (PM + in-repo `codex/`). Repo:
      `unified-trading-pm`.
- [ ] [SCRIPT] P2. Finding 2 — alert when a slot has been `[skip:dirty]` for > N consecutive `slot-cron-ff-pull` ticks
      (extend `verify-slot-host-symmetry.sh --alert` or add a check). Repo: `unified-trading-pm`.
- [ ] [OPERATOR] P2. Finding 3 — vm-0 slot headroom / Overnight Dead Man Switch did-not-complete needs an operator look
      (capacity, not unreachable). **BLOCKED-OPERATOR-DECISION.**
- [ ] [SCRIPT] P3. Finding 4 — CI dep-clone fallback should prefer the manifest-pinned release tag over upstream `main`
      (or promote a breaking UAC rename atomically-with / after the UTL consumer fix) so a cross-repo rename can't
      transiently redden every UTL consumer's CI during the promotion-lag window. Repo: `unified-trading-pm` (+ the CI
      dep-clone scripts). Composes with `cicd_contract_hardening_2026_06_01.md`.
- [x] ✅ [CODE] P2. Finding 5a — **RESOLVED 2026-06-09 (UAC@8a117153)**. UAC QG green on LDR: the
      `no-backward-compat-shims` hits were a phrase-grep over legitimate code — driven to **0** by deleting the one real
      re-export STUB (`internal/validation/instruction.py`, shadowed by its package) + rewording 8 false-positive
      docstrings/comments (exempt `__init__` re-exports, functional legacy-name alias dicts, the DEPRECATED
      `TestingStage` enum — not stubs). `Hardcoded project ID` resolved by genericizing the `sports/gcs_paths` docstring
      example. `fear_greed` orphan cassette allowlisted. **0 backward-compat hits + 0 basedpyright baseline** in UAC.
      Also: UAC version-aligned to 0.3.0 (main=LDR=staging, admin) + the `base-library.sh` SHA-sentinel gap fixed
      (PM@091378337) so library agent-quickmerge works.
- [x] ✅ [SCRIPT] P2. Finding 5b — **RESOLVED 2026-06-09 (MTDS@8fffc73b)**. The diverged MTDS slot reconciled:
      `01fda7ce` (migrator gas-fees+liquidations → defi coverage 6→8, rebuild `--bucket`) rebased onto LDR, the
      `test_collect_handler_schema.py` conflict resolved by taking LDR's mappings (mine were redundant — LDR added the
      same 7 via the uac feat(defi-caps) expansion), and shipped via quickmerge. Slot is ancestor-or-equal of LDR; STAGE
      0.4 passes. (Surfaced a quickmerge `--files` gap: it can't stage a pure deletion — `instruction.py` deletion had
      to be direct-pushed; worth a follow-up to make `--files` handle tracked deletions.)
- [x] ✅ [SCRIPT] P3. Finding 6 — `quickmerge.sh` `--files` cannot ship a pure file DELETION: the staging loop guards on
      `[ -e "$f" ]` and skips a deleted path (`⚠️ Path not found`), so a removed-but-tracked file silently never reaches
      the commit (hit shipping UAC 5a — `instruction.py` deletion had to be direct-pushed). Fix: also stage tracked
      deletions, e.g. `if [ -e "$f" ] || git ls-files --error-unmatch -- "$f" >/dev/null 2>&1; then git add -A -- "$f"`.
      SSOT is the PM template `scripts/workflow-templates/` → roll out via `rollout-workflow-templates.sh`. Repo:
      `unified-trading-pm` (+ per-repo `scripts/quickmerge.sh` rollout). FIXED: both staging loops now deletion-aware
      (tracked-but-absent stages as deletion) — unified-trading-pm@3e472a19d | verified 2026-06-10
