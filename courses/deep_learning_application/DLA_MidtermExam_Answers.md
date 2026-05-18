# DLA 期中考答案

> 來源依據：AI Coding rules.pdf、Smart Speaker Platform.pdf、Network Compression.pdf、Knowledge Distillation.pdf、What_Is_OpenClaw.pdf、night light main board.pdf

---

## 一、AI Agents

### HumanEval 和 CommitPack 的評估有何不同？

| 維度 | HumanEval | CommitPack |
|------|-----------|------------|
| **任務類型** | 給定函式 docstring，要求模型補全 Python 函式主體 | 給定 git diff（程式碼變更），要求模型撰寫 commit message |
| **評估對象** | 功能正確性（functional correctness）：產生的程式碼能否通過 unit test | 程式碼變更理解力：能否精準描述程式碼做了什麼改動 |
| **輸入** | 自然語言描述（docstring） | 程式碼差異（code diff） |
| **輸出** | 可執行的程式碼 | 自然語言（commit 訊息） |
| **評估指標** | pass@k（k 次嘗試內通過測試的比率） | BLEU / 人工評估語意匹配度 |
| **側重能力** | 程式碼生成（code generation） | 程式碼理解與描述（code comprehension） |

**關鍵差異**：HumanEval 測試「能否寫出正確的程式碼」，CommitPack 測試「能否理解程式碼的意圖並用自然語言表達」。兩者共同組成 AI coding agent 的完整評估面向。

---

### 什麼情況下我們會想用 MCP 來輔助 AI coding agent？

**MCP（Model Context Protocol）** 是讓 AI agent 存取外部工具與資源的標準化協定。以下情境適合使用：

1. **存取本地檔案系統**：agent 需要讀取、編輯、建立程式碼檔案時，透過 MCP 的 filesystem server 提供標準化的檔案操作介面。

2. **呼叫外部工具**：需要執行程式碼（run terminal）、查詢資料庫、呼叫 API 時，MCP 提供統一的 tool-use 介面，避免每個 agent 自行實作。

3. **需要即時上下文**：程式碼搜尋（grep/搜尋 codebase）、Git 歷史查詢、依賴套件文件查詢（如 context7）需要最新資訊，MCP server 可以動態拉取。

4. **跨工具協作**：agent 需要同時使用多個工具（如 Slack 通知 + GitHub PR 建立 + 測試執行），MCP 統一協定讓 agent 可以組合使用不同 server。

5. **避免 context 污染**：不需要把大型 codebase 全部塞入 context，透過 MCP 的 resource 機制按需取用，降低 token 浪費。

---

### Roo Code 幾個不同模式的使用情境？

Roo Code 提供以下主要模式，各有其適用情境：

| 模式 | 使用情境 |
|------|---------|
| **Code 模式** | 直接撰寫、修改、重構程式碼。有明確的實作任務，讓 agent 直接動手修改檔案。 |
| **Ask 模式** | 只詢問問題、理解程式碼邏輯，不會修改任何檔案。適合探索陌生 codebase 或釐清問題時使用。 |
| **Architect 模式** | 高層次設計討論：規劃系統架構、API 設計、技術選型。只輸出規格與建議，不直接寫程式碼。 |
| **Debug 模式** | 聚焦於找出 bug 根因，嚴格限制只做最小必要的修正，避免引入額外變更。 |
| **Orchestrator 模式** | 協調多個 sub-agent 並行完成複雜任務，將大型任務拆解後分配給不同模式的 agent 執行。 |

**核心概念**：不同模式對應不同的「工具權限」與「行為邊界」，避免 agent 在不該動程式碼時修改了檔案，或在應該深入思考時直接輸出程式碼。

---

### 什麼是 SDD（Spec-Driven Development）？

**SDD（規格驅動開發）** 是一種先撰寫規格（specification），再根據規格實作的開發方法：

**流程**：
1. **撰寫規格**：明確定義功能目標、輸入輸出格式、邊界條件、驗收標準
2. **建立測試**：依規格先寫 unit test / integration test（類似 TDD）
3. **實作程式碼**：讓程式碼通過規格定義的所有測試
4. **驗證**：確認實作結果符合規格

