#!/usr/bin/env python3
"""Verify structural, naming, and worklist governance expectations."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
from pathlib import Path

SNAKE_SEGMENT = re.compile(r"^[a-z0-9._-]+$")
IGNORE_DIRS = {".git", ".venv", "__pycache__", ".ipynb_checkpoints"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository root path")
    parser.add_argument(
        "--report",
        default="ops/reorg/reports/verify_result.json",
        help="Verify report output path",
    )
    return parser.parse_args()


def check_snake_case(root: Path) -> list[str]:
    """Validate naming in managed top-level namespaces only.

    This intentionally avoids deep legacy content checks so teams can migrate
    course internals incrementally.
    """

    issues: list[str] = []
    top_targets = ["courses", "projects", "shared", "inbox", "archive", "ops", "worklist"]

    for target in top_targets:
        base = root / target
        if not base.exists():
            continue

        if not SNAKE_SEGMENT.match(target):
            issues.append(target)

        for child in base.iterdir():
            if child.name in IGNORE_DIRS:
                continue
            if child.is_dir() and not SNAKE_SEGMENT.match(child.name):
                issues.append(str(child.relative_to(root)))

    return sorted(set(issues))



def check_manifest_coverage(root: Path) -> dict:
    worklist = root / "worklist"
    manifest_path = worklist / "_meta" / "manifest.csv"
    if not manifest_path.exists():
        return {"missing_manifest": True, "untracked_files": []}

    manifest_entries = set()
    with manifest_path.open("r", newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            path = row.get("file_path", "").strip()
            if path:
                manifest_entries.add(path)

    real_files = []
    for dirpath, dirnames, filenames in os.walk(worklist):
        rel_dir = Path(dirpath).relative_to(root)
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        if rel_dir.parts[:2] == ("worklist", "_meta"):
            continue
        if rel_dir.parts[:2] == ("worklist", "private_only"):
            # Private content is intentionally excluded from tracked manifest.
            continue
        for filename in filenames:
            if filename in {".gitkeep", ".DS_Store"}:
                continue
            rel_file = str((Path(dirpath) / filename).relative_to(root)).replace("\\", "/")
            real_files.append(rel_file)

    untracked = sorted(set(real_files) - manifest_entries)
    return {
        "missing_manifest": False,
        "manifest_count": len(manifest_entries),
        "real_file_count": len(real_files),
        "untracked_files": untracked,
    }


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    snake_case_issues = check_snake_case(root)
    manifest_coverage = check_manifest_coverage(root)

    report = {
        "snake_case_issues": snake_case_issues,
        "manifest_coverage": manifest_coverage,
        "status": "ok" if not snake_case_issues and not manifest_coverage.get("untracked_files") else "needs_attention",
    }

    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"status: {report['status']}")
    print(f"snake_case_issues: {len(snake_case_issues)}")
    print(f"untracked_manifest_files: {len(manifest_coverage.get('untracked_files', []))}")
    print(f"report: {report_path}")
    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
