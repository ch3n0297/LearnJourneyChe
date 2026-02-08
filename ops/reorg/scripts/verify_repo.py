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
ROUND3_NAME = re.compile(r"^[a-z0-9._]+$")
IGNORE_DIRS = {".git", ".venv", "__pycache__", ".ipynb_checkpoints"}

COURSE_SKELETON = [
    "notes",
    "homework",
    "labs",
    "projects",
    "datasets",
    "reports",
    "assets",
    "references",
    "archive",
]

MANAGED_ROOTS = {"notes", "homework", "labs", "projects", "reports", "references"}
KEEP_NAMES = {
    "README",
    "README.md",
    "LICENSE",
    "Makefile",
    "CMakeLists.txt",
    ".gitignore",
    ".gitattributes",
    ".gitmodules",
}
EXCLUDED_SEGMENTS = {
    ".git",
    ".venv",
    ".vscode",
    "__pycache__",
    ".ipynb_checkpoints",
    "data",
    "images",
    "open3d_data",
    "pet_seg_data",
    "training_logs",
    "project_files",
    "results",
    "runs_unet_pet",
    "third_party",
    "dist",
    "extract",
    "download",
    "sumodata",
    "hw4",
    "bunny",
    "action_man",
    "age_prediction",
    "haarcascades",
    "pic",
    "texture_test",
    "test_data",
}


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
    """Validate naming in managed top-level namespaces only."""
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


def check_course_skeleton(root: Path) -> list[str]:
    missing: list[str] = []
    courses_root = root / "courses"
    if not courses_root.exists():
        return missing

    for course_dir in sorted([p for p in courses_root.iterdir() if p.is_dir()], key=lambda p: p.name.lower()):
        for required in COURSE_SKELETON:
            if not (course_dir / required).exists():
                missing.append(f"{course_dir.relative_to(root)}/{required}")

    return missing


def in_round3_scope(rel_to_course: Path) -> bool:
    if not rel_to_course.parts:
        return False
    if rel_to_course.parts[0] not in MANAGED_ROOTS:
        return False

    lowered = [seg.lower().replace("-", "_") for seg in rel_to_course.parts]
    if any(seg in EXCLUDED_SEGMENTS for seg in lowered):
        return False

    if len(rel_to_course.parts) > 6:
        return False

    return True


def check_round3_names(root: Path) -> list[str]:
    issues: list[str] = []
    courses_root = root / "courses"
    if not courses_root.exists():
        return issues

    for course_dir in sorted([p for p in courses_root.iterdir() if p.is_dir()], key=lambda p: p.name.lower()):
        for path in course_dir.rglob("*"):
            if path.name in KEEP_NAMES:
                continue

            rel_to_course = path.relative_to(course_dir)
            if not in_round3_scope(rel_to_course):
                continue

            if not ROUND3_NAME.match(path.name):
                issues.append(str(path.relative_to(root)))

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
    course_skeleton_missing = check_course_skeleton(root)
    round3_name_issues = check_round3_names(root)
    manifest_coverage = check_manifest_coverage(root)

    status_ok = (
        not snake_case_issues
        and not course_skeleton_missing
        and not round3_name_issues
        and not manifest_coverage.get("untracked_files")
    )

    report = {
        "snake_case_issues": snake_case_issues,
        "course_skeleton_missing": course_skeleton_missing,
        "round3_name_issues": round3_name_issues,
        "manifest_coverage": manifest_coverage,
        "status": "ok" if status_ok else "needs_attention",
    }

    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"status: {report['status']}")
    print(f"snake_case_issues: {len(snake_case_issues)}")
    print(f"course_skeleton_missing: {len(course_skeleton_missing)}")
    print(f"round3_name_issues: {len(round3_name_issues)}")
    print(f"untracked_manifest_files: {len(manifest_coverage.get('untracked_files', []))}")
    print(f"report: {report_path}")
    return 0 if status_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
