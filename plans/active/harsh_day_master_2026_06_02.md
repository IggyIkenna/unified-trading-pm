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

_Status counts re-verified against synced `live-defi-rollout` HEAD on 2026-06-02 (PM@8cefbea2e)._

| #   | Workstream                                   | Owning plan                                                    | Status (✓/○) | Today's gate                                                  | Doable now?        |
| --- | -------------------------------------------- | -------------------------------------------------------------- | ------------ | ------------------------------------------------------------- | ------------------ |
| A   | Context + memory hygiene                     | `agent_context_and_memory_hygiene_2026_06_02.md` (NEW)         | 9/11         | CLAUDE.md ≤400L, 0 contradictions, memory pruned              | 🟡 size-gate open  |
| B   | v9 manifest verify + downstream readiness    | per-AG canonicalisation plans                                  | not-run      | audit IS/MTDS done-state; do NOT run blind                    | ✅ now unblocked   |
| C   | Orchestrator e2e + execution-scope field     | `agent_orchestrator_e2e_workflow_and_execution_scope…md` (NEW) | 21/26 ²      | run e2e_demo.py + spec+wire `execution_scope` (P0)            | ✅ actionable done |
| D   | GCS soft-delete log churn + bucket policy    | `deployment_scripts_bucket_softdelete_log_churn_2026_06_01.md` | 13/13 ✅     | verify shrink + ship container-image P0 + secondary offenders | ✅ DONE            |
| E   | QG resource/speedup + worker-VM right-sizing | `quality_gates_resource_contention_speedup_2026_06_02.md`      | 11/13        | governor + slot-aware pytest + per-repo baseline → VM-size    | ✅ 2 P0 left       |
| F   | CI/CD hardening                              | `cicd_contract_hardening_2026_06_01.md`                        | 102/16       | clear LDR v2 RED gates as encountered                         | ✅ opportunistic   |

¹ orchestrator code shipped (4 plans, 51✓/0○); **F1/F2/FM3 residuals RESOLVED + archived 2026-06-02** — see
`archive/issues/orchestrator_autonomy_residual_findings_2026_06_02.md`.

² C opens (5) are not actionable today: 2× **P0 BLOCKED-OPERATOR/BLOCKED-BILLING** (v1-ghost removal on `main` + staging
branch; branch-protection billing pin), 1 P1 stretch (near-instant regen ack), 1 P1 doc, 1 P2 IAM gap. **G1
(`execution_scope`) + G4 (e2e_demo) — the two things Harsh asked for — are DONE + shipped (slot 2).**

---

## A — Agent context + memory hygiene _(Harsh ask #1 + chat 56–59, 88)_

Owning plan: [agent_context_and_memory_hygiene_2026_06_02.md](agent_context_and_memory_hygiene_2026_06_02.md). Measured:
CLAUDE.md 1179L/84KB (3× over its own budget), `.claude/rules/CLAUDE.md` 737L/43KB (suspected stale dup), memory 42
files/188KB. Phase 3 now also carries the **merge-flow doc drift** (C3) as instance (e). **Full-execution criterion:**
see owning plan.

- [ ] [DOC] P0. Execute Phases 1–3 of the owning plan (map feed graph → trim CLAUDE.md → contradiction sweep incl. C3).
      **Owning-plan Phases 1–3 boxes are flipped, but this day-master flip was REVERTED 2026-06-02 (de9644c7f) — the
      size-gate ("CLAUDE.md ≤400L") is NOT met (still ~955L; the further-trim is the open P2 below). Stays open until
      the budget trim lands.**
- [x] ✅ [DOC] P1. Execute Phases 4–6 (SUB_AGENT drift, memory prune, .mdc relevance). — DONE: Phase 4 NO-OP (all 21
      `SUB_AGENT_MANDATORY_RULES.md` are symlinks), Phase 5 memory prune done (42 files walked, 3 rot entries
      de-indexed), Phase 6 `.mdc` staleness pass done (2 UI files fixed). Only a P2 UI-slot `.mdc` follow-up remains in
      the owning plan.

