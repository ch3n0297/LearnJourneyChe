# Round4 Policy

This folder stores guardrails for course `assets/` and `datasets/` naming checks.

## Files

- `asset_dataset_policy.json`: main policy configuration.
- `asset_dataset_whitelist.txt`: explicit path globs that bypass strict checks.
- `asset_dataset_ignore.txt`: ignored noise patterns (OS temp files, VCS internals, etc.).

## Usage

```bash
python3 ops/reorg/scripts/verify_asset_dataset_policy.py
```

If a new raw asset must keep original naming, add a targeted glob to
`asset_dataset_whitelist.txt` instead of weakening the global regex.
