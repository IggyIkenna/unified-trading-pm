---
title: CI/CD Pipeline ↔ Plans Drift Audit
name: cicd_pipeline_vs_plans_drift_audit_2026_06_17
type: audit-result
epic: infrastructure_master
parent_audit: infrastructure_master_audit_instructions
instructions_ref: plans/audit/instructions/infrastructure_master_audit_instructions.md
created: 2026-06-17
date: 2026-06-17
author: ikenna [autonomous audit]
auditor: ikennaigboaka
status: active
assigned_vm: vm-cross-cutting
source:
  - codex/08-workflows/ci-cd-flow.md
  - cursor-configs/CLAUDE.md
  - scripts/quickmerge.sh
  - scripts/quality-gates-base/base-service.sh
  - scripts/cicd/*.py
  - .github/workflows/*.yml
  - plans/active/*cicd*, *ldr*, *qg*, *quality*, *dependency*, *staging*, *ci_*
  - plans/active/issues/*ci*, *cicd*, *provenance*, *promotion*, *uv_lock*, *semver*
---

# CI/CD Pipeline ↔ Plans Drift Audit — 2026-06-17

> **Scope.** Audit the LIVE CI/CD pipeline (quickmerge + quality-gates machinery, the `scripts/cicd/*.py` gate scripts,
> the ~51 PM GitHub-Actions workflows) against the documented INTENT (the engineer SSOT
> `codex/08-workflows/ci-cd-flow.md`, `CLAUDE.md`, and the ~27 active CI/CD plans + issue docs). Find three drift
> classes: **(1) pipeline-vs-doc** (a doc/SSOT claims something the live pipeline no longer does), **(2) plan-vs-plan**
> (two plans/issues assert contradictory contracts), **(3) stale/obsolete plan items** (flipped-but-torn-out, dead
> machinery, archivable). **This is a triage artifact — it documents drifts and recommends a disposition per finding; it
> does NOT autonomously rewrite the live pipeline or the governing SSOTs** (CI/CD-wide drift is a "big finding" per
> Findings-Triage Discipline → document + decide, don't unilaterally rewrite).

> **Method + confidence.** Ground truth read directly from the live files (quickmerge.sh 1617 lines, base-service.sh, 16
> `scripts/cicd/*.py`, 51 workflows). Intent read from ci-cd-flow.md (1020 lines), CLAUDE.md, and 14 active plans + 12
> issue docs. The three load-bearing findings (D1 `--frozen`, D2 service-deps gate, D4 cron) were re-verified by direct
> grep after the read pass. **Where this audit sampled vs walked:** every live workflow trigger/concurrency was read;
> quickmerge stages + QG sentinel logic walked line-by-line; plan open-item counts are mechanical checkbox tallies, not
> a per-item actionability filter. Remaining gap: image-build path (cloudbuild.yaml/buildspec) was only spot-checked,
> not fully walked — a follow-up audit cell.

---

## Executive summary

The **live pipeline is healthy and largely matches the latest model** (LDR-trunk decoupling is correctly implemented in
code; the promote bots, cascade own-group, strict-quickmerge provenance marker-range, and the service-deps gate are all
live and correct). **The drift is almost entirely in the DOCS and the PLAN LAYER lagging a fast-moving pipeline** —
exactly the failure mode the operator predicted ("when solving the pipeline we made changes that don't align with the
plans"). Two findings are genuine _unresolved contradictions_ that need an operator decision, not just a doc edit.

**Headline drifts (full register below):**

1. **🔴 D1/D10 — the `uv.lock` / `--frozen` model is self-contradictory and unresolved.** CLAUDE.md asserts CI installs
   via `uv sync --frozen` + a dep-floor change "only reaches CI if the lock is regenerated"; the **deployed** v2 does a
   bare `uv sync` (`python-quality-gates-v2.yml:459`) with a **warn-only** `uv lock --check` (`base-service.sh:305`,
   "lock is a record, not a pin"), and local QG uses `uv pip install -e .` with no `uv sync` at all
   (`base-service.sh:299`). A plan marks this "DECIDED 2026-06-12" (still an _open_ checkbox); the issue doc says it was
   docs-only, never wired, and dangerous to action naively. **DECIDED 2026-06-17 (operator): adopt the frozen-lock model
   end-to-end (`uv sync --frozen` in CI + local, lock-as-SSOT from LDR, external-only regen), sequenced behind the
   LDR-landing prerequisite — implementation tracked in `dependency_promotion_…` § Phase 1.5; not yet wired.**
2. **🔴 D5 — the engineer SSOT `ci-cd-flow.md` still teaches the OLD per-unit-staging-PR quickmerge model** in 4 places
   while the live quickmerge lands on LDR and stops (decoupling). An agent reading only the SSOT operates the wrong
   model.
3. **🟠 D2/D3/D4 — CLAUDE.md + ci-cd-flow.md carry stale facts the live pipeline already moved past**: the "service-deps
   enforcement is DEAD" warning is false (gate is live), the aiohttp "two `--ignore-vuln`" is now ~20, and the
   promote-bot cadences in the docs (30 min / `*/20`) disagree with the live crons (15 min / hourly). Three separate
   SSOTs disagree on the `ldr-to-staging` cadence alone.
4. **🟠 D22/D24 — lifecycle + sprawl hygiene**: two migrated issue docs retain residual todos not in their parent plan
   (dual-tracking, review-blocking), and three workflow-template dirs hold dead duplicate
   `feature-branch-to-staging.yml` templates (retired v1 model, deployed nowhere) that the sprawl issue doesn't
   enumerate.

**Disposition counts:** 25 findings — 3 need an operator/triage decision; 9 are mechanical doc/comment fixes; 7 are
plan-hygiene (banner/migrate/archive/frontmatter); 4 are small code fixes; 2 are "note only / latent". **0 live pipeline
regressions found.**

> **Progress 2026-06-17 (autonomous):** **10 findings shipped** — D2–D9 (all 8 no-decision doc/SSOT-truth fixes,
> PM@235c5fd3b + PM@eeece9802; ci-cd-flow.md + CLAUDE.md now match the live pipeline) + **D14** (unwired-AR-gate record)
> and the **D11 callout**, both filed in `cloud_build_router_aws_parity` (PM@98bdf756c). **Still open:** D1/D10 (the
> `--frozen` model — **DECIDED 2026-06-17**: frozen-lock end-to-end, implementation tracked in `dependency_promotion` §
> Phase 1.5), D11 (DECIDED 2026-06-17 — drop in-image QG), D12 (RESOLVED 2026-06-18 — stale premise, issue
> closed+archived), D16 (DECIDED 2026-06-18 — scripts governance plan), and the LOW-tier items D13/D15/D17–D25. The
> latter are **deferred for one of two reasons:** a code fix would need a PM-QG run that contends with the active QG
> agent (D15/D18), or a markdown edit would force a 100–170-line prettier-reflow of a hot, actively-edited foreign plan
> on commit (D13/D20/D24/D25). All captured per-item below — apply at triage / in a quiet window.

---

## Drift register (severity-ranked)

Legend: **P** pipeline-vs-doc · **X** plan-vs-plan/cross-SSOT contradiction · **S** stale/obsolete · **H** hygiene. Each
finding's checkbox is the triage handle (migrate to the named destination plan when accepted).

| ID  | Sev     | Class | One-line                                                                                                                                             | Disposition / destination                                                                                     |
| --- | ------- | ----- | ---------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| D1  | 🔴 HIGH | P+X   | `--frozen` asserted in docs; deployed CI does bare `uv sync` + warn-only lock; local uses `uv pip install -e .`                                      | **DECISION** → `uv_lock_frozen_model_contradiction` (pick one model, then wire docs+CI to agree)              |
| D5  | 🔴 HIGH | P     | ci-cd-flow.md teaches OLD per-unit staging-PR model (L176/L571-576/L611/L618) vs live land-on-LDR-and-stop                                           | Doc rewrite → ci-cd-flow.md (owner: cicd_contract_hardening codex-audit phase)                                |
| D10 | 🔴 HIGH | X     | "DECIDED 2026-06-12 `--frozen`" is still an OPEN checkbox + contradicts the issue doc                                                                | Same as D1 (this is the intent side)                                                                          |
| D2  | 🟠 MED  | P     | CLAUDE.md "service-deps enforcement is DEAD (wrong path / type==service only)" — FALSE, gate is live                                                 | Edit CLAUDE.md (remove ⚠️ DEAD warning)                                                                       |
| D3  | 🟠 MED  | P     | CLAUDE.md "the two aiohttp `--ignore-vuln`" — actual is ~20 vulns                                                                                    | Edit CLAUDE.md count + the "drop the two flags" instruction                                                   |
| D4  | 🟠 MED  | P+X   | Cron drift: ldr-to-staging live `2,17,32,47`(15m) vs ci-cd-flow `13,43`(30m); main-backmerge live hourly vs CLAUDE `*/20`                            | Edit ci-cd-flow.md + CLAUDE.md to live values                                                                 |
| D11 | 🟠 MED  | X     | In-image QG: router plan wants advisory→blocking; sibling-context issue shipped `_RUN_INIMAGE_QG:false` skip                                         | Reconcile → `cloud_build_router_aws_parity` L67                                                               |
| D12 | ✅ DONE | X     | ~~Content-hash sentinel owned by 2 plans, neither closes the race~~ — premise STALE (Rec#1 shipped 977c5548f; plan archived)                         | RESOLVED 2026-06-18 — issue closed + archived; nothing to consolidate                                         |
| D13 | 🟠 MED  | S     | `qg_commit_quality_boundary` L220 flipped `[x] SHIPPED tab-mirror BIDIRECTIONAL` — machinery since DELETED by Path-B, no SUPERSEDED banner           | Add SUPERSEDED banner → that plan                                                                             |
| D14 | 🟠 MED  | S     | `assert_deps_published_to_ar.py` is UNWIRED (own STATUS comment 2026-06-16); reserved for unlaunched image-build path                                | Note as reserved/dead → `cloud_build_router_aws_parity` (AR-publish item)                                     |
| D22 | 🟠 MED  | H     | `semver_version_bump_skip_ci` + `cicd_workflow_sprawl_audit` migrated core but keep residual todos not in parent (dual-tracking)                     | Migrate residuals → `cicd_contract_hardening`, then archive                                                   |
| D24 | 🟠 MED  | S     | 3 template dirs; `feature-branch-to-staging.yml` dup'd in 2 dead dirs (retired v1 model, deployed nowhere); `staging-version-gate.yml` orphan        | Delete dead templates → `cicd_workflow_sprawl_audit`                                                          |
| D6  | 🟡 LOW  | P     | ci-cd-flow.md L32 lists `tab/hk/<N>` tab-branch as live; Path-B retired it                                                                           | Doc edit → ci-cd-flow.md branch-model table                                                                   |
| D7  | 🟡 LOW  | P     | ci-cd-flow.md L918-929 "post-cutover LDR retired" block — wrong; LDR is the SSOT                                                                     | Delete/rewrite block → ci-cd-flow.md                                                                          |
| D8  | 🟡 LOW  | X     | ci-cd-flow.md L620 "kill-switch arming ❌ NOT ALLOWED" vs CLAUDE.md "protective arming always autonomous"                                            | Doc edit → ci-cd-flow.md table                                                                                |
| D9  | 🟡 LOW  | S     | ci-cd-flow.md L756-796 "Operational status snapshot 2026-06-01; being repaired" — 6wk stale                                                          | Refresh/archive section → ci-cd-flow.md                                                                       |
| D15 | ✅ DONE | P     | `promotion_lag_monitor.py` + `reconcile_release_tags.py` use `GOOGLE_CLOUD_PROJECT` (rule mandates `GCP_PROJECT_ID`) → silent Firestore no-op on VMs | ✅ DONE 2026-06-18 — renamed env both sides; +`ci_failure_watcher.py` (same bug) + 3 workflows — PM@409fd7661 |
| D16 | 🟡 LOW  | P     | `check_strict_quickmerge.py` carves `scripts/` as a prefix in ANY repo; CLAUDE.md implies PM-only (code more permissive)                             | Align doc OR tighten code → decision (small)                                                                  |
| D17 | 🟡 LOW  | note  | `ci_status_store` ranks STAGING_PENDING == STAGING_GREEN but `tier_c_promotion_gate` excludes PENDING from ON_STAGING                                | Note only (latent confusion, not a live bug)                                                                  |
| D18 | 🟡 LOW  | P     | quickmerge.sh:1481/1534 messages say "Tier-C drain ≤30min" vs live 15min                                                                             | Comment fix → quickmerge.sh                                                                                   |
| D19 | 🟡 LOW  | P     | `sit-starvation-detector.yml` header comment "every 15 minutes" vs cron `*/30`                                                                       | Comment fix → that workflow                                                                                   |
| D20 | 🟡 LOW  | H     | `ci_status_firestore_side_store` + `ldr_tarball_auto_refresh` carry `locked_since:2026-05-21` predating `created`                                    | Frontmatter fix → those plans                                                                                 |
| D21 | 🟡 LOW  | H     | `fleet_git_health_orchestrator` `assigned_vm: vm-orchestrator` — that VM STOPPED 2026-06-04 (vestigial)                                              | Reassign VM → that plan                                                                                       |
| D23 | 🟡 LOW  | H     | 4 plans/issues likely-archivable (see §"Archivable")                                                                                                 | Archive per ritual                                                                                            |
| D25 | 🟡 LOW  | S     | `cicd_workflow_sprawl_audit` issue itself states ldr-to-staging cron as `17 */6` — wrong vs live                                                     | Fix the issue doc number                                                                                      |

---

## Detailed findings

### Class P — Pipeline-vs-doc drift (the doc/SSOT is wrong; the live pipeline is right)

**D1 / D10 — `uv.lock` / `--frozen` model (🔴 the one genuine live contradiction).**

- **Live pipeline:** CI v2 runs **bare `uv sync`** (`python-quality-gates-v2.yml:459`); the lock check is **warn-only**
  (`base-service.sh:305` → `uv lock --check 2>/dev/null || echo "⚠️ … non-blocking — lock is a record, not a pin"`);
  local QG installs via **`uv pip install -e .`** with no `uv sync`/`--frozen`/`--locked` at all
  (`base-service.sh:299`).
- **Doc claim:** CLAUDE.md § Dependencies — "CI installs via `uv sync --frozen` … a dep-floor change only reaches CI if
  the lock is regenerated … `--frozen` NOT `--locked`."
- **Plan claim:** `dependency_promotion_range_pins_and_major_bump_sit_2026_06_09` L120 marks this "🟡 DECIDED 2026-06-12
  (operator Harsh) — align CI to local via `uv sync --frozen`; speed > security" — but the **checkbox is still open**.
- **Counter-evidence:** `uv_lock_frozen_model_contradiction_2026_06_15` states the decision was docs-only/never-wired,
  is internally inconsistent, and that a naive fleet-wide `uv lock` + commit would **restart the Tier-C promote
  runaways**. Field datapoint 2026-06-16: 9/10 repos worked pyproject-only, fund-admin needed a lock regen.
- **Why it matters:** an agent following CLAUDE.md would regen+commit locks (the documented rule) and trigger the exact
  runaway the issue warns against. Local and CI use _different installers_, so "local-green = CI-green" parity is not
  guaranteed for dep resolution.
- **Disposition: operator decision** (the issue doc already frames options A/B). This is the top triage item.

**D2 — CLAUDE.md "service-deps enforcement is currently DEAD" is stale/false.**

- CLAUDE.md § "Dep tiers" carries a ⚠️ block: "`check-no-service-deps.py` is wired at a wrong path … so it never runs,
  and it only classifies `type=='service'`." **Both halves are now false:** wired at `base-service.sh:673` →
  `scripts/validation/check-no-service-deps.py` (exists, `exit 1`s on violation), and
  `_SERVICE_REPO_TYPES = {"service","api-service","batch-service","api"}` (`check-no-service-deps.py:47`). The in-code
  comment documents the fix in past tense. **Disposition:** delete the ⚠️ DEAD warning from CLAUDE.md (it currently
  tells agents a live gate is dead).

**D3 — aiohttp `--ignore-vuln` count.** CLAUDE.md says "the **two** `--ignore-vuln`" and "drop the **two** flags" when
vcrpy supports aiohttp 3.14. Actual: ~20 ignored vulns in `base-service.sh:1182` + `base-library.sh:892` (the 3.13.5 CVE
set grew through 2026-06-15 OSV advisories). **Disposition:** edit CLAUDE.md to say "the `--ignore-vuln` block" and
"drop the block".

**D4 — promote-bot cadence drift (three SSOTs disagree).**

- `ldr-to-staging-promote`: **live `2,17,32,47 * * * *` (15 min)**; ci-cd-flow.md L117 says `13,43` (30 min); the sprawl
  issue says `17 */6`; CLAUDE.md says `*/15` (closest-correct).
- `main-backmerge-to-ldr`: **live `0 * * * *` (hourly)** — comment: "`*/20`→hourly to cut Actions spend (billing
  2026-06-11)"; CLAUDE.md § "LDR is the SSOT" still says `schedule: */20`.
- **Disposition:** the live workflow cron is authoritative; update ci-cd-flow.md L117, CLAUDE.md, and the sprawl issue.

**D15 — `GOOGLE_CLOUD_PROJECT` vs `GCP_PROJECT_ID`.** `promotion_lag_monitor.py` + `reconcile_release_tags.py` read
`GOOGLE_CLOUD_PROJECT` for best-effort Firestore write-through; workspace rule mandates `GCP_PROJECT_ID` (never
`GOOGLE_CLOUD_PROJECT`). Both are inside catch-all `except` → no breakage, but the Firestore write **silently never
happens** on a VM that sets only `GCP_PROJECT_ID`. **✅ RESOLVED 2026-06-18 (PM@409fd7661):** the audit under-scoped
this — `ci_failure_watcher.py` has the **same** read (3rd script, not originally named), and all 3 are invoked by
workflows that mapped `vars.GCP_PROJECT_ID` under the banned env name (so GHA worked, only the VM path no-op'd). Renamed
both sides to canonical `GCP_PROJECT_ID` across the 3 scripts + 3 workflows in lockstep; `firestore.Client(project=...)`
is explicit, so nothing relied on the SDK's implicit `GOOGLE_CLOUD_PROJECT` default. (The base-library gate only scans
`$SOURCE_DIR/`, never `scripts/` — which is why these reads were never flagged.)

**D16 — `check_strict_quickmerge.py` carve-out broader than the doc.** Code carves `scripts/` as a path prefix in
**any** repo (`CARVE_PREFIX`); CLAUDE.md's carve-out 3 reads "PM `scripts/**`", implying PM-only. The code is _more
permissive_ than the doc — a `scripts/*.py` commit in a service repo would pass the provenance gate. **Disposition:**
decide whether the breadth is intended (then fix the doc) or a bug (then scope the carve-out to PM).

**D18 / D19 — code/comment cadence lag.** quickmerge.sh:1481/1534 print "Tier-C drain (≤30min)/every 30min" (live
15min); `sit-starvation-detector.yml` header says "every 15 minutes" but cron is `*/30`. Cosmetic comment fixes.

### Class P (doc) — `ci-cd-flow.md` internal staleness (D5/D6/D7/D8/D9)

The engineer SSOT lags the live pipeline by ~2–6 weeks. It got a single 2026-06-17 line touch (provenance marker-range
ref) but the structural sections were not updated in that pass.

- **D5 (🔴):** OLD per-unit-staging-PR model survives in **4 places** — L176 (Pass-2 code block "creates PR targeting
  staging"), L571–576 (Full-CI/CD-Flow diagram "→ staging PR → workspace-qg"), L611 + L618 (Agent-vs-Human table). Live
  `quickmerge.sh:1533-1537` lands a service-repo unit on LDR and `exit 0`s ("Tier-C drain promotes LDR→staging"); the
  per-unit staging PR is gone for service repos (only `--hotfix` opens one). An agent reading only ci-cd-flow.md
  operates the wrong model — this is the most consequential doc drift.
- **D6:** L32 branch-model table lists `tab/hk/<N>` as a current branch type; Path-B (2026-06-08) retired tab branches
  and deleted `tab-mirror-to-ldr.yml` fleet-wide.
- **D7:** L918–929 "Post-cutover trigger surface — after 2026-05-23 — LDR retired" is **wrong**; LDR was made the
  integration SSOT, never retired.
- **D8:** L620 "Kill-switch arming ❌ NOT ALLOWED" contradicts CLAUDE.md (protective arming is always autonomous,
  codified 2026-06-02).
- **D9:** L756–796 "Operational status — snapshot 2026-06-01; being repaired" is ~6 weeks stale and superseded by
  LDR-trunk decoupling + the SIT loop-closure fixes.
- **Disposition:** a single ci-cd-flow.md refresh pass (owner: `cicd_contract_hardening` codex-audit phase, or a small
  dedicated doc-sync item). Recommend doing D5–D9 together since they're the same file.

### Class X — Plan-vs-plan / cross-SSOT contradictions

- **D11 — in-image QG blocking vs skip.** `cloud_build_router_aws_parity_2026_06_10` L67 (open P1): "flip in-image QG
  step from advisory to blocking." `gcp_cloudbuild_sibling_context_staging_2026_06_15` (resolved, shipped) added
  `_RUN_INIMAGE_QG:false` because the in-image `quality-gates.sh` is "redundant AND impossible (no PM harness in the
  image → exit 127)." The router's open item is partly counter to what already shipped. **Reconcile before actioning.**
- **D12 — content-hash sentinel duplicate ownership. ✅ RESOLVED 2026-06-18 — the premise was a stale read.** By the
  time of disposition: (1) Rec#1 (the content-hash sentinel — the dominant race fix) had **SHIPPED 2026-06-17**
  (`977c5548f`: quickmerge accepts a green QG when HEAD only fast-forwarded + the `--files` are byte-identical to the
  sentinel commit); (2) `quality_gates_speed_and_config_ssot` was **archived** (so no second owner / no
  double-tracking); (3) Rec#2 (change-scoped slicing) is an explicit **WON'T-DO** (Harsh, 2026-06-17 —
  tests+basedpyright always-full, only ~1.1% scopable); (4) Rec#3 (merge queue) superseded by Rec#1 + LDR-trunk
  decoupling. The issue `qg_sentinel_content_hash_and_slicing` was **closed + archived** to `plans/archive/issues/`.
  Nothing to consolidate.
- (D1/D10 also belong here — see Class P.)

### Class S — Stale/obsolete items & dead machinery

- **D13 — flipped-but-torn-out.** `qg_commit_quality_boundary_and_slot_ff_push_2026_06_03` L220 is flipped
  `[x] ✅ SHIPPED 2026-06-04` for "tab-mirror BIDIRECTIONAL" (the `tab-mirror-to-ldr.yml` / `ldr_to_tabs` machinery) —
  which `worktree_ldr_unification` Path-B subsequently **deleted fleet-wide**. No SUPERSEDED banner here (the
  `cicd_contract_hardening` plan bannered its equivalents). Reads as live when it's torn out. **Add SUPERSEDED banner.**
- **D14 — unwired gate.** `assert_deps_published_to_ar.py` carries its own STATUS comment (2026-06-16): "NOT currently
  wired into any workflow — RESERVED for the production IMAGE-BUILD dep-publish gate." That image-build path has not
  launched. Nothing in the plans flags it as a dead/reserved gate. **Note it; tie to the AR-publish item in
  `cloud_build_router_aws_parity`.**
- **D24 — template-dir triplication (new finding, beyond the sprawl issue).** Three dirs hold workflow/artifact
  templates: `scripts/workflow-templates/` (canonical SSOT), `scripts/propagation/templates/`, `scripts/templates/`.
  `feature-branch-to-staging.yml` is duplicated in the latter two, both the **retired v1 model**
  (`on: workflow_run: workflows:["Quality Gates"] branches:[live-defi-rollout]`) — superseded by the
  `ldr-to-staging-promote` bot, **deployed to 0 of 25 repos**. `staging-version-gate.yml` (propagation) is also deployed
  nowhere. (`staging-lock-check.yml` in propagation IS live fleet-wide, so the dir isn't purely dead.) The sprawl issue
  doc does not enumerate these. **Delete the dead templates; fold into the sprawl remediation tranche.**
- **D25 — the sprawl issue is itself stale** on the ldr-to-staging cron (`17 */6` vs live `2,17,32,47`). Fix the number.

### Class H — Plan hygiene / lifecycle governance

- **D22 — dual-tracking (review-blocking per Issue-Doc-Lifecycle HARD RULE).**
  `semver_version_bump_skip_ci_promotion_block` and `cicd_workflow_sprawl_audit` both migrated their core items to
  `cicd_contract_hardening` but retain OPEN residual todos NOT in the parent plan. Per the lifecycle rule, migrate the
  residuals into the parent (or close them) and archive the issue.
- **D20 — frontmatter copy-paste.** `ci_status_firestore_side_store_2026_06_10` and
  `ldr_tarball_auto_refresh_2026_06_17` carry `locked_since: 2026-05-21`, predating their `created` dates. Fix the lock
  dates.
- **D21 — stale `assigned_vm`.** `fleet_git_health_orchestrator_2026_06_10` is `assigned_vm: vm-orchestrator`; that
  instance (`i-007e8d99`) was STOPPED 2026-06-04 (vestigial) per the 2026-06-12 human/central VM split. Reassign to
  `planning` (central) or `human-planning`.
- **D23 — archivable.** See next section.

---

## Verified-correct — do NOT second-guess at triage

So triage knows what is solid (these were checked against live code/workflows and match intent):

- ✅ **LDR-trunk decoupling is correctly implemented** — service quickmerge lands on LDR + `exit 0`
  (`quickmerge.sh:1533`); PM is Option-B main-direct with a `--merge` (not squash) standing PR.
- ✅ **`cascade-qg-ordering.yml` runs in its OWN concurrency group** (not `manifest-update`) — the codified HARD RULE.
- ✅ **`check-no-service-deps` gate is LIVE** (path + types correct) — contra the stale CLAUDE.md warning (D2).
- ✅ **No `quality-gates-v2` duplicate** — `quality-gates-v2.yml` (caller) + `python-quality-gates-v2.yml`
  (`workflow_call` callee, matrix-sliced) are a pair; v1 `quality-gates`/`workspace-qg` are gone.
- ✅ **`promote_provenance_range.py` uses the since-last-promote marker range** (raw range as fail-safe) — the `14b11e2`
  perpetual-block fix is live.
- ✅ **No live retired-model workflows** — `tab-mirror-to-ldr.yml` gone from all 25 active repos; no deployed
  `feature/*→staging`; no `workflow_run:["Quality Gates"]` (v1).
- ✅ **QG sentinel `.qg_last_passed_sha` is written on any complete green run** (not gated on fix-mode); host-governor
  floor is `max(2, floor(cores/4))`.
- ✅ **`semver-agent` watches `quality-gates-v2`**; `staging-to-main` own group with the quarantine-cap clearing.

---

## Likely-archivable (resolved but still in active/) — D23

Verify each gate before moving (`pw:L2 ✓` for the UI one), then archive per the 5-step ritual:

- `plans/active/staging_clean_start_and_stale_pr_hygiene_2026_06_08.md` — 0 open, model live.
- `plans/active/ci_dashboard_deployment_ui_2026_06_10.md` — 0 open; **gate on `pw:L2 ✓` + regression spec first** (scope
  is BLOCKED-PLAYWRIGHT).
- `plans/active/issues/gcp_cloudbuild_sibling_context_staging_2026_06_15.md` — option B shipped + validated (self-marked
  "archive on next sweep").
- `plans/archive/issues/provenance_gate_squash_perpetual_block_2026_06_17.md` — resolved same-day, both items flipped,
  prod-verified, already in CLAUDE.md.

---

## Recommended triage order

1. **Decide D1/D10 (`--frozen` model)** — it's the only finding that can actively _cause_ an incident if an agent
   follows the current CLAUDE.md rule. Everything else is documentation safety.
2. **Refresh `ci-cd-flow.md` (D5–D9) in one pass** — it's the engineer SSOT; a stale SSOT mis-trains every agent.
3. **Fix the CLAUDE.md stale facts (D2/D3/D4)** — quick, high-value (they actively mislead).
4. ~~Reconcile the two X-contradictions (D11/D12)~~ — both RESOLVED (D11 dropped, D12 stale-premise/closed); add the D13
   SUPERSEDED banner.
5. **Sprawl + lifecycle cleanup (D22/D24/D25)** and the small code/hygiene fixes (D15/D16/D18–D21/D23).

> **Note on capture.** These 25 findings live here as a triage register (audit-result checkboxes are NOT auto-dispatched
> by the orchestrator's `plans/active/` regen). On acceptance, migrate each `- [ ]` into the named destination plan so
> it becomes a tracked todo; this result file archives when all findings are `- [x]` in their parent plans (per
> `plans/audit/README.md`).

---

## Findings checklist (triage handles)

- [ ] D1/D10 🔴 **DECISION RATIFIED 2026-06-17 (operator):** adopt the frozen-lock model end-to-end (`uv sync --frozen`
      in CI + local, lock-as-SSOT flowing from LDR, external-only regen) — sequenced behind the LDR-landing
      prerequisite. Decision recorded in `uv_lock_frozen_model_contradiction_2026_06_15` (status: decided);
      implementation tracked as `- [ ]` todos in `dependency_promotion_range_pins_and_major_bump_sit_2026_06_09` §
      "Phase 1.5". **Not yet implemented** (docs-only this pass).
- [x] D5 ✅ — rewrote ci-cd-flow.md per-unit-staging-PR sections (Pass-2 block, Full-flow diagram, Agent-vs-Human
      Push-to-LDR + Promote rows) to the land-on-LDR / Tier-C-drain model — PM@235c5fd3b
- [x] D2 ✅ — replaced the false "service-deps enforcement is DEAD" warning in CLAUDE.md with "LIVE (fixed 2026-06-11)"
      — PM@235c5fd3b
- [x] D3 ✅ — corrected CLAUDE.md aiohttp `--ignore-vuln` ("two" → "~20-entry block") — PM@235c5fd3b
- [x] D4 ✅ — corrected ldr-to-staging (15m, ci-cd-flow.md) + main-backmerge (hourly, CLAUDE.md) cadences —
      PM@235c5fd3b. The sprawl-issue-doc cron number is tracked separately as D25 (still open).
- [x] D11 ✅ **DECIDED 2026-06-17 (operator): DROP in-image QG** — `_RUN_INIMAGE_QG:false` canonical; pre-build
      `quality-gates-v2` PR gate is authoritative; deploy-safety via an image-boot smoke owned by the build-images
      workstream (separate agent). Router plan Phase 1 re-scoped to RESOLVED/dropped.
- [x] D12 ✅ — RESOLVED 2026-06-18: premise stale. Rec#1 (content-hash sentinel) SHIPPED 2026-06-17 (`977c5548f`); Rec#2
      (change-scoped slicing) WON'T-DO (Harsh, ~1.1%); Rec#3 superseded; `quality_gates_speed` archived → no
      double-tracking. Issue closed + archived to `plans/archive/issues/`.
- [x] D13 ✅ — added SUPERSEDED-2026-06-08 banner to qg_commit_quality_boundary (the flipped tab-mirror BIDIRECTIONAL
      item — machinery deleted by Path-B) — 2026-06-18
- [x] D14 ✅ — recorded `assert_deps_published_to_ar.py` as reserved/unwired (callout in
      `cloud_build_router_aws_parity`) — PM@98bdf756c
- [ ] D22 🟠 — migrate residual todos out of semver_version_bump_skip_ci + cicd_workflow_sprawl_audit, then archive
- [x] D24 ✅ — deleted 3 dead retired-v1 templates (`feature-branch-to-staging.yml` ×2 + `staging-version-gate.yml`;
      verified deployed to 0/25 + unreferenced); recorded in the sprawl issue — 2026-06-18
- [x] D6 ✅ — branch-model table: `tab/hk/<N>` row → Path-B reference-clone; staging who-merges → Tier-C drain —
      PM@eeece9802
- [x] D7 ✅ — corrected the wrong "post-cutover — LDR retired" block (LDR is the trunk, runs no server QG; drain PR
      does) — PM@eeece9802
- [x] D8 ✅ — kill-switch arming row → protective arming autonomous, resume-within-matrix (manual_unkill human-only) —
      PM@eeece9802
- [x] D9 ✅ — bannered the 2026-06-01 "being repaired" operational snapshot as HISTORICAL/superseded — PM@eeece9802
- [x] D15 ✅ — `GOOGLE_CLOUD_PROJECT`→`GCP_PROJECT_ID` in promotion_lag_monitor.py + reconcile_release_tags.py +
      **ci_failure_watcher.py** (same bug, not originally named) + their **3 invoking workflows** (env key renamed in
      lockstep so GHA keeps working) — PM@409fd7661
- [ ] D16 🟡 — check_strict_quickmerge `scripts/` carve breadth. **Verified 2026-06-18:** the carve affects only
      PROVENANCE (trailer + dep-gate), NOT content — `scripts/` is QG-unchecked either way; `tests/` IS caught in
      staging (ruff+pytest). Operator 2026-06-18: scripts stay out of typecheck/coverage (by design); add ruff-lint
      only; tests unchanged. **Carve scope (PM-only vs all) PENDING a scripts audit** → migrated to
      `plans/active/repo_scripts_governance_audit_2026_06_18.md` (Phase 3).
- [ ] D17 🟡 — (note) STAGING_PENDING rank-equivalence vs ON_STAGING_STATUSES exclusion
- [ ] D18 🟡 — quickmerge.sh:1481/1534 "30min" → 15min drain comment
- [ ] D19 🟡 — sit-starvation-detector.yml header comment "15 minutes" → matches `*/30`
- [x] D20 ✅ — fixed `locked_since` frontmatter (ci_status_firestore_side_store→2026-06-10,
      ldr_tarball_auto_refresh→2026-06-17) — 2026-06-18
- [x] D21 ✅ — reassigned fleet_git_health_orchestrator `assigned_vm` vm-orchestrator (stopped 2026-06-04) → `planning`
      (live central VM) — 2026-06-18
- [ ] D23 🟡 — archive the 4 resolved plans/issues (gate the UI one on `pw:L2 ✓`)
- [x] D25 ✅ — fixed the ldr-to-staging cron number (`17 */6`→`2,17,32,47`) in the sprawl issue — 2026-06-18
