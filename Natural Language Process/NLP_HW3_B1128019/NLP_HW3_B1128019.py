# %% [markdown]
# # NLP 作業3

# %% [markdown]
# ## 安裝需要的套件

# %%
#!pip install datasets
#!pip install evaluate
#!pip install seqeval

# %%
import datasets
import evaluate
import seqeval

print(datasets.__version__)
print(evaluate.__version__)

# %%
!pip list | grep seqeval

# %%
import torch

# 測試現在這個 Colab 環境是否已經使用 GPU
# 否則等下可能會需要重新啟動 Colab 環境
torch.cuda.is_available() # 結果需要顯示為 True

# %% [markdown]
# ## Start

# %%
from transformers import AutoTokenizer
from transformers import AutoModelForTokenClassification
from transformers import DataCollatorForTokenClassification
from transformers import TrainingArguments, Trainer
from transformers import EvalPrediction

# %%
MODEL_NAME = "bert-base-uncased"
DATA_NAME = "ncbi_disease"
TRAIN_BATCH_SIZE = 16
EVAL_BATCH_SIZE = 20
NUM_TRAIN_EPOCHS = 3
LEARNING_RATE = 2e-5

# %%
# 載入資料集
dataset = datasets.load_dataset(DATA_NAME, trust_remote_code=True)

# %%
# 檢查每個 split 的數量

for data_type in ["train", "validation", "test"]:
    print(f"{data_type}: {len(dataset[data_type])} samples")

# %%
# Show NER tag names
label_names = dataset["train"].features["ner_tags"].feature.names
print(label_names)

# %%
# 觀察資料
first_example = dataset["train"][1]
print(type(first_example))

for k, v in first_example.items():
    print(f"{k}: {v}")

# %%
# TODO1: 建立 tokenizer

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)# Write your code here


# %%
tokenized_inputs = tokenizer(
        first_example["tokens"],
        truncation=True,
        is_split_into_words=True,
)
print("Tokenized 後的結果：")
print(tokenized_inputs)
print("Tokenized 後的 word_ids：")
print(tokenized_inputs.word_ids())

print("原始資料的 labels：")
print(first_example["ner_tags"])
print("我們下一步需要轉換 labels 為：")
print("[-100, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 0, 0, 0, -100]")

# %%
# TODO2: labels 處理
# 我們可以發現資料集的 labels (ner_tags) 是以 word 為單位
# 但是我們要使用的 tokenizer (如 BERT 的 tokenizer) 會把 word 切成 subwords
# 因此要針對 labels 的部分進行處理

def tokenize_and_align_labels(example):
    original_labels = example["ner_tags"]

    tokenized_inputs = tokenizer(
        example["tokens"],
        truncation=True,
        is_split_into_words=True,
    )
    word_ids = tokenized_inputs.word_ids()
    labels = []
    current_word_idx = None
    for word_idx in word_ids:
        # Write your code here
        # Hints:
        # (1) [CLS] or [SEP] 設為 -100
        # (2) 由左至右給予新的 labels，
        # 因此需要 current_word_idx
        # 來幫助我們觀察下個 token 是否進到新的 word，還是是 上一個 word 的 sub-word
        if word_idx is None:
            labels.append(-100)
        elif word_idx != current_word_idx:
            labels.append(original_labels[word_idx])
        else:
            labels.append(-100)
    
    current_word_idx = word_idx
    tokenized_inputs["labels"] = labels
    return tokenized_inputs

# %%
tokenized_datasets = dataset.map(
    tokenize_and_align_labels,
    batched=False,
    remove_columns=dataset["train"].column_names,
)

# %%
tokenized_datasets["train"]

# %%
data_collator = DataCollatorForTokenClassification(tokenizer=tokenizer)

# %%
fake_batch = [tokenized_datasets["train"][i] for i in range(2)]
batch = data_collator(fake_batch)
batch["labels"]

# %%
# TODO3: 建立 id -> label (`id2label`) 以及 label -> id (`label2id`) 的轉換
# `id2label` 和 `label2id` 都是 Python dict，且 key 跟 value 都是 int

id2label = {idx: label for idx, label in enumerate(label_names)} # Write your code here
label2id = {label: idx for idx, label in enumerate(label_names)} # Write your code here

print(id2label)
print(label2id)

# %%
model = AutoModelForTokenClassification.from_pretrained(
    MODEL_NAME,
    num_labels=len(label_names),
    id2label=id2label,
    label2id=label2id
)