**與 AI coding agent 的關係**：
- AI agent 容易在模糊需求下「猜測」使用者意圖，導致錯誤實作
- SDD 要求在 coding 之前就有明確規格，符合「Think Before Coding」原則（AI Coding rules PDF 中的四大防禦支柱之一）
- 規格作為 AI agent 的「驗證標準」，避免 agent 產出看起來能跑但邏輯錯誤的程式碼

---

## 二、ESP32 Platform and Audio Wakeup Word Detection

### RTOS 是什麼東西？

**RTOS（Real-Time Operating System，即時作業系統）** 是一種專為即時應用設計的作業系統。

**核心特性**：
- **確定性時序**（Deterministic timing）：任務必須在明確的時間截止前完成，執行延遲有嚴格上限
- **任務排程**：根據優先權（priority）進行搶佔式排程（preemptive scheduling）
- **輕量化**：低 RAM/ROM 佔用，適合嵌入式微控制器
- **同步原語**：提供 Queue、Semaphore、Mutex、Event Group 等機制協調任務間通訊

**常見用途**：音訊處理、馬達控制、感測器讀取等對時序敏感的嵌入式應用。

---

### FreeRTOS 和 Linux 有何不同？

| 比較維度 | FreeRTOS | Linux |
|---------|---------|-------|
| **目標** | 嵌入式即時應用 | 通用作業系統 |
| **核心大小** | 數 KB（~10 KB） | 數 MB 以上 |
| **記憶體需求** | 極低（ESP32 只需數十 KB） | 通常需要數十 MB RAM |
| **即時性** | 硬即時（hard real-time），確定性延遲 | 非即時（soft real-time 需要 RT patch） |
| **排程器** | 優先權搶佔式，tick-based | CFS（完全公平排程器），針對吞吐量最佳化 |
| **檔案系統** | 無內建（需外加 FATFS/SPIFFS） | 完整的 VFS、ext4 等 |
| **行程隔離** | 無 MMU，所有任務共用記憶體空間 | 有 MMU，行程間記憶體保護 |
| **開機時間** | 毫秒級 | 秒到十幾秒 |
| **API** | 自有 API（xTaskCreate、xQueueSend 等） | POSIX 標準 |
| **ESP32 支援** | 原生支援（ESP-IDF 內建） | 不支援（ESP32 無 MMU） |

---

### ESP32 常用於什麼樣的系統之中？

ESP32 是 Espressif 的雙核心 240MHz MCU，常見於以下系統：

1. **智慧音箱 / 喚醒詞偵測**：本課程的 nn-speaker 專案，透過麥克風接收語音並執行神經網路推論
2. **IoT 感測器節點**：溫濕度感測、環境監測（如本課程的 night light 主板，搭載 STS31 溫度感測器）
3. **智慧家居裝置**：Wi-Fi/BLE 連網的燈控、插座控制
4. **穿戴裝置**：需要低功耗藍牙傳輸的健康監測裝置
5. **工業 IoT**：邊緣計算節點，將感測數據預處理後傳至雲端
6. **機器人控制**：馬達驅動、感測器融合的即時控制系統

**技術優勢**：雙核心（一核處理 AI 推論、另一核處理通訊）、內建 Wi-Fi/BLE、PSRAM 擴充記憶體支援較大的 ML 模型。

---

### Queue / Semaphore / Event Group 有什麼不同？要如何選用？

| 機制 | 用途 | 特性 | 適用情境 |
|------|------|------|---------|
| **Queue** | 任務間傳遞**資料** | FIFO，有容量限制；可攜帶資料內容；sender 可 block 等待空間，receiver 可 block 等待資料 | 音訊緩衝區傳遞、感測器讀值送給處理任務 |
| **Semaphore** | 任務間**同步**或資源**互斥** | Binary semaphore（0/1，用於同步）；Counting semaphore（計數，用於資源池）；Mutex（帶優先權繼承，防死鎖） | 等待中斷觸發（binary）、限制同時存取資源的任務數量（counting）、保護共享資料（mutex） |
| **Event Group** | 等待**多個事件組合** | 可同時設定/等待多個 bit；可設定「等所有 bit 都被設定」或「等任一 bit 被設定」 | 等待 Wi-Fi 連線成功 AND 麥克風初始化完成後才開始錄音 |

