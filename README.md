# Learn Journey

這個倉庫用來整理我的學習歷程，採用「課程主軸 + 專案區 + Worklist 中繼區」結構，讓內容能長期維護、可追溯、可逐步發布。

## Repository Layout

- `courses/`: 課程內容（作業、筆記、實驗、專題）。
- `projects/`: 跨課程專案與會議記錄。
- `shared/`: 共用筆記、參考資料與素材。
- `inbox/triage/`: 尚未分類內容的暫存入口。
- `worklist/`: 中繼區（未完成、原始檔、敏感檔管理）。
- `ops/reorg/`: 重整規則、mapping、腳本與報表。

## Course Index

- `courses/aiot`
- `courses/biologic_information`
- `courses/blockchain`
- `courses/computer_vision`
- `courses/data_mining`
- `courses/eecs101`
- `courses/multimedia_information_system`
- `courses/natural_language_processing`
- `courses/network_security`
- `courses/parallel_programming_design`

## Project Index

- `projects/ai_car_flow`
- `projects/mcp_research`
- `projects/meeting_minutes`

## Worklist Governance (重要)

`worklist/` 是中繼區，不是最終內容區。預設流程如下：

1. 新檔案先放入 `worklist/intake/`。
2. 在 `worklist/_meta/manifest.csv` 登記檔案狀態與敏感級別。
3. 審核後移到 `drafting/`、`publish_queue/` 或 `private_only/`。
4. 只有 `publish_queue/` 可升級到 `courses/`、`projects/`、`shared/`。

更多規則請看 `worklist/README.md` 與 `worklist/_meta/publish_rules.yaml`。

## Reorganization Automation

重整腳本位於 `ops/reorg/scripts/`：

- `inventory.py`: 產生檔案盤點報告。
- `build_mapping.py`: 依規則產生 `ops/reorg/mapping.csv`。
- `apply_mapping.py`: 依 mapping 執行 dry-run 或實際搬移。
- `rewrite_links.py`: 批次修正 Markdown/TXT 路徑引用。
- `verify_repo.py`: 檢查命名與 worklist manifest 覆蓋率。

範例：

```bash
python3 ops/reorg/scripts/inventory.py --max-hash-bytes 0
python3 ops/reorg/scripts/build_mapping.py
python3 ops/reorg/scripts/apply_mapping.py --mode dry-run
python3 ops/reorg/scripts/apply_mapping.py --mode execute
python3 ops/reorg/scripts/rewrite_links.py --mode write
python3 ops/reorg/scripts/verify_repo.py
```

## Contact

- Email: `hjcaieng@gmail.com`
- Lab Website: https://sites.google.com/view/cgu-icps-lab/home
