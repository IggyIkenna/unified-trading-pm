---
title:
  uv.lock / --frozen model is half-applied + contradictory — collides with LDR↔staging tree convergence, makes the
  "regen lock" fix restart the Tier-C promote runaways
created: 2026-06-15
source:
  - e2e-testing Tier-C runaway promote breaker (Slack #ci-failures 2026-06-15 10:06)
  - features-service provenance-gate block + 28/6h promote runaway (Slack 2026-06-15 10:06)
  - PM@5bde2d641 "codify CI uv sync --frozen + floor-bump-regen-lock rule; hand CI diff to Ikenna" (2026-06-12)
  - PM@a89e234ee "relax uv lock --check to warn-only" (2026-06-09)
  - origin/main python-quality-gates-v2.yml:459 (bare `uv sync`)
  - e2e-testing `uv lock --check` exit 1 after floor bump (empirical 2026-06-15)
locked_by: live-defi-rollout
priority: P1
status: active
---

## What I found

A Tier-C LDR→staging promote **runaway** (e2e-testing 30 merges/6h → breaker tripped; features-service at 28/6h, ~2
ticks behind) was traced to a one-line `pyproject.toml` dependency-floor divergence. While fixing it, a deeper,
fleet-wide contradiction in the `uv.lock` / `--frozen` model surfaced that makes the _obvious_ fix dangerous. This doc
captures it for a proper decision **before** anyone runs a fleet-wide `uv sync` + commit-lock pass.

### 1. The runaway's direct cause is the dep-bump bot, NOT the lock rule

The divergent commit on e2e-testing (identical pattern on features-service, greeks-service):

```
2be3675  chore(deps): pin unified-api-contracts to 0.7.0
         Author: github-actions[bot]   Date: 2026-06-14 20:43 UTC
         pyproject.toml | 2 +-          ← ONLY pyproject.toml, NO uv.lock
```

It landed on **staging only** (never `live-defi-rollout`), pyproject-only, with **no staging→LDR back-merge**. That
one-line floor difference (`unified-api-contracts>=0.6.0` vs `>=0.7.0`) keeps LDR's tree SHA ≠ staging's tree SHA, so
the drain's tree-equality convergence gate
([ldr-to-staging-promote.yml:169](../../.github/workflows/ldr-to-staging-promote.yml#L169)) never trips → the drain
re-promotes every ~40s (amplified by `ci-status-update.yml` re-firing `tier-ab-green` on every `STAGING_GREEN`) → 30
merges/6h → runaway breaker.

**The actual runaway source is: `update-dependency-version.yml` / the dep-bump bot bumps dependency floors on
staging/main only, not on the LDR integration axis, and nothing propagates them down.**

### 2. The Friday `--frozen` rule is half-applied — docs say one thing, CI does another

- **PM@5bde2d641 (Fri 2026-06-12 19:37 +0530): "codify CI uv sync --frozen + floor-bump-regen-lock rule; hand CI diff to
  Ikenna"** changed **docs only** (CLAUDE.md, codex `quality-gates.md` + `ci-cd-flow.md`, the dep-promotion plan, agent
  pings). **No `.yml` / `.sh` touched.** The CI implementation was explicitly _handed to Ikenna_ and never wired.
- **Deployed reality on `origin/main` today:** `python-quality-gates-v2.yml:459` is bare **`uv sync`** — _not_
  `--frozen`. And `base-service.sh:305` / `base-library.sh:175` run `uv lock --check` **warn-only** (PM@a89e234ee,
  2026-06-09: _"nothing installs --frozen → lock is a record not a pin; pyproject range is the real contract"_).

So **CLAUDE.md asserts "CI installs via `uv sync --frozen`, so a floor change only reaches CI if the lock is
regenerated," but the running v2 does bare `uv sync` and treats the lock as a warn-only record.** The rule's premise is
false as deployed. Doc and machinery contradict each other.

### 3. The dangerous interaction — "regen + commit the lock" would RESTART the runaways

Empirical, on e2e-testing after the floor bump:

```
uv lock --check  →  exit 1: "The lockfile at `uv.lock` needs to be updated"
```

Regenerating the lock here is **not** a no-op — it rewrites `uv.lock`. The trap:

- The staging dep-bump (`2be3675`) bumped pyproject **without** regenerating the lock → staging's lock is the _old_ one.
- The runaway was stopped (e2e-testing@a0a3e01) by matching staging's pyproject **and deliberately NOT regenerating the
  lock** — both branches keep the identical (stale) lock, so only pyproject had to converge. Trees verified equal
  (`ef174b2`).
- **If we now run `uv sync` + commit `uv.lock` on LDR fleet-wide, LDR's lock changes → LDR lock ≠ staging lock → trees
  re-diverge → the Tier-C runaways come straight back.**

The Friday "regen lock on every toml change" rule and the "LDR tree must equal staging tree" convergence requirement are
in **direct conflict for editable-internal-dep bumps**, unless the lock is regenerated in lockstep across LDR +
staging + main per repo.

### 4. The rule is also over-broad for internal editable deps

`unified-api-contracts` is an editable path source in the lock (`editable = "../unified-api-contracts"`). Its lock
`version` field is cosmetic — `uv sync` resolves the on-disk sibling regardless of the floor. CLAUDE.md _already_ says
(PM@d1c9967ca): _"uv.lock already right (editable internal / exact external) — no exact-pin bug to fix."_ So for
**internal** editable deps a floor bump needs no lock regen for correctness; the Friday rule meaningfully applies only
to **external** (exact-pinned) deps. Applied to internal deps it just manufactures cross-branch lock churn — already a
known toil source (PM@1afb7582d: _"plain `uv sync` re-stamped uv.lock (editable UTL bump) and jammed the ff-pull
cron"_).

## Why it matters

- **Live incident class:** at least 3 repos (e2e-testing [fixed], features-service [28/6h, imminent], greeks-service
  [6/6h]) are/were in a Tier-C promote runaway burning Actions spend and tripping breakers. More may follow as the
  dep-bump bot keeps landing staging-only floors.
- **Booby-trapped fix:** the intuitive remediation ("update the lock files and commit them") will reintroduce the loops.
  Anyone acting on the current CLAUDE.md rule without knowing the convergence constraint will make it worse.
- **Contradicts a workspace SSOT:** CLAUDE.md / codex assert a `--frozen` model the deployed CI doesn't implement →
  cross-repo, affects every Python repo's dep handling.

## Recommended decision (to resolve, not yet actioned)

1. **Pick ONE lock model and make docs + CI agree.** Either:
   - (a) Truly adopt `--frozen`: wire `python-quality-gates-v2.yml` install to `uv sync --frozen`, make
     `uv lock --check` blocking in `base-*.sh`, **and** solve the cross-branch lockstep problem (lock must be
     regenerated on LDR+staging+main together, or via a clean-start force-sync) so it doesn't perpetuate tree
     divergence; **or**
   - (b) Keep "lock is a record" (status quo CI): **revert/scope the Friday CLAUDE.md + codex rule** so docs match the
     bare-`uv sync`, warn-only reality.
2. **If keeping regen-lock: scope it to EXTERNAL deps only.** Internal editable deps (`unified-*` siblings) are exempt —
   regen there causes churn + cross-branch divergence + runaway-restart risk and is unnecessary for correctness.
3. **Fix `update-dependency-version.yml`** (the actual runaway source) to land floor bumps on `live-defi-rollout` (the
   SSOT integration axis), not staging-only, so they propagate without a manual back-merge.
4. **Add staging→LDR convergence** for genuinely-newer staging-only content (today only `main-backmerge-to-ldr.yml`
   exists; there is no staging→LDR drain, so any staging-only floor bump loops until reconciled by hand).

**Hold:** do not run a fleet-wide `uv sync` + commit-lock pass until #1 is decided — it is the step that determines
whether lock regeneration is safe. Until then, stop active runaways the convergence-safe way (match pyproject to staging
on LDR, do **not** touch the lock), as already done for e2e-testing@a0a3e01.

## Field evidence (2026-06-16, QG-agent)

The fleet CVE + starlette propagation (`starlette_cve_2026_54282_fleet_alignment_2026_06_16.md`) bumped 8 service repos

- UTL + UAC (`pyarrow>=23.0.1`, `python-multipart>=0.0.31`, `starlette>=1.3.1,<2.0.0`) **pyproject-only** — and the
  result is a SPLIT datapoint that sharpens (not resolves) the contradiction:

* **9 of 10 repos:** pyproject-only worked — `quality-gates.sh` GREEN locally (bare `uv sync` re-resolves to the bumped
  floor → pip-audit clean), landed on LDR, `check-dependency-alignment.py` GREEN, no Tier-C runaway restarted.
* **fund-administration-service: pyproject-only was NOT enough.** My local QG went green (bare `uv sync`), but a later
  pass hit a **pip-audit QG BLOCK** (`python-multipart 0.0.29` still installed from the stale lock) →
  fund-admin@`ab51c0c` **regenerated `uv.lock`** (`python-multipart 0.0.29→0.0.32`, `starlette 1.1.0→1.3.1`) to actually
  clear the CVE. This is exactly the §2 contradiction in the wild: an environment that resolves from the **lock** (not a
  bare re-resolve) keeps the vulnerable pin despite the bumped floor, so the floor alone doesn't reach pip-audit there —
  a lock regen was required.

Takeaway: the convergence-safe pyproject-only path works **when the gate re-resolves from the range**, but **breaks
where the lock is authoritative** — fund-admin needed the regen the §1 decision is meant to govern. Still does NOT
resolve the underlying `--frozen`-vs-bare-`uv sync` contradiction (#1 remains the open decision); fund-admin is now a
concrete data point for it.

## Composes with

- `plans/active/dependency_promotion_range_pins_and_major_bump_sit_2026_06_09.md` (the dep-promotion model this rule
  edits).
- The Tier-C drain / runaway-breaker machinery in `ldr-to-staging-promote.yml` + `ci-status-update.yml` (Ikenna's
  actively-redesigned promote-bot surface — items 3/4 above touch it).
- CLAUDE.md § "Dependencies + builds" (the floor-bump-regen-lock bullet, codified 2026-06-12) — the doc side of the
  contradiction.
