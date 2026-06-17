---
title:
  "QG base-service.sh exit-code bug — a FAILED ratchet step (STEP 5.94 observed) falls through to overall exit 0 +
  sentinel write"
created: 2026-06-11
source:
  - mtds CF-11 swallow batch QG runs 2026-06-11 (mtds_honest_absence_swallow_remediation_2026_06_10.md)
locked_by: live-defi-rollout
priority: P2
status: active
---

## What I found

While running the mtds CF-11 swallow batch through `bash scripts/quality-gates.sh --no-fix` (mtds, slot-4 host), a run
with a **❌ FAILED STEP 5.94** (fallback-import ratchet over baseline, 5 > 3) still finished with **overall exit 0 and
wrote `.qg_last_passed_sha`**. Root cause observed in `unified-trading-pm/scripts/quality-gates-base/base-service.sh`
(~line 2295): an integer comparison receives a multi-line value (`[: 0\n0: integer expression expected` on stderr), so
the step's failure is not propagated into the overall verdict — the red step is printed but does not gate.

The mtds batch itself was fixed properly (shims removed → 5.94 back at baseline 3, true-green run) — but the gate would
have let it ship red.

## Why it matters

- The QG sentinel is the workspace's commit/merge quality boundary (HARD RULE) — a hollow green sentinel means ratchet
  regressions (fallback-imports, ruff-rule ratchets, possibly other `check_*` post-gates that share the same
  exit-aggregation path) can reach `live-defi-rollout` and the staging PR believing they were gated.
- Composes with (but is distinct from) the known "LOCAL QG HARNESS collects the WRONG test suite — hollow sentinel" P2
  finding in `master_data_canonicalisation_migration_catalogue_2026_06_07.md`: that one is test-collection scope; this
  one is exit-code aggregation of a step that DID run and DID fail.
- Fleet-wide blast radius: `base-service.sh` is PM-sourced and fleet-live the moment it's fixed (no per-repo rollout) —
  and per AUTONOMOUS_AGENT_RULES rule 11, the fix must be proven against every repo before shipping (a stricter gate
  that suddenly enforces could redden repos that were silently over-ratchet).

## Recommended decision

1. Fix the aggregation: sanitize/scalarize the step-result variable before the integer test (likely a
   `wc -l`/command-substitution emitting two lines), add `set -u`-safe handling, and make ANY ❌ step force overall exit
   ≠ 0 + suppress the sentinel write.
2. BEFORE shipping the fix, sweep `quality-gates.sh --no-fix` across all repos to find which are currently
   silently-over-ratchet (the fix flips them loud) — fix or re-baseline those in the SAME change (rule 11a).
3. Add a regression test/assertion in the QG harness (a planted failing ratchet step must produce exit 1 + no sentinel).

Owner suggestion: vm-cross-cutting (PM quality-gates-base). Repos: unified-trading-pm (+ fleet verification).

## Progress / status (2026-06-16, QG-agent)

- **Step 1 (fix) — AUTHORED, HELD.** The aggregation fix is written + verified on
  `origin/wip-preserve/qg-ratchet-hardening-2026-06-16` (base-service.sh: `_V_PRE_RATCHET=$V` snapshot after the
  codex-compliance verdict + a post-ratchet `_RATCHET_FAILS=$((V-_V_PRE_RATCHET)); [[ >0 ]] && exit 1` before the
  sentinel write; integers are scalar so the `[: integer expression expected` symptom can't recur). NOT shipped yet.
- **Step 2 (fleet sweep) — DONE.** Swept all three ratchets fleet-wide:
  - **5.94 fallback-imports:** ✅ clean.
  - **5.95 DTZ/TID251:** found instruments-service `tid251 60>59` (1 new `from google.cloud import storage`) — **FIXED +
    landed** (`validate_sports_fixtures_v2_parity.py` → UCI `get_storage_client`); now 59==baseline, fleet-clean.
  - **5.97 DeFi citations:** ❌ **8 repos over baseline 0 (~468 uncited addresses)** — the 2026-06-16 seed only
    grandfathered UAC=138, missing all service-repo source. **This is the rollout blocker.**
- **Step 3 (regression test) — AUTHORED, HELD.** `tests/test-ratchet-exit-code-aggregation.sh` on the same preserve
  branch (planted failing ratchet step → asserts exit 1 + no sentinel).
- **✅ UNBLOCKED 2026-06-17** — Ikenna chose **cite-first** and cited the ~468 fleet-wide (execution 225, UAC 138, e2e
  demo-wallet, …); `defi_address_citation_baseline.yaml` ratcheted to 0 for every repo. Live fleet sweep is clean on all
  three ratchets (5.94 / 5.95 / 5.97 = 0 over-baseline). **The hardening (Step 1 + Step 3) is now shippable** from
  `wip-preserve/qg-ratchet-hardening-2026-06-16` — promote it to PM `main` (base-service.sh is PM-sourced, fleet-live on
  merge; re-verify a fleet QG-green sample first). Blocker doc closed:
  `defi_address_citation_baseline_incomplete_seed_2026_06_16.md` (status: resolved).
