"""Phase-1 VERIFY — emulator-backed integration test for the CI-status Firestore side store.

SSOT: plans/active/ci_status_firestore_side_store_2026_06_10.md (Phase 1 — "Run a drain / a few
transitions; assert the Firestore docs match the manifest ci_status … Confirm concurrent multi-repo
transitions produce NO contention").

The ``tests/unit/test_ci_status_store.py`` suite covers ``resolve_status`` (pure) and the CAS write
path against an INJECTED FAKE module whose ``transactional`` just invokes the body once — it does
NOT exercise the real ``google.cloud.firestore`` ``@transactional`` decorator, real document
read→resolve→write atomicity, or genuine concurrency. This module closes that gap by driving the
REAL SDK path (``set_status`` / ``get_all`` with the production ``_default_firestore_module``)
against a throwaway **Firestore emulator** — so it is credential-free and validates:

  * Layer-2 same-repo ordering under real transactional CAS (no-downgrade preserved, FAILING
    unconditional, main authoritative) — incl. under concurrent writers;
  * Layer-1 cross-repo no-contention (disjoint per-repo docs — concurrent multi-repo writes all
    land, none lost);
  * a realistic out-of-order "drain" produces Firestore docs IDENTICAL to an independent
    re-implementation of the manifest no-downgrade rule.

Skips cleanly when the emulator (``gcloud emulators firestore`` component) or a JRE is unavailable,
so it never reddens a host without the emulator installed.
"""

from __future__ import annotations

import contextlib
import importlib.util
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
from collections.abc import Iterator
from pathlib import Path

import pytest

# The google-cloud-firestore SDK is NOT a PM dependency (the dual-write GHA pip-installs it at
# runtime) — so the local quality-gate `.venv` has no `google` namespace. Skip the whole module
# cleanly there, exactly as we skip when the emulator binary/JRE is absent. This keeps the gate green
# (an integration test correctly skips without its infra) while the test still runs wherever the SDK
# + emulator are present (this host, a CI service container with FIRESTORE_EMULATOR_HOST).
pytest.importorskip("google.cloud.firestore", reason="google-cloud-firestore SDK not installed")

# ── Load the store module by path (PM scripts are not an installed package) ──────────────────────
_STORE = Path(__file__).resolve().parents[2] / "scripts" / "cicd" / "ci_status_store.py"
_spec = importlib.util.spec_from_file_location("ci_status_store", _STORE)
assert _spec and _spec.loader
ci_status_store = importlib.util.module_from_spec(_spec)
sys.modules["ci_status_store"] = ci_status_store
_spec.loader.exec_module(ci_status_store)

set_status = ci_status_store.set_status
get_all = ci_status_store.get_all
rank = ci_status_store.rank

_PROJECT = "demo-pm-ci-status"


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("localhost", 0))
        return int(s.getsockname()[1])


