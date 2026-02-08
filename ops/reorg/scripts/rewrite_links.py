#!/usr/bin/env python3
"""Rewrite Markdown link paths according to a mapping CSV."""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path


DEFAULT_EXCLUDES = {".git", ".venv", "__pycache__", ".ipynb_checkpoints"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository root path")
    parser.add_argument("--mapping", default="ops/reorg/mapping.csv", help="Mapping CSV path")
    parser.add_argument("--mode", choices=["dry-run", "write"], default="dry-run")
    parser.add_argument(
        "--report",
        default="ops/reorg/reports/link_fix_result.json",
        help="Link rewrite report output path",
    )
    return parser.parse_args()


def load_replacements(mapping_path: Path) -> list[tuple[str, str]]:
    replacements: list[tuple[str, str]] = []
    with mapping_path.open("r", newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row.get("action") != "move":
                continue
            old_path = row.get("old_path", "").strip().replace("\\", "/")
            new_path = row.get("new_path", "").strip().replace("\\", "/")
            if old_path and new_path:
                replacements.append((old_path, new_path))
    replacements.sort(key=lambda x: len(x[0]), reverse=True)
    return replacements


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    report = Path(args.report)
    report.parent.mkdir(parents=True, exist_ok=True)

    replacements = load_replacements(Path(args.mapping))

    changed_files = []
    total_replacements = 0

    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = Path(dirpath).relative_to(root)
        dirnames[:] = [d for d in dirnames if d not in DEFAULT_EXCLUDES]
        if any(part in DEFAULT_EXCLUDES for part in rel_dir.parts):
            continue

        for filename in filenames:
            if not filename.lower().endswith((".md", ".markdown", ".txt")):
                continue

            file_path = Path(dirpath) / filename
            try:
                original = file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue

            updated = original
            file_count = 0
            for old_path, new_path in replacements:
                hits = updated.count(old_path)
                if hits:
                    updated = updated.replace(old_path, new_path)
                    file_count += hits

            if file_count:
                total_replacements += file_count
                changed_files.append(
                    {"path": str(file_path.relative_to(root)), "replacements": file_count}
                )
                if args.mode == "write":
                    file_path.write_text(updated, encoding="utf-8")

    result = {
        "mode": args.mode,
        "changed_files": changed_files,
        "total_changed_files": len(changed_files),
        "total_replacements": total_replacements,
    }

    report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"mode: {args.mode}")
    print(f"changed_files: {len(changed_files)}")
    print(f"total_replacements: {total_replacements}")
    print(f"report: {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
