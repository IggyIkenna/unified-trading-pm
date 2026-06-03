---
title:
  "Commit identity wrong fleet-wide — ~14/25 worktrees author as semver-rollout[bot], ~7 as agent@ci.local; + add
  slot·host attribution"
created: 2026-06-03
author: ikenna (slot-3)
source:
  - slot-3 worktree audit 2026-06-03 (git config user.email across .tabs/3/*)
  - codex/05-infrastructure/per-tab-worktrees.md § "Commit attribution"
locked_by: live-defi-rollout
priority: P1
---

## What I found

Auditing `git config user.email` across all 25 repos in the slot-3 worktree set (`.tabs/3/*`): **only
`unified-trading-pm` had the correct `ikennaigboaka@gmail.com`.** The rest are misconfigured:

- **~14 repos author as `semver-rollout[bot]@users.noreply.github.com`** — instruments-service, mtds, MDPS, UAC, UTL,
  execution / strategy / deployment / alerting / batch-live-recon / client-reporting / deployment-api / ibkr /
  trading-agent. **Any agent commit to these masquerades as the semver bot.**
- **~7 repos author as `agent@ci.local`** — agent-orchestrator, e2e-testing, greeks, ml-service,
  system-integration-tests, unified-trading-api, unified-trading-system-ui (unattributed generic CI identity).

The author **name** is bare `ikennaigboaka` everywhere, so CI alerts + cross-agent triage cannot tell which slot/host
produced a commit (the gap that made the 2026-06-03 PM branch-alignment triage guess-work).

Slot-3 worktrees were fixed in place this session (`user.name = "ikennaigboaka [slot-3·laptop]"`,
`user.email = "ikennaigboaka@gmail.com"` on all 25). **This is a per-worktree fix on ONE slot only — the misconfig
recurs on every other slot/host until the provisioning is fixed.**

## Why it matters

- The `semver-rollout[bot]` email leaking into agent worktrees means agent commits look bot-authored — semver-agent's
  own bot/author detection keys off that email, risking skipped-as-own-commit / loop / mis-attribution; and it pollutes
  the "who did what" signal the operator wants for CI alerts.
- Cross-repo / fleet-wide / contradicts the just-codified commit-attribution contract → "Big finding" per Findings
  Triage.

## Recommended decision

> **Enforcement is inherently CLIENT-SIDE** (GitHub accepts any commit author — no server gate). Three layers; the
> shared-template commit hook is the only one that applies to EVERY commit in EVERY repo. The CLAUDE.md directive is a
> read-it-and-comply instruction, NOT a gate — it does not block a bad commit.

- [x] ✅ [INFRA] P1. **Commit-time identity hook BUILT (the "everywhere" enforcer)** — `PM@92223c894`. Script
      `scripts/hooks/fix-commit-identity.sh` (derives slot from `tab/<op>/<N>` branch + host from `VM_NAME` else laptop;
      enforces `git config --worktree user.name="ikennaigboaka [slot-N·host]"` / `user.email=ikennaigboaka@gmail.com`;
      **FAIL-CLOSED** — git resolves author before hooks, so it blocks + self-heals on drift, re-commit lands correct;
      **silent no-op when correct**; **skips in CI** so the semver bot identity is preserved). Wired into all 4
      `scripts/pre-commit-templates/*.pre-commit-config.yaml` + PM's live `.pre-commit-config.yaml`. Tested end-to-end
      (laptop→`slot-7·laptop`, `VM_NAME=vm-cefi`→`slot-7·vm-cefi`, wrong-identity commit blocked then retry correct) and
      ran live on PM@92223c894 ("Enforce slot·host commit identity … Passed").
- [ ] [INFRA] P1. **DEPLOY the hook to all repos + VMs** — run `bash scripts/propagation/rollout-pre-commit-configs.sh`
      (copies the updated templates → every repo's `.pre-commit-config.yaml`; dry-run 2026-06-03 shows all 25 repos
      drifted from template, so this ALSO re-aligns pre-existing config drift), then commit+push each changed
      `.pre-commit-config.yaml` per repo (→ tab → LDR → VMs pull → `prek install` → enforced on every commit). 25-repo
      controlled deploy (handle per-repo tab-vs-LDR divergence as in the recovery rule). SSOT:
      `codex/05-infrastructure/per-tab-worktrees.md` § "Commit attribution".
- [ ] [INFRA] P1. **`setup-tab-worktrees.sh` standardises identity per worktree** at
      `--init`/`--add-slot`/`--reset-slot` via `git config extensions.worktreeConfig true` (once per repo) +
      `git config --worktree user.name     "ikennaigboaka [slot-<N>·<host>]"` +
      `git config --worktree user.email "ikennaigboaka@gmail.com"` (`<host>` = `laptop`/hostname on a workstation,
      `vm-<id>` on a fleet VM; `<N>` from the `tab/<op>/<N>` branch). Repo: unified-trading-pm
      (`scripts/dev/setup-tab-worktrees.sh`). SSOT: `codex/05-infrastructure/per-tab-worktrees.md` § "Commit
      attribution".
- [ ] [INFRA] P1. **Root-cause the bot-email leak** — find what writes `semver-rollout[bot]` / `agent@ci.local` into
      persistent per-worktree `git config` (candidate: a `setup.sh` / semver-agent / CI bootstrap step using
      `git config` instead of `git -c user.email=…` one-shots) and stop it writing persistent identity. Add a recurrence
      guard to `verify-slot-host-symmetry.sh` (fail a worktree whose `user.email != ikennaigboaka@gmail.com` or whose
      `user.name` lacks `[slot-<N>·`). Repos: unified-trading-pm + wherever the leak originates.
- [ ] [INFRA] P2. **Fleet rollout** — apply the standardised identity across every other slot + VM worktree (loop,
      idempotent), then verify zero non-canonical emails fleet-wide. Optional follow-up: a `prepare-commit-msg` hook
      emitting machine-parseable `Agent-Slot:` / `Agent-Host:` trailers if the name string proves awkward for CI to
      parse.