# %%
# 檢查模型是否確實被設定為3種類別輸出
model.config.num_labels

# %%
# TODO4: 設定 TrainingArguments

training_args = TrainingArguments(
    output_dir="./bertNER",
    overwrite_output_dir=True,
    eval_strategy="epoch",
    save_strategy="epoch",
    logging_strategy="steps",
    logging_steps=50,
    save_total_limit=3,
    load_best_model_at_end=True,
    metric_for_best_model="f1",
    fp16=True,
    learning_rate=5e-5,
    weight_decay=0.01,
    num_train_epochs=3,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=32,
    gradient_accumulation_steps=2,
    warmup_ratio=0.1,
    report_to='tensorboard',
    push_to_hub=False,
)

# %%
print("↳ max label in dataset :", max(dataset["train"].features["ner_tags"].feature.names))
print("↳ len(label_names)     :", len(label_names))
print("↳ model.config.num_labels :", model.config.num_labels)
print("↳ id2label keys range  :", sorted(id2label.keys()))


# %%
# TODO5: 完成 compute_metrics
import numpy as np

metric = evaluate.load("seqeval")

def compute_metrics(eval_pred: EvalPrediction):
    predictions, labels = eval_pred.predictions, eval_pred.label_ids
    # Write your code here
    pred_ids = np.argmax(predictions, axis=2) # (batch, seq_len, num_labels)變成(batch, seq_len)
    true_pred, true_label = [], []
    for pred_seq, label_seq in zip(pred_ids, labels):
        sent_preds, sent_labels = [], []
        for p_id, l_id in zip(pred_seq, label_seq):
            if l_id == -100:
                continue
            sent_labels.append(id2label[int(l_id)])
            sent_preds.append(id2label[int(p_id)])
        true_label.append(sent_labels)
        true_pred.append(sent_preds)
    #ChatGPT fix this bug ▼
    metrics = metric.compute(predictions = true_pred, references = true_label) #seqeval 計算整體指標，這邊要注意是使用references當作變數名稱，按照Hugging Face 格式
    return { # Write your code here
        "precision": metrics["overall_precision"],
        "recall": metrics["overall_recall"],
        "f1": metrics["overall_f1"],
        "accuracy": metrics["overall_accuracy"],
    } 

# %%
# TODO6: set up trainer

trainer = Trainer(
    # Write your code here
    model=model,
    args=training_args,
    train_dataset=tokenized_datasets["train"],
    eval_dataset=tokenized_datasets["validation"],
    tokenizer=tokenizer,
    data_collator=data_collator,
    compute_metrics=compute_metrics,
)

# %% [markdown]
# ### 相關官方文件連結
# - [TokenClassifierOutput](https://huggingface.co/docs/transformers/en/main_classes/output#transformers.modeling_outputs.TokenClassifierOutput)
# - [EvalPrediction](https://huggingface.co/docs/transformers/internal/trainer_utils#transformers.EvalPrediction)

# %%
# compute_metrics 模擬測試區

eval_dataloader = trainer.get_eval_dataloader()
batch = next(iter(eval_dataloader))
with torch.no_grad():
    outputs = model(**{k: v.to(model.device) for k, v in batch.items()})
print(f"AutoModelForTokenClassification 輸出的型態為: {type(outputs)}")
print(f"Logits shape: {outputs.logits.shape}")
print(f"Labels shape: {batch['labels'].shape}")
print(f"Loss: {outputs.loss.item()}")
print(f"Type of `outputs.loss`: {type(outputs.loss)}")
print(f"Type of `outputs.loss.item()`: {type(outputs.loss.item())}")
print()

# 取得 logits 和 labels
logits = outputs.logits.cpu().numpy()
labels = batch["labels"].cpu().numpy()

# 建立 EvalPrediction 模擬 compute_metrics 呼叫
mock_eval = EvalPrediction(
    predictions=logits,
    label_ids=labels,
)
print(f"Trainer 在輸進去 compute_metrics 前的型態為: {type(mock_eval)}")

# 呼叫你自己寫的 metrics function
metrics = compute_metrics(mock_eval)
for k, v in metrics.items():
    print(f"{k}: {v}")

# %%
trainer.train()

# %%
trainer.evaluate(tokenized_datasets["test"])

# %%
#這次幾乎無使用GPT，中間有修BUG有使用ChatGPT-4o已標注