**選用原則**：
- 需要傳資料 → **Queue**
- 只需要通知（有/無）→ **Binary Semaphore**
- 保護共享資源 → **Mutex**
- 需要等待多個條件同時或任一滿足 → **Event Group**

---

### ESP32 有哪些不同的記憶體？

ESP32 的記憶體架構（以 ESP32-WROVER 為例）：

| 記憶體類型 | 大小 | 特性 |
|-----------|------|------|
| **IRAM**（Instruction RAM） | ~128 KB | 存放需要快速執行的程式碼（中斷服務程式）；CPU 可直接存取 |
| **DRAM**（Data RAM） | ~320 KB | 存放動態資料（heap、stack）；CPU 可直接存取 |
| **RTC RAM** | 8 KB fast + 8 KB slow | 深度睡眠時保留資料；可在 ULP 協處理器中使用 |
| **Flash（SPI Flash）** | 4–16 MB | 存放程式碼與唯讀資料（SPIFFS 檔案系統）；需透過 cache 存取 |
| **PSRAM（外部 SPI RAM）** | 4–8 MB | 擴充 RAM，適合存放較大的緩衝區與 ML 模型；比內部 SRAM 慢 |

---

### SRAM 和 PSRAM 有什麼不同？

| 比較維度 | SRAM（Static RAM，內部） | PSRAM（Pseudo-Static RAM，外部） |
|---------|----------------------|-------------------------------|
| **位置** | 晶片內部 | 外部 IC（透過 SPI 介面連接） |
| **速度** | 快（CPU 直接定址，無延遲） | 慢（需要透過 SPI 匯流排，帶寬受限） |
| **容量** | 小（ESP32 約 520 KB） | 大（ESP32-WROVER 有 4/8 MB） |
| **功耗** | 較低 | 較高（需要持續刷新） |
| **存取方式** | CPU 直接讀寫 | 透過 SPI 介面，ESP-IDF 自動做 cache 管理 |
| **用途** | Stack、中斷 handler、時間敏感資料 | 音訊緩衝區、ML 模型參數、較大的陣列 |

**本課程應用**：ESP32-WROVER 內建 8 MB PSRAM，用來存放較大的神經網路模型與 mel spectrogram 緩衝區。

---

### I2C 和 I2S 分別用在哪些場景？

| 比較維度 | I2C（Inter-Integrated Circuit） | I2S（Inter-IC Sound） |
|---------|--------------------------------|----------------------|
| **訊號線** | SDA（資料）+ SCL（時脈），共 2 條 | SD（資料）+ WS（字選擇）+ SCK（時脈）+ MCK（主時脈），共 3–4 條 |
| **速度** | 低至中速（100 kbps ~ 3.4 Mbps） | 高速（達 MHz 級，支援 CD 品質音訊） |
| **資料格式** | 位址 + 暫存器 + 資料（封包式） | 連續的 PCM 數位音訊串流 |
| **用途** | 設定/控制外部 IC（感測器、DAC 設定）| 傳輸數位音訊資料流（麥克風到 MCU、MCU 到喇叭） |
| **ESP32 應用** | STS31 溫度感測器、Touch IC（BS8112）的設定 | ES8388 Audio Codec 的音訊資料傳輸（MCLK/SCLK/LRCLK/DSIN/ASDOUT） |

**記憶口訣**：I²C 管「控制」（慢速設定），I²S 管「聲音」（高速串流）。

---

### 如何用 SDA/SCL 發出 I2C 的 START/STOP 訊號？

**I2C 訊號規則**：在 SCL 為 HIGH 時，SDA 的狀態變化具有特殊意義。

**START 訊號**：
```
SCL: ___________HIGH________________
SDA: ___HIGH______↓↓↓LOW____________
```
- 當 **SCL 保持 HIGH** 時，**SDA 從 HIGH 變為 LOW**
- 表示「通訊開始，總線被佔用」

