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
   docs-only, never wired, and dangerous to action naively. **Needs a decision, not a patch.**
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

---

## Drift register (severity-ranked)

Legend: **P** pipeline-vs-doc · **X** plan-vs-plan/cross-SSOT contradiction · **S** stale/obsolete · **H** hygiene. Each
finding's checkbox is the triage handle (migrate to the named destination plan when accepted).

| ID  | Sev     | Class | One-line                                                                                                                                             | Disposition / destination                                                                        |
| --- | ------- | ----- | ---------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| D1  | 🔴 HIGH | P+X   | `--frozen` asserted in docs; deployed CI does bare `uv sync` + warn-only lock; local uses `uv pip install -e .`                                      | **DECISION** → `uv_lock_frozen_model_contradiction` (pick one model, then wire docs+CI to agree) |
| D5  | 🔴 HIGH | P     | ci-cd-flow.md teaches OLD per-unit staging-PR model (L176/L571-576/L611/L618) vs live land-on-LDR-and-stop                                           | Doc rewrite → ci-cd-flow.md (owner: cicd_contract_hardening codex-audit phase)                   |
| D10 | 🔴 HIGH | X     | "DECIDED 2026-06-12 `--frozen`" is still an OPEN checkbox + contradicts the issue doc                                                                | Same as D1 (this is the intent side)                                                             |
| D2  | 🟠 MED  | P     | CLAUDE.md "service-deps enforcement is DEAD (wrong path / type==service only)" — FALSE, gate is live                                                 | Edit CLAUDE.md (remove ⚠️ DEAD warning)                                                          |
| D3  | 🟠 MED  | P     | CLAUDE.md "the two aiohttp `--ignore-vuln`" — actual is ~20 vulns                                                                                    | Edit CLAUDE.md count + the "drop the two flags" instruction                                      |
| D4  | 🟠 MED  | P+X   | Cron drift: ldr-to-staging live `2,17,32,47`(15m) vs ci-cd-flow `13,43`(30m); main-backmerge live hourly vs CLAUDE `*/20`                            | Edit ci-cd-flow.md + CLAUDE.md to live values                                                    |
| D11 | 🟠 MED  | X     | In-image QG: router plan wants advisory→blocking; sibling-context issue shipped `_RUN_INIMAGE_QG:false` skip                                         | Reconcile → `cloud_build_router_aws_parity` L67                                                  |
| D12 | 🟠 MED  | X     | Content-hash sentinel owned by 2 plans, neither closes the quickmerge `--files` race                                                                 | Consolidate ownership → `qg_sentinel_content_hash` ⇄ `quality_gates_speed`                       |
| D13 | 🟠 MED  | S     | `qg_commit_quality_boundary` L220 flipped `[x] SHIPPED tab-mirror BIDIRECTIONAL` — machinery since DELETED by Path-B, no SUPERSEDED banner           | Add SUPERSEDED banner → that plan                                                                |
| D14 | 🟠 MED  | S     | `assert_deps_published_to_ar.py` is UNWIRED (own STATUS comment 2026-06-16); reserved for unlaunched image-build path                                | Note as reserved/dead → `cloud_build_router_aws_parity` (AR-publish item)                        |
| D22 | 🟠 MED  | H     | `semver_version_bump_skip_ci` + `cicd_workflow_sprawl_audit` migrated core but keep residual todos not in parent (dual-tracking)                     | Migrate residuals → `cicd_contract_hardening`, then archive                                      |
| D24 | 🟠 MED  | S     | 3 template dirs; `feature-branch-to-staging.yml` dup'd in 2 dead dirs (retired v1 model, deployed nowhere); `staging-version-gate.yml` orphan        | Delete dead templates → `cicd_workflow_sprawl_audit`                                             |
| D6  | 🟡 LOW  | P     | ci-cd-flow.md L32 lists `tab/hk/<N>` tab-branch as live; Path-B retired it                                                                           | Doc edit → ci-cd-flow.md branch-model table                                                      |
| D7  | 🟡 LOW  | P     | ci-cd-flow.md L918-929 "post-cutover LDR retired" block — wrong; LDR is the SSOT                                                                     | Delete/rewrite block → ci-cd-flow.md                                                             |
| D8  | 🟡 LOW  | X     | ci-cd-flow.md L620 "kill-switch arming ❌ NOT ALLOWED" vs CLAUDE.md "protective arming always autonomous"                                            | Doc edit → ci-cd-flow.md table                                                                   |
| D9  | 🟡 LOW  | S     | ci-cd-flow.md L756-796 "Operational status snapshot 2026-06-01; being repaired" — 6wk stale                                                          | Refresh/archive section → ci-cd-flow.md                                                          |
| D15 | 🟡 LOW  | P     | `promotion_lag_monitor.py` + `reconcile_release_tags.py` use `GOOGLE_CLOUD_PROJECT` (rule mandates `GCP_PROJECT_ID`) → silent Firestore no-op on VMs | Small code fix → `gh_rate_budget_reduction` (has adjacent P3)                                    |
| D16 | 🟡 LOW  | P     | `check_strict_quickmerge.py` carves `scripts/` as a prefix in ANY repo; CLAUDE.md implies PM-only (code more permissive)                             | Align doc OR tighten code → decision (small)                                                     |
| D17 | 🟡 LOW  | note  | `ci_status_store` ranks STAGING_PENDING == STAGING_GREEN but `tier_c_promotion_gate` excludes PENDING from ON_STAGING                                | Note only (latent confusion, not a live bug)                                                     |
| D18 | 🟡 LOW  | P     | quickmerge.sh:1481/1534 messages say "Tier-C drain ≤30min" vs live 15min                                                                             | Comment fix → quickmerge.sh                                                                      |
| D19 | 🟡 LOW  | P     | `sit-starvation-detector.yml` header comment "every 15 minutes" vs cron `*/30`                                                                       | Comment fix → that workflow                                                                      |
| D20 | 🟡 LOW  | H     | `ci_status_firestore_side_store` + `ldr_tarball_auto_refresh` carry `locked_since:2026-05-21` predating `created`                                    | Frontmatter fix → those plans                                                                    |
| D21 | 🟡 LOW  | H     | `fleet_git_health_orchestrator` `assigned_vm: vm-orchestrator` — that VM STOPPED 2026-06-04 (vestigial)                                              | Reassign VM → that plan                                                                          |
| D23 | 🟡 LOW  | H     | 4 plans/issues likely-archivable (see §"Archivable")                                                                                                 | Archive per ritual                                                                               |
| D25 | 🟡 LOW  | S     | `cicd_workflow_sprawl_audit` issue itself states ldr-to-staging cron as `17 */6` — wrong vs live                                                     | Fix the issue doc number                                                                         |

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
happens** on a VM that sets only `GCP_PROJECT_ID`. **Disposition:** small env-var fix (adjacent to the existing
`gh_rate_budget_reduction` P3 Firestore-write-through item).

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
- **D12 — content-hash sentinel duplicate ownership.** `qg_sentinel_content_hash_and_slicing_2026_06_10` Rec#1
  (content-hash sentinel) is NOT done; `quality_gates_speed_and_config_ssot_2026_06_09` ships `.qg_content_sentinel` but
  only short-circuits CI-matrix slices, NOT the quickmerge `--files` race. Same target surface, two homes, neither
  closes the race (a "declare your target surface" overlap). **Consolidate to one owner.**
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
- `plans/active/issues/provenance_gate_squash_perpetual_block_2026_06_17.md` — resolved same-day, both items flipped,
  prod-verified, already in CLAUDE.md.