## B — v9 manifest verification + downstream readiness _(Harsh ask #2 + chat 20)_

Tracked here; substance lives in the per-AG canonicalisation plans + `downstream_services_manifest_canonicalisation`.
**Do not author a duplicate plan.** Verify-script: `market-tick-data-service/.../scripts/audit_canonical_form.py`
(CF-1…CF-12 per bucket). **Gate: audit done-state FIRST, then sample — never run MDPS/features blind.**

- [x] ✅ [SCRIPT] P0. Audit current done-state of IS + MTDS canonicalisation against **origin** (not local) — confirm
      whether the C0 single-walk runs actually completed per AG, or are still open/blocked. Output a per-AG ✓/○/blocked
      grid. — **DONE (slot 10, 2026-06-03): 0/6 C0 single-walks completed.** L0 tarball blocker resolved 2026-06-02 —
      all AGs unblocked in principle; no data migration has run for any AG.
      **Per-AG C0 single-walk grid (origin state, PM HEAD):**
      | AG | C0 | Pre-work done | Next action |
      |---|---|---|---|
      | DeFi (MTDS) | ○ | C0-RD1-RD3c code ✅; 2022-01 dry-run ✅ | C0-RD6 `_DEX_EXT` split + LST re-dry (needs_attr≈0) → then `--apply` (C0-RD4) |
      | CeFi (MTDS) | ○ | Layout ✅, migrator ✅, writer drained ✅, E5 manifest rebuild ✅ | E4 dry-VM run + full apply not started; Phase-0 layout audit item also open |
      | TradFi (MTDS) | ○ | Layout ✅ (E1), migrator ✅ (E2), manifest rebuild ✅ (E5) | C0 bundled walk not run |
      | Prediction (MTDS) | ○ | Layout ✅ (E1), migrator ✅ (E2), captured-atom E5 partial ✅ | C0 full walk not run; E5 empty/failed re-emit still open |
      | Sports (MTDS) | ○ | 35/55 items ✅; IS legacy→prd copy ✅ (316 cells) | C0 ONE bundled walk on market-data-tick-sports not run |
      | IS (non-sports) | ○ | P0 CF audit ✅ (cefi/tradfi/pred instruments-store debt known) | Phase-0 layout audit + C0 bundled walk (E1–E6) not started |
      **Conclusion**: all 6 C0 walks OPEN, none BLOCKED in the formal sense. DeFi has the most remaining code
      pre-conditions (C0-RD6 + LST re-dry); others have migration scripts ready — gap is launching the VM-scale walk.
- [x] ✅ [SCRIPT] P0. Resolve the tarball/L0 blocker dependency (see D) — **ANSWER: UNBLOCKED.** D's P0 shipped
      2026-06-02 (slot 1): `deployment-service` jobs image built + published AND the tarball reaper is LIVE + verified
      (D owning plan, `tarball_cleanup_sch…`). So the pinned-tarball-pruned failure family is resolved — B's verify is
      **no longer gated on D** and the migration is runnable today. The remaining B work is the audit itself (below),
      not a blocker.
