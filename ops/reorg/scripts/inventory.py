#!/usr/bin/env python3
"""Generate a repository inventory report for reorganization planning."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import Counter, defaultdict
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository root path")
    parser.add_argument(
        "--output",
        default="ops/reorg/reports/inventory.json",
        help="Inventory output path",
    )
    parser.add_argument(
        "--max-hash-bytes",
        type=int,
        default=10 * 1024 * 1024,
        help="Only compute sha256 for files up to this size (bytes)",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[".git", ".venv", "__pycache__", ".ipynb_checkpoints"],
        help="Directory names to exclude during scan",
    )
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    excludes = set(args.exclude)
    entries = []
    ext_counter: Counter[str] = Counter()
    top_level_counter: Counter[str] = Counter()
    hash_to_paths: defaultdict[str, list[str]] = defaultdict(list)

    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = Path(dirpath).relative_to(root)
        dirnames[:] = [d for d in dirnames if d not in excludes]

        if any(part in excludes for part in rel_dir.parts):
            continue

        for filename in filenames:
            file_path = Path(dirpath) / filename
            rel_path = file_path.relative_to(root)

            try:
                size_bytes = file_path.stat().st_size
            except OSError:
                continue

            ext = file_path.suffix.lower() or "[noext]"
            top_level = rel_path.parts[0] if rel_path.parts else "_root"
            item = {
                "path": str(rel_path),
                "size_bytes": size_bytes,
                "ext": ext,
                "top_level": top_level,
                "sha256": None,
            }

            if size_bytes <= args.max_hash_bytes:
                try:
                    file_hash = sha256(file_path)
                    item["sha256"] = file_hash
                    hash_to_paths[file_hash].append(str(rel_path))
                except OSError:
                    pass

            entries.append(item)
            ext_counter[ext] += 1
            top_level_counter[top_level] += 1

    duplicate_groups = {
        digest: paths
        for digest, paths in hash_to_paths.items()
        if digest and len(paths) > 1
    }

    report = {
        "summary": {
            "total_files": len(entries),
            "total_size_bytes": sum(e["size_bytes"] for e in entries),
            "excluded_dirs": sorted(excludes),
            "max_hash_bytes": args.max_hash_bytes,
        },
        "top_extensions": ext_counter.most_common(40),
        "top_level_counts": top_level_counter.most_common(80),
        "duplicate_groups": duplicate_groups,
        "entries": entries,
    }

    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote inventory report: {output}")
    print(f"files scanned: {len(entries)}")
    print(f"duplicate groups: {len(duplicate_groups)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
