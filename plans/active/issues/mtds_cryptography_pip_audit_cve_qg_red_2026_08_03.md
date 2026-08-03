---
doc_type: issue
title: >-
  market-tick-data-service quality-gates.sh RED repo-wide — pip-audit CVE-2026-69247 in pinned cryptography 49.0.0 fails
  Codex Compliance for every commit
summary: >-
  While shipping an unrelated tradfi manifest bug fix (tradfi_es_cme_ohlcv_zero_capture_2026_07_30.md's P2 todo), full
  `bash scripts/quality-gates.sh` on market-tick-data-service failed with exit code 1 — the ONLY failing check (9924+
  tests all green) is `pip-audit vulnerabilities found: cryptography 49.0.0: CVE-2026-69247`, which the Codex Compliance
  gate counts as 1 violation against a max-allowed of 0. Verified pre-existing and unrelated to my diff via `git stash`
  (cryptography==49.0.0 is the pinned/locked version regardless of my 3-file change, which touches zero dependency
  files). This blocks `quickmerge --agent` for EVERY commit to this repo right now, not just mine (Pass-1 QG never
  writes the `.qg_last_passed_sha` sentinel on a non-zero exit).
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [ci, quality-gates, pip-audit, cve, cryptography, repo-blocker, dependency]
related: [/plans/active/issues/tradfi_es_cme_ohlcv_zero_capture_2026_07_30.md]
created: 2026-08-03
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
source:
  [
    "slot-3 worker, tradfi_es_cme_ohlcv_zero_capture-008, discovered while running Pass-1 quality-gates.sh for an
    unrelated CME OHLCV manifest fix, 2026-08-03",
  ]
context_scope: [market-tick-data-service/pyproject.toml, market-tick-data-service/uv.lock]
---

# market-tick-data-service quality-gates.sh RED — pip-audit CVE in pinned `cryptography`

## What I found

Running `bash scripts/quality-gates.sh` (and `--no-fix`) on market-tick-data-service HEAD (`c59f55c0`,
live-defi-rollout) exits **1**. Every other check passes — 9924 tests passed / 25 skipped / 1 xpassed,
ruff/basedpyright/codex-compliance all green except one line:

```
❌ pip-audit vulnerabilities found
  cryptography 49.0.0: CVE-2026-69247 — ### Summary  `pkcs7_decrypt_der`, `pkcs7_decrypt_pem`, and
  `pkcs7_decrypt_smime` reported the outcome of decrypting a `R...` [truncated by the gate's own output]
✅ No internal advisories defined — check passed
❌ Codex compliance FAILED: 1 violations (max allowed: 0)
```

`pyproject.toml` pins `cryptography>=47.0.0,<50.0.0`; `uv.lock` resolves that to `49.0.0` (uploaded 2026-06-12 per the
lockfile). Confirmed via `git stash` (removing my unrelated 3-file diff) that `cryptography==49.0.0` is installed in
`.venv` regardless of my change — this is a dependency-pin issue, not something my diff introduced or can fix by editing
application code.

## Why it matters

- Every commit to market-tick-data-service — not just this one — hits the same Codex Compliance gate failure right now,
  so Pass-1 `quality-gates.sh` never writes `.qg_last_passed_sha` for ANY HEAD SHA, which means Pass-2
  `quickmerge --agent` refuses for the whole repo (sentinel mismatch). This is a repo-wide shipping blocker, not scoped
  to my task.
- My actual task (`tradfi_es_cme_ohlcv_zero_capture_2026_07_30.md`'s P2 todo — CME OHLCV manifest `instrument_id`
  blank-write fix) is otherwise fully done: root-caused, fixed, 3 new regression tests
  - all existing tests green, committed `c59f55c0`. It cannot ship via the mandated quickmerge flow until this is
    resolved.

## Recommended decision

Two independent paths, either closes this issue:

1. **Version bump**: if a `cryptography` release ≥50.0.0 (or a patched 49.x, if the CVE has a backport) fixes
   CVE-2026-69247, bump `pyproject.toml`'s pin + `uv lock` + re-run the full fleet's QG to confirm no breaking API
   changes (cryptography backs several TLS/JWT/encryption call sites — needs a real test pass, not just a version-string
   edit).
2. **Internal advisory suppression**: if no fix release exists yet (or the exploit path doesn't apply to how this
   workspace uses `cryptography`), the gate output shows an existing "internal advisories" mechanism
   (`✅ No internal advisories defined — check passed` — i.e. an advisories file/registry the codex-compliance check
   already consults). An operator/security-owning agent should assess applicability and, if accepted, register
   CVE-2026-69247 there with a stated justification — never silently disable the pip-audit check itself.

This is a dependency-security judgment call (patch vs. accept-and-suppress), not a mechanical fix I should make
unilaterally inside an unrelated data-pipeline bug-fix task.

## Todos

- [ ] [INFRA] P1. Assess `cryptography` CVE-2026-69247 against market-tick-data-service's actual usage
      (TLS/JWT/encryption call sites) and either (a) bump to a patched version + fleet-wide QG re-verify, or (b)
      register an accepted internal advisory with justification if the exploit path doesn't apply. Repo:
      market-tick-data-service.
- [ ] [INFRA] P2. Once resolved, sweep sibling repos' `uv.lock` for the same `cryptography` pin (shared dependency
      across the fleet) — confirm whether this is single-repo or fleet-wide exposure.
