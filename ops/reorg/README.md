# Repository Reorganization Ops

This folder stores the reorganization source of truth and automation tools.

## Files

- `rules.yaml`: mapping rules and root move policy.
- `mapping.csv`: generated move plan (`old_path -> new_path`).
- `scripts/`: automation scripts for inventory, mapping, apply, link rewrite, and verify.
- `reports/`: generated JSON reports (ignored by Git).

## Suggested workflow

1. `inventory.py` to inspect current repository shape.
2. `build_mapping.py` to generate `mapping.csv`.
3. `apply_mapping.py --mode dry-run` and review report.
4. `apply_mapping.py --mode execute` after confirmation.
5. `rewrite_links.py --mode write` to update references.
6. `verify_repo.py` to validate naming and worklist governance.