---

## Recommended triage order

1. **Decide D1/D10 (`--frozen` model)** — it's the only finding that can actively _cause_ an incident if an agent
   follows the current CLAUDE.md rule. Everything else is documentation safety.
2. **Refresh `ci-cd-flow.md` (D5–D9) in one pass** — it's the engineer SSOT; a stale SSOT mis-trains every agent.
3. **Fix the CLAUDE.md stale facts (D2/D3/D4)** — quick, high-value (they actively mislead).
4. **Reconcile the two X-contradictions (D11/D12)** and add the D13 SUPERSEDED banner.
5. **Sprawl + lifecycle cleanup (D22/D24/D25)** and the small code/hygiene fixes (D15/D16/D18–D21/D23).

> **Note on capture.** These 25 findings live here as a triage register (audit-result checkboxes are NOT auto-dispatched
> by the orchestrator's `plans/active/` regen). On acceptance, migrate each `- [ ]` into the named destination plan so
> it becomes a tracked todo; this result file archives when all findings are `- [x]` in their parent plans (per
> `plans/audit/README.md`).

---

## Findings checklist (triage handles)

- [ ] D1/D10 🔴 DECISION — resolve the `uv.lock`/`--frozen` model; wire docs + CI to agree →
      `uv_lock_frozen_model_contradiction_2026_06_15`
- [x] D5 ✅ — rewrote ci-cd-flow.md per-unit-staging-PR sections (Pass-2 block, Full-flow diagram, Agent-vs-Human
      Push-to-LDR + Promote rows) to the land-on-LDR / Tier-C-drain model — PM@235c5fd3b
- [x] D2 ✅ — replaced the false "service-deps enforcement is DEAD" warning in CLAUDE.md with "LIVE (fixed 2026-06-11)"
      — PM@235c5fd3b
- [x] D3 ✅ — corrected CLAUDE.md aiohttp `--ignore-vuln` ("two" → "~20-entry block") — PM@235c5fd3b
- [x] D4 ✅ — corrected ldr-to-staging (15m, ci-cd-flow.md) + main-backmerge (hourly, CLAUDE.md) cadences —
      PM@235c5fd3b. The sprawl-issue-doc cron number is tracked separately as D25 (still open).
- [ ] D11 🟠 — reconcile in-image-QG blocking (router plan L67) vs the shipped `_RUN_INIMAGE_QG:false` skip
- [ ] D12 🟠 — consolidate content-hash-sentinel ownership (qg_sentinel_content_hash ⇄ quality_gates_speed)
- [ ] D13 🟠 — add SUPERSEDED banner to qg_commit_quality_boundary L220 (tab-mirror torn out by Path-B)
- [ ] D14 🟠 — record `assert_deps_published_to_ar.py` as reserved/unwired in `cloud_build_router_aws_parity`
- [ ] D22 🟠 — migrate residual todos out of semver_version_bump_skip_ci + cicd_workflow_sprawl_audit, then archive
- [ ] D24 🟠 — delete dead `feature-branch-to-staging.yml` (2 dirs) + `staging-version-gate.yml`; fold into sprawl
      remediation
- [ ] D6 🟡 — ci-cd-flow.md branch-model table: replace `tab/hk/<N>` row with Path-B
- [ ] D7 🟡 — ci-cd-flow.md: delete the wrong "post-cutover LDR retired" block (L918-929)
- [ ] D8 🟡 — ci-cd-flow.md L620: kill-switch arming = protective-autonomous (align to CLAUDE.md)
- [ ] D9 🟡 — ci-cd-flow.md L756-796: refresh/archive the 2026-06-01 "being repaired" snapshot
- [ ] D15 🟡 — `GOOGLE_CLOUD_PROJECT`→`GCP_PROJECT_ID` in promotion_lag_monitor.py + reconcile_release_tags.py
- [ ] D16 🟡 — decide check_strict_quickmerge `scripts/` carve breadth (fix doc or scope code to PM)
- [ ] D17 🟡 — (note) STAGING_PENDING rank-equivalence vs ON_STAGING_STATUSES exclusion
- [ ] D18 🟡 — quickmerge.sh:1481/1534 "30min" → 15min drain comment
- [ ] D19 🟡 — sit-starvation-detector.yml header comment "15 minutes" → matches `*/30`
- [ ] D20 🟡 — fix `locked_since` frontmatter (ci_status_firestore_side_store, ldr_tarball_auto_refresh)
- [ ] D21 🟡 — reassign fleet_git_health_orchestrator `assigned_vm` off the stopped vm-orchestrator
- [ ] D23 🟡 — archive the 4 resolved plans/issues (gate the UI one on `pw:L2 ✓`)
- [ ] D25 🟡 — fix the ldr-to-staging cron number in the cicd_workflow_sprawl_audit issue doc
