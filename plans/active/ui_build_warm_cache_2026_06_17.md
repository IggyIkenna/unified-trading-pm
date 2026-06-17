---
title: UI build warm-cache — keep the UI QG build cache warm so only changed code rebuilds
parent_epic: infrastructure_master
assigned_vm: vm-cross-cutting
priority: P2
status: active
execution_scope: local-only
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
created: 2026-06-17
locked_by: live-defi-rollout
related_plans:
  - plans/archive/2026_06/quality_gates_speed_and_config_ssot_2026_06_09.md
source:
  - MIGRATED FROM quality_gates_speed_and_config_ssot_2026_06_09.md § "UI build warm-cache" (2026-06-17)
  - slot-3 2026-06-10 — cold-clone UI build tripped the 90s QG gate; warm rebuild = 365 ms
---

# UI build warm-cache

> **MIGRATED FROM** `quality_gates_speed_and_config_ssot_2026_06_09.md` (2026-06-17) so the QG-speed/config plan could
> close its completed core. These are UI-repo build-performance items, **distinct from the Python-fleet QG-speed work**
> (which is done). They need a **UI-capable slot** + the **playwright gate** (`pw:L2 ✓` + a regression spec) for any
> change touching `deployment-ui` / `unified-trading-system-ui` source — see CLAUDE.md § "UI changes — playwright gate".
> Do NOT rush them through a non-UI slot.
>
> **Operator direction (2026-06-10)**: if fundamental deps don't change, the build cache should be warm ALWAYS — only
> our code rebuilds.

- [ ] [CODE] P2. `tsc` incremental for UI repos: `"incremental": true` + gitignored `.tsbuildinfo` (deployment-ui +
      unified-trading-system-ui tsconfigs) — only changed files re-check; cold cost limited to a fresh clone's first
      build. Repo: deployment-ui, unified-trading-system-ui. **[UI]** — needs `pw:L2 ✓` + regression spec.
- [ ] [CODE] P2. Pre-warm in `setup.sh`: run one `npm run build` at clone-setup time so the QG gate never pays the
      cold-cache cost (the cold build moves to where there is no timeout). Repo: unified-trading-pm
      (`scripts/quality-gates-base` setup template) + the two UI repos.
- [ ] [INFRA] P3. Evaluate pnpm global content-addressable store for UI repos: hardlinked node_modules → identical
      inodes across ALL slot clones → OS page cache warm fleet-wide while deps are unchanged (npm copies per-clone: N×
      disk + N× cold reads). Decision item — changes lockfile format + CI install steps.
- [ ] [SCRIPT] P3. base-ui.sh: one automatic retry on the build-timeout class (cold-trip passes on retry; a genuine hang
      fails twice) — removes the human re-run without weakening the budget. Repo: unified-trading-pm
      (`scripts/quality-gates-base/base-ui.sh`); exercise against a UI repo build before shipping.

## Success criteria

- A warm-cache UI QG build re-checks only changed files (sub-second incremental); a fresh clone pays the cold build once
  (at setup, off the timed gate path).
- No UI source change ships without `pw:L2 ✓` + a cited regression spec (playwright gate).
