---
title: Harsh slot-1 day master — 2026-06-02 (context hygiene · v9 verify · orchestrator e2e · ops verify)
parent_epic: plan_hygiene_master
priority: P1
status: active
execution_scope: local-only
estimate_class: infra
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 1.6
created: 2026-06-02
locked_by: live-defi-rollout
locked_since: 2026-06-02
related_plans:
  - plans/active/agent_context_and_memory_hygiene_2026_06_02.md
  - plans/active/agent_orchestrator_e2e_workflow_and_execution_scope_2026_06_02.md
  - plans/active/quality_gates_resource_contention_speedup_2026_06_02.md
  - plans/active/cicd_contract_hardening_2026_06_01.md
  - plans/active/issues/deployment_scripts_bucket_softdelete_log_churn_2026_06_01.md
  - plans/archive/issues/orchestrator_autonomy_residual_findings_2026_06_02.md
  - plans/epics/orchestrator_master.md
  - plans/active/defi_manifest_canonicalisation_2026_06_01.md
  - plans/active/instruments_manifest_canonicalisation_2026_06_01.md
  - plans/active/downstream_services_manifest_canonicalisation_2026_06_01.md
---

# Harsh slot-1 day master — 2026-06-02

Coordination tracker for today's Harsh-side work, distilled from the Harsh↔Ikenna chat (chat-20260602.md) + Harsh's
asks. Indexes 6 workstreams; net-new work has its own plan, the rest point to their owning plan. Slot-1 owns this
tracker; do **not** duplicate the owning plans' checkboxes here — track today's gate only. `execution_scope: local-only`
(this is operator coordination, not agent-dispatchable work — see workstream C / G1).

## ⚠️ Critical framing (read before starting B)

