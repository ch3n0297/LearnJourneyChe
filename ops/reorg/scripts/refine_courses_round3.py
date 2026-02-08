#!/usr/bin/env python3
"""Third-round refinement: normalize course-level filenames to snake_case.

Scope is intentionally conservative:
- only content under notes/homework/labs/projects/reports/references
- skip heavy/raw subtrees (datasets, generated outputs, vendor code)
- preserve conventional names such as README.md and Makefile
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

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

# Skip heavy/raw/vendor trees to avoid noisy churn.
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
    "hw4",  # nested local repo under computer_vision/labs/l6_s/HW4
    "bunny",
    "action_man",
    "age_prediction",
    "haarcascades",
    "pic",
    "texture_test",
    "test_data",
}

MANUAL_RENAMES = {
    "B1128019黃教丞FINAL.pdf": "b1128019_final.pdf",
    "資料探勘期末B1128019.md": "data_mining_final_b1128019.md",
    "B1128019_黃教丞_1002.html": "b1128019_1002.html",
    "簡報1.pptx": "slides_1.pptx",
    "B1128019黃教丞_cv_L5_s.ipynb": "b1128019_cv_l5_s.ipynb",
    "B1128019黃教丞.ipynb": "b1128019.ipynb",
    "生物資訊學第五次作業.pdf": "biologic_information_homework_5.pdf",
    "規則格式.rtf": "rule_format.rtf",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--mode", choices=["dry-run", "execute"], default="dry-run")
    parser.add_argument(
        "--report",
        default="ops/reorg/reports/refine_round3_result.json",
        help="JSON report path",
    )
    parser.add_argument(
        "--mapping",
        default="ops/reorg/round3_mapping.csv",
        help="CSV mapping path for link rewrite",
    )
    parser.add_argument("--owner", default="hjc", help="Owner value in mapping.csv")
    return parser.parse_args()


def normalize_ascii_name(name: str) -> str:
    if name in MANUAL_RENAMES:
        return MANUAL_RENAMES[name]

    if name in KEEP_NAMES:
        return name

    if name.startswith(".") and name not in {".gitignore", ".gitattributes", ".gitmodules"}:
        return name

    path_name = Path(name)
    ext = path_name.suffix.lower()
    if ext:
        base = name[: -len(ext)]
    else:
        base = name

    base = base.replace("&", " and ")
    base = base.replace("+", " plus ")
    base = base.replace("'", "")
    base = re.sub(r"[\s\-\/\\,:;()\[\]{}]+", "_", base)
    base = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", base)
    base = base.lower()
    base = re.sub(r"[^a-z0-9_]+", "_", base)
    base = re.sub(r"_+", "_", base).strip("_")

    if not base:
        base = "untitled"

    return f"{base}{ext}"


def in_scope(rel_to_courses: Path) -> bool:
    if not rel_to_courses.parts:
        return False

    if rel_to_courses.parts[0] not in MANAGED_ROOTS:
        return False

    lowered_parts = [p.lower().replace("-", "_") for p in rel_to_courses.parts]
    if any(seg in EXCLUDED_SEGMENTS for seg in lowered_parts):
        return False

    # Avoid renaming deep raw content.
    if len(rel_to_courses.parts) > 6:
        return False

    return True


def same_file(src: Path, dst: Path) -> bool:
    try:
        return src.exists() and dst.exists() and src.samefile(dst)
    except OSError:
        return False


def choose_destination(src: Path, target_name: str) -> Path:
    target = src.with_name(target_name)

    # Case-only rename on case-insensitive filesystem should reuse target.
    if same_file(src, target):
        return target

    if not target.exists():
        return target

    idx = 1
    while True:
        candidate = target.with_name(f"{target.stem}_dup{idx}{target.suffix}")
        if not candidate.exists():
            return candidate
        idx += 1


def build_candidates(courses_root: Path) -> tuple[list[Path], list[Path]]:
    files: list[Path] = []
    dirs: list[Path] = []

    for course_dir in sorted([p for p in courses_root.iterdir() if p.is_dir()], key=lambda p: p.name.lower()):
        for path in course_dir.rglob("*"):
            rel = path.relative_to(course_dir)
            if not in_scope(rel):
                continue

            if path.name in KEEP_NAMES:
                continue

            new_name = normalize_ascii_name(path.name)
            if new_name == path.name:
                continue

            if path.is_dir():
                dirs.append(path)
            elif path.is_file():
                files.append(path)

    files.sort(key=lambda p: len(p.parts), reverse=True)
    dirs.sort(key=lambda p: len(p.parts), reverse=True)
    return files, dirs


def apply_rename(path: Path, new_name: str, root: Path, execute: bool) -> tuple[str, str]:
    destination = choose_destination(path, new_name)

    old_rel = str(path.relative_to(root)).replace("\\", "/")
    new_rel = str(destination.relative_to(root)).replace("\\", "/")

    if execute:
        # Handle case-only renames on case-insensitive filesystem.
        if same_file(path, destination) and path.name != destination.name:
            tmp = path.with_name(f"__tmp_rename__{path.name}")
            idx = 1
            while tmp.exists():
                tmp = path.with_name(f"__tmp_rename__{idx}_{path.name}")
                idx += 1
            path.rename(tmp)
            tmp.rename(destination)
        elif path != destination:
            path.rename(destination)

    return old_rel, new_rel


def write_mapping(rows: list[dict[str, str]], mapping_path: Path) -> None:
    mapping_path.parent.mkdir(parents=True, exist_ok=True)
    with mapping_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["old_path", "new_path", "action", "reason", "owner", "status"],
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    courses_root = root / "courses"

    execute = args.mode == "execute"

    file_candidates, dir_candidates = build_candidates(courses_root)

    operations: list[dict[str, str]] = []

    for path in file_candidates:
        if execute and not path.exists():
            continue
        old_rel, new_rel = apply_rename(path, normalize_ascii_name(path.name), root, execute)
        operations.append({"old_path": old_rel, "new_path": new_rel, "kind": "file"})

    for path in dir_candidates:
        if execute and not path.exists():
            continue
        old_rel, new_rel = apply_rename(path, normalize_ascii_name(path.name), root, execute)
        operations.append({"old_path": old_rel, "new_path": new_rel, "kind": "dir"})

    mapping_rows = [
        {
            "old_path": op["old_path"],
            "new_path": op["new_path"],
            "action": "move",
            "reason": "round3_filename_normalization",
            "owner": args.owner,
            "status": "applied" if execute else "planned",
        }
        for op in operations
    ]

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "mode": args.mode,
        "summary": {
            "file_candidates": len(file_candidates),
            "dir_candidates": len(dir_candidates),
            "operations": len(operations),
        },
        "operations": operations,
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    write_mapping(mapping_rows, Path(args.mapping))

    print(f"mode: {args.mode}")
    print(f"files: {len(file_candidates)}")
    print(f"dirs: {len(dir_candidates)}")
    print(f"operations: {len(operations)}")
    print(f"report: {report_path}")
    print(f"mapping: {args.mapping}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
