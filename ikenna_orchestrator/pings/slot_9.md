> **⚠️ FRESH LEDGER — 2026-05-19 dispatch.** Booting agents: read this file top-to-bottom + then
> `plans/active/work_split_2026_05_19_ikenna.md` § Slot 9. This is your full intra-side ping ledger.

---

# Slot 9 — Intra-side ping ledger (tab/ikennaigboaka/9)

## [slot 1 main → slot 9] 2026-05-19 ~14:30 UTC — 🔴 NEW THEME — ML repo consolidation (FULL PLAN)

Your previous theme (batch_live_symmetry Tabs 4–7 + cme_polymarket_arb Phase 1 + promote_workflow_may23
residuals) is **DEFERRED to Cycle 3**. New theme: **ml_repo_consolidation_2026_05_19 — ALL 10 PHASES,
single-slot ownership**. ~6 cal-AI-days. **Independent of strategy-twin slots (3-8)** — execute in parallel.

The ML consolidation is the smaller of the two: 2 source repos (`ml-training-service` + `ml-inference-service`)
into a new `ml-service` repo. Pre-audit confirmed **ZERO external Python imports** between the source repos —
Phase 4 (a) import-rewrite scope is trivial (~3-4 string-literal updates only).

**Critical P0 sequencing**:

1. **Phase 0.5 (Phase 0 audit finding #7)**: rename `ml_inference_service/io/loader.py:FeatureSubscriber` →
   `IoFeatureSubscriber` BEFORE Phase 3 subtree-merge. Two distinct classes share the same name in the same
   package (`app/core/feature_subscriber.py:FeatureSubscriber` also exists) — name-collision would create
   ambiguous symbols post-merge.
2. **Phase 2 is operator-gated**: `gh repo create IggyIkenna/ml-service --private --add-readme` is a human
   action. File ping in `plans/active/_agent_pings.md` when Phase 1 completes; wait for operator ack before
   bootstrapping the skeleton.
3. **Phase 4 (h) decision RESOLVED 2026-05-19**: operator picked Option 2 — single flat-deps Docker image
   (~1.2GB). No `[project.optional-dependencies] training` split. No `INFERENCE_ONLY` build-arg. Plan body
   updated; codex stub updated. See [`ikenna_orchestrator/pings/slot_1.md`](slot_1.md) for rationale.

**Phase summary**:

| Phase | Description                                                                   |
| ----- | ----------------------------------------------------------------------------- |
| 0     | Pre-audit (DONE 2026-05-19 — read artifact)                                   |
| 0.5   | FeatureSubscriber rename (P0 name-collision fix)                              |
| 1     | UAC/UTL schema prep (likely no-op — no new enums needed)                      |
| 2     | NEW `ml-service` repo bootstrap (operator-gated `gh repo create`)             |
| 3     | Subtree-merge 2 source repos with history preserved                           |
| 4     | Fix internal imports + unify CLI (flat-deps Docker per operator decision)     |
| 5     | UTL lifts (`pre_crash_checkpoint`, `ConfigReloaderBase` shared with slot 5)   |
| 6     | Parity validation (boot + QG + functional, byte-identical model weights)      |
| 7     | Archive 2 source repos via `gh repo archive` (operator-gated)                 |
| 8A    | Launcher migration in deployment-service                                      |
| 8B    | deployment-api + deployment-ui service-list update                            |
| 9     | Codex SSOT updates (8 enumerated paths; `ml-service-architecture.md` STUB already created — promote to stable) |
| 10    | Workspace QG sweep                                                             |

**Coordination with slot 5**: slot 5 lifts `ConfigReloaderBase` to UTL as part of strategy consolidation. After
their UTL PR lands, your Phase 5 can absorb ml-service's config_reloaders into the same base class.

- Plan: [`plans/active/ml_repo_consolidation_2026_05_19.md`](../../plans/active/ml_repo_consolidation_2026_05_19.md) — read top-to-bottom; "Phase 0 audit findings" section has confirmed scope.
- Pre-audit (READ FIRST): [`plans/active/issues/ml_repo_consolidation_preaudit_2026_05_19.md`](../../plans/active/issues/ml_repo_consolidation_preaudit_2026_05_19.md) — 598 lines, all 8 sections (a)-(h) populated.
- Codex stub already created: [`codex/04-architecture/ml-service-architecture.md`](../../codex/04-architecture/ml-service-architecture.md) — currently `status: stub`; promote to `stable` in Phase 9 after merge ships.
- Boot fresh per `cursor-configs/SUB_AGENT_MANDATORY_RULES.md`.

**Gap-close addendum 2026-05-19 ~14:45 UTC** (revised total: ~7.2 cal-AI-days; bundled into your existing scope):

- **P0 Phase 4 (a-extension)** — e2e-testing shell scripts beyond Python imports (~0.25 cal-day). Pre-audit
  § (b) found ~3-4 Python `import` updates; shell-script invocations not audited:

  ```bash
  rg -nF -e 'ml_training_service' -e 'ml_inference_service' -e 'ml-training-service' -e 'ml-inference-service' \
     e2e-testing/scripts/ system-integration-tests/scripts/ 2>/dev/null
  rg -n 'python -m ml_(training|inference)_service' e2e-testing/ system-integration-tests/ 2>/dev/null
  ```

  Rewrite to `python -m ml_service --operation <op>`.

- **P1 Phase 4 (i)** — Logging + observability consolidation (~0.5 cal-day). Mirrors strategy-twin slot 4:
  per-sub-package logger naming (`ml_service.training`, `ml_service.inference` via `logging.getLogger(__name__)`);
  OpenTelemetry `service.name=ml-service` + `subsurface={training,inference}` labels; Prometheus + Cloud Trace
  consolidation. **Coordinate with slot 4** if `ConfigReloaderBase` lift surfaces shared logger-config patterns.

- **P2 Phase 3 addendum** — Drop source-repo `docs/` during subtree-merge (5-min addendum to recipe). Record
  in DEPRECATION_NOTICE.md: "docs/ content not migrated — see `codex/04-architecture/ml-service-architecture.md`."

- **P2 Phase 2 + 8A addendum** — GitHub Actions workflows (~0.25 cal-day). Phase 2 (g) seeds ml-service with
  templated workflows. ADD: enumerate any per-source-repo CUSTOM workflows (cron-scheduled retraining,
  scheduled model-bake jobs) NOT in the rollout template; migrate to ml-service or confirm obsolete.

- **P3 Phase 7 addendum** — Per-repo markdown files (~0.1 cal-day). Each source repo carries `CHANGELOG.md`,
  `QUALITY_GATE_BYPASS_AUDIT.md`, `CONTRIBUTING.md`. Decision: prepend each `CHANGELOG.md` to
  `ml-service/CHANGELOG.md` under `## Consolidation 2026-05-19` heading; merge `QUALITY_GATE_BYPASS_AUDIT.md`
  rows per sub-package; preserve only workspace-canonical `CONTRIBUTING.md`.

- **P3 Phase 2 addendum — GitHub repo settings on NEW ml-service repo** (~0.1 cal-day). After Phase 2 (a)
  `gh repo create`: configure branch protection on `main`:

  ```bash
  gh api repos/IggyIkenna/ml-service/branches/main/protection -X PUT \
     -f required_status_checks[strict]=true \
     -f required_status_checks[contexts][]='quality-gates' \
     -f required_status_checks[contexts][]='workspace-qg' \
     -f required_status_checks[contexts][]='staging-lock-check' \
     -F enforce_admins=true \
     -F required_pull_request_reviews[required_approving_review_count]=1 \
     -F allow_force_pushes=false
  ```

  Also seed `.github/semver-agent.yml` per workspace template (copy from
  `unified-trading-pm/scripts/workflow-templates/semver-agent.yml.tmpl`).

Ack with `[ack] slot 9 booted` once you've read the plan + pre-audit and started Phase 0.5 (FeatureSubscriber rename).