**STOP 訊號**：
```
SCL: ___________HIGH________________
SDA: ___LOW______↑↑↑HIGH____________
```
- 當 **SCL 保持 HIGH** 時，**SDA 從 LOW 變為 HIGH**
- 表示「通訊結束，總線釋放」

**正常資料傳輸**：資料位元（SDA 的 0/1）只能在 **SCL 為 LOW** 時改變，SCL 為 HIGH 時 SDA 必須穩定，否則會被誤判為 START/STOP。

---

### 什麼是 Audio Spectrum？

**Audio Spectrum（音訊頻譜）** 是將時域的音訊訊號轉換為頻域表示的方法：

**產生過程**：
1. 對音訊訊號取短時窗（windowing）
2. 對每個視窗做 **FFT（快速傅立葉轉換）**，得到各頻率的能量
3. 沿時間軸排列所有視窗的頻率能量 → 得到 **頻譜圖（spectrogram）**
4. 頻譜圖是一張 2D 影像（橫軸=時間、縱軸=頻率、顏色=能量強度）

**用作分類器**：將頻譜圖當成圖片輸入 2D CNN，就能偵測音訊中的特定模式（如喚醒詞）。

---

### 什麼是 Mel Spectrum？

**Mel Spectrum（梅爾頻譜）** 是在 Audio Spectrum 基礎上，進一步模擬人耳聽覺特性的非線性頻率表示：

**核心概念**：
- 人耳對**低頻敏感**（可以分辨相近的低頻）、對**高頻不敏感**（難以分辨相近的高頻）
- Mel Scale 是一種非線性頻率尺度：低頻區間**較密**（解析度高）、高頻區間**較疏**（解析度低）

**公式**：`mel = 2595 × log10(1 + f/700)`

**處理流程**：
1. 計算 STFT 頻譜
2. 套用 **Mel Filter Bank**（三角形濾波器組，非均勻分布在頻率軸上）
3. 取對數（log），壓縮動態範圍
4. 得到 Mel Spectrogram

**優點**：特徵維度更緊湊、更符合語音感知特性，提升語音辨識準確率。

---

### 為什麼我們可以用 2D CNN 來做 Audio Detection？

**核心原因**：Mel Spectrogram 是一張 2D 影像，具有空間局部性（spatial locality）。

**詳細說明**：
1. **Mel Spectrogram 的結構**：橫軸是時間、縱軸是梅爾頻率，每個像素代表特定時刻特定頻率的能量
2. **局部相關性**：喚醒詞的聲音特徵（如母音、子音的頻率模式）在時間-頻率平面上是**局部連續**的 patch，類似圖像中的紋理
3. **2D CNN 的優勢**：卷積核能偵測這些局部時頻模式，並透過池化層獲得時間/頻率方向的平移不變性
4. **本課程實作**（Smart Speaker Platform PDF）：
   - 輸入：99×43 的 Mel Spectrogram（99 個時間 frame × 43 個 mel 頻帶）
   - 架構：Conv2D → MaxPool2D → Conv2D → MaxPool2D → Flatten → Dense
   - 平均推論時間：~115ms（在 ESP32 上執行 TFLite 模型）

---

## 三、Network Compression

### 為什麼要壓縮網路？

根據 Network Compression PDF，有三大動機：

1. **減少儲存與計算需求**：深度神經網路動輒數百 MB 到數 GB，壓縮後可大幅降低記憶體佔用與推論時間
2. **部署到 IoT/邊緣裝置**：手機、ESP32、智慧手錶等嵌入式裝置資源有限，無法執行原始大型模型
3. **盡量保持精度**：壓縮後的模型準確率應盡可能接近原始模型（Compressed Accuracy ≈ Original Accuracy）

---

### 如何將 MLP/CNN/Transformer 轉換成大型的矩陣運算？

**核心公式**：`Y = X * W`（輸出 = 輸入矩陣 × 權重矩陣）

**MLP（全連接層）**：
- 直接就是矩陣乘法：`Y = X * W`，X 為 batch × 輸入維度，W 為輸入維度 × 輸出維度

