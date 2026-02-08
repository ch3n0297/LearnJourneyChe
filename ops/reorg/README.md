# Repository Reorganization Ops

This folder stores the reorganization source of truth and automation tools.

## Files

- `rules.yaml`: root-level move rules.
- `mapping.csv`: generated move plan (`old_path -> new_path`).
- `scripts/`: inventory, mapping, apply, link rewrite, round2 refine, and verify.
- `reports/`: generated JSON reports (ignored by Git except `.gitkeep`).

## Suggested workflow

1. `inventory.py` to inspect repository shape.
2. `build_mapping.py` to generate `mapping.csv`.
3. `apply_mapping.py --mode dry-run` and review report.
4. `apply_mapping.py --mode execute` after confirmation.
5. `rewrite_links.py --mode write` to update references.
6. `refine_courses_round2.py --mode execute` to normalize course first-level structure.
7. `verify_repo.py` to validate naming and worklist governance.
