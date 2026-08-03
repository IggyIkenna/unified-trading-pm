#!/usr/bin/env bash
# Epic: agent_operating_framework_master
# Lifecycle: permanent
# Delete-when: NA
#
# refresh-doc-index.sh — on-demand L0 index freshness guard an agent calls BEFORE grepping.
#
# The "grep the L0 index FIRST" retrieval rule (CLAUDE.md § "Doc retrieval") reads the per-clone,
# gitignored DOC_INDEX.generated.md. The FF-pull cron already keeps that file fresh across every
# clone (`gen_doc_index.py --stale-check`, ~5-min cadence), but that leaves an inter-tick gap: an
# agent grepping within a 5-minute window of a doc change reads a stale map. This wrapper closes
# the gap — invoke it first, then grep:
#
#     bash scripts/docs/refresh-doc-index.sh && rg '<pattern>' DOC_INDEX.generated.md
#
# It runs the SAME `--stale-check` the cron uses, so it regenerates ONLY when content actually
# changed (~1.4s) and is a near-instant no-op otherwise. It resolves the CALLING clone's own
# generator (the one whose DOC_INDEX.generated.md the agent is about to grep), so it works
# identically from the main workspace PM or any .tabs/<N>/unified-trading-pm slot clone.
#
# CONCURRENCY: safe to call from multiple slots and concurrently with the FF-pull cron. Each slot
# clone has its own DOC_INDEX.generated.md, and the write itself is atomic (temp file + os.replace
# in gen_doc_index.py::_atomic_write_text), so two simultaneous regens of the same file can never
# leave a truncated index on disk — a reader always sees a complete old-or-new file.
set -euo pipefail

# Resolve THIS wrapper's own PM clone root (…/scripts/docs/ -> clone root), so we refresh the index
# the caller will grep, not some other clone's.
_pm_clone="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
_gen="${_pm_clone}/scripts/docs/gen_doc_index.py"
if [[ ! -f "${_gen}" ]]; then
    echo "refresh-doc-index: generator not found at ${_gen}" >&2
    exit 1
fi

# Prefer the clone's own venv python (has PyYAML); fall back to system python3.
_py="${_pm_clone}/.venv/bin/python"
[[ -x "${_py}" ]] || _py="python3"

# `--stale-check` is a no-op when the index is already fresh and rewrites atomically when not.
# timeout-bounded so a generator hang can never wedge the caller; quiet on success.
timeout 60 "${_py}" "${_gen}" --stale-check