**CNN（卷積層）**：
- 使用 **im2col** 技巧：將每個卷積視窗的輸入展開成一列
- 例如：4 個 3×3×3 視窗 → 4×27 的矩陣
- 卷積核展平為 27×輸出通道數的矩陣
- 卷積 → 變成一次 GEMM（General Matrix Multiplication）

**Transformer**：
- Embedding Layer：`x * W_embed`
- QKV Projection：`q = x * W_Q`、`k = x * W_K`、`v = x * W_V`
- Output Projection：`h = o * W_O`
- Feed-Forward Network：兩層 Linear → `x * W_1` 和 `x * W_2`
- 每個 Transformer 層的參數數量：`3d² + d² + 4d² + 4d² = 12d²`
- **全部都是線性層，全部都是矩陣乘法**

---

### 如何將各式網路轉換成適合在不同硬體執行的格式？

根據 Network Compression PDF 的 **compile computational graph** 概念：

1. **im2col + GEMM**：將 CNN 卷積轉成矩陣乘法，可用標準 BLAS 函式庫加速
2. **TFLite（TensorFlow Lite）**：本課程使用的格式，將模型轉成 C 語言陣列嵌入 ESP32 韌體
3. **ONNX**：跨框架的中間表示格式，可部署到 CPU/GPU/FPGA
4. **TensorRT**：NVIDIA 的推論最佳化引擎（INT8 量化 + 核融合）
5. **CUDA 障礙（CUDA Barrier）**：從計算圖到 GPU 核心，需要針對不同硬體（CPU/GPU/TPU/ASIC）實作數百種 kernel variant

---

### 什麼是 Systolic Array？

**Systolic Array（脈動陣列）** 是一種由大量 **MAC（Multiply-Accumulate，乘累加）單元**組成的矩陣式計算架構：

**原理**：
- 多個 PE（Processing Element）排列成 2D 矩陣格狀
- 資料從左方流入（矩陣 A 的行），從上方流入（矩陣 B 的列）
- 每個 PE 計算 `Y_out = Y_in + X_in * W`
- 資料在 PE 間流動，無需回到記憶體，大幅降低記憶體頻寬需求

**關鍵特性**：
- **非常適合大型矩陣乘法**（如 Transformer 的 QKV 計算）
- **無法處理不規則/稀疏網路**（irregular/sparse networks）
- 傳統 PE：最多 5M ops/s；Systolic Array：可達 30M ops/s

**實際應用硬體**：NVIDIA Tensor Core、Google TPU、Eyeriss I/II、ShiDianNao、Cambricon-X

---

### 如何使用 Systolic Array 計算矩陣乘法？

以 3×3 Systolic Array 計算 GEMM 為例（A × B = C）：

**設定**：
- 矩陣 A 的行從左側「對角線錯開」逐步送入
- 矩陣 B 的列從頂部「對角線錯開」逐步送入
- 每個 PE 負責累積輸出矩陣 C 的一個元素

**步驟**（以 1D CNN 為例，每個 PE 的操作）：
```
Y_out = Y_in + X_in * W
```
- T=1：a0,0 和 b0,0 進入 PE(0,0)，計算 a0,0 * b0,0
- T=2：資料向右、向下流動，同時進入更多 PE
- T=7（3×3 矩陣）：所有輸出元素累積完成

**優勢**：矩陣 A 和 B 的每個元素只需從記憶體讀取一次，之後在 PE 間流動重複使用，大幅節省記憶體頻寬。

---

### Google TPU 和 Nvidia GPU 有什麼相同和不同之處？

**相同點**：
- 都內建大量平行乘法單元（Tensor Core / Matrix Multiply Unit）
- 都為矩陣運算最佳化
- 都支援低精度計算（INT8/FP16/BF16）

**不同點**：

