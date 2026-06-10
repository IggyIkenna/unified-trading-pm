---
title: library-repo quickmerge --agent checks .qg_last_passed_sha but base-library.sh only writes .qg_content_sentinel
created: 2026-06-07
source:
  - unified-trading-pm/scripts/quality-gates-base/base-library.sh (writes .qg_content_sentinel only)
  - unified-trading-pm/scripts/quality-gates-base/base-service.sh (writes .qg_last_passed_sha)
  - unified-trading-pm/scripts/quickmerge.sh (STAGE 3 AGENT_MODE checks .qg_last_passed_sha)
  - plans/active/cicd_contract_hardening_2026_06_01.md (live cicd track)
priority: P2
status: active
---

> **✅ RESOLVED 2026-06-10 — ARCHIVE CANDIDATE (dup of base_library_qg_sha_sentinel_gap).** Fixed by
> base-library.sh:1130 writing `.qg_last_passed_sha` on green. Verified on origin/main.
>
> **ACKED-INTO-CODE** → archived 2026-06-10 — fix shipped in unified-trading-pm@09137833 (duplicate of
> `base_library_qg_sha_sentinel_gap_2026_06_08.md`, archived same sweep). The interim hand-written-sentinel bridge
> described below is RETIRED — a green `quality-gates.sh` now writes the SHA sentinel itself.

## What I found

`quickmerge.sh` STAGE 3 in `--agent` mode strictly verifies `.qg_last_passed_sha == HEAD` (`quickmerge.sh:1018-1028`).
That SHA sentinel is written **only by base-service.sh** (`base-service.sh:2679`
`git rev-parse HEAD > .qg_last_passed_sha`). **base-library.sh writes only `.qg_content_sentinel`** (content-hash;
`base-library.sh:1000`) and never the SHA sentinel.

So for any **library** repo (sources base-library.sh — e.g. `unified-api-contracts`), a green `quality-gates.sh` run
leaves `.qg_last_passed_sha` empty/missing, and `quickmerge --agent` then hard-fails STAGE 3 with
`❌ Pass 1 quality-gates.sh not run on current HEAD (SHA mismatch) … Sentinel: <missing>` even though the gate genuinely
passed.

Hit live shipping A11c-candle-enum in `unified-api-contracts`: full `quality-gates.sh` PASSED green (343s, content
sentinel written) but quickmerge refused on the missing SHA sentinel.

## Why it matters

Every **library-type** repo is affected → `quickmerge --agent` is unusable for libraries as-is. The likely current
workaround fleet-wide is agents hand-writing the SHA sentinel (`git rev-parse HEAD > .qg_last_passed_sha`) after a
confirmed-green run — which is what unblocked the A11c UAC ship (uac@d4dacac5), and is safe ONLY because the content
sentinel proves the tree is the green one. But a hand-written SHA sentinel is fragile: if it is ever written without a
real green run, quickmerge's Pass-1 guarantee is silently void.

## Recommended decision

Make `base-library.sh` write `.qg_last_passed_sha` on a complete green run, mirroring `base-service.sh:2679` (one block
at the end of the green path), so the SHA sentinel quickmerge checks is produced by the gate itself for libraries too.
Then library `quickmerge --agent` works without any hand-written sentinel. Owner = cicd track
(`cicd_contract_hardening_2026_06_01.md`); roll out via the canonical `scripts/quality-gates-base/` template (it is the
SSOT — no per-repo edits).

Interim (until fixed): after a confirmed-green `quality-gates.sh` on a library repo, the SHA sentinel may be bridged
with `git rev-parse HEAD > .qg_last_passed_sha` ONLY when the tree is unchanged since that green run (the
`.qg_content_sentinel` proves it).
