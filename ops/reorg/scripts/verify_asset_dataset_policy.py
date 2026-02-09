#!/usr/bin/env python3
"""Validate naming policy for courses/*/(assets|datasets)."""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository root path")
    parser.add_argument(
        "--policy",
        default="ops/reorg/policies/asset_dataset_policy.json",
        help="Policy JSON file",
    )
    parser.add_argument(
        "--report",
        default="ops/reorg/reports/asset_dataset_policy_verify.json",
        help="Output JSON report path",
    )
    return parser.parse_args()


def load_rule_lines(path: Path) -> list[str]:
    if not path.exists():
        return []

    rules: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        rules.append(line)
    return rules


def matches_any(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def find_managed_roots(root: Path, patterns: list[str]) -> list[Path]:
    roots: set[Path] = set()
    for pattern in patterns:
        for candidate in root.glob(pattern):
            if candidate.is_dir():
                roots.add(candidate)
    return sorted(roots)


def extension_allowed(name: str, allowed_extensions: list[str]) -> bool:
    lowered = name.lower()
    return any(lowered.endswith(ext.lower()) for ext in allowed_extensions)


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()

    policy_path = root / args.policy
    report_path = root / args.report
    report_path.parent.mkdir(parents=True, exist_ok=True)

    if not policy_path.exists():
        report = {
            "status": "needs_attention",
            "error": f"policy_not_found: {policy_path}",
        }
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(report["error"])
        return 1

    policy = json.loads(policy_path.read_text(encoding="utf-8"))

    name_regex = re.compile(policy.get("name_regex", r"^[a-z0-9._-]+$"))
    enforce_extension = bool(policy.get("enforce_extension", False))
    allowed_extensions = policy.get("allowed_extensions", [])
    allowed_filenames = set(policy.get("allowed_filenames", []))

    ignore_rules_path = root / policy.get("ignore_rules_file", "")
    whitelist_path = root / policy.get("whitelist_file", "")

    ignore_rules = load_rule_lines(ignore_rules_path)
    whitelist_rules = load_rule_lines(whitelist_path)

    managed_roots = find_managed_roots(root, policy.get("managed_roots", []))

    invalid_name_paths: list[str] = []
    invalid_extension_paths: list[str] = []
    skipped_paths: list[str] = []
    scanned_paths: list[str] = []

    for managed_root in managed_roots:
        for path in managed_root.rglob("*"):
            rel = str(path.relative_to(root)).replace("\\", "/")

            if matches_any(rel, ignore_rules):
                skipped_paths.append(rel)
                continue

            if matches_any(rel, whitelist_rules):
                skipped_paths.append(rel)
                continue

            scanned_paths.append(rel)

            name = path.name
            if name in allowed_filenames:
                continue

            if not name_regex.match(name):
                invalid_name_paths.append(rel)

            if path.is_file() and enforce_extension and name not in allowed_filenames:
                if not extension_allowed(name, allowed_extensions):
                    invalid_extension_paths.append(rel)

    status = "ok" if not invalid_name_paths and not invalid_extension_paths else "needs_attention"

    report = {
        "status": status,
        "policy": str(policy_path.relative_to(root)),
        "managed_roots": [str(p.relative_to(root)) for p in managed_roots],
        "summary": {
            "managed_root_count": len(managed_roots),
            "scanned_path_count": len(scanned_paths),
            "skipped_path_count": len(skipped_paths),
            "invalid_name_count": len(invalid_name_paths),
            "invalid_extension_count": len(invalid_extension_paths),
        },
        "invalid_name_paths": sorted(set(invalid_name_paths)),
        "invalid_extension_paths": sorted(set(invalid_extension_paths)),
    }

    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"status: {status}")
    print(f"managed_root_count: {len(managed_roots)}")
    print(f"scanned_path_count: {len(scanned_paths)}")
    print(f"invalid_name_count: {len(invalid_name_paths)}")
    print(f"invalid_extension_count: {len(invalid_extension_paths)}")
    print(f"report: {report_path}")
    return 0 if status == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
