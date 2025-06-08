### 逐字稿1（英文解說 → 中文重點）

---

**1. Argument parser**

> _“We begin by instantiating an `argparse.ArgumentParser` with the description _‘Select entry/exit lines for each route’_.  
> Two command-line options are declared: `--video` is **required**, forcing the user to specify a video file, while `--config` is **optional** and defaults to `config.yaml`.  
> Finally, `args = parser.parse_args()` materialises these choices into a namespace we can use later.”_

> 這段利用 `argparse` 建立命令列介面：`--video` 必填，`--config` 有預設值 `config.yaml`，並以 `parse_args()` 取得結果。

---

**2. Open video & sanity check**

> _“`cv2.VideoCapture(args.video)` opens the chosen file.  
> We immediately read one frame; if that read fails, we raise a `RuntimeError`, aborting before any GUI resources are allocated.”_

> 用 OpenCV 開啟影片並讀首張影格；若失敗就丟 `RuntimeError`，避免後續 GUI 出錯。

---

**3. Session state variables**

> _“Four variables track the interactive session:  
> `clicks` buffers two mouse points;  
> `routes` stores finished entry/exit pairs;  
> `route_idx` labels each route sequentially;  
> `line_type` toggles between _entry_ (green) and _exit_ (red).”_

> 互動過程的狀態：`clicks` 暫存 2 點，`routes` 收集路線，`route_idx` 編號，`line_type` 決定畫綠線或紅線。

---

**4. Mouse callback**

> _“`mouse_cb` fires on every left-click.  
> Each click is stored and marked with a yellow dot.  
> After two clicks we draw a line in green or red, label it with `route{n}_{entry|exit}`, and update the `routes` list.  
> When an entry line is finished, `line_type` flips to ‘exit’; after the exit line, we reset to ‘entry’ and increment `route_idx`.”_

> 滑鼠左鍵點一下存座標並畫黃點；湊滿兩點就畫線、貼標籤並寫進 `routes`。畫完 Entry 轉畫 Exit，完成一對後編號加一。

---

**5. Window setup & user prompts**

> _“We create a named window, bind the mouse callback, and print concise instructions:  
> – click two points per line;  
> – draw entry first, exit second;  
> – `s` to save, `r` to reset, `Esc` to quit.”_

> 建立視窗與滑鼠回呼，並輸出提示：雙擊成線、先綠後紅；`s` 儲存、`r` 重繪、`Esc` 離開。

---

**6. Real-time preview loop**

> _“Inside an infinite `while` loop we refresh the preview with `cv2.imshow`.  
> Key events are polled every millisecond:  
> • `r` clears all state and restarts from the first frame;  
> • `s` exits the loop and proceeds to saving;  
> • `Esc` aborts the session, releasing resources immediately.”_

> 主迴圈持續顯示影像並監聽鍵盤：`r` 重設、`s` 結束並進入儲存、`Esc` 放棄並釋放資源。

---

**7. Persist routes to YAML**

> _“After leaving the loop we load (or create) the YAML file given by `--config`, update `video_path` and `routes`, and dump it back with `yaml.dump`.  
> A final print statement confirms how many routes were recorded.”_

> 退出迴圈後讀取或建立 YAML；覆寫 `video_path` 與 `routes`，再寫回檔案，最後列印路線總數。

---

### 逐字稿2（英文說明 → 中文重點）

_只涵蓋你貼出的 `utils/tracker.py` 內容，完全依照原註釋與說明。_

---

#### 1 · Module purpose

> _“This file implements a **minimal centroid-based tracker** for the CarFlow project.  
> Its sole job is to take raw detection boxes from YOLO and return them with **stable object IDs** so later stages can count vehicles consistently.”_

> 這個檔案提供最精簡的質心追蹤器，讓 YOLO 偵測框附上固定 ID，方便後續統計。

---

#### 2 · Constructor (`__init__`)