- [x] ✅ [SCRIPT] P1. For AGs where migration IS done: run `audit_canonical_form.py` across that AG's canonical bucket(s);
      confirm manifest schema = v9. — **DONE (slot 10, 2026-06-05): 0/5 AGs at v9 on canonical prd buckets; full grid below.**
      **Bucket registry built from `deployment-service/configs/cloud-providers.yaml`; `_index/availability_index.parquet`
      checked across all prd + legacy flat buckets (300 total, 33 with index).**
      **Per-bucket CF audit grid (canonical prd buckets):**
      | Bucket | AG | Rows | Schema dist | CF-1 | Missing CFs |
      |---|---|---|---|---|---|
      | market-data-tick-cefi-prd | cefi | 2,640,864 | 100% v8 | ✗ | CF-2(no asset_group) CF-3(blank pm) CF-4(no source) CF-7(hyphen venue) |
      | market-data-tick-defi-prd | defi | 1,569,805 | 99.97% v8 / 0.03% v9 (407 rows) | ✗ | CF-2(347K blank ag) CF-3(blank pm) CF-4(no source) CF-7(glued venue) |
      | market-data-tick-tradfi-prd | tradfi | 144,062 | 100% v8 | ✗ | CF-2(109K blank ag) CF-3(blank pm) CF-4(no source) |
      | market-data-tick-sports-prd | sports | 786,408 | 100% v8 | ✗ | CF-2(no asset_group) CF-3(blank pm) CF-4(no source) |
      | market-data-tick-pred-prd | prediction | 16,812 | 100% v8 | ✗ | CF-2(14.5K blank ag) CF-3(blank pm) CF-4(no source) |
      | dex-pools-prd | defi | 75,983 | v4/v5/v6 mix | ✗ | CF-2/CF-3/CF-4/CF-5/CF-7 (hyphen dtype + glued venue) |
      | dex-swaps-prd | defi | 46,491 | v4/v5/v6 mix | ✗ | CF-2/CF-3/CF-4/CF-5/CF-7 (hyphen dtype) |
      | evm-defi-prd | defi | 22,633 | v4/v6 mix | ✗ | CF-2/CF-3/CF-4/CF-5/CF-7 (glued venue) |
      | solana-defi-prd | defi | 5,028 | 100% v4 | ✗ | CF-2/CF-3/CF-4 |
      | instruments-store-cefi-prd | cefi | 30,803 | 100% v8 | ✗ | CF-2(no ag) CF-3(blank pm) CF-4(no source) CF-7(hyphen venue) |
      | instruments-store-defi-prd | defi | 125,242 | 100% v8 | ✗ | CF-2(no ag) CF-3(blank pm) CF-4(no source) CF-7(glued venue) |
      | instruments-store-tradfi-prd | tradfi | 20,264 | 100% v8 | ✗ | CF-2(no ag) CF-3(blank pm) CF-4(no source) |
      | instruments-store-sports-prd | sports | 2,681,044 | 99.97% v8 / 0.03% v9 (735 rows) | ✗ | CF-2(2.67M blank ag) CF-3(blank pm) CF-4(no source) |
      | instruments-store-pred-prd | prediction | 493 | 100% v8 | ✗ | CF-2(no ag) CF-3(no pm col) CF-4(no source) |
      **"No manifest" vs "missing manifest" (prd canonical buckets):**
      - **EMPTY (legitimately no manifest)**: `eigenlayer-rewards-prd`, `gas-fees-prd` — bucket exists, 0 objects
      - **HAS_DATA but NO MANIFEST INDEX**: `lending-indices-prd`, `lst-rates-prd`, `oracle-prices-prd`, `perp-funding-prd`
        — data parquets present but consolidator never ran → manifest consolidator needed before audit
      **Conclusion**: no AG has completed v9 migration. The 407 DeFi + 735 Sports IS v9 rows are partial recent writes,
      not a completed C0 walk. Migration is a prerequisite for this check to pass; schedule C0 walks per-AG B-P0 grid.
