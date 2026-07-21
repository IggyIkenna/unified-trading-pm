---
doc_type: issue
title: >-
  unified-trading-library's pip-audit gate fails on pyasn1 0.6.3 CVEs (CVE-2026-59885/59886), blocking every quickmerge
  in the repo — unrelated to any single agent's in-flight diff
summary: >-
  `bash scripts/quality-gates.sh --no-fix` on `live-defi-rollout` fails the CODEX COMPLIANCE section's `pip-audit`
  check: pyasn1 0.6.3 (a transitive dependency, pinned via `pyasn1-modules` in `uv.lock`, likely pulled in through
  google-auth/google-cloud libs) has two disclosed CVEs (CVE-2026-59885: quadratic-time BER/CER/DER OID decoding;
  CVE-2026-59886: `univ.Real` mantissa/exponent-to-float conversion issue). Confirmed unrelated to a small,
  already-tested 2-file diff (`pipeline_mode_resolver.py` + its test, adding an `"AAVE"` venue override) via `git stash`
  isolation — a dependency CVE cannot be caused by a 6-line addition to unrelated source, and the finding persists
  identically with that diff fully removed. Not attempted as a quick fix here: a `pyasn1` version bump is a
  transitive-dependency change with workspace-wide blast radius (re-locking `uv.lock`, verifying every consumer of
  `pyasn1`/`pyasn1-modules`/anything depending on them still resolves), out of scope for an inline fix alongside an
  unrelated ship per the dirty-deps/dependency-bump caution in CLAUDE.md.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [unified-trading-library]
scope: [engineer]
tags: [pip-audit, cve, dependency, quality-gates, quickmerge-blocked, security]
related: []
created: "2026-07-21"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
source:
  [
    "hit while shipping an unrelated lst_rate_honest_coverage_2026_07_21.md Phase 2 fix (AAVE pipeline_mode venue
    override) 2026-07-21",
  ]
resolved_by:
locked_by:
---

# UTL pip-audit gate fails on pyasn1 CVEs — blocks every quickmerge

## Reproduction

```
cd unified-trading-library && bash scripts/quality-gates.sh --no-fix
```

Fails at `── [5/6] CODEX COMPLIANCE ──`:

```
❌ pip-audit vulnerabilities
  pyasn1 0.6.3: CVE-2026-59885 — quadratic-time BER/CER/DER OID decoding
  pyasn1 0.6.3: CVE-2026-59886 — univ.Real mantissa/base/exponent -> float conversion issue
❌ Codex compliance FAILED: 1 violations (max allowed: 0)
```

**Verified NOT caused by any in-flight change**: reproduced with a small, already-tested, isolated diff
(`unified_trading_library/pipeline_mode_resolver.py` + `tests/unit/test_pipeline_mode_resolver.py`, adding one venue
override) fully stashed away — the failure persists identically. `pyasn1` is a transitive dependency (via
`pyasn1-modules`, itself likely pulled in by a `google-auth`/`google-cloud-*` package), pinned in `uv.lock` at
`>=0.6.3,<0.7.0` — a source-level 6-line addition to unrelated code cannot affect this.

## Impact

Blocks **every** `quickmerge --agent` in `unified-trading-library` — the sentinel is only written on a fully green
`quality-gates.sh` run, and the pip-audit check appears deterministic (a disclosed CVE, not flaky).

## Why not fixed here

A `pyasn1` version bump touches a transitive dependency with workspace-wide reach (anything importing
`pyasn1`/`pyasn1-modules` directly or via `google-auth`), requiring a `uv.lock` re-resolution and a check that every
consumer still resolves cleanly — a bigger, riskier change than is appropriate to bundle into an unrelated ship. Filed
here per the findings-triage rule (fits nobody's active plan, cross-cutting, blocks everyone) rather than attempted
inline.

## Todos

- [ ] 1. [BACKEND] P1. Check whether a `pyasn1` patch release (still within or bumping past `<0.7.0`) fixes both CVEs;
      if so, bump the pin and re-lock `uv.lock` (`uv lock --upgrade-package pyasn1`), then run the full
      `unified-trading-library` test suite to confirm no regression. (repo: unified-trading-library)
- [ ] 2. [REVIEW] P2. Once green, sweep for any quickmerge attempts in this repo that were silently blocked by this same
      pip-audit failure and ship them. (repo: unified-trading-library)

## Independent re-confirmation (2026-07-21, separate session)

Hit the identical wall shipping `downstream_funding_staking_canonical_reader_audit_2026_07_21.md` todo 4 (a 5-row
`PATH_REGISTRY` `bucket_template` env-tiering fix — unrelated to `pipeline_mode_resolver.py`). Same `git stash`
isolation technique, same result: `❌ pip-audit vulnerabilities` / `pyasn1 0.6.3: CVE-2026-59885` / `CVE-2026-59886` /
`❌ Codex compliance FAILED: 1 violations (max allowed: 0)`, reproduced twice (`QG_SENTINEL_DISABLE=true` re-runs),
persisting identically whether the isolated diff is present or fully reverted. This is now confirmed across 2 sessions
with 2 completely different diffs — strengthens todo 2 above ("sweep for any quickmerge attempts... that were silently
blocked") since it's clearly not a one-off. The todo-4 fix itself was reverted from the working tree (not left as stale
uncommitted WIP) with the exact replacement documented inline in that issue doc's todo 4, ready to re-apply the moment
this is resolved.
