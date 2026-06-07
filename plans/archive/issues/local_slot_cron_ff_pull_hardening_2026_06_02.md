---
title: Local slot-cron FF-pull hardening — stale top-level clones + ping-ledger FF-block
created: 2026-06-02
source:
  - plans/active/cicd_contract_hardening_2026_06_01.md
  - codex/05-infrastructure/per-tab-worktrees.md
  - "CLAUDE.md § Local slot host = VM slot host — symmetric worker model"
locked_by: live-defi-rollout
status: RESOLVED — ready to archive once acked
parent_epic: infrastructure_master
estimate_calibrated_ai_days: 0.4
estimate_class: infra
priority: P2
---

> **✅ RESOLVED 2026-06-02.** All three layers shipped + one-time sync executed. This doc records the problem +
> resolution for the audit trail; archive once the operator acks. The only residual is the source-elimination _operator
> decision_ which lives in the parent plan (`cicd_contract_hardening_2026_06_01.md` line ~469), not here.

## What I found

The FF-pull cron (`scripts/dev/slot-cron-ff-pull.sh`, `--all-slots`) already walks **every** repo — the `.tabs/N` slot
worktrees **and** the top-level (non-tab) base clones (via `main_workspace="$(dirname "${tabs_root}")"`). So top-level
coverage was never the gap.

The real reason top-level base clones drift stale is that FF-pull (correctly) **skips on genuine tracked-dirty**, and
two classes of dirt legitimately accumulate there:

1. **Generated artifacts** — `WORKSPACE_MANIFEST_DAG.svg`, `DATA_FLOW_DAG.svg`, and `ci_status`-only churn inside
   `workspace-manifest.json`. Disposable locally; CI is authoritative.
2. **Agent ping ledgers** — `ikenna_orchestrator/_agent_pings.md`, `harsh_orchestrator/_agent_pings.md`,
   `plans/active/_agent_pings.md`. Append-only **real cross-agent data** — must NOT be discarded.

The top-level PM clone (the clone the operator's crontab actually runs the script _from_) had drifted **1164 commits
behind** + dirty on the ping ledgers (~575 uncommitted lines each) + 2 stale cursor-config edits. Because nothing
auto-flushed the pings, the cron `[skip:dirty]`'d the clone every cycle → stale forever → and since the cron _script
itself_ lives in that clone, the cron was running **1164-commits-old logic**.

**AWS orchestrator VMs share the same class:** `pm-pull-ff.sh` (Linux) already auto-drops the regen artifacts, but a VM
dirty on its ping ledgers (the orchestrator writes them) would `[skip]` and go stale just the same.

## Why it matters

- The cron's home clone going stale = the cron runs old logic on **every** slot it pulls.
- Symmetric-host model (CLAUDE.md) requires every host — operator laptop (macOS), Harsh laptop (Linux), VMs (Linux) — to
  stay current off the same shared script. A stale clone breaks that invariant silently.
- Manual `commit+push` toil every time the manifest/DAG/pings go dirty.

## Resolution (all shipped 2026-06-02)

| #   | Fix                                                                                                                                                                                                                                                                                                                                                                                                                                | Evidence                       |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------ |
| 1   | **Regen auto-discard** in `slot-cron-ff-pull.sh` — drops the SVGs unconditionally + `workspace-manifest.json` only when the diff is `ci_status`-only (CI-authoritative). Mirrors the VM's `pm-pull-ff.sh` (closes the prior local-vs-VM asymmetry).                                                                                                                                                                                | `unified-trading-pm@9ed004d5f` |
| 2   | **Ping-ledger auto-flush** — when the only remaining dirt is `_agent_pings.md` ledgers, commit + push them (tree clean → FF proceeds). Scoped to PM **on the integration branch only** (never a slot tab branch — would leak tab commits to LDR); rebase-retry handles push races; conflict aborts cleanly (no mid-rebase, no data loss).                                                                                          | `unified-trading-pm@85c8f9eed` |
| 3   | **One-time top-level base-clone sync** — all 24 top-level clones brought onto `live-defi-rollout`, behind=0. Stale dirt stashed recoverably (`pre-ldr-sync-2026-06-02` in alerting-service, e2e-testing, features-service, system-integration-tests, unified-trading-pm). `batch-live-reconciliation-service`'s one unpushed (superseded, conflicting) QG-fix commit preserved as branch `ldr-sync-recovery-ab4b25a` before reset. | one-time op, 2026-06-02        |

Cross-platform: the fixes use only portable `git`/`grep -E`/`awk` (no `sed -i`) → identical on macOS (operator) and
Linux (Harsh + VMs).

## Recommended decision (residual — lives in parent plan, not here)

- **Source-elimination** (untrack the SVGs + regenerate on demand; move mutable `ci_status` to a sidecar file outside
  `workspace-manifest.json`) remains a `BLOCKED-OPERATOR-DECISION` block in `cicd_contract_hardening_2026_06_01.md`. The
  self-heal layers above make this cleanup-not-blocker.
- **AWS VMs**: spot-check each VM stays current after a deploy via
  `bash unified-trading-pm/scripts/verify-slot-host-symmetry.sh` + `tail /tmp/slot-cron-ff-pull.log`; the ping-flush
  reaches them automatically once their PM clone pulls past `85c8f9eed`.