| 比較維度 | Google TPU | NVIDIA GPU |
|---------|-----------|-----------|
| **架構** | Systolic Array（ASIC 專用） | SIMT（Single Instruction Multiple Thread）+ CUDA Cores + Tensor Cores |
| **程式模型** | 專為矩陣乘法設計，無通用計算 | CUDA 通用並行計算，支援各種 kernel |
| **靈活性** | 低（只擅長規則矩陣運算） | 高（可執行任意 GPU 程式） |
| **適用場景** | 大型 Transformer 訓練/推論、規則矩陣計算 | 視覺模型、生成模型、稀疏網路、靈活實驗 |
| **記憶體** | TPU v1：8 GB HBM；新版 HBM 高頻寬 | HBM2/HBM3（H100：80 GB HBM3） |
| **互連** | TPU Pod：專屬 ICI 高速互連 | NVLink 互連 |
| **TPU v1 特色** | 256×256 Matrix Multiply Unit，每週期完成 65536 次 MAC | — |

---

### 什麼是 Weight Pruning？我們要如何選擇刪除哪些權重？

**Weight Pruning（權重剪枝）** 是將神經網路中重要性低的連線（權重）設為零或移除的技術，以減少模型大小與計算量。

**Connection Pruning（連線剪枝）**：
- 刪除權重值接近零的連線
- 問題：產生**不規則的稀疏結構**，難以用硬體加速

**如何選擇刪除哪些權重**：

1. **選近零的權重**：`Y = Σ Xi * Wi`，Wi 越小對輸出影響越小
2. **Weight Decay（L2 正則化）**：
   - 在 loss 中加入 `L = Σ Wi²` 的懲罰項
   - 訓練過程中自動把不重要的權重壓向零
   - L1 正則化（絕對值）在無 retrain 時較好；L2 + retrain 效果最佳
3. **Pruning + Retrain（迭代剪枝）**：先剪枝再重新訓練，效果優於一次性剪枝

---

### 什麼是 Structure Pruning？

**Structure Pruning（結構化剪枝）** 是以整個結構單元（而非單一權重）為單位進行剪枝，保留網路的規則性，便於硬體加速：

- 剪枝後的網路仍是**規則的矩陣**，可直接用 GEMM / Systolic Array 加速
- 對比 Connection Pruning：後者產生稀疏不規則結構，需要特殊稀疏計算函式庫

**包含層次**：
- **Channel Pruning**：移除整個特徵通道（channel）
- **Filter Pruning**：移除整個 3D 卷積核（filter）
- **Layer Pruning**：移除整個網路層

---

### 什麼是 Channel Pruning？

**Channel Pruning（通道剪枝）** 是從 CNN 的卷積層中移除整個特徵通道（feature map channel）的技術。

**關鍵方法（使用 BN 層的 gamma 參數）**：

1. **為什麼用 gamma**：Batch Normalization 的公式為 `y = γ * x̂ + β`，gamma 是每個通道的縮放因子
   - gamma 小 → 這個通道被 BN 層「抑制」→ 該通道不重要
2. **訓練時加入稀疏化**：在 loss 中加入 `λ * Σ g(γ)` 懲罰項，強迫 gamma 向零收縮
3. **剪枝**：移除 gamma 小於閾值的通道
4. **Fine-tuning**：剪枝後重新訓練以恢復精度

**效果**（Channel Pruning 論文結果）：
- VGGNet 剪去 88.5% 參數，精度反而略有提升
- DenseNet-40 剪去 35.7% 參數，精度最優

---

### 什麼是 Filter Pruning？

**Filter Pruning（濾波器剪枝）** 是移除 CNN 中整個 3D 卷積核（filter）的技術。

**原理**：
- 每個 filter 是形狀為 `(input_channels × kernel_H × kernel_W)` 的 3D 張量
- 移除某層的一個 filter，等於移除了下一層對應的輸入 feature map
- 因此移除當前層 filter 後，**必須同時移除下一層對應的 filter**，保持維度一致

**選擇要移除的 Filter 的方法**：
- **Filter L1 Norm**：L1 範數小的 filter，對輸出影響小
- **Mean Activations**：平均激活值低的 filter
- **Average Percentage of Zeros**：零值比例高的 filter（類似 dead neuron）
- **Entropy**：對不同輸入圖片輸出相近的 filter（表示它的辨別力弱）
- 也可用：隨機選擇、演化演算法、貝葉斯演算法