**The migration is NOT complete.** Current open/done across the per-asset-group canonicalisation plans (origin state,
2026-06-02): defi 26✓/50○ · cefi 6/14 · tradfi 6/16 · prediction 5/16 · sports 28/25 · instruments 2/11 · downstream
20/16. So Harsh's ask "re-verify all manifests are on v9 **once migration completed**" is **premature as a
completion-verify** — today it is an **audit + unblock**, exactly as Ikenna framed it ("audit that IS/MTDS are FULLY
done … otherwise you're just going to end up redoing it").

**Likely blocker (confirm, don't assume):** canonical-migration VMs reportedly failed when the pinned `mtds-code@<sha>`
tarball was pruned before pull. That is a tarball-lifecycle problem — the same family as D's P0 (no `deployment-service`
image → the tarball-cleanup job can't run). So **B's runnability is coupled to the tarball/image work in D**; B-P0 below
confirms the exact blocker before concluding "gated."

## Workstream dashboard

| #   | Workstream                                   | Owning plan                                                    | Status (✓/○) | Today's gate                                                  | Doable now?      |
| --- | -------------------------------------------- | -------------------------------------------------------------- | ------------ | ------------------------------------------------------------- | ---------------- |
| A   | Context + memory hygiene                     | `agent_context_and_memory_hygiene_2026_06_02.md` (NEW)         | 0/14         | CLAUDE.md ≤400L, 0 contradictions, memory pruned              | ✅ yes           |
| B   | v9 manifest verify + downstream readiness    | per-AG canonicalisation plans                                  | in-flight    | audit IS/MTDS done-state; do NOT run blind                    | ⚠️ audit-only    |
| C   | Orchestrator e2e + execution-scope field     | `agent_orchestrator_e2e_workflow_and_execution_scope…md` (NEW) | done¹        | run e2e_demo.py + spec+wire `execution_scope` (P0)            | ✅ yes           |
| D   | GCS soft-delete log churn + bucket policy    | `deployment_scripts_bucket_softdelete_log_churn_2026_06_01.md` | 3/5          | verify shrink + ship container-image P0 + secondary offenders | ✅ yes           |
| E   | QG resource/speedup + worker-VM right-sizing | `quality_gates_resource_contention_speedup_2026_06_02.md`      | 0/12         | governor + slot-aware pytest + per-repo baseline → VM-size    | ✅ yes           |
| F   | CI/CD hardening                              | `cicd_contract_hardening_2026_06_01.md`                        | 78/18        | clear LDR v2 RED gates as encountered                         | ✅ opportunistic |

¹ orchestrator code shipped (4 plans, 51✓/0○); **F1/F2/FM3 residuals RESOLVED + archived 2026-06-02** — see
`archive/issues/orchestrator_autonomy_residual_findings_2026_06_02.md`.

---

## A — Agent context + memory hygiene _(Harsh ask #1 + chat 56–59, 88)_

Owning plan: [agent_context_and_memory_hygiene_2026_06_02.md](agent_context_and_memory_hygiene_2026_06_02.md). Measured:
CLAUDE.md 1179L/84KB (3× over its own budget), `.claude/rules/CLAUDE.md` 737L/43KB (suspected stale dup), memory 42
files/188KB. Phase 3 now also carries the **merge-flow doc drift** (C3) as instance (e). **Full-execution criterion:**
see owning plan.

- [ ] [DOC] P0. Execute Phases 1–3 of the owning plan (map feed graph → trim CLAUDE.md → contradiction sweep incl. C3).
- [ ] [DOC] P1. Execute Phases 4–6 (SUB_AGENT drift, memory prune, .mdc relevance).

## B — v9 manifest verification + downstream readiness _(Harsh ask #2 + chat 20)_

Tracked here; substance lives in the per-AG canonicalisation plans + `downstream_services_manifest_canonicalisation`.
**Do not author a duplicate plan.** Verify-script: `market-tick-data-service/.../scripts/audit_canonical_form.py`
(CF-1…CF-12 per bucket). **Gate: audit done-state FIRST, then sample — never run MDPS/features blind.**

- [ ] [SCRIPT] P0. Audit current done-state of IS + MTDS canonicalisation against **origin** (not local) — confirm
      whether the C0 single-walk runs actually completed per AG, or are still open/blocked. Output a per-AG ✓/○/blocked
      grid.
- [ ] [SCRIPT] P0. Resolve the tarball/L0 blocker dependency (see D) — is the migration runnable today, or waiting on
      the deployment-service container image? State the answer explicitly; if blocked, B's verify waits on D.
- [ ] [SCRIPT] P1. For AGs where migration IS done: run `audit_canonical_form.py` across that AG's canonical bucket(s);
      confirm manifest schema = v9. Empty buckets legitimately have no manifest — enumerate which, so "no manifest" is
      distinguishable from "missing manifest". (No central bucket registry found → build the expected-bucket list from
      `deployment-service/configs/cloud-providers.yaml` + the per-AG plans.)
- [ ] [SCRIPT] P1. Sanity (not blind-run) the MDPS + features-service downstream todos in
      `downstream_services_manifest_canonicalisation` — verify live=batch dep-check + v9-schema asserts; run only on AGs
      whose upstream is migrated, sampling across data_types/venues/AGs (per Harsh's standing approach).

## C — Orchestrator e2e + execution-scope field _(Harsh ask #3 + chat 39–48, 89)_

Owning plan:
[agent_orchestrator_e2e_workflow_and_execution_scope_2026_06_02.md](agent_orchestrator_e2e_workflow_and_execution_scope_2026_06_02.md)
(NEW). Flow **verified against code 2026-06-02**: quickmerge→staging→SIT→main→CICD is **live**; assignment is automated;
discovery is **polling** (G2 — Harsh-owned, will confirm interval). The orchestrator-vs-local field **does not exist
yet** (only `assigned_vm`; absent ⇒ picked up globally) → that's **G1 (P0)**, the field Harsh asked for. AO-on-`main` is
resolved/codified — no action. Fleet currently consolidated to **2 running VMs** (9 epic VMs stopped) → low risk that
pushing today's plans auto-dispatches; the `execution_scope: local-only` stamps make it safe once G1 lands.

- [ ] [DESIGN] P0. Spec `execution_scope` in PLAN_FORMAT + wire it into `regen_backlog_from_plan.py` (owning plan G1).
- [ ] [TEST] P1. Run `e2e_demo.py` + `dev.sh --mock` locally; capture pass/fail (owning plan G4).

## D — GCS soft-delete log churn + bucket policy _(Ikenna handoff #1 + Harsh ask #2-bucket-policy + chat 22–37)_

Owning plan:
[deployment_scripts_bucket_softdelete_log_churn_2026_06_01.md](issues/deployment_scripts_bucket_softdelete_log_churn_2026_06_01.md)
(3✓/5○). Harsh's "verify no soft-delete / retention **across the bucket(s)**" is **largely already done**: the
cross-bucket soft-delete + versioning audit RAN 2026-06-02 (295 buckets) — deployment-scripts ages out ~06-08, TF-state

- strategy-store are intentional versioning, 3 secondary offenders (~1.2 TiB) tracked. Remaining:

* [ ] [SCRIPT] P0. Verify the policy held + bytes shrinking: `retentionDurationSeconds==0` + `gcs_bucket_stats.py` shows
      deployment-scripts 57,516 → ~66 GiB by ~06-08 (Cloud Monitoring totals, not `du`).
* [ ] [INFRA] P0. Ship the owning plan's P0 — build + publish the `deployment-service` container image (root cause of
      the dead tarball-cleanup job; same tarball-lifecycle family as B's migration blocker).
* [ ] [INFRA] P1. Fix the secondary offenders (instruments-store-sports soft-delete churn; client-reporting-data
      noncurrent versioning) + schedule `cleanup_old_tarballs.py`.

## E — QG resource/speedup + worker-VM right-sizing _(Ikenna handoff #2 + Harsh asks #1+#3 + chat 60)_

Owning plan:
[quality_gates_resource_contention_speedup_2026_06_02.md](quality_gates_resource_contention_speedup_2026_06_02.md)
(0✓/12○). Fix = **do-less-work + cross-slot governance, NOT more parallelism** (matches Ikenna). Now also carries
Harsh's per-repo baseline (ask #3) + worker-VM right-sizing (ask #1).

- [ ] [SCRIPT] P0. Governor (`QG_HOST_CONCURRENCY`) + slot-aware `pytest -n` + aggregate-load benchmark (owning todos
      qg-governor / qg-slot-aware-workers / qg-bench-aggregate).
- [ ] [SCRIPT] P0. Per-repo QG baseline — time/CPU/RAM, **local + on an AWS worker VM** → committed baseline file + a 2×
      deviation guard (ask #3; owning todo qg-perrepo-baseline).
- [ ] [INFRA] P1. Worker-VM right-sizing, **data-driven off the baseline**: current AWS `m7i.xlarge` (4 vCPU/16 GB × 8
      slots) is OOM-prone; decide machine type + slots-per-VM together vs Harsh's ~64 GB/8 vCPU hypothesis (ask #1;
      owning todo qg-vm-rightsizing).

## F — CI/CD hardening _(Ikenna handoff #3 — opportunistic)_

Owning plan: [cicd_contract_hardening_2026_06_01.md](cicd_contract_hardening_2026_06_01.md) (78✓/18○). Pick up RED v2
gates as encountered while working other streams (UTL bucket-naming test, coverage-floor=0 on a few repos). Don't make
this the day's focus — it churns as Ikenna adjusts pre-migration code.

- [ ] [TEST] P2. As encountered: fix LDR `quality-gates-v2` RED gates that block my own pushes; log the rest in the
      owning plan, don't sweep.

---

## Coordination + discipline

- **Conditional push** before each push: `git fetch` → 0 incoming → push; any incoming → STOP, document 🟡, ping.
- **Commit + push + flip checkbox** same agent turn per shippable unit (the #1 wasted-reallocation source).
- **Order today:** A (no infra dep) ∥ **D-P0 image** (unblocks B + the dead cleanup job) → B audit → E baseline+governor
  → C (spec `execution_scope` + e2e). F opportunistic.
- Ikenna explicitly advised **against** ad-hoc plans (data-status UI etc.) today — stay on these 6.

## Full-execution criterion (PLAN_FORMAT §8)

Day is "run to completion" when: A's owning plan hits its full-execution criterion (incl. C3 merge-flow doc drift); B
has a published per-AG v9 done/blocked grid + (for migrated AGs) a passing `audit_canonical_form.py` run; C's e2e_demo
passes + `execution_scope` is specced and wired (G1); D's soft-delete is verified shrinking + container image published

- secondary offenders fixed; E's governor is landed + benchmarked + per-repo baseline committed + VM-size decided.
  Anything not finished is left as a `- [ ]` in its owning plan (not lost in chat), with status noted here.
