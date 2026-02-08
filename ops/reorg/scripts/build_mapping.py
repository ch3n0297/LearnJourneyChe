#!/usr/bin/env python3
"""Build a move mapping from ops/reorg/rules.yaml (JSON-compatible YAML)."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository root path")
    parser.add_argument("--rules", default="ops/reorg/rules.yaml", help="Rules file")
    parser.add_argument("--output", default="ops/reorg/mapping.csv", help="Mapping CSV path")
    parser.add_argument("--owner", default="hjc", help="Owner name for mapping rows")
    return parser.parse_args()


def load_rules(path: Path) -> dict:
    content = path.read_text(encoding="utf-8")
    return json.loads(content)


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    rules = load_rules(Path(args.rules))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    keep_root = set(rules.get("keep_root_paths", []))
    top_level_moves = rules.get("top_level_moves", {})
    root_file_moves = rules.get("root_file_moves", {})
    fallback_root = rules.get("default_root_file_destination", "inbox/triage")

    rows = []
    columns = ["old_path", "new_path", "action", "reason", "owner", "status"]

    for old, new in sorted(top_level_moves.items()):
        src = root / old
        if src.exists():
            rows.append(
                {
                    "old_path": old,
                    "new_path": new,
                    "action": "move",
                    "reason": "top_level_reorg",
                    "owner": args.owner,
                    "status": "planned",
                }
            )

    for entry in sorted(root.iterdir(), key=lambda p: p.name.lower()):
        if entry.name in keep_root or entry.name.startswith("."):
            continue
        if entry.is_dir() and entry.name in top_level_moves:
            continue

        if entry.is_file():
            mapped = root_file_moves.get(entry.name)
            if mapped is None:
                mapped = f"{fallback_root}/{entry.name}"
            rows.append(
                {
                    "old_path": entry.name,
                    "new_path": mapped,
                    "action": "move",
                    "reason": "root_file_cleanup",
                    "owner": args.owner,
                    "status": "planned",
                }
            )

    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

    print(f"wrote mapping: {output}")
    print(f"rows: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
