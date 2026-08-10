#!/usr/bin/env python3
"""Auto-resolve git conflict markers left by a `prek`/prettier stash-restore corruption
(the class `check_conflict_markers.sh` detects but does not fix — see that script's own
provenance note, 2026-06-21: mid-line markers + prettier-mangled `> > > > > > >` markers).

Why this exists: on a shared, high-churn checkout, `git pull --rebase --autostash` +
`prek`'s own internal stash/patch cycle regularly leaves conflict blocks where prettier's
proseWrap has reflowed the marker lines into surrounding prose, so the three sides
(upstream / base / stashed) are frequently either (a) whitespace-identical after
reflow, or (b) a clean superset relationship (one side = base + a pure insertion,
e.g. a `context_scope:` field added by the other party's edit). Both cases are safe to
resolve mechanically; only a genuine content divergence (a real edit conflict) needs a
human/agent to look at it.

Handles three marker shapes:
  - diff3 with a `|||||||` base section
  - plain 2-way (`<<<<<<<` / `=======` / `>>>>>>>`, no base)
  - the prettier-mangled variant where markers land mid-line or as `> > > > > > >`

Resolution rules, in order:
  1. upstream == stashed (whitespace-normalized) -> take upstream (dedup).
  2. diff3 with base, and stashed = base + pure insertion (no deletion/replace vs base)
     -> take upstream + the inserted lines (both edits are real and additive).
  3. plain 2-way, sides differ -> take upstream (the already-landed peer edit) and drop
     the stashed side; this loses a genuine stashed-only edit if one exists, which is why
     files resolved this way are NOT silently trusted -- inspect the printed diff if the
     stashed side mattered.
  4. anything else (a real replace/delete inside the diff3 base-vs-stashed diff) -> left
     untouched and reported as MANUAL.

Never guesses silently: every file gets one of AUTO-RESOLVED / MANUAL / NO-MARKERS printed,
so a caller can grep the output for MANUAL and go look at those by hand.

# Epic: agent_operating_framework_master
# Lifecycle: permanent
# Delete-when: NA (pairs with check_conflict_markers.sh's detection; keep as long as that does)
"""

from __future__ import annotations

import argparse
import difflib
import re
import subprocess
from pathlib import Path

PM = Path(__file__).resolve().parents[2]


def _norm(line: str) -> str:
    return re.sub(r"[ \t]+", " ", line).strip()


def _is_close_marker(line: str) -> bool:
    # matches both a clean ">>>>>>>" and the prettier-mangled "> > > > > > >"
    return line.replace(" ", "").startswith(">>>>>>>")


def _is_mid_marker(line: str) -> bool:
    return line.startswith("|||||||")


def _get_uu_files() -> list[str]:
    out = subprocess.run(["git", "status", "--short"], capture_output=True, text=True, cwd=PM, check=True).stdout
    return [line[3:].strip() for line in out.splitlines() if line[:2] in ("UU", "AA")]


def resolve_file(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")
    out: list[str] = []
    i = 0
    n_blocks = 0
    manual_blocks: list[int] = []

    while i < len(lines):
        if not lines[i].startswith("<<<<<<<"):
            out.append(lines[i])
            i += 1
            continue

        s = i
        j = s + 1
        mid = None
        while j < len(lines) and lines[j] != "=======" and not _is_mid_marker(lines[j]):
            j += 1
        if j < len(lines) and _is_mid_marker(lines[j]):
            mid = j
            eq = next(k for k in range(mid, len(lines)) if lines[k] == "=======")
        else:
            eq = j
        e = next(k for k in range(eq, len(lines)) if _is_close_marker(lines[k]))

        upstream = lines[s + 1 : (mid if mid is not None else eq)]
        base = lines[mid + 1 : eq] if mid is not None else None
        stashed = lines[eq + 1 : e]
        n_blocks += 1

        if [_norm(line) for line in upstream] == [_norm(line) for line in stashed]:
            out.extend(upstream)
        elif base is not None:
            sm = difflib.SequenceMatcher(None, base, stashed)
            inserted: list[str] = []
            clean_insert_only = True
            for tag, _i1, _i2, j1, j2 in sm.get_opcodes():
                if tag == "equal":
                    continue
                if tag == "insert":
                    inserted.extend(stashed[j1:j2])
                else:
                    clean_insert_only = False
            if clean_insert_only:
                out.extend(upstream)
                out.extend(inserted)
            else:
                manual_blocks.append(n_blocks)
                out.extend(lines[s : e + 1])
        else:
            # plain 2-way, genuinely different content -> prefer the already-landed
            # upstream edit; report so the caller can check what was dropped.
            out.extend(upstream)
        i = e + 1

    if n_blocks == 0:
        return "NO-MARKERS"
    if manual_blocks:
        return f"MANUAL: blocks {manual_blocks} of {n_blocks} need a human/agent look"
    path.write_text("\n".join(out), encoding="utf-8")
    return f"AUTO-RESOLVED ({n_blocks} block(s))"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="*", help="paths to resolve; default = every UU/AA file in `git status`")
    args = parser.parse_args(argv)

    targets = args.files or _get_uu_files()
    if not targets:
        print("No conflicted (UU/AA) files found.")
        return 0

    manual = []
    for rel in targets:
        path = PM / rel
        try:
            verdict = resolve_file(path)
        except (OSError, UnicodeDecodeError, StopIteration, IndexError) as e:
            verdict = f"ERROR: {e}"
        print(f"{rel}: {verdict}")
        if verdict.startswith("MANUAL") or verdict.startswith("ERROR"):
            manual.append(rel)

    print(f"\n{len(targets)} file(s) processed, {len(manual)} need manual review")
    for rel in manual:
        print(" ", rel)
    return 1 if manual else 0


if __name__ == "__main__":
    raise SystemExit(main())