> *“When we instantiate `Tracker`, we keep three pieces of state:
> 
> 1. `self.center_points` – a dictionary mapping **object ID → last known centroid (cx, cy)**.
>     
> 2. `self.id_count` – a monotonically increasing counter that guarantees every new track gets a unique ID.
>     
> 3. `self.max_distance` – the only hyper-parameter; two centroids closer than this many pixels are assumed to be the _same_ object.”*
>     

> 物件狀態：`center_points` 存質心、`id_count` 產生遞增 ID、`max_distance` 決定配對距離。

---

#### 3 · Core algorithm (`update`)

> *“`update(rectangles)` is called once per frame.  
> For **each** detection box `(x, y, w, h)` we:
> 
> 1. Compute its centroid `cx, cy`.
>     
> 2. Scan all existing centroids; the first one within `max_distance` is treated as a match.
>     
> 3. If no match is found, we create a **new ID** using `self.id_count`.
>     
> 4. Regardless of match or new, we overwrite `self.center_points[id]` with the current centroid and append `[x, y, w, h, id]` to the return list.”*
>     

> 每個偵測框 → 算質心 → 找最近舊質心若距離 < `max_distance` 就沿用 ID，否則新建 ID；最後回傳含 ID 的清單。

---

#### 4 · Return value

> _“The method returns a list shaped like `[[x, y, w, h, id], …]`.  
> Downstream code can draw bounding boxes and print the same ID on every frame, achieving temporal consistency without heavy models or Kalman filters.”_

> 回傳格式為 `[x, y, w, h, id]`，下游可直接畫框並顯示同一 ID。

---

#### 5 · Intentional simplifications

> _“By design this tracker is **deliberately minimal**:  
> • No track termination – IDs live forever;  
> • No motion prediction – we rely on a single Euclidean distance check;  
> • No appearance features – perfect for demos and low-resource devices.”_

> 刻意簡化：不終止軌跡、不做運動預測、不用外觀特徵，適合教學與輕量應用。

---

#### 6 · Take-away

> _“In roughly 40 lines we transform raw detections into structured, ID-aware data.  
> The code illustrates Python’s readability and the power of small, single-responsibility classes.”_

> 約 40 行程式把偵測結果轉成帶 ID 的資料，示範 Python 簡潔與單一職責設計。

### 逐字稿3（English narrative ➜ 中文重點）

_Strictly reflects the code and inline comments you provided; nothing extra._

---

#### 1 · Module banner

> _“We begin with a doc-string that lays out the entire pipeline in four bullets:  
> read `config.yaml`, run YOLOv8, assign unique IDs with our `Tracker`, decide whether a vehicle crosses entry or exit, then show live counts and dump both an annotated video and a CSV.”_

> 四行綱要：讀設定 → YOLOv8 偵測 → Tracker 配 ID → 判斷跨線 → 即時顯示並輸出影片與 CSV。

---

#### 2 · Imports

> _“Only standard libraries plus `numpy`, `yaml`, `cv2`, the Ultralytics `YOLO` class, and our in-house `Tracker`.  
> Everything else stays inside this single file, keeping external dependencies minimal.”_

> 只用標準庫及 `numpy / yaml / cv2`、Ultralytics YOLO，以及自製 `Tracker`；依賴簡潔。

---

#### 3 · Geometry helpers (`ccw`, `crossed`, `get_color`)

> _“Three tiny helpers: `ccw` tests orientation, `crossed` reports whether two points cross a directed line, and `get_color` maps class names to BGR tuples, adding a green entry for motorcycles.”_

> `ccw` 判方向、`crossed` 判是否跨線、`get_color` 給顏色（含摩托車綠色）。

---

#### 4 · Config loading

> _“`config.yaml` is parsed once; we pull out `routes`, `classes`, and `model_path`.  
> If the YAML omits `classes`, we fall back to the four defaults listed in the header.”_

> 讀 YAML 抓 `routes / classes / model_path`；若沒寫 `classes` 就用預設四類。

---

#### 5 · Model setup

> _“A YOLOv8 model is loaded with the chosen weights.  
> The COCO class list is read from `coco.txt`, and we pre-build a name-to-index map for later filtering.”_

> 載入 YOLOv8 權重；讀 `coco.txt` 產生名稱→索引對照。