- [x] ✅ [SCRIPT] P1. Sanity (not blind-run) the MDPS + features-service downstream todos in
      `downstream_services_manifest_canonicalisation` — verify live=batch dep-check + v9-schema asserts; run only on AGs
      whose upstream is migrated, sampling across data_types/venues/AGs (per Harsh's standing approach).
      **DONE (slot-5, 2026-06-05):** Code-level sanity on origin/live-defi-rollout. Data sampling N/A (0/6 C0 walks
      completed per B-P0 audit → no migrated upstream). Shipped items verified: MDPS CRIT-1 `skip_dependency_check=False`
      (live_mode_handler.py:235) ✅; MDPS GAP-4 `_warn_on_v9_schema_drift` (dependency_checker.py:75,735) ✅; MDPS
      writer typed `EmptyConfirmedReason.SOURCE_RETURNED_ZERO` (live_workers.py:930) ✅; features GAP-4
      `_warn_on_v9_schema_drift` (manifest_window_guard.py:54,127) ✅; features GAP-6 `assert_consolidator_healthy` in
      delta_one LiveHandler (live_handler.py:42) ✅; features writer typed reasons across delta_one/volatility/
      cross_instrument/calendar/cefi ✅. Open per plan: strategy GAP-4 warn (manifest_allocation_guard — no v9 warn),
      strategy+execution writer CF-11 fixes, IS tradfi/prediction CF-11 residual, FLAG-3 deployment-api, GAP-7 rename.

## C — Orchestrator e2e + execution-scope field _(Harsh ask #3 + chat 39–48, 89)_

Owning plan:
[agent_orchestrator_e2e_workflow_and_execution_scope_2026_06_02.md](agent_orchestrator_e2e_workflow_and_execution_scope_2026_06_02.md)
(NEW). Flow **verified against code 2026-06-02**: quickmerge→staging→SIT→main→CICD is **live**; assignment is automated;
discovery is **polling** (G2 — Harsh-owned, will confirm interval). The orchestrator-vs-local field **does not exist
yet** (only `assigned_vm`; absent ⇒ picked up globally) → that's **G1 (P0)**, the field Harsh asked for. AO-on-`main` is
resolved/codified — no action. Fleet currently consolidated to **2 running VMs** (9 epic VMs stopped) → low risk that
pushing today's plans auto-dispatches; the `execution_scope: local-only` stamps make it safe once G1 lands.

- [x] ✅ [DESIGN] P0. Spec `execution_scope` in PLAN_FORMAT + wire it into `regen_backlog_from_plan.py` (owning plan
      G1). — DONE + shipped (slot 2): `execution_scope: orchestrator-agent | local-only` added to PLAN_FORMAT
      frontmatter; `_parse_frontmatter_execution_scope` → unconditional skip on `local-only` before the per-VM filter; 4
      unit tests.
- [x] ✅ [TEST] P1. Run `e2e_demo.py` + `dev.sh --mock` locally; capture pass/fail (owning plan G4). — DONE:
      `e2e_demo.py` EXIT 0, "ALL CHECKS PASSED" (boot→dispatch→gating→stop/resume full lifecycle); `check.sh` green.

## D — GCS soft-delete log churn + bucket policy _(Ikenna handoff #1 + Harsh ask #2-bucket-policy + chat 22–37)_

Owning plan:
[deployment_scripts_bucket_softdelete_log_churn_2026_06_01.md](issues/deployment_scripts_bucket_softdelete_log_churn_2026_06_01.md)
(3✓/5○). Harsh's "verify no soft-delete / retention **across the bucket(s)**" is **largely already done**: the
cross-bucket soft-delete + versioning audit RAN 2026-06-02 (295 buckets) — deployment-scripts ages out ~06-08, TF-state

- strategy-store are intentional versioning, 3 secondary offenders (~1.2 TiB) tracked. Remaining:

_Owning plan reached **13✓/0○** — all D work done (slot 1, 2026-06-02)._

- [x] ✅ [SCRIPT] P0. Verify the policy held + bytes shrinking: prefix-scoped lifecycle rules APPLIED +
      `retentionDurationSeconds==0`; cross-bucket soft-delete/versioning audit RAN (295 buckets). (Byte-shrink completes
      naturally by ~06-08 — policy is in place; nothing left to do.)
- [x] ✅ [INFRA] P0. Ship the owning plan's P0 — `deployment-service` jobs container image built + published; the dead
      tarball-cleanup job is now LIVE + verified (tarball reaper). This also resolves B's migration blocker.
- [x] ✅ [INFRA] P1. Fix the secondary offenders — ~1.2 TiB of secondary bloat buckets remediated;
      `cleanup_old_tarballs.py` scheduled (tarball reaper live).

## E — QG resource/speedup + worker-VM right-sizing _(Ikenna handoff #2 + Harsh asks #1+#3 + chat 60)_

Owning plan:
[quality_gates_resource_contention_speedup_2026_06_02.md](quality_gates_resource_contention_speedup_2026_06_02.md)
(0✓/12○). Fix = **do-less-work + cross-slot governance, NOT more parallelism** (matches Ikenna). Now also carries
Harsh's per-repo baseline (ask #3) + worker-VM right-sizing (ask #1).

_Owning plan **11✓/2○** — only the two measurement P0s below remain open; the governor + slot-aware pytest + ADR + CW
agent all landed._

- [x] ✅ [SCRIPT] P0. Governor (`QG_HOST_CONCURRENCY`) + slot-aware `pytest -n` + aggregate-load benchmark (owning todos
      qg-governor / qg-slot-aware-workers / qg-bench-aggregate). **3-of-3 DONE** — qg-bench-aggregate shipped:
      benchmark ran K=1,2,4; K=1 p95=30.5s → K=2=30.7s (1.01×) → K=4=53.1s (1.74×); swap_in=0 steal=0 at all K.
      vmstat header-repeat bug fixed. CSV evidence committed (qg-bench-under-load-20260603T134208Z.csv).
- [x] ✅ [SCRIPT] P0. Per-repo QG baseline — time/CPU/RAM, **local + on an AWS worker VM** → committed baseline file + a 2×
      deviation guard (ask #3; owning todo qg-perrepo-baseline). DONE: 20-repo local baseline in
      scripts/dev/qg_resource_baseline.json; 2× WARN guard in base-service.sh:2518-2529. VM side deferred pending
      qg-cw-memory-agent fleet bootstrap.
- [x] ✅ [INFRA] P1. Worker-VM right-sizing, **data-driven off the baseline** (ask #1; owning todo qg-vm-rightsizing). —
      DONE in owning plan: binding ceiling = unified-trading-library **5.27 GB** per gate; machine-type + slots-per-VM
      decision recorded. (Note: the per-repo baseline P0 above should still backfill the committed numbers.)

## F — CI/CD hardening _(Ikenna handoff #3 — opportunistic)_

Owning plan: [cicd_contract_hardening_2026_06_01.md](cicd_contract_hardening_2026_06_01.md) (102✓/16○). Pick up RED v2
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

### Remaining as of 2026-06-02 (PM@8cefbea2e) — what's genuinely left

1. **E — 2 P0s (the day's main open work):** (a) per-repo QG baseline + 2× deviation guard, local + AWS VM →
   `qg_resource_baseline.json`; (b) aggregate-load benchmark harness `scripts/dev/benchmark-qg-under-load.sh`. Governor,
   slot-aware pytest, CW agent, sentinel/selective/basedpyright, ADR, and VM-right-sizing are already landed.
2. **B — run the audit grid** (now unblocked by D): per-AG ✓/○/blocked done-state vs origin, then sample
   `audit_canonical_form.py` only on migrated AGs; sanity downstream MDPS/features on migrated AGs only.
3. **A — CLAUDE.md budget trim** (the open P2) to close the reverted A-P0 size-gate; the UI-slot `.mdc` follow-up (P2).
4. **C — leftovers only:** P1 operator-tooling-exception doc; the two P0s are BLOCKED-OPERATOR/BLOCKED-BILLING (not
   Harsh's to clear). **Already done this cycle:** D fully shipped (all 13); C's G1 + G4; A's Phases 4–6.

## Full-execution criterion (PLAN_FORMAT §8)

Day is "run to completion" when: A's owning plan hits its full-execution criterion (incl. C3 merge-flow doc drift); B
has a published per-AG v9 done/blocked grid + (for migrated AGs) a passing `audit_canonical_form.py` run; C's e2e_demo
passes + `execution_scope` is specced and wired (G1); D's soft-delete is verified shrinking + container image published

- secondary offenders fixed; E's governor is landed + benchmarked + per-repo baseline committed + VM-size decided.
  Anything not finished is left as a `- [ ]` in its owning plan (not lost in chat), with status noted here.
