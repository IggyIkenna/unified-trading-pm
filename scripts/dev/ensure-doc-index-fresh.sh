#!/usr/bin/env bash
# Epic: agent_operating_framework_master
# Lifecycle: permanent
# Delete-when: NA
#
# ensure-doc-index-fresh.sh — on-demand stale-check wrapper for the L0 doc index
# (DOC_INDEX.generated.md), for an agent to call FIRST, before grepping the index.
#
# Why: the FF-pull cron (slot-cron-ff-pull.sh) already regenerates the index on a 5-minute
# tick via `gen_doc_index.py --stale-check`, but that leaves an inter-tick gap — a doc edited
# seconds ago won't show up in the index until the next tick, so an agent grepping mid-window
# reads a stale map. This wrapper closes that gap on demand: it runs the SAME --stale-check
# entrypoint (only rewrites when content actually changed; regen is ~1.4s, a no-op check is
# near-instant), so "grep the L0 index FIRST" never routes off a stale index.
#
# Safe to call concurrently — from multiple slots against the SAME PM clone, or racing the FF-
# pull cron's own tick: gen_doc_index.py writes the index atomically (temp file + os.replace),
# so a concurrent writer can never leave a truncated/interleaved file on disk. A reader always
# sees either the fully-old or the fully-new content.
set -euo pipefail

_pm_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
_py="${_pm_root}/.venv/bin/python"
[[ -x "${_py}" ]] || _py="python3"

exec "${_py}" "${_pm_root}/scripts/docs/gen_doc_index.py" --stale-check
