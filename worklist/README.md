# Worklist Governance

`worklist/` is a staging area for unfinished drafts, raw sources, and private materials.

## Folders

- `intake/`: new files awaiting triage.
- `drafting/`: active drafts that can become publishable content.
- `raw_sources/`: raw images, scans, or extracted source files.
- `private_only/`: sensitive files that must never be published.
- `publish_queue/`: reviewed items waiting for final promotion.
- `_meta/`: process metadata (manifest, rules, review logs).

## Required workflow

1. Put new files under `intake/` first.
2. Register non-private files in `_meta/manifest.csv` (private_only stays out of tracked manifest).
3. During review, classify into `drafting/`, `publish_queue/`, or `private_only/`.
4. Only files in `publish_queue/` can be promoted into `courses/`, `projects/`, or `shared/`.
5. For any private file, set `sensitivity=private` and keep it under `private_only/`.

## Publish gate checklist

- The target path is determined and recorded.
- The filename follows snake_case.
- Sensitivity is not `private`.
- A review entry is appended to `_meta/review_log.md`.
- Private-only filenames should stay in local notes, not in tracked metadata.