---

### 請說明 Iterative Pruning 的步驟和每一個步驟的目的

**Iterative Pruning（迭代剪枝）** 是「剪枝 → 重新訓練」的循環流程：

```
訓練完整網路 → 剪枝 → 重新訓練 → 剪枝 → 重新訓練 → ...
```

**詳細步驟**：

1. **Train Connectivity（訓練完整網路）**
   - 目的：讓網路學習到完整的特徵表示，建立初始的連線重要性
   
2. **Prune Connections（執行剪枝）**
   - 目的：根據重要性指標（如 L1 norm、gamma 值）移除不重要的連線/通道/濾波器
   - 每次只剪掉一部分（不一次全剪），避免精度崩潰
   
3. **Train Weights（重新訓練/Fine-tune）**
   - 目的：讓剩餘的網路「補償」被移除的連線，恢復甚至超越原始精度
   - 網路有一定的冗餘性，可以通過重新訓練適應剪枝後的結構

**循環效果**：
- 相比一次性剪枝，迭代剪枝可以在保持精度的情況下移除更高比例的參數（可達 90%+）
- Multi-pass 實驗顯示：6 次迭代可移除 99.4% 的通道，精度損失很小

---

### 什麼是 Lottery Hypothesis？

**Lottery Ticket Hypothesis（彩票假說）** 由 Frankle & Carlin（2019）提出：

**核心論點**：
> 一個大型神經網路可以被視為**眾多小型子網路的集合（ensemble）**。訓練大型網路時，每個子網路都有一定的機率被訓練成高效能的模型。只要其中任何一個「中獎」，整體網路就能獲得好的表現。因此，大型網路的「中獎機率」更高。

**實際意涵**：
1. 我們通常可以把大型網路剪枝到原始大小的 5–10%，並維持相近的精度
2. 直接訓練一個小型網路，效果往往不如「先訓練大網路再剪枝」
3. **為什麼？** 因為大型網路的冗餘架構提供了更高的「抽到好的初始化組合」的機率

**後續爭議（Rethinking the Value of Network Pruning）**：
- 研究發現：Fine-tuning 剪枝後的模型效果不一定優於「用剪枝後的架構從頭訓練」
- 結論：**剪枝後的架構（architecture itself）** 比繼承的「重要權重」更關鍵
- 目前仍有爭議，但彩票假說仍是理解為何剪枝有效的重要視角

---

### 什麼是 Quantization？

**Quantization（量化）** 是將神經網路的浮點數權重與激活值轉換為低位元整數的技術，以減少記憶體佔用與加速推論：

**位元精度層次**：
```
FP32（32位元）→ FP16（16位元）→ INT8（8位元）→ INT4（4位元）→ BNN（1位元）
```

**INT8 量化流程**：
1. 找出每一層的 `(min, max)` 範圍
2. 將浮點數線性映射到 8-bit 整數：`quantize: float → INT8`
3. 推論時在整數域計算
4. 輸出時還原：`dequantize: INT8 → float`

**好處**：
- 記憶體減少 4x（FP32 → INT8）
- 整數運算硬體加速（不需要 FPU）
- 適合在 ESP32 等嵌入式裝置執行 TFLite 量化模型

---

### 為什麼在選擇 Quantization 參數時要使用 KL Divergence？

**問題**：INT8 量化需要找每一層最佳的 `(min, max)` 截斷範圍，錯誤的範圍會造成精度損失。

**直覺**：並非一定要用絕對的 `(global_min, global_max)`。例如有些 outlier 值很大但很少出現，用它們當作範圍會浪費大量量化刻度在無效區間。

**KL Divergence 的作用**：
1. 用**校準資料集（calibration dataset）** 跑推論，收集每層激活值的分布
2. 嘗試不同的截斷閾值（threshold T），將 `[-T, T]` 以外的值截斷
3. 計算 **量化前的 FP32 分布** 與 **量化後的 INT8 分布** 之間的 KL Divergence
4. 選擇使 KL Divergence **最小**的 T 值 → 代表量化後的分布最接近原始分布
5. 這樣找到的 `(min, max)` 能更好地保留信息，減少精度損失

**本質**：用資訊論衡量兩個概率分布的差異，找到信息損失最小的量化範圍。

---

### 為什麼 BNN 的矩陣乘法會變成 XNOR 運算？

**BNN（Binary Neural Network，二值化神經網路）** 將所有權重和激活值量化為 ±1（用 1-bit 表示）。

**推導過程**：

將浮點數量化到 1-bit：
- `+1 → 1`（bit = 1）
- `-1 → 0`（bit = 0）

矩陣乘法的元素計算：

| x_bit | W_bit | x * W | XNOR | XOR |
|-------|-------|-------|------|-----|
| +1(1) | +1(1) | +1(1) | 1 | 0 |
| +1(1) | -1(0) | -1(0) | 0 | 1 |
| -1(0) | +1(1) | -1(0) | 0 | 1 |
| -1(0) | -1(0) | +1(1) | 1 | 0 |

觀察規律：**乘積為 +1 當且僅當 XNOR = 1**

因此：
```
Σ x_bit * W_bit = (相同bits的數量) - (不同bits的數量)
               = XNOR_count - XOR_count
               = XNOR_count - (N - XNOR_count)
               = 2 * XNOR_count - N
```

**優勢**：
- XNOR 是位元運算，一個 64-bit 整數可以同時計算 64 個 XNOR
- 大幅減少記憶體（FP32 → 1-bit，節省 32x 空間）
- 硬體實現極簡單（只需 XNOR + popcount 指令）

**缺點**：精度下降明顯，需要 fine-tuning 來部分恢復。

---

### 什麼是 Knowledge Distillation？它和網路壓縮有什麼關係？

**Knowledge Distillation（知識蒸餾）** 是用大型的「教師網路（Teacher）」來訓練小型的「學生網路（Student）」的技術。

**核心機制**：

1. **Hard Label（一般訓練）**：ground truth = `[0, 0, 1, 0, ...]`（one-hot），資訊量有限
2. **Soft Label（蒸餾訓練）**：使用教師網路的輸出概率分布作為訓練目標
   - 例如：`[0.01, 0.02, 0.85, 0.08, ...]`
   - Soft label 包含**類別間相似度的資訊**（如 2 和 7 形狀相似，所以分類到「7」時「2」的機率也不為零）

3. **Temperature Scaling**：
   - 用高溫 T 軟化教師的輸出分布：`q_i = exp(z_i/T) / Σ exp(z_j/T)`
   - 高溫 → 分布更平滑，學生更容易學習類別間的關係

**訓練 Loss**：
```
total_loss = prediction_loss（與 ground truth）+ distillation_loss（與教師軟標籤）
```

**可以傳遞的「知識」**：
- **Logits**（輸出概率）：最基本的蒸餾方式
- **Feature Maps**（中間特徵）：讓學生的中間層模仿教師
- **Attention Map**：讓學生模仿教師關注的區域
- **Weights**（權重相似性）
- **Relation-based KD**：傳遞各層輸入輸出的關係

**變體**：
- **Multiple Teachers / TA（Teacher Assistant）**：resnet152 → resnet50 → resnet34 → resnet18，逐步蒸餾避免能力差距過大
- **Self-distillation**：模型從自己的前一代版本學習
- **Online Distillation**：多個模型同時訓練，互相蒸餾

**與網路壓縮的關係**：
知識蒸餾是網路壓縮的五大主要方法之一（另外四個是：Network Pruning、Parameter Quantization、Low-Rank Decomposition、Light-Weighted Model Design）。它不直接修改原始模型，而是訓練一個全新的小型模型，並確保小模型的行為接近大模型，是在「精度-效率」trade-off 中效果最好的方法之一。

---

*答案依據：AI Coding rules.pdf（AI 協作協議）、Smart Speaker Platform.pdf（ESP32 智慧音箱）、Network Compression.pdf（網路壓縮）、Knowledge Distillation.pdf（知識蒸餾）、night light main board.pdf（硬體電路圖）、What_Is_OpenClaw.pdf（AI Agent 架構與 LLM 推論）*
