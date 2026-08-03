#!/usr/bin/env python3
# Epic: agent_operating_framework_master
# Lifecycle: permanent
# Delete-when: NA
"""Smoke + determinism tests for gen_doc_index (the L0 map generator, W4).

Run: .venv/bin/python -m pytest scripts/docs/test_gen_doc_index.py -q

# Epic: agent_operating_framework_master
# Lifecycle: permanent
"""

from __future__ import annotations

import concurrent.futures
import threading

import gen_doc_index
from gen_doc_index import _atomic_write, _fmt_val, build_index


def test_fmt_val_list_is_comma_joined():
    assert _fmt_val(["defi", "cefi"]) == "defi,cefi"
    assert _fmt_val("active") == "active"
    assert _fmt_val([]) == ""


def test_build_index_is_deterministic(tmp_path):
    # the whole point of consumer-side-local + gitignored: two regens of the SAME tree are
    # byte-identical (no incidental set/dict-ordering nondeterminism in the renderer).
    #
    # This asserts the RENDERER's algorithm is deterministic for a fixed input -- it must NOT
    # depend on the live, mutable `plans/` corpus staying still for the test's duration.
    # Originally this called `build_index(pm_root)` twice back-to-back against the LIVE PM
    # root, which raced concurrent agents committing/archiving docs on this heavily
    # multi-agent-written shared workspace (found 2026-07-25: a doc's `status: resolved` ->
    # `status: open` landed between the two filesystem walks -- a genuine corpus race, not a
    # renderer bug; see the now-closed
    # test_build_index_deterministic_races_on_concurrent_corpus_writes_2026_07_25 issue). A
    # retry loop reduced the flake rate but never eliminated the race (and the tail assertion
    # still did one more unretried live double-call). Fixed per the issue's own recommendation:
    # build from a FROZEN `tmp_path` fixture seeded with a handful of representative docs
    # instead of the live corpus -- proves determinism without depending on anything else's
    # concurrent writes. `build_index()` skips any of its configured roots that isn't a
    # directory, so a tmp tree only needing 2 of the ~7 roots populated is a valid input.
    plans_dir = tmp_path / "plans" / "active"
    plans_dir.mkdir(parents=True)
    codex_dir = tmp_path / "codex" / "01-example"
    codex_dir.mkdir(parents=True)
    (plans_dir / "frozen_fixture_plan_2026_01_01.md").write_text(
        "---\n"
        "doc_type: plan\n"
        "title: Frozen fixture plan\n"
        "summary: a static, non-live doc used only to prove build_index's render step is\n"
        "  deterministic for a fixed input.\n"
        "status: active\n"
        "nature: process\n"
        "asset_group: [meta]\n"
        "priority: P3\n"
        "assigned_vm: NA\n"
        "---\n\n# Frozen fixture plan\n\nStatic content, never mutated by this test.\n",
        encoding="utf-8",
    )
    (codex_dir / "frozen_fixture_codex_doc.md").write_text(
        "---\n"
        "doc_type: codex-ssot\n"
        "title: Frozen fixture codex doc\n"
        "summary: also static.\n"
        "authoritative_for: nothing-real\n"
        "owner: nobody\n"
        "---\n\n# Frozen fixture codex doc\n",
        encoding="utf-8",
    )
    first = build_index(tmp_path)
    second = build_index(tmp_path)
    assert first == second
    assert "Frozen fixture plan" in first
    assert "Frozen fixture codex doc" in first


def test_build_index_has_sections_and_entries():
    out = build_index(gen_doc_index._pm_root())
    assert out.startswith("# UTS documentation index")
    assert "## plan (" in out  # at least the plan section exists
    assert "\n- [" in out  # at least one doc entry
    # facets render as a greppable bracketed group on seeded docs
    assert "doc_type" not in out or "asset_group=" in out  # if any facets present, they're key=val form


def test_atomic_write_readers_never_see_truncated_content(tmp_path):
    # Multiple slots can call `ensure-doc-index-fresh.sh` concurrently against the SAME
    # per-clone DOC_INDEX.generated.md (or race the FF-pull cron's own --stale-check tick), so
    # `_atomic_write` must guarantee a concurrent reader never observes a partial/interleaved
    # file. Distinct, differently-sized payloads make any interleaving or truncation show up as
    # content that matches none of the writers' full payloads.
    out = tmp_path / "DOC_INDEX.generated.md"
    payloads = [f"payload-{i}\n" + ("x" * (i + 1) * 20_000) + f"\nend-{i}\n" for i in range(6)]
    stop = threading.Event()
    bad_reads: list[str] = []

    def _reader() -> None:
        while not stop.is_set():
            if out.exists():
                content = out.read_text()
                if content and content not in payloads:
                    bad_reads.append(content[:80])

    def _writer(content: str) -> None:
        _atomic_write(out, content)

    readers = [threading.Thread(target=_reader) for _ in range(4)]
    for t in readers:
        t.start()
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(payloads)) as pool:
            list(pool.map(_writer, payloads))
    finally:
        stop.set()
        for t in readers:
            t.join()

    assert not bad_reads, f"reader observed a truncated/interleaved write: {bad_reads[0]!r}"
    assert out.read_text() in payloads


def test_main_stale_check_concurrent_invocation_never_truncates(tmp_path):
    # Exercises the real CLI entrypoint (what the wrapper script actually shells out to), not
    # just the helper: several concurrent `--stale-check` regens against one shared --out path
    # must all leave a complete, valid index behind -- never a truncated file.
    out = tmp_path / "DOC_INDEX.generated.md"

    def _run() -> int:
        return gen_doc_index.main(["--out", str(out), "--stale-check"])

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        results = [f.result() for f in [pool.submit(_run) for _ in range(6)]]

    assert all(code == 0 for code in results)
    expected = build_index(gen_doc_index._pm_root())
    assert out.read_text() == expected
