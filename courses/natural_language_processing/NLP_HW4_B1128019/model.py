from transformers import AutoModel
import torch

# TODO2: Construct your model
class MultiLabelModel(torch.nn.Module):
    def __init__(
        self,
        model_name="microsoft/deberta-large",
        num_labels_A=1,
        num_labels_B=3,
    ):
        super().__init__()
        # Load the pretrained transformer model
        self.bert = AutoModel.from_pretrained(model_name)
        self.config = self.bert.config
        # Dropout layer for regularization
        self.dropout = torch.nn.Dropout(0.1)
        # Regression head: outputs a single scalar for relatedness_score
        self.reg_head = torch.nn.Linear(self.bert.config.hidden_size, num_labels_A)
        # Classification head: outputs logits for 3 classes
        self.cls_head = torch.nn.Linear(self.bert.config.hidden_size, num_labels_B)

    def forward(self, **kwargs):
        # Extract inputs from kwargs
        input_ids = kwargs.get("input_ids")
        attention_mask = kwargs.get("attention_mask")
        token_type_ids = kwargs.get("token_type_ids", None)
        # Pass through BERT
        outputs = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
            return_dict=True
        )
        # Obtain [CLS] token representation
        pooled = outputs.last_hidden_state[:, 0, :]  # shape: (batch_size, hidden_size)
        # Apply dropout
        dropped = self.dropout(pooled)
        # Compute regression output (squeeze to get shape [batch])
        score_pred = self.reg_head(dropped).squeeze(-1)
        # Compute classification logits
        class_logits = self.cls_head(dropped)
        return score_pred, class_logits



     
