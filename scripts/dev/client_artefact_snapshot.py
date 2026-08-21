#!/usr/bin/env python3
"""
Pre-write safety snapshot utility for agent-authored client-artefact edits.
Snapshots target files (content-hashed, timestamped) to a secure directory outside
the shared working tree, maintaining a metadata manifest and providing an explicit
recovery/restore mechanism.

Lifecycle marker:
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent-utility
"""

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

# Default storage directory outside the repo/working tree
DEFAULT_SNAPSHOT_DIR = Path.home() / ".unified_trading_snapshots"

def compute_sha256(file_path: Path) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(65536), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def create_snapshot(target_path: Path, snapshot_dir: Path) -> dict:
    if not target_path.exists():
        print(f"Error: Target path {target_path} does not exist.", file=sys.stderr)
        sys.exit(1)

    target_path = target_path.resolve()
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    file_hash = compute_sha256(target_path)

    # Unique snapshot filename based on timestamp and hash prefix
    safe_name = target_path.name.replace("/", "_")
    hash_prefix = file_hash[:12]
    time_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    snapshot_filename = f"{safe_name}_{time_str}_{hash_prefix}.bak"
    snapshot_file_path = snapshot_dir / snapshot_filename

    # Copy file to snapshot location
    shutil.copy2(target_path, snapshot_file_path)

    manifest = {
        "original_path": str(target_path),
        "snapshot_path": str(snapshot_file_path),
        "timestamp": timestamp,
        "sha256": file_hash,
        "size_bytes": target_path.stat().st_size
    }

    manifest_path = snapshot_dir / f"{snapshot_filename}.json"
    with open(manifest_path, "w", encoding="utf-8") as mf:
        json.dump(manifest, mf, indent=2)

    print(f"Successfully snapshotted {target_path}")
    print(f"  Snapshot: {snapshot_file_path}")
    print(f"  SHA256:   {file_hash}")
    return manifest

def restore_snapshot(snapshot_path: Path, target_path: Path) -> None:
    if not snapshot_path.exists():
        print(f"Error: Snapshot path {snapshot_path} does not exist.", file=sys.stderr)
        sys.exit(1)

    target_path = target_path.resolve()
    target_path.parent.mkdir(parents=True, exist_ok=True)

    shutil.copy2(snapshot_path, target_path)

    restored_hash = compute_sha256(target_path)
    print(f"Successfully restored {snapshot_path} to {target_path}")
    print(f"  Restored file SHA256: {restored_hash}")

def list_snapshots(snapshot_dir: Path) -> None:
    if not snapshot_dir.exists():
        print(f"No snapshots directory found at {snapshot_dir}")
        return

    manifests = sorted(snapshot_dir.glob("*.json"))
    if not manifests:
        print(f"No snapshots found in {snapshot_dir}")
        return

    print(f"Available snapshots in {snapshot_dir}:")
    for mf_path in manifests:
        try:
            with open(mf_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(f"  - [{data['timestamp']}] {data['original_path']}")
            print(f"    Backup: {data['snapshot_path']}")
            print(f"    Hash:   {data['sha256'][:16]}...")
        except Exception as e:
            print(f"  - Error reading {mf_path}: {e}")

def main() -> None:
    parser = argparse.ArgumentParser(description="Pre-write safety snapshot utility for client artifacts.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Snapshot command
    snap_parser = subparsers.add_parser("snapshot", help="Create a safety snapshot of a file")
    snap_parser.add_argument("target", type=Path, help="Path to the file to snapshot")
    snap_parser.add_argument("--dir", type=Path, default=DEFAULT_SNAPSHOT_DIR, help="Directory to store snapshots")

    # Restore command
    restore_parser = subparsers.add_parser("restore", help="Restore a file from a safety snapshot")
    restore_parser.add_argument("snapshot", type=Path, help="Path to the .bak snapshot file")
    restore_parser.add_argument("target", type=Path, help="Path to restore the file to")

    # List command
    list_parser = subparsers.add_parser("list", help="List all available safety snapshots")
    list_parser.add_argument("--dir", type=Path, default=DEFAULT_SNAPSHOT_DIR, help="Directory storing snapshots")

    args = parser.parse_args()

    if args.command == "snapshot":
        create_snapshot(args.target.resolve(), args.dir.resolve())
    elif args.command == "restore":
        restore_snapshot(args.snapshot.resolve(), args.target.resolve())
    elif args.command == "list":
        list_snapshots(args.dir.resolve())

if __name__ == "__main__":
    main()
