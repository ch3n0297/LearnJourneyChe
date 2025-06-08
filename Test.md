|參數|值|
|---|---|
|預訓練模型|`bert-base-uncased`|
|Epoch 數|3|
|Batch Size|8（訓練與驗證皆相同）|
|Learning Rate|2e-5|
|Weight Decay|0.01|
|評估頻率|每 500 steps 評估並保存 checkpoint|
|Optimizer|AdamW（由 HuggingFace 預設設定）|
|儲存限制|最多保留 2 個 checkpoint (`save_total_limit=2`)|
|評估指標|使用 `evaluate.load("squad_v2")` 套件，計算 Exact Match、F1 Score、HasAns/NoAns 各類別分數|

|指標|驗證集結果|
|---|---|
|F1 Score|40.1|
|Exact Match|40.1|
|NoAns F1|99.9（模型很會判空）|
|HasAns F1|0.01（模型抓不到 span）|
|Eval Loss|約 3.2|

|階段|項目|目標|說明與建議|
|---|---|---|---|
|目前進度|已完成基礎流程驗證|- 模型能成功訓練與預測- F1/EM 能產出指標- 資料處理與 Token 對齊成功|目前模型偏向預測無答案（NoAns），說明還沒學會抓 span，需要針對 **樣本不平衡** 和 **模型策略** 優化。|
|解決1.|處理樣本不平衡問題|- 加入 class weights 或調整 loss- 改進 sampler 與 batch 組成| 已有 weighted sampler，可以試著改變正負比，或實驗是否加入 `focal loss` 替代 default cross-entropy。|
|解決2.|多視窗（multi-span）擷取強化|- 將同一樣本的多個 window 預測整合- 保留 top-k 答案拼接或挑選|現階段僅取 `argmax`，可以使用 n-best 策略，提升抓到完整 span 的機率；也可分析是否有「跨視窗答案被截斷」的情況。|
|解決3.|模型替換或升級|- 改為 `deberta-v3-base`、`electra-large`- 或加上 RoPE、Longformer 支援長文本|同樣流程下只需更換 `from_pretrained()` 的 model name 並重新訓練；預期能有 3~8 分的 F1 提升空間。|
|解決4.|Threshold 微調 + 最佳 checkpoint 推論|- 對 `null_score` 設定最佳閾值- 對驗證集推論使用 ensemble 或模型融合|可針對 `no_answer_probability` 進行 grid search 找最優分界值；若有多模型，可進行加權平均 logits 融合。|
| 解決5.|**Kaggle Submission 無法執行**|- 修正提交格式錯誤、欄位對應問題- 製作可供 `sample_submission.csv` 比對的結果檔案|目前 baseline 還未輸出 Kaggle 格式的 submission file，可新增：➤ 建立 `{id, prediction_string}` 格式 CSV➤ 將每筆預測的所有 span `start end` 串成字串，用 `;` 分隔➤ 若為空答案，直接輸出空字串（與範例一致） 可加入 `convert_predictions_to_submission(preds)` 函式處理格式對應與合併|