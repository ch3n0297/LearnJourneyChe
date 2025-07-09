# 第三次作業-Mandelbrot
## 簡介:
**簡單介紹：** Mandelbrot 集合（Mandelbrot Set）是數學中一個著名的分形圖形，以法國數學家本華·曼德博（Benoît Mandelbrot）的名字命名。它展示了簡單數學規則如何產生無限複雜且自相似的圖案。來自[資料來源1 ](https://zh.wikipedia.org/zh-tw/%E6%9B%BC%E5%BE%B7%E5%8D%9A%E9%9B%86%E5%90%88) 。
## 程式碼設計介紹：
>**本次的作業目標為：**使用 C 語言實作 Mandelbrot Set 的 Serial 與 Parallel 版本，並透過 MPI（靜態與動態排程）與 OpenMP 探討平行化效能、負載平衡與擴展性。

**程式設計介紹：**我將會在以下使用片段程式碼去解釋四種不同的之處。我將會以主要的片段程式碼去做講解與它是如何影響效能的。

#### 首先是解釋Serial部分:
```c
for (int y = 0; y < height; ++y) {
        double ci = y_max - y * (y_max - y_min) / height;
        unsigned char *row = image + (size_t)y * width * 3;
        for (int x = 0; x < width; ++x) {
            double cr = x_min + x * (x_max - x_min) / width;
            int iter  = mandelbrot(cr, ci);
            int r=0,g=0,b=0;
            if (iter < MAX_ITER) {
                double t=(double)iter/MAX_ITER;
                rgb_color(t,&r,&g,&b);
            } else r=g=b=10;
            row[x*3]   = (unsigned char)r;
            row[x*3+1] = (unsigned char)g;
            row[x*3+2] = (unsigned char)b;
        }
    }
```

這是計算 Mandelbrot 的主要方式，雖然Serial的程式碼可讀性高，容易Debug，但單執行緒、單核心順序處理所有像素且無通訊、同步或併發邏輯，使它(Serial)執行時間最久，因為完全無法使用多核資源。當遇到高解析度、大圖像或高 MAX_ITER 時效能下降最嚴重。(Serial的iteration值設定為1000)
![[Ppd/Homework3_B1128019/mandelbrot_rgb(serial).png]]
#### 再來是MPI的Static和Dynamic：
>那在撰寫 MPI-static 版本時，我從 Serial 的兩層迴圈中抽出 y 軸行數，改為依 rank 分段計算，並利用 `MPI_Gatherv` 統一回傳結果；而 MPI-dynamic 則進一步改為主控端依序分配每一行，並要求每個 worker 回傳行號與內容。OpenMP 則直接以 `#pragma omp parallel for` 套在外層 y 迴圈，配合 dynamic 分派提高效能。

以下放置主要的程式碼片段：
**Static: **
```c
    int rows_per   = (height + size - 1) / size;     /* ceiling */
    int row_start  = rank * rows_per;
    int row_end    = ((rank+1)*rows_per > height) ? height : (rank+1)*rows_per;
    int my_rows    = row_end - row_start;

    unsigned char *subimg = malloc((size_t)my_rows * width * 3);
    if (!subimg) { perror("malloc"); MPI_Abort(MPI_COMM_WORLD, 1); }
    ...

for (int y = row_start; y < row_end; ++y) {
        double ci = y_max - y * (y_max - y_min) / height;
        unsigned char *row = subimg + (size_t)(y-row_start) * width * 3;
        for (int x = 0; x < width; ++x) {
            double cr = x_min + x * (x_max - x_min) / width;
            int iter  = mandelbrot(cr, ci);

            int r=0,g=0,b=0;
            if (iter < MAX_ITER) {
                double t = (double)iter / MAX_ITER;
                rgb_color(t,&r,&g,&b);
            } else r=g=b=10;

            row[x*3]   = (unsigned char)r;
            row[x*3+1] = (unsigned char)g;
            row[x*3+2] = (unsigned char)b;
        }
    }
```

我在程式一開始就把圖像的「行(row)」固定平均分給每個 MPI rank 處理，計算後用 `MPI_Gatherv()` 收集回 rank 0 合併影像。這種方式實作很簡單且我把通訊模式排的清晰，邏輯和可讀性高，但易受「發散速度不均」影響（這個部分需要計算較多次迭代，我們後面會詳細說明），會發現某些 rank 提早完成後會 idle，造成 **load imbalance**。
![[Ppd/Homework3_B1128019/mandelbrot_rgb(mpi-static).png]]
**Dynamic:**
```c
if (rank == 0) {
	unsigned char *image = malloc((size_t)width * height * 3);
	if (!image) { perror("malloc"); MPI_Abort(MPI_COMM_WORLD,1); }
	
	int next_row = 0;                  /* 下一行尚未派發的 row index */
	int active_workers = size - 1;
	
	/* 初始派工：先給每個 worker 一行 */
	for (int w = 1; w < size && next_row < height; ++w, ++next_row)
		MPI_Send(&next_row, 1, MPI_INT, w, TAG_WORK, MPI_COMM_WORLD);
	
	/* 主排程迴圈 */
	while (active_workers > 0) {
		int row_idx;                   /* 先收 row index 再收像素 */
		MPI_Status st;
		MPI_Recv(&row_idx, 1, MPI_INT, MPI_ANY_SOURCE,
				 MPI_ANY_TAG, MPI_COMM_WORLD, &st);
		int worker = st.MPI_SOURCE;
	
		/* 接收該行像素資料 */
		MPI_Recv(image + (size_t)row_idx * width * 3,
				 width*3, MPI_UNSIGNED_CHAR,
				 worker, TAG_WORK, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
	
		/* 指派新工作或送終止訊息 */
		if (next_row < height) {
			MPI_Send(&next_row, 1, MPI_INT, worker, TAG_WORK, MPI_COMM_WORLD);
			++next_row;
		} else {
			MPI_Send(&next_row, 1, MPI_INT, worker, TAG_STOP, MPI_COMM_WORLD);
			--active_workers;
		}
	}
```

我使用了workpool去做排程，且也使用了**master-worker** 架構，由 rank 0 動態分配行任務給空閒的 rank。當每完成一行就回傳，再從 master 接收下一行。這樣的做法，最能平衡負載，特別在 fractal 發散不均時效果顯著。計算效率穩定，每個 rank 都工作到最後，不會有rank事情做完了結果在休息。通訊次數較多（每行都有兩次通訊），但整體換得 **最少 idle**
![[mandelbrot_rgb(mpi-dynamic).png]]
#### 最後帶到OpenMP:
```c
    #pragma omp parallel for schedule(dynamic, 4)
    for (int y = 0; y < height; ++y) {
        double ci = y_max - y * (y_max - y_min) / height;
        unsigned char *row = image + (size_t)y * width * 3;
        for (int x = 0; x < width; ++x) {
            double cr = x_min + x * (x_max - x_min) / width;
            int iter  = mandelbrot(cr, ci);
            int r=0,g=0,b=0;
            if (iter < MAX_ITER) {
                double t = (double)iter / MAX_ITER;
                rgb_color(t,&r,&g,&b);
            } else r=g=b=10;
            row[x*3]   = (unsigned char)r;
            row[x*3+1] = (unsigned char)g;
            row[x*3+2] = (unsigned char)b;
        }
    }
```

在同一個節點內，你可以看到:

>- 我用 OpenMP 將 row 分配給多執行緒處理 。
>- 使用 `schedule(dynamic, 4)` 動態分配每 4 行為單位的工作，避免負載不均。

這麼做，則無需顧慮 MPI rank 與通訊且適合單節點多核並行，效能與 MPI-dynamic 接近（在核數足夠情況下），但缺點是，受限於單機 CPU 資源，無法跨節點擴展。
![[Ppd/Homework3_B1128019/mandelbrot_rgb(omp).png]]
**這邊有四種方式的輸出內容：**

### 執行時間比較表（單位：秒）

| 版本         | Compute Time | Communication Time | I/O Time | Total Time |
|--------------|---------------|---------------------|----------|-------------|
| OpenMP       | 1.557         | 0.000               | 3.109    | 4.666       |
| MPI Dynamic  | 2.757         | 0.484               | 4.311    | 7.552       |
| MPI Static   | 6.287         | 0.010               | 3.721    | 10.019      |
| Serial       | 18.157        | 3.486               | 0.000    | 21.643      |

![[Pasted image 20250510225210.png]]

從下圖與表格可明顯看出，四種不同平行化策略對 Mandelbrot Set 計算效能產生顯著影響：

1. **Serial 版本**
    
    - 執行時間最長（Total Time 約 21.643 秒），其中超過 18 秒為純計算時間，且幾乎無 I/O。
        
    - 單核心處理所有像素，未能使用任何平行資源，效率最低。
        
2. **MPI Static**
    
    - 藉由靜態將 row 平均分配至各 MPI rank，有效降低計算時間至 6.287 秒。
        
    - 然而，由於負載分配不均（某些行比其他行計算慢），造成部分 rank 提早 idle，導致總時間仍達 10 秒。
        
3. **MPI Dynamic**
    
    - 採 master-worker 模式動態分派 row，進一步減少 idle 核心時間。
        
    - 儘管通訊時間略高（0.484 秒），但能換得最佳的 rank 利用率，使總時間縮短至 7.552 秒。
        
4. **OpenMP**
    
    - 在單節點上利用 12 執行緒並行計算，無通訊開銷（comm = 0）。
        
    - 雖然 I/O 時間偏高（3.109 秒），但整體表現仍為最快，僅 4.666 秒完成整體任務，**是所有方法中表現最佳者**。

### 最後讓我們回到問題討論本身：

#### (a) Static 與 Dynamic Scheduling 對 MPI 效能與負載平衡的影響

###### 靜態分配（MPI Static）

在 MPI Static 中，每個 rank 在一開始就被指派一段固定的 row 區間（如 rank 0 處理第 0–1249 行，rank 1 處理 1250–2499 行……）。這種分配方式實作簡單，通訊開銷極小，但效能高度依賴圖像中每一行的計算負擔是否均等。

在 Mandelbrot Set 中，由於圖形中心區域（例如圓形與外層螺旋）內部的像素多半需要經過完整的 MAX_ITER 次迭代才會確定是否發散，因此某些 row 的運算會明顯比其他 row 更耗時。如果這些高計算負擔的 row 恰好集中在同一個 rank 的區段，會導致該 rank 成為「效能瓶頸」，而其他 rank 提早計算完畢後會 idle 等待收尾。

這種「負載不均衡（load imbalance）」的現象直接反映在 MPI Static 的總執行時間偏長（約 10.019 秒），比 MPI Dynamic 慢了超過 2 秒，即使計算總量相同。

---

#### 動態分配（MPI Dynamic）的優勢

MPI Dynamic 採用 master-worker 模式：rank 0 為 master，其餘 rank 為 worker。每當某個 worker 完成一行 row 計算後，就立即向 master 請求下一行任務，直到所有 row 被處理完畢。這種設計讓每個 rank 都能保持忙碌狀態，且 row 的分配會根據實際執行速度進行動態調整。

如此一來，即使某些 row 計算較慢，它們也能平均地分散到不同的 rank，而非集中於某一 rank。這種動態分派策略大幅提升了 **核使用率**，也降低了 **等待與 idle 時間**。

在你提供的實驗中，MPI Dynamic 總執行時間為 7.552 秒，明顯比 MPI Static 快，且在高解析度（5000×5000）與 MAX_ITER 為 1000 的情況下展現出明顯優勢。

---

#### 動態分配的優勢適用情境

- **圖像解析度越高**：row 計算負擔差異越明顯，動態分配越能有效平衡負載。
    
- **MAX_ITER 越大**：發散慢的 row 需要更多時間處理，靜態分配更容易造成 bottleneck。
    
- **圖像目標區域越集中在高密度結構**（如放大中央黑色區域）：越容易出現 row 間耗時極端不均，需使用動態排程改善效率。
    

---

#### (b) 哪一種平行方法最適合用於 Mandelbrot 計算？為什麼？

根據實驗結果與圖表分析，**OpenMP 是本次實驗中表現最優的平行方法**，其總執行時間僅 4.666 秒，明顯快於所有 MPI 方法。

##### 原因如下：

|評估面向|OpenMP 優勢|
|---|---|
|**執行效率**|總時間最短，I/O 與 Compute 均表現良好|
|**通訊開銷**|無 MPI 通訊開銷，記憶體共享架構直達|
|**程式簡潔性**|單行 `#pragma omp parallel for` 即可實現|
|**負載平衡**|使用 dynamic schedule 可有效平衡迴圈中各 row 的工作量|

#### 限制與補充：

OpenMP 的優勢來自於單機多核架構，在國網中心的 `ctest` 節點中可以發揮良好。但若需擴展至多節點、高核心數（例如 32–64 核以上），則仍需仰賴 MPI 模型以支援分散式架構運算。
若考慮 **擴展性（scalability）**，我認為MPI Dynamic 是更好的選擇；但在單節點多核心的教學環境下，OpenMP 是最實用、最穩定的解法。

---

####  (c) 實作過程中遇到的挑戰與困難

##### 動態排程的通訊設計較複雜

在實作 MPI Dynamic 時，需要處理任務的指派與接收流程，包含：

- master 需監控所有 worker 的執行狀態
    
- 每個 row 需標註行號，避免合併結果時拼錯
    
這要求對 `MPI_Send/MPI_Recv` 的使用非常精準，否則會導致 row 排錯或死鎖（deadlock）。

---

#### 並行圖像輸出（I/O）時間變異

尤其是 OpenMP 版本，儘管計算時間短，卻觀察到輸出圖像所需的 I/O 時間達 3.1 秒，幾乎是計算時間的兩倍。這可能與單執行緒寫入 `.ppm` 檔案的速度、檔案大小（高解析）有關，也反映了 I/O 成為效能瓶頸的一種可能。

---

#### 程式驗證與測試成本

為確保四種版本的圖像一致性，需對輸出圖像進行像素比對（使用 `diff` 或 Python 檢查 pixel 值），這在並行版本中特別重要，避免因拼接順序或資料遺失造成誤差。