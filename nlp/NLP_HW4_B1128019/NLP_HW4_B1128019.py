# %% [markdown]
# # Homework 4
# - 開始寫作業前，若使用 Colab 請先設定使用 GPU!!

# %%
# 0. 安裝套件

# !pip install torch==2.6.0 --index-url https://download.pytorch.org/whl/cu124
# !pip install -r requirements.txt

# %%
# 1. 載入套件

import torch
from pathlib import Path
from transformers import AutoTokenizer
from torch.utils.data import DataLoader
from torch.optim import AdamW
from tqdm import tqdm
from torchmetrics import SpearmanCorrCoef, Accuracy, F1Score

# Hugging Face PEFT
from peft import get_peft_model, LoraConfig, TaskType
from peft.utils.other import prepare_model_for_kbit_training

# 客製化模組
from dataset import SemevalDataset
from model import MultiLabelModel

# %%
# 2. 設定參數

MODEL_NAME = "microsoft/deberta-large" # "bert-base-uncased"
LR = 1e-5
NUM_EPOCHS = 3
TRAIN_BATCH_SIZE = 8
VAL_BATCH_SIZE = 8
SAVE_DIR = "./saved_models/"

# Create the directory if it doesn't exist
if not Path(SAVE_DIR).exists():
    Path(SAVE_DIR).mkdir(parents=True, exist_ok=False)

# %%
# 3. 載入資料集與測試

data_sample = SemevalDataset(split="train").data[:3]
print(f"Dataset example: \n{data_sample[0]} \n{data_sample[1]} \n{data_sample[2]}")

# %%
# 4. 載入 tokenizer

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, cache_dir="./cache/")

# %%
# 5. 將 batch 資料進行整理
# 取出每筆資料的 'premise' 和 'hypothesis' 內容
# 將內容進行 tokenization 換成 token_ids 後，轉成 tensors
# 將 labels 也轉成 tensors

def collate_fn(batch):
    # TODO1: 完成 collate_fn
    # Write your code here
    # Extract premise and hypothesis from each example
    premises = [ex["premise"] for ex in batch]
    hypotheses = [ex["hypothesis"] for ex in batch]
    
    encoded = tokenizer(
        premises,
        hypotheses,
        padding=True,
        truncation=True,
        return_tensors="pt"
    )
    # Prepare labels for regression (relatedness_score) and classification (entailment_judgment)
    scores = torch.tensor([ex["relatedness_score"] for ex in batch], dtype=torch.float)
    labels = torch.tensor([ex["entailment_judgment"] for ex in batch], dtype=torch.long)
    # Map to the expected variable names
    input_text = encoded
    labels1 = scores
    labels2 = labels
    return input_text, labels1, labels2

# %%
# 6. 建立 DataLoader

train_loader = DataLoader(
    SemevalDataset(split="train"),
    collate_fn=collate_fn,
    batch_size=TRAIN_BATCH_SIZE,
    shuffle=True,
)
val_loader = DataLoader(
    SemevalDataset(split="validation"),
    collate_fn=collate_fn,
    batch_size=VAL_BATCH_SIZE,
    shuffle=False,
)

# %%
# 7. 設置 loss functions
# 因為是 multi-output learning
# 所以應該要有 2 種 loss functions

loss_fn1 = torch.nn.MSELoss()
loss_fn2 = torch.nn.CrossEntropyLoss()

# %%
# 8. 設置評估指標

spc = SpearmanCorrCoef()
acc = Accuracy(task="multiclass", num_classes=3)
f1 = F1Score(task="multiclass", num_classes=3, average='macro')

# %%
# 9. 載入模型，並直接把模型送至 GPU

device = "cuda:0" if torch.cuda.is_available() else "cpu"
model = MultiLabelModel(MODEL_NAME).to(device)

# %%
# Wrap validation loader to move data to device and provide __len__
class ValLoaderDeviceWrapper:
    def __init__(self, loader, device):
        self.loader = loader
        self.device = device
    def __iter__(self):
        for input_text, labels1, labels2 in self.loader:
            input_text = {k: v.to(self.device) for k, v in input_text.items()}
            labels1 = labels1.to(self.device)
            labels2 = labels2.to(self.device)
            yield input_text, labels1, labels2
    def __len__(self):
        return len(self.loader)

# %%
# 11. 配置LoRA
peft_config = LoraConfig(
    task_type=TaskType.SEQ_CLS,
    r=16,                          # LoRA矩陣的秩
    lora_alpha=32,                 # LoRA的縮放參數
    lora_dropout=0.1,              # LoRA層的dropout率
    bias="none",                   # 是否包含偏置參數
    target_modules=["query_proj", "key_proj", "value_proj", "output.dense"],  # 要應用LoRA的模塊
)

# 為主幹模型做準備
model = prepare_model_for_kbit_training(model)

# 將模型轉換為PEFT模型
model = get_peft_model(model, peft_config)

# 只訓練LoRA參數
for name, param in model.named_parameters():
    if "lora" not in name and "regression_head" not in name and "classification_head" not in name:
        param.requires_grad = False

# 印出可訓練參數的數量
trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
total_params = sum(p.numel() for p in model.parameters())
print(f"可訓練參數數量: {trainable_params} ({trainable_params/total_params:.2%})")

# %%
# 12. 載入模型與 optimizer

optimizer = AdamW(model.parameters(), lr = LR)

# %%
# 13. 建立測試函數

def do_test(
    dataloader,
    model,
    loss_fn1,
    loss_fn2,
    mode="validation",
    cur_epoch=0,
    num_epochs=NUM_EPOCHS,
):
    model.eval()

    pbar = tqdm(dataloader)
    pbar.set_description(f"{mode} epoch [{cur_epoch+1}/{NUM_EPOCHS}]")

    pred1 = torch.tensor([])
    pred2 = torch.tensor([])
    gt1 = torch.tensor([])
    gt2 = torch.tensor([])
    loss1 = 0
    loss2 = 0

    with torch.no_grad():
        for input_text, labels1, labels2 in pbar:
            outputs1, outputs2 = model(**input_text)

            loss1 += loss_fn1(outputs1, labels1).item()
            loss2 += loss_fn2(outputs2, labels2).item()

            outputs1 = outputs1.squeeze()
            outputs2 = torch.argmax(outputs2, dim=-1)
            pred1 = torch.cat((pred1, outputs1.to("cpu")), dim=-1)
            pred2 = torch.cat((pred2, outputs2.to("cpu")), dim=-1)
            gt1 = torch.cat((gt1, labels1.to("cpu")), dim=-1)
            gt2 = torch.cat((gt2, labels2.to("cpu")), dim=-1)

    print(f"Spearman Corr: {spc(pred1, gt1)} \nAccuracy: {acc(pred2, gt2)} \nF1 Score: {f1(pred2, gt2)}")
    loss1 /= len(dataloader)
    loss2 /= len(dataloader)
    return loss1, loss2


# %%
# 10a. Baseline (non-LoRA) training
# Clone model for baseline
baseline_model = MultiLabelModel(MODEL_NAME).to(device)
baseline_optimizer = AdamW(baseline_model.parameters(), lr=LR)
print("Starting baseline training (no LoRA)...")
for ep_base in range(NUM_EPOCHS):
    pbar_base = tqdm(train_loader)
    pbar_base.set_description(f"Baseline Training epoch [{ep_base+1}/{NUM_EPOCHS}]")
    baseline_model.train()
    for batch in pbar_base:
        baseline_optimizer.zero_grad()
        input_text_b, labels1_b, labels2_b = batch
        input_text_b = {k: v.to(device) for k, v in input_text_b.items()}
        labels1_b = labels1_b.to(device)
        labels2_b = labels2_b.to(device)
        score_b, logits_b = baseline_model(**input_text_b)
        loss1_b = loss_fn1(score_b, labels1_b)
        loss2_b = loss_fn2(logits_b, labels2_b)
        loss_b = loss1_b + loss2_b
        loss_b.backward()
        baseline_optimizer.step()
    val_loader_device = ValLoaderDeviceWrapper(val_loader, device)
    val_loss1_b, val_loss2_b = do_test(
        val_loader_device,
        baseline_model,
        loss_fn1,
        loss_fn2,
        mode="baseline_validation",
        cur_epoch=ep_base,
        num_epochs=NUM_EPOCHS,
    )

# %%
# 14. 開始訓練模型

for ep in range(NUM_EPOCHS):
    pbar = tqdm(train_loader)
    pbar.set_description(f"Training epoch [{ep+1}/{NUM_EPOCHS}]")
    model.train()
    for batch in pbar:
        optimizer.zero_grad()

        # Unpack tuple from collate_fn
        input_text, labels1, labels2 = batch

        # Move inputs and labels to device
        input_text = {k: v.to(device) for k, v in input_text.items()}
        labels1 = labels1.to(device)
        labels2 = labels2.to(device)

        # forward pass
        score_pred, logits_pred = model(**input_text)
        # compute loss
        loss1 = loss_fn1(score_pred, labels1)
        loss2 = loss_fn2(logits_pred, labels2)
        loss = loss1 + loss2
        # back-propagation
        loss.backward()
        # model optimization
        optimizer.step()

    val_loader_device = ValLoaderDeviceWrapper(val_loader, device)
    val_loss1, val_loss2 = do_test(
        val_loader_device,
        model,
        loss_fn1,
        loss_fn2,
        mode="validation",
        cur_epoch=ep,
        num_epochs=NUM_EPOCHS,
    )
    torch.save(model, f'./saved_models/ep{ep}.ckpt')
print(f"Model saved to {SAVE_DIR}ep{ep}.ckpt!")

# %%
# 15. 單一子任務訓練 (Single-Task Training for Comparison)
# 為了比較一次多任務訓練與單一子任務訓練的效果，下面示範單一子任務的訓練流程：
#    - 先訓練回歸子任務，再訓練分類子任務
single_model = MultiLabelModel(MODEL_NAME).to(device)
# Apply LoRA to single_model
single_model = prepare_model_for_kbit_training(single_model)
single_model = get_peft_model(single_model, peft_config)
# Freeze non-LoRA parameters and heads
for name, param in single_model.named_parameters():
    if "lora" not in name and "regression_head" not in name and "classification_head" not in name:
        param.requires_grad = False
single_optimizer = AdamW(single_model.parameters(), lr=LR)
print("Starting single-task training with LoRA (regression then classification)...")
for ep_st in range(NUM_EPOCHS):
    # ------ Regression only ------
    single_model.train()
    pbar_st_reg = tqdm(train_loader, desc=f"SingleTask Reg epoch [{ep_st+1}/{NUM_EPOCHS}]")
    for input_text_st, labels1_st, _ in pbar_st_reg:
        single_optimizer.zero_grad()
        input_text_st = {k: v.to(device) for k, v in input_text_st.items()}
        labels1_st = labels1_st.to(device)
        score_st, _ = single_model(**input_text_st)
        loss_reg_st = loss_fn1(score_st, labels1_st)
        loss_reg_st.backward()
        single_optimizer.step()

    # ------ Classification only ------
    single_model.train()
    pbar_st_cls = tqdm(train_loader, desc=f"SingleTask Cls epoch [{ep_st+1}/{NUM_EPOCHS}]")
    for input_text_st, _, labels2_st in pbar_st_cls:
        single_optimizer.zero_grad()
        input_text_st = {k: v.to(device) for k, v in input_text_st.items()}
        labels2_st = labels2_st.to(device)
        _, logits_st = single_model(**input_text_st)
        loss_cls_st = loss_fn2(logits_st, labels2_st)
        loss_cls_st.backward()
        single_optimizer.step()

    # Validation for single-task mode
    val_loader_device_st = ValLoaderDeviceWrapper(val_loader, device)
    val_loss1_st, val_loss2_st = do_test(
        val_loader_device_st,
        single_model,
        loss_fn1,
        loss_fn2,
        mode="single_task_validation",
        cur_epoch=ep_st,
        num_epochs=NUM_EPOCHS,
    )
    print(f"Single-Task epoch {ep_st+1}: val_loss_reg = {val_loss1_st:.4f}, val_loss_cls = {val_loss2_st:.4f}")

# %%
