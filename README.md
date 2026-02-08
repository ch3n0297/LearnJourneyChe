# Learn Journey

這個倉庫用來整理我的學習歷程，採用「課程主軸 + 專案區 + Worklist 中繼區」架構，確保內容可長期維護、可追溯、可逐步發布。

## Repository Layout

- `courses/`: 課程內容。
- `projects/`: 跨課程專案與會議記錄。
- `shared/`: 共用筆記、參考資料與素材。
- `inbox/triage/`: 尚未分類內容暫存。
- `worklist/`: 中繼區（草稿、原始檔、敏感檔）。
- `ops/reorg/`: 倉庫重整規則、腳本、報告。

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

## Standard Course Skeleton

第二輪細化後，每個課程資料夾都採用相同第一層結構：

```text
notes/ homework/ labs/ projects/ datasets/ reports/ assets/ references/ archive/
```

這讓課程新增內容時不需要再重新決定放置規則。

## Worklist Governance

`worklist/` 是中繼區，不是最終發布區。流程如下：

1. 新檔案先放入 `worklist/intake/`。
2. 在 `worklist/_meta/manifest.csv` 登記「非 private」檔案狀態。
3. 審核後移到 `drafting/`、`publish_queue/` 或 `private_only/`。
4. 只有 `publish_queue/` 可升級到 `courses/`、`projects/`、`shared/`。

更多規則請見 `worklist/README.md` 與 `worklist/_meta/publish_rules.yaml`。

## Reorganization Automation

重整腳本位於 `ops/reorg/scripts/`：

- `inventory.py`: 產生檔案盤點報告。
- `build_mapping.py`: 依規則產生 `ops/reorg/mapping.csv`。
- `apply_mapping.py`: 依 mapping 執行 dry-run 或實際搬移。
- `rewrite_links.py`: 批次修正 Markdown/TXT 路徑引用。
- `verify_repo.py`: 檢查命名與 worklist manifest 覆蓋率。
- `refine_courses_round2.py`: 第二輪課程內部細化（統一第一層結構與主要命名）。
- `refine_courses_round3.py`: 第三輪課程內容檔名正規化（受控範圍內改為 snake_case）。

範例：

```bash
python3 ops/reorg/scripts/inventory.py --max-hash-bytes 0
python3 ops/reorg/scripts/build_mapping.py
python3 ops/reorg/scripts/apply_mapping.py --mode dry-run
python3 ops/reorg/scripts/apply_mapping.py --mode execute
python3 ops/reorg/scripts/rewrite_links.py --mode write
python3 ops/reorg/scripts/refine_courses_round2.py --mode execute
python3 ops/reorg/scripts/refine_courses_round3.py --mode execute
python3 ops/reorg/scripts/verify_repo.py
```

## Contact

- Email: `hjcaieng@gmail.com`
- Lab Website: https://sites.google.com/view/cgu-icps-lab/home
