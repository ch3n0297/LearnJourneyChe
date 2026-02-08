#!/usr/bin/env python3
"""Second-round course refinement: normalize first-level structure and naming."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


STANDARD_SUBDIRS = [
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

DIRECTORY_MOVES = {
    ("aiot", "homework_QLearning"): "homework/homework_q_learning",
    ("aiot", "SUMO_SDPAS"): "projects/sumo_sdpas",
    ("aiot", "traffic-optimization-project"): "projects/traffic_optimization_project",
    ("computer_vision", "L2_S"): "labs/l2_s",
    ("computer_vision", "L3_S"): "labs/l3_s",
    ("computer_vision", "L4_S"): "labs/l4_s",
    ("computer_vision", "L5_S"): "labs/l5_s",
    ("computer_vision", "L6_S"): "labs/l6_s",
    ("computer_vision", "L7_S"): "labs/l7_s",
    ("computer_vision", "L8_S"): "labs/l8_s",
    ("computer_vision", "L9_S"): "labs/l9_s",
    ("computer_vision", "L10_S"): "labs/l10_s",
    ("computer_vision", "L12_S"): "labs/l12_s",
    ("data_mining", "HW1"): "homework/hw1",
    ("data_mining", "HW2"): "homework/hw2",
    ("data_mining", "DM_Final"): "projects/dm_final",
    ("multimedia_information_system", "HW1_DFT_Filter"): "homework/hw1_dft_filter",
    ("multimedia_information_system", "Hw2_YUV_Subtransform"): "homework/hw2_yuv_subtransform",
    ("natural_language_processing", "NLP_HW1_B1128019"): "homework/nlp_hw1_b1128019",
    ("natural_language_processing", "NLP_HW2_B1128019"): "homework/nlp_hw2_b1128019",
    ("natural_language_processing", "NLP_HW3_B1128019"): "homework/nlp_hw3_b1128019",
    ("natural_language_processing", "NLP_HW4_B1128019"): "homework/nlp_hw4_b1128019",
    ("natural_language_processing", "NLP_Finalproject"): "projects/nlp_finalproject",
    ("network_security", "DES_Cpp_Project-main"): "projects/des_cpp_project_main",
    ("parallel_programming_design", "Homework1_B1128019"): "homework/homework1_b1128019",
    ("parallel_programming_design", "Homework2_B1128019"): "homework/homework2_b1128019",
    ("parallel_programming_design", "Homework3_B1128019"): "homework/homework3_b1128019",
    ("parallel_programming_design", "Homework4_B1128019"): "homework/homework4_b1128019",
    ("parallel_programming_design", "Final_B1128019"): "projects/final_b1128019",
}

FILE_MOVES = {
    ("natural_language_processing", "期中考試重點問題.md"): "notes/midterm_key_questions.md",
    ("multimedia_information_system", "111_1_Quiz3_ans.pdf"): "references/quiz3_ans_111_1.pdf",
    ("multimedia_information_system", "112_1_Quiz3.pdf"): "references/quiz3_112_1.pdf",
    ("multimedia_information_system", "多媒體_108+109考古合集.pdf"): "references/multimedia_108_109_exam_collection.pdf",
    ("network_security", "HW_3.doc"): "homework/hw_3.doc",
    ("network_security", "Ns_HW3.pdf"): "homework/ns_hw3.pdf",
    ("network_security", "Ns_筆記.md"): "notes/ns_notes.md",
    ("parallel_programming_design", "Self-learning.pdf"): "references/self_learning.pdf",
    ("blockchain", "H1_BC.md"): "homework/h1_bc.md",
    ("blockchain", "H1_BC_B1128019.pdf"): "homework/h1_bc_b1128019.pdf",
    ("blockchain", "rho_B1128019.py"): "homework/rho_b1128019.py",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--mode", choices=["dry-run", "execute"], default="dry-run")
    parser.add_argument(
        "--report",
        default="ops/reorg/reports/refine_round2_result.json",
        help="JSON output report",
    )
    return parser.parse_args()


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    idx = 1
    while True:
        candidate = path.with_name(f"{path.stem}_dup{idx}{path.suffix}")
        if not candidate.exists():
            return candidate
        idx += 1


def apply_move(src: Path, dst: Path, execute: bool) -> tuple[str, str, str]:
    final_dst = unique_path(dst)
    if execute:
        final_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(final_dst))
    return str(src), str(final_dst), "move"


def refine_biologic(course_dir: Path, execute: bool, actions: list[tuple[str, str, str]]) -> None:
    # First-level files only; keep directory safety conservative.
    for entry in sorted(course_dir.iterdir(), key=lambda p: p.name.lower()):
        if not entry.is_file() or entry.name.startswith("."):
            continue

        lower = entry.name.lower()
        if lower.endswith(".png"):
            rel_dst = f"assets/{lower.replace(' ', '_')}"
        elif lower.endswith((".fasta.txt", ".aln-clustal_num")) or lower.startswith(("iprscan", "seqdump")):
            rel_dst = f"datasets/{lower.replace(' ', '_')}"
        elif lower.endswith((".zip", ".pdf")):
            rel_dst = f"reports/{lower.replace(' ', '_')}"
        else:
            rel_dst = f"notes/{lower.replace(' ', '_')}"

        src = entry
        dst = course_dir / rel_dst
        actions.append(apply_move(src, dst, execute))


def remove_ds_store(root: Path, execute: bool, actions: list[tuple[str, str, str]]) -> None:
    for path in root.rglob(".DS_Store"):
        if ".git" in path.parts:
            continue
        if execute:
            path.unlink(missing_ok=True)
        actions.append((str(path), "", "delete"))


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    courses = root / "courses"
    execute = args.mode == "execute"

    actions: list[tuple[str, str, str]] = []
    created_dirs: list[str] = []
    skipped: list[str] = []

    for course_dir in sorted([p for p in courses.iterdir() if p.is_dir()], key=lambda p: p.name.lower()):
        # Build standard skeleton.
        for name in STANDARD_SUBDIRS:
            target = course_dir / name
            if not target.exists():
                if execute:
                    target.mkdir(parents=True, exist_ok=True)
                created_dirs.append(str(target))

        # Move known first-level directories.
        for (course_name, old_name), rel_new in DIRECTORY_MOVES.items():
            if course_name != course_dir.name:
                continue
            src = course_dir / old_name
            if not src.exists():
                continue
            dst = course_dir / rel_new
            actions.append(apply_move(src, dst, execute))

        # Move known first-level files.
        for (course_name, old_name), rel_new in FILE_MOVES.items():
            if course_name != course_dir.name:
                continue
            src = course_dir / old_name
            if not src.exists():
                continue
            dst = course_dir / rel_new
            actions.append(apply_move(src, dst, execute))

        # Course-specific heuristic handling.
        if course_dir.name == "biologic_information":
            refine_biologic(course_dir, execute, actions)

        # Cleanup obvious noise files at first level.
        ds = course_dir / ".DS_Store"
        if ds.exists():
            if execute:
                ds.unlink(missing_ok=True)
            actions.append((str(ds), "", "delete"))

        # Keep only managed/known first-level entries; flag unfamiliar items.
        known = set(STANDARD_SUBDIRS) | {".venv", ".vscode", "notes"}
        for child in course_dir.iterdir():
            if child.name.startswith("."):
                continue
            if child.name in known:
                continue
            if child.is_dir() and child.name not in known:
                # Some courses may still have custom folders after round2.
                skipped.append(str(child))
            elif child.is_file():
                skipped.append(str(child))

    remove_ds_store(root, execute, actions)

    report = {
        "mode": args.mode,
        "created_dirs": created_dirs,
        "actions": [{"src": a[0], "dst": a[1], "op": a[2]} for a in actions],
        "skipped": sorted(set(skipped)),
        "summary": {
            "created_dirs": len(created_dirs),
            "actions": len(actions),
            "skipped": len(set(skipped)),
        },
    }

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"mode: {args.mode}")
    print(f"created_dirs: {len(created_dirs)}")
    print(f"actions: {len(actions)}")
    print(f"skipped: {len(set(skipped))}")
    print(f"report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
