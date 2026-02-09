#!/usr/bin/env python3
"""Verify structural, naming, and worklist governance expectations."""

from __future__ import annotations

import argparse
import fnmatch
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
ASSET_DATASET_POLICY_PATH = "ops/reorg/policies/asset_dataset_policy.json"

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


def _load_rule_lines(path: Path) -> list[str]:
    if not path.exists():
        return []

    rules: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        rules.append(line)
    return rules


def _matches_any(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def check_asset_dataset_policy(root: Path) -> dict:
    policy_path = root / ASSET_DATASET_POLICY_PATH
    if not policy_path.exists():
        return {
            "status": "needs_attention",
            "error": f"policy_not_found:{ASSET_DATASET_POLICY_PATH}",
            "invalid_name_paths": [],
            "invalid_extension_paths": [],
        }

    policy = json.loads(policy_path.read_text(encoding="utf-8"))

    name_regex = re.compile(policy.get("name_regex", r"^[a-z0-9._-]+$"))
    enforce_extension = bool(policy.get("enforce_extension", False))
    allowed_extensions = policy.get("allowed_extensions", [])
    allowed_filenames = set(policy.get("allowed_filenames", []))

    ignore_rules_file = policy.get("ignore_rules_file", "")
    whitelist_file = policy.get("whitelist_file", "")

    ignore_rules = _load_rule_lines(root / ignore_rules_file) if ignore_rules_file else []
    whitelist_rules = _load_rule_lines(root / whitelist_file) if whitelist_file else []

    managed_roots: list[Path] = []
    for pattern in policy.get("managed_roots", []):
        for candidate in root.glob(pattern):
            if candidate.is_dir():
                managed_roots.append(candidate)

    invalid_name_paths: list[str] = []
    invalid_extension_paths: list[str] = []
    scanned_count = 0

    for managed_root in managed_roots:
        for path in managed_root.rglob("*"):
            rel = str(path.relative_to(root)).replace("\\", "/")

            if _matches_any(rel, ignore_rules) or _matches_any(rel, whitelist_rules):
                continue

            scanned_count += 1
            name = path.name

            if name in allowed_filenames:
                continue

            if not name_regex.match(name):
                invalid_name_paths.append(rel)

            if path.is_file() and enforce_extension and name not in allowed_filenames:
                lowered = name.lower()
                if not any(lowered.endswith(ext.lower()) for ext in allowed_extensions):
                    invalid_extension_paths.append(rel)

    status = "ok" if not invalid_name_paths and not invalid_extension_paths else "needs_attention"
    return {
        "status": status,
        "policy": ASSET_DATASET_POLICY_PATH,
        "managed_root_count": len(managed_roots),
        "scanned_path_count": scanned_count,
        "invalid_name_paths": sorted(set(invalid_name_paths)),
        "invalid_extension_paths": sorted(set(invalid_extension_paths)),
    }


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
    asset_dataset_policy = check_asset_dataset_policy(root)
    manifest_coverage = check_manifest_coverage(root)

    status_ok = (
        not snake_case_issues
        and not course_skeleton_missing
        and not round3_name_issues
        and asset_dataset_policy.get("status") == "ok"
        and not manifest_coverage.get("untracked_files")
    )

    report = {
        "snake_case_issues": snake_case_issues,
        "course_skeleton_missing": course_skeleton_missing,
        "round3_name_issues": round3_name_issues,
        "asset_dataset_policy": asset_dataset_policy,
        "manifest_coverage": manifest_coverage,
        "status": "ok" if status_ok else "needs_attention",
    }

    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"status: {report['status']}")
    print(f"snake_case_issues: {len(snake_case_issues)}")
    print(f"course_skeleton_missing: {len(course_skeleton_missing)}")
    print(f"round3_name_issues: {len(round3_name_issues)}")
    print(f"asset_dataset_invalid_names: {len(asset_dataset_policy.get('invalid_name_paths', []))}")
    print(f"asset_dataset_invalid_exts: {len(asset_dataset_policy.get('invalid_extension_paths', []))}")
    print(f"untracked_manifest_files: {len(manifest_coverage.get('untracked_files', []))}")
    print(f"report: {report_path}")
    return 0 if status_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
