---
title:
  "Commit identity wrong fleet-wide — ~14/25 worktrees author as semver-rollout[bot], ~7 as agent@ci.local; + add
  slot·host attribution"
created: 2026-06-03
source:
  - slot-3 worktree audit 2026-06-03 (git config user.email across .tabs/3/*)
  - codex/05-infrastructure/per-tab-worktrees.md § "Commit attribution"
resolved: 2026-06-07
priority: P1
parent_epic: infrastructure_master
estimate_calibrated_ai_days: 0.4
estimate_class: infra
status: RESOLVED
---

> ## ✅ RESOLVED 2026-06-07 — archived (ACKED-INTO-CODE)
>
> All 6 todos shipped + verified 2026-06-07: (1) commit-time identity hook `fix-commit-identity.sh` built (fail-closed,
> CI-skip) + wired into all 4 pre-commit templates + PM live config (PM@92223c894); (2) `rollout-pre-commit-configs.sh`
> deployed the hook to the 7 drifted repos (deployment-service was the only one still lacking it) — fleet now carries
> `fix-commit-identity` + a single canonical gitleaks block; (3) `setup-tab-worktrees.sh` standardises per-worktree
> identity at init/add/reset (host-stable CANON resolution); (4) bot-email leak root-caused + closed
> (`setup-workspace-from-manifest.sh` + `setup-github-auth.sh` writers now guarded; `verify-slot-host-symmetry.sh` is
> the recurrence detector); (5) slot-1 worktrees verified attributing `ikennaigboaka [slot-1·laptop]
> <ikennaigboaka@gmail.com>`; the deployed hook self-heals every other slot/VM on next commit. Codex updated in step:
> `codex/05-infrastructure/per-tab-worktrees.md` § "Commit attribution" reflects what shipped. The optional
> `prepare-commit-msg` trailer remains a nice-to-have only (not blocking). No new durable contract beyond the already-in-
> CLAUDE.md commit-attribution rule.

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
- [x] ✅ [INFRA] P1. **DONE 2026-06-07** — ran `bash scripts/propagation/rollout-pre-commit-configs.sh` (dry-run first:
      7 repos drifted, 18 already-current — the fleet had largely converged since the 2026-06-03 dry-run). Deployed the
      canonical templates (which carry the `fix-commit-identity` hook) to the 7 drifted repos: deployment-service (the
      ONLY one that still LACKED the identity hook — now `identity-hook=2`), client-reporting-api, deployment-api,
      batch-live-reconciliation-service, ibkr-gateway-infra, trading-agent-service, unified-trading-system-ui (the rest
      had the hook but drifted on a duplicated gitleaks block — de-duped to the one canonical block). Committed+pushed
      each `.pre-commit-config.yaml` to its `tab/ikennaigboaka/1` branch (→ tab-mirror → LDR → VMs pull → enforced).
      Verified the rolled-out repos now carry `fix-commit-identity` + the single canonical gitleaks block, and that the
      slot-1 commits correctly attribute to `ikennaigboaka [slot-1·laptop] <ikennaigboaka@gmail.com>` (the hook +
      per-worktree identity working). SSOT: `codex/05-infrastructure/per-tab-worktrees.md` § "Commit attribution".
- [x] ✅ [INFRA] P1. **DONE — VERIFIED 2026-06-07 (already shipped).** `setup-tab-worktrees.sh` already standardises
      per-worktree identity at `--init`/`--add-slot`/`--reset-slot` (lines ~283-285):
      `git config     extensions.worktreeConfig true` +
      `git config --worktree user.name "${CANON_GIT_NAME} [slot-<N>·<host>]"` + `user.email "${CANON_GIT_EMAIL}"`, where
      CANON\_\* resolve host-stably (env `SLOT_CANON_*` → per-machine `git config --global slotIdentity.*` → Ikenna
      default) and `<host>` = `laptop`/hostname or `vm-<id>`. Confirmed in `scripts/dev/setup-tab-worktrees.sh`. Repo:
      unified-trading-pm.
- [x] ✅ [INFRA] P1. **Root-cause the bot-email leak — DONE 2026-06-07.** Found + closed the leak CLASS. (1) The
      provisioning writer is ALREADY repaired: `scripts/setup-workspace-from-manifest.sh` (lines ~347-361) now writes
      the canonical operator identity GUARDED by `-z` ("NOT `agent@ci.local`", resolves env → `slotIdentity.*` → Ikenna
      default) — the historical unguarded `git config --local user.email "agent@ci.local"` that seeded worktree configs
      is gone. (2) Closed the remaining unguarded global-identity writer:
      `github-integration/scripts/automation/     setup-github-auth.sh` unconditionally did
      `git config --global user.email "automation@yourdomain.com"` (the leak class — clobbers an operator identity); now
      GUARDED (only writes when unset, prefers the canonical operator identity over the bot placeholder) —
      PM@<this-commit>. (3) The recurrence guard is ALREADY in `verify-slot-host-symmetry.sh` (lines ~204-243): it fails
      any slot worktree whose `user.email != CANON_EMAIL` or whose `user.name` lacks `[slot-<N>·`, explicitly flagging
      `semver-rollout[bot]` / `agent@ci.local` as a recurred leak. (4) The semver-agent's OWN `chore(release)` commit
      legitimately uses `semver-rollout[bot]` — that runs in CI (ephemeral runner, NOT a worktree) + the hook skips CI,
      so it is not a worktree-leak source. Repos: unified-trading-pm.
- [x] ✅ [INFRA] P2. **Fleet rollout — applied + verified for slot-1 2026-06-07; self-healing fleet-wide via the
      deployed hook.** Slot-1's worktrees carry the canonical `ikennaigboaka [slot-1·laptop] <ikennaigboaka@gmail.com>`
      identity (verified on deployment-service / batch-live-recon / unified-trading-system-ui — both commit author AND
      live `git config user.*`). The `fix-commit-identity` hook (now deployed fleet-wide via the P1 above) is the
      self-healing enforcer for every other slot/VM: it fail-closes + re-writes per-worktree identity on the next
      commit, and `verify-slot-host-symmetry.sh` is the recurrence detector. A one-shot mass-rewrite of every OTHER
      slot's existing worktree configs is a per-slot/per-host operation (each host runs `setup-tab-worktrees.sh` /
      `verify-slot-host-symmetry.sh`) — the hook makes a stale config self-correct on first commit rather than requiring
      a central sweep. Optional `prepare-commit-msg` trailers remain a nice-to-have if CI name-parsing proves awkward.
