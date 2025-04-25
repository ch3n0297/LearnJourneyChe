**🔍 .kv 是什麼？**

  

.kv 是 Gensim 中 **KeyedVectors** 的儲存檔案格式，它只包含「詞向量」與「詞彙表」，**不含模型結構與訓練狀態**。

  

**通常是這樣產生的：**

```
model.wv.save("my_vectors.kv")
```

這只會儲存：

• 每個詞對應的向量

• 詞彙索引表

---

**✅ .kv 與 .model 的比較表**

|**比較項目**|.model**（完整模型）**|.kv**（詞向量）**|
|---|---|---|
|檔名範例|my_word2vec.model|my_vectors.kv|
|儲存方式|model.save()|model.wv.save()|
|是否含詞彙表|✅|✅|
|是否含訓練參數|✅|❌|
|是否能續訓|✅|❌|
|是否能進行相似詞查詢|✅|✅|
|是否推薦部署/上線用|❌（太大）|✅（較輕量、較快）|

  

---

**✅ 那你為什麼會看到 .kv 呢？**

  

很可能你的程式碼或教材中有這一行：

```
model.wv.save("my_vectors.kv")
```

或者你在做某些視覺化、比較時，只想保存詞向量的部分（不需要完整模型），所以老師或教材用了 .kv。

---

**🚀 使用上的建議**

• 若你要**重新載入整個模型並續訓** → 用 .model

```
model = Word2Vec.load("my_word2vec.model")
```

  

• 若你只要**查詢向量或做推論（如相似詞、詞類比）** → 用 .kv

```
from gensim.models import KeyedVectors
wv = KeyedVectors.load("my_vectors.kv")
```

  