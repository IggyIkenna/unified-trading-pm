"""Unit tests for scripts/quality_gates/check_credential_ask_orphans.py's ask-evidence
detection — specifically the `BLK-<hex>` id token (the live `/api/slots/<N>/blocked`
endpoint's ack format), per
credential_ask_orphan_checker_ping_format_stale_2026_07_27.md.
"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path


def _load_module() -> types.ModuleType:
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "scripts" / "quality_gates" / "check_credential_ask_orphans.py"
    spec = importlib.util.spec_from_file_location("check_credential_ask_orphans", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["check_credential_ask_orphans"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


MOD = _load_module()


class TestBlkIdRecognizedAsAskEvidence:
    def test_blk_id_in_context_counts_as_ask_evidence(self) -> None:
        lines = [
            "- [ ] BLOCKED-CREDENTIALS this session's SA lacks setIamPolicy.",
            "  Escalated via /blocked, answered: BLK-4b104acc",
        ]
        assert MOD._has_ask_evidence(lines, 0) is True

    def test_blk_id_alone_does_not_match_the_old_file_ping_regex(self) -> None:
        # regression guard: BLK-<hex> is NOT a ping-file path, so it must be recognized via
        # BLK_ID_RE specifically, not accidentally by PING_PATH_RE.
        assert MOD.PING_PATH_RE.search("Escalated, answered: BLK-4b104acc") is None
        assert MOD.BLK_ID_RE.search("Escalated, answered: BLK-4b104acc") is not None

    def test_no_ask_evidence_without_any_recognized_token(self) -> None:
        lines = ["- [ ] BLOCKED-CREDENTIALS need a vendor API key, not yet actioned."]
        assert MOD._has_ask_evidence(lines, 0) is False

    def test_blk_id_requires_minimum_hex_length(self) -> None:
        # a short/garbage token shaped like "BLK-1" (a mocked test return value, not a real
        # /blocked id) should not be treated as evidence of a real escalation.
        assert MOD.BLK_ID_RE.search("mocked return value BLK-1") is None