def _emulator_available() -> bool:
    if shutil.which("gcloud") is None or shutil.which("java") is None:
        return False
    probe = subprocess.run(
        ["gcloud", "emulators", "firestore", "start", "--help"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    return probe.returncode == 0


@pytest.fixture(scope="module")
def emulator_host() -> Iterator[str]:
    """Start a throwaway Firestore emulator for the module; honour an already-running one.

    If ``FIRESTORE_EMULATOR_HOST`` is already exported (e.g. a CI service container) we reuse it and
    do not manage a process. Otherwise we boot ``gcloud emulators firestore`` on a free port and tear
    it down at module teardown. Skips the whole module if the emulator/JRE is missing.
    """
    preset = os.environ.get("FIRESTORE_EMULATOR_HOST")
    if preset:
        yield preset
        return

    if not _emulator_available():
        pytest.skip("Firestore emulator (gcloud component + JRE) not available on this host")

    port = _free_port()
    host = f"localhost:{port}"
    proc = subprocess.Popen(
        ["gcloud", "emulators", "firestore", "start", f"--host-port={host}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=True,  # own process group so teardown can reap the Java grandchild too
    )
    # Wait for readiness: the emulator prints "Dev App Server is now running" then accepts TCP.
    deadline = time.monotonic() + 45
    ready = False
    assert proc.stdout is not None
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            break
        line = proc.stdout.readline()
        if "Dev App Server is now running" in line or "running on" in line:
            ready = True
            break
    if ready:
        # give the TCP listener a beat to bind
        for _ in range(20):
            with contextlib.suppress(OSError), socket.create_connection(("localhost", port), timeout=1):
                break
            time.sleep(0.5)
    os.environ["FIRESTORE_EMULATOR_HOST"] = host
    try:
        if not ready:
            proc.terminate()
            pytest.skip("Firestore emulator failed to start within the deadline")
        yield host
    finally:
        os.environ.pop("FIRESTORE_EMULATOR_HOST", None)
        # Reap the whole process group (gcloud wrapper + its Java emulator grandchild). Leaving the
        # Java child alive orphans it holding the inherited stdout fd → the parent shell never sees
        # EOF and is SIGTERM'd (exit 144). killpg covers the whole tree.
        with contextlib.suppress(ProcessLookupError, PermissionError):
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        with contextlib.suppress(subprocess.TimeoutExpired):
            proc.wait(timeout=10)
        with contextlib.suppress(ProcessLookupError, PermissionError):
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)


@pytest.fixture()
def clean_collection(emulator_host: str) -> Iterator[None]:
    """Wipe the ``ci_status`` collection before each test for isolation."""
    _ = emulator_host  # fixture dependency — ensures the emulator is up before we touch Firestore
    from google.cloud import firestore

    client = firestore.Client(project=_PROJECT)
    for doc in client.collection(ci_status_store.COLLECTION).stream():
        doc.reference.delete()
    yield
    for doc in client.collection(ci_status_store.COLLECTION).stream():
        doc.reference.delete()


def _set(repo: str, status: str, branch: str, sha: str = "deadbeef") -> tuple[str, str]:
    return set_status(repo, status, branch, sha, project_id=_PROJECT)


def _set_resilient(repo: str, status: str, branch: str, attempts: int = 6) -> None:
    """``_set`` with an outer retry on transaction-contention exhaustion.

    The store's ``set_status`` leans on the SDK transaction's DEFAULT retry budget; under heavy
    same-document contention the EMULATOR (which serialises contended transactions far more weakly
    than real Firestore) can exhaust it and raise ``ValueError`` / ``DeadlineExceeded``. A real
    caller of a burst-contended doc should retry — which is exactly what we do here so the test
    asserts the no-downgrade INVARIANT, not the emulator's contention throughput.
    """
    from google.api_core import exceptions as gax_exceptions

    for i in range(attempts):
        try:
            _set(repo, status, branch)
            return
        except (ValueError, gax_exceptions.DeadlineExceeded, gax_exceptions.Aborted):
            if i == attempts - 1:
                raise
            time.sleep(0.2 * (i + 1))


# ── Real-SDK CAS semantics (the gap the fake never covered) ──────────────────────────────────────


@pytest.mark.usefixtures("clean_collection")
def test_real_txn_fresh_repo_advances():
    prev, written = _set("uac", "STAGING_GREEN", "staging", "sha-a")
    assert (prev, written) == ("NONE", "STAGING_GREEN")
    docs = get_all(project_id=_PROJECT)
    assert docs["uac"]["status"] == "STAGING_GREEN"
    assert docs["uac"]["rank"] == rank("STAGING_GREEN")
    assert docs["uac"]["branch"] == "staging"
    assert docs["uac"]["sha"] == "sha-a"
    assert docs["uac"]["updated_at"] is not None  # SERVER_TIMESTAMP resolved by the emulator


@pytest.mark.usefixtures("clean_collection")
def test_real_txn_no_downgrade():
    _set("uac", "MAIN_GREEN", "main")
    prev, written = _set("uac", "STAGING_GREEN", "staging")  # late staging re-run
    assert (prev, written) == ("MAIN_GREEN", "MAIN_GREEN")
    assert get_all(project_id=_PROJECT)["uac"]["status"] == "MAIN_GREEN"


@pytest.mark.usefixtures("clean_collection")
def test_real_txn_failing_is_unconditional():
    _set("uac", "MAIN_GREEN", "main")
    prev, written = _set("uac", "FAILING", "staging")
    assert (prev, written) == ("MAIN_GREEN", "FAILING")
    assert get_all(project_id=_PROJECT)["uac"]["status"] == "FAILING"


@pytest.mark.usefixtures("clean_collection")
def test_real_txn_main_is_authoritative():
    _set("uac", "MAIN_GREEN", "main")
    # an on-main signal may legitimately set a LOWER state (the on-main truth)
    written = _set("uac", "STAGING_GREEN", "main")[1]
    assert written == "STAGING_GREEN"
    assert get_all(project_id=_PROJECT)["uac"]["status"] == "STAGING_GREEN"


# ── Drain parity: Firestore docs == an independent manifest-rule re-implementation ───────────────


def _manifest_rule(prev: str, new: str, branch: str) -> str:
    """Independent re-implementation of the no-downgrade rule (NOT importing the store) so the
    assertion is a genuine cross-check, not a tautology."""
    ranks = {"FAILING": 0, "FEATURE_GREEN": 1, "STAGING_GREEN": 2, "SIT_VALIDATED": 3, "MAIN_GREEN": 4}
    if new == "FAILING":
        return new
    if branch == "main":
        return new
    if ranks.get(new, 0) < ranks.get(prev, 0):
        return prev
    return new


@pytest.mark.usefixtures("clean_collection")
def test_drain_matches_manifest_semantics():
    # a realistic, deliberately out-of-order multi-repo drain
    sequence = [
        ("uac", "FEATURE_GREEN", "live-defi-rollout"),
        ("utl", "FEATURE_GREEN", "live-defi-rollout"),
        ("uac", "STAGING_GREEN", "staging"),
        ("mtds", "STAGING_GREEN", "staging"),
        ("uac", "MAIN_GREEN", "main"),
        ("uac", "STAGING_GREEN", "staging"),  # late re-run — must NOT downgrade MAIN_GREEN
        ("utl", "SIT_VALIDATED", "staging"),
        ("mtds", "FAILING", "staging"),
        ("utl", "MAIN_GREEN", "main"),
        ("mtds", "FEATURE_GREEN", "live-defi-rollout"),  # the fix lands on LDR → clears the FAILING
        ("greeks", "MAIN_GREEN", "main"),
        ("greeks", "FAILING", "staging"),  # a failure AFTER promotion — must persist at drain end
    ]
    expected: dict[str, str] = {}
    for repo, status, branch in sequence:
        expected[repo] = _manifest_rule(expected.get(repo, "NONE"), status, branch)
        _set(repo, status, branch)

    docs = get_all(project_id=_PROJECT)
    got = {repo: docs[repo]["status"] for repo in expected}
    assert got == expected
    # sanity on the tricky cells:
    #   uac    — MAIN_GREEN survives the late staging re-run (no-downgrade);
    #   mtds   — a non-main green re-run (rank 1) AFTER a FAILING (rank 0) clears it → correct recovery;
    #   greeks — a FAILING that arrives over MAIN_GREEN persists (unconditional, never suppressed).
    assert got["uac"] == "MAIN_GREEN"
    assert got["mtds"] == "FEATURE_GREEN"
    assert got["greeks"] == "FAILING"


# ── Concurrency: Layer-2 (same repo serialises) + Layer-1 (cross-repo no contention) ─────────────


@pytest.mark.usefixtures("clean_collection")
def test_concurrent_same_repo_no_downgrade_under_contention():
    """Concurrent writers on the SAME repo at mixed lower ranks — the highest (MAIN_GREEN) must
    survive regardless of arrival order (real transactional CAS retry, no lost-update flap).

    Kept light (6 contended writers): the Firestore EMULATOR serialises contended transactions and
    chokes (504 DeadlineExceeded) well before real Firestore would — the no-downgrade invariant is
    what we assert, not throughput."""
    from concurrent.futures import ThreadPoolExecutor

    _set("uac", "MAIN_GREEN", "main")  # the value that must never be clobbered by a lower green
    lower = ["FEATURE_GREEN", "STAGING_GREEN", "SIT_VALIDATED"] * 2  # 6 concurrent non-main writers
    with ThreadPoolExecutor(max_workers=4) as ex:
        list(ex.map(lambda s: _set_resilient("uac", s, "staging"), lower))

    assert get_all(project_id=_PROJECT)["uac"]["status"] == "MAIN_GREEN"


@pytest.mark.usefixtures("clean_collection")
def test_concurrent_multi_repo_all_land():
    """Layer-1: N repos written concurrently touch DISJOINT docs — every one lands, none lost."""
    from concurrent.futures import ThreadPoolExecutor

    repos = [f"repo-{i:02d}" for i in range(25)]
    with ThreadPoolExecutor(max_workers=16) as ex:
        list(ex.map(lambda r: _set(r, "STAGING_GREEN", "staging", sha=r), repos))

    docs = get_all(project_id=_PROJECT)
    assert set(repos).issubset(docs.keys())
    assert all(docs[r]["status"] == "STAGING_GREEN" and docs[r]["sha"] == r for r in repos)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