---

#### 6 · Tracker instance

> _“`tracker = Tracker()` gives us the centroid-based tracker defined in `utils/tracker.py`.  
> No parameters are changed, we stick with the default `max_distance`.”_

> 直接以預設 `max_distance` 建立簡易中心追蹤器。

---

#### 7 · Video I/O

> _“`cv2.VideoCapture` opens the source video, we query width, height, fps, create a `results/` folder, and then allocate a `cv2.VideoWriter` named `annotated.mp4`.”_

> 讀影片取得尺寸與 FPS，創 `results` 夾並準備 `annotated.mp4` 輸出。

---

#### 8 · Statistics containers

> _“Three dictionaries track progress:  
> `route_serials` stores running serial numbers per route and class,  
> `vehicle_info` remembers each ID’s assigned route and serial,  
> `route_counts` keeps the final tally for CSV export.  
> `last_center` caches centroids frame-to-frame.”_

> `route_serials` 管流水號、`vehicle_info` 記 ID–路線–序號、`route_counts` 累計總數、`last_center` 存上一幀質心。

---

#### 9 · Main loop guard

> _“A `while True` loop streams frames until EOF.  
> Frame skipping respects `skip_frame` from YAML—non-detection frames are written out untouched for speed.”_

> 主迴圈讀影格直到結束；依 `skip_frame` 跳幀加速。

---

#### 10 · YOLO detection

> _“We run YOLO once per processed frame, filter detections to our target classes, convert bounding boxes to integer pixel coords, and collect two parallel lists: rectangles and class names.”_

> 執行 YOLO → 篩選目標類別 → 蒐集框與類別兩清單。

---

#### 11 · Tracker update

> _“Bounding boxes are converted from `(x1,y1,x2,y2)` to `(x,y,w,h)` then passed to `tracker.update`, returning `[x,y,w,h,id]` tuples.”_

> 轉成 `(x,y,w,h)` 交給 `update`，取得含 ID 的追蹤結果。

---

#### 12 · Per-vehicle logic (entry / exit)

> _“For each tracked object we compute its current centroid.  
> **Step 1**: if the ID has no `vehicle_info`, we check all entry lines; crossing any of them assigns a route but **not** a serial.  
> **Step 2**: once a route is set, we watch the matching exit line; crossing it locks in a serial number and increments the count.”_

> 先找 Entry 線決定路線，不計數；再跨 Exit 線才發序號並 +1。

---

#### 13 · Drawing boxes & labels

> _“Each bounding box is rendered with the class-specific color.  
> If a serial number exists, the label shows ‘route:serial class’; otherwise it falls back to ‘class ID:id’.”_

> 畫框顏色依類別；若已有序號則顯示「路線:序號 類別」，否則「類別 ID」。

---

#### 14 · Drawing route lines

> _“Every route from YAML is drawn: entry in green, exit in red, each with text labels `*_entry` and `*_exit`.”_

> 逐條路線畫綠色 Entry、紅色 Exit 並標註文字。

---

#### 15 · On-screen statistics

> _“Current counts per route and class are overlaid down the left edge, one line per route.”_

> 左側逐行顯示各路線各類車輛累計。

---

#### 16 · FPS overlay

> _“Instantaneous FPS is computed as processed frames divided by elapsed seconds and painted in the top-right corner.”_

> 以已處理影格除花費時間計 FPS，顯示於右上。

---

#### 17 · Display, write, break key

> _“`cv2.imshow` streams live video, `out.write` records it, and hitting `Esc` breaks the loop.”_

> 即時顯示並寫檔；按 `Esc` 離開。

---

#### 18 · Cleanup

> _“After the loop we release both the capture and writer, then close all OpenCV windows.”_

> 迴圈結束後釋放資源並關閉視窗。

---

#### 19 · CSV export

> _“Finally we dump `route_counts` into `results/counts.csv` with three columns: route, class, count, and print two confirmation messages.”_

> 將統計寫入 `counts.csv`（route, class, count），並印出兩行完成訊息。

---

