import os
import re
import sys
import json
import math
import pickle
import argparse
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from transformers import AutoTokenizer, AutoModel, get_cosine_schedule_with_warmup
from tqdm import tqdm

# Ensure reproducibility
import random
def seed_everything(seed=42):
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

seed_everything(42)

# ===========================================================================
# PATHS CONFIGURATION
# ===========================================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_PATH = os.path.join(BASE_DIR, "dataset", "train_augmented.csv")
MODEL_OUT_DIR = os.path.join(BASE_DIR, "working", "model_v2")


def parse_args():
    parser = argparse.ArgumentParser(description="Train PhoBERT multi-task model")
    parser.add_argument("--dataset", type=str, default=DATASET_PATH,
                        help="Path to base training dataset (CSV with text, Dòng SP, Loại, Lớp 1, Lớp 2, weight)")
    parser.add_argument("--phase6-data", type=str, default=None,
                        help="Path to Phase 6 augmented data CSV to merge and continue training")
    parser.add_argument("--resume-from", type=str, default=None,
                        help="Path to existing model checkpoint (pytorch_model.bin) to resume training")
    parser.add_argument("--output-dir", type=str, default=MODEL_OUT_DIR,
                        help="Directory to save model checkpoints")
    parser.add_argument("--epochs", type=int, default=5,
                        help="Number of training epochs")
    parser.add_argument("--lr", type=float, default=2e-5,
                        help="Learning rate")
    parser.add_argument("--batch-size", type=int, default=4,
                        help="Per-device batch size")
    parser.add_argument("--no-fp16", action="store_true",
                        help="Disable mixed precision training")
    return parser.parse_args()


# ===========================================================================
# MODEL ARCHITECTURE

# ===========================================================================
# MODEL ARCHITECTURE
# ===========================================================================
class PhoBertMultiTask(nn.Module):
    def __init__(self, num_dong_sp, num_loai, num_lop1, num_lop2, model_name="vinai/phobert-base-v2"):
        super(PhoBertMultiTask, self).__init__()
        print(f"Initializing PhoBertMultiTask with base model: {model_name}")
        self.phobert = AutoModel.from_pretrained(model_name)
        self.dropout = nn.Dropout(0.1)
        
        hidden_size = self.phobert.config.hidden_size
        
        # 4 independent classification heads for multi-task learning
        self.head_dong_sp = nn.Linear(hidden_size, num_dong_sp)
        self.head_loai = nn.Linear(hidden_size, num_loai)
        self.head_lop1 = nn.Linear(hidden_size, num_lop1)
        self.head_lop2 = nn.Linear(hidden_size, num_lop2)

    def forward(self, input_ids, attention_mask):
        outputs = self.phobert(input_ids=input_ids, attention_mask=attention_mask)
        # Use the CLS token representation (first token in PhoBERT)
        cls_output = outputs.last_hidden_state[:, 0, :]
        cls_output = self.dropout(cls_output)
        
        logits_dong_sp = self.head_dong_sp(cls_output)
        logits_loai = self.head_loai(cls_output)
        logits_lop1 = self.head_lop1(cls_output)
        logits_lop2 = self.head_lop2(cls_output)
        
        return logits_dong_sp, logits_loai, logits_lop1, logits_lop2

# ===========================================================================
# PYTORCH DATASET
# ===========================================================================
class MultiTaskDataset(Dataset):
    def __init__(self, texts, labels, weights):
        self.texts = list(texts)
        self.labels = labels  # dict with keys: dong_sp, loai, lop1, lop2
        self.weights = list(weights)

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        item = {
            'text': self.texts[idx],
            'dong_sp': self.labels['dong_sp'][idx],
            'loai': self.labels['loai'][idx],
            'lop1': self.labels['lop1'][idx],
            'lop2': self.labels['lop2'][idx],
            'weight': self.weights[idx]
        }
        return item

class MultiTaskCollator:
    def __init__(self, tokenizer, max_length=64):
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __call__(self, batch):
        texts = [item['text'] for item in batch]
        
        encoding = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt"
        )
        
        input_ids = encoding['input_ids']
        attention_mask = encoding['attention_mask']
        
        dong_sp = torch.tensor([item['dong_sp'] for item in batch], dtype=torch.long)
        loai = torch.tensor([item['loai'] for item in batch], dtype=torch.long)
        lop1 = torch.tensor([item['lop1'] for item in batch], dtype=torch.long)
        lop2 = torch.tensor([item['lop2'] for item in batch], dtype=torch.long)
        weights = torch.tensor([item['weight'] for item in batch], dtype=torch.float)
        
        return {
            'input_ids': input_ids,
            'attention_mask': attention_mask,
            'dong_sp': dong_sp,
            'loai': loai,
            'lop1': lop1,
            'lop2': lop2,
            'weight': weights
        }

# ===========================================================================
# HUẤN LUYỆN CHÍNH
# ===========================================================================
def train(args):
    dataset_path = args.dataset
    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # Auto detect VRAM and configure parameters for RTX 2070 Super (8GB)
    batch_size = args.batch_size
    grad_accum_steps = 8
    use_fp16 = not args.no_fp16 and torch.cuda.is_available()
    use_grad_ckpt = True

    if torch.cuda.is_available():
        vram_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
        print(f"Detected GPU VRAM: {vram_gb:.2f} GB")
        if vram_gb > 8.5:
            print("Large VRAM GPU detected. Adjusting batch sizes.")
            batch_size = 16
            grad_accum_steps = 2
        else:
            print("Configured for local GPU (VRAM <= 8GB). Enabling memory optimization.")
    else:
        print("No GPU detected! Running on CPU (slow fallback).")
        use_fp16 = False
        use_grad_ckpt = False

    # 1.2 Load and encode dataset
    print(f"Loading augmented dataset from {dataset_path}...")
    df = pd.read_csv(dataset_path)
    df = df.fillna('không_có')
    print(f"Loaded dataset shape: {df.shape}")

    # Merge Phase 6 augmented data if provided
    if args.phase6_data:
        if not os.path.exists(args.phase6_data):
            print(f"WARNING: Phase 6 data not found at {args.phase6_data}, skipping.")
        else:
            print(f"Merging Phase 6 training data from {args.phase6_data}...")
            df_phase6 = pd.read_csv(args.phase6_data)
            df_phase6 = df_phase6.fillna('không_có')
            print(f"  Phase 6 data shape: {df_phase6.shape}")

            required_cols = ['text', 'Dòng SP', 'Loại', 'Lớp 1', 'Lớp 2', 'weight']
            available = [c for c in required_cols if c in df_phase6.columns]
            missing = [c for c in required_cols if c not in df_phase6.columns]
            if missing:
                print(f"  WARNING: Missing columns in Phase 6 data: {missing}. Filling with 'không_có'.")
                for c in missing:
                    df_phase6[c] = 'không_có'

            has_hs = 'HS_Code' in df_phase6.columns
            if has_hs:
                print(f"  Phase 6 samples by HS code: {df_phase6['HS_Code'].value_counts().to_dict()}")

            before = len(df)
            df = pd.concat([df, df_phase6[required_cols]], ignore_index=True)
            df = df.drop_duplicates(subset=['text'], keep='first')
            after = len(df)
            print(f"  Merged: {before} + {len(df_phase6)} -> {after} (removed {before + len(df_phase6) - after} duplicates)")

    label_cols = ['Dòng SP', 'Loại', 'Lớp 1', 'Lớp 2']
    encoders = {}
    encoded_labels = {}

    print("Encoding labels and saving encoders...")
    for col in label_cols:
        le = LabelEncoder()
        # Ensure 'không_có' is included in label classes
        unique_vals = list(df[col].unique())
        if 'không_có' not in unique_vals:
            unique_vals.append('không_có')
        le.fit(unique_vals)
        
        col_to_key = {
            'Dòng SP': 'dong_sp',
            'Loại': 'loai',
            'Lớp 1': 'lop1',
            'Lớp 2': 'lop2'
        }
        col_key = col_to_key[col]
        encoders[col_key] = le
        encoded_labels[col_key] = le.transform(df[col])
        
        # Save LabelEncoder to pickle
        pkl_path = os.path.join(output_dir, f"label_encoder_{col_key}.pkl")
        with open(pkl_path, 'wb') as f:
            pickle.dump(le, f)
        print(f"Saved {col} encoder ({len(le.classes_)} classes) to {pkl_path}")

    # Train/Val split (80% train, 20% validation)
    print("Splitting dataset...")
    train_idx, val_idx = train_test_split(
        np.arange(len(df)),
        test_size=0.10,
        random_state=42,
        stratify=None
    )

    train_labels = {k: v[train_idx] for k, v in encoded_labels.items()}
    val_labels = {k: v[val_idx] for k, v in encoded_labels.items()}

    train_dataset = MultiTaskDataset(df['text'].iloc[train_idx], train_labels, df['weight'].iloc[train_idx])
    val_dataset = MultiTaskDataset(df['text'].iloc[val_idx], val_labels, df['weight'].iloc[val_idx])

    tokenizer = AutoTokenizer.from_pretrained("vinai/phobert-base-v2")
    collator = MultiTaskCollator(tokenizer, max_length=64)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, collate_fn=collator, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, collate_fn=collator, num_workers=0)

    # 1.3 Initialize Model
    model = PhoBertMultiTask(
        num_dong_sp=len(encoders['dong_sp'].classes_),
        num_loai=len(encoders['loai'].classes_),
        num_lop1=len(encoders['lop1'].classes_),
        num_lop2=len(encoders['lop2'].classes_)
    )

    # Load existing checkpoint if --resume-from is provided
    if args.resume_from:
        resume_path = args.resume_from
        if not os.path.exists(resume_path):
            print(f"WARNING: Checkpoint not found at {resume_path}. Starting from scratch.")
        else:
            print(f"Resuming from checkpoint: {resume_path}")
            state_dict = torch.load(resume_path, map_location="cpu")
            model.load_state_dict(state_dict, strict=False)
            print(f"  Loaded checkpoint (strict=False, ignoring mismatched heads if any).")

    if use_grad_ckpt:
        print("Enabling gradient checkpointing for PhoBERT...")
        model.phobert.gradient_checkpointing_enable()

    model.to(device)

    # 1.5 Loss functions with Label Smoothing
    # We use reduction='none' to apply sample weights element-wise, then take the mean
    criterion = nn.CrossEntropyLoss(label_smoothing=0.1, reduction='none')

    # Optimization setup
    epochs = args.epochs
    lr = args.lr
    weight_decay = 0.01
    
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    
    total_steps = len(train_loader) // grad_accum_steps * epochs
    scheduler = get_cosine_schedule_with_warmup(
        optimizer,
        num_warmup_steps=int(total_steps * 0.1),
        num_training_steps=total_steps
    )

    if torch.cuda.is_available():
        scaler = torch.amp.GradScaler('cuda', enabled=use_fp16)
    else:
        scaler = torch.amp.GradScaler('cpu', enabled=False)

    best_val_loss = float('inf')
    early_stopping_patience = 2
    epochs_no_improve = 0

    print(f"Starting training loop. Steps per epoch: {len(train_loader)}, Effective batch size: {batch_size * grad_accum_steps}")
    for epoch in range(epochs):
        model.train()
        train_loss = 0.0
        optimizer.zero_grad()

        train_bar = tqdm(train_loader, desc=f"Epoch {epoch+1}/{epochs} [Train]", unit="batch")
        for step, batch in enumerate(train_bar):
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            
            y_dong_sp = batch['dong_sp'].to(device)
            y_loai = batch['loai'].to(device)
            y_lop1 = batch['lop1'].to(device)
            y_lop2 = batch['lop2'].to(device)
            weights = batch['weight'].to(device)

            with torch.amp.autocast('cuda', enabled=use_fp16):
                logits_dong, logits_loai, logits_lop1, logits_lop2 = model(input_ids, attention_mask)
                
                # Compute raw losses element-wise
                loss_dong = criterion(logits_dong, y_dong_sp)
                loss_l = criterion(logits_loai, y_loai)
                loss_l1 = criterion(logits_lop1, y_lop1)
                loss_l2 = criterion(logits_lop2, y_lop2)

                # Apply weights and calculate task losses
                task_loss_dong = (loss_dong * weights).mean()
                task_loss_loai = (loss_l * weights).mean()
                task_loss_lop1 = (loss_l1 * weights).mean()
                task_loss_lop2 = (loss_l2 * weights).mean()

                # Weighted multi-task loss (Dòng SP: 0.5, Loại: 0.5, Lớp 1: 2.0, Lớp 2: 2.0)
                loss = (0.5 * task_loss_dong + 
                        0.5 * task_loss_loai + 
                        2.0 * task_loss_lop1 + 
                        2.0 * task_loss_lop2)
                
                # Scale loss by gradient accumulation steps
                loss = loss / grad_accum_steps

            # Backward pass
            scaler.scale(loss).backward()
            train_loss += loss.item() * grad_accum_steps

            if (step + 1) % grad_accum_steps == 0 or (step + 1) == len(train_loader):
                # Gradient clipping
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                
                scaler.step(optimizer)
                scaler.update()
                scheduler.step()
                optimizer.zero_grad()

            if step % 10 == 0:
                train_bar.set_postfix(loss=f"{loss.item() * grad_accum_steps:.4f}")

        avg_train_loss = train_loss / len(train_loader)
        
        # Validation phase
        model.eval()
        val_loss = 0.0
        correct_dong, correct_loai, correct_lop1, correct_lop2 = 0, 0, 0, 0
        total_samples = 0

        val_bar = tqdm(val_loader, desc=f"Epoch {epoch+1}/{epochs} [Val]", unit="batch")
        with torch.no_grad():
            for batch in val_bar:
                input_ids = batch['input_ids'].to(device)
                attention_mask = batch['attention_mask'].to(device)
                
                y_dong_sp = batch['dong_sp'].to(device)
                y_loai = batch['loai'].to(device)
                y_lop1 = batch['lop1'].to(device)
                y_lop2 = batch['lop2'].to(device)
                weights = batch['weight'].to(device)

                with torch.amp.autocast('cuda', enabled=use_fp16):
                    logits_dong, logits_loai, logits_lop1, logits_lop2 = model(input_ids, attention_mask)
                    
                    loss_dong = criterion(logits_dong, y_dong_sp)
                    loss_l = criterion(logits_loai, y_loai)
                    loss_l1 = criterion(logits_lop1, y_lop1)
                    loss_l2 = criterion(logits_lop2, y_lop2)

                    task_loss_dong = (loss_dong * weights).mean()
                    task_loss_loai = (loss_l * weights).mean()
                    task_loss_lop1 = (loss_l1 * weights).mean()
                    task_loss_lop2 = (loss_l2 * weights).mean()

                    loss = (0.5 * task_loss_dong + 
                            0.5 * task_loss_loai + 
                            2.0 * task_loss_lop1 + 
                            2.0 * task_loss_lop2)
                    
                    val_loss += loss.item()
                    val_bar.set_postfix(loss=f"{loss.item():.4f}")

                    # Calculate accuracies
                    correct_dong += (logits_dong.argmax(dim=-1) == y_dong_sp).sum().item()
                    correct_loai += (logits_loai.argmax(dim=-1) == y_loai).sum().item()
                    correct_lop1 += (logits_lop1.argmax(dim=-1) == y_lop1).sum().item()
                    correct_lop2 += (logits_lop2.argmax(dim=-1) == y_lop2).sum().item()
                    total_samples += len(y_dong_sp)

        avg_val_loss = val_loss / len(val_loader)
        acc_dong = correct_dong / total_samples
        acc_loai = correct_loai / total_samples
        acc_lop1 = correct_lop1 / total_samples
        acc_lop2 = correct_lop2 / total_samples

        print(f"Epoch {epoch+1} Results:")
        print(f"  Train Loss: {avg_train_loss:.4f} | Val Loss: {avg_val_loss:.4f}")
        print(f"  Val Accuracies: Dòng SP: {acc_dong:.4%}, Loại: {acc_loai:.4%}, Lớp 1: {acc_lop1:.4%}, Lớp 2: {acc_lop2:.4%}")

        # Check for improvement
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            epochs_no_improve = 0
            # Save the best model
            model_save_path = os.path.join(output_dir, "pytorch_model.bin")
            torch.save(model.state_dict(), model_save_path)
            # Save configuration
            config_save_path = os.path.join(output_dir, "config.json")
            with open(config_save_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "model_type": "phobert_multitask",
                    "num_dong_sp": len(encoders['dong_sp'].classes_),
                    "num_loai": len(encoders['loai'].classes_),
                    "num_lop1": len(encoders['lop1'].classes_),
                    "num_lop2": len(encoders['lop2'].classes_)
                }, f, indent=2)
            print(f"  -> Saved best model checkpoint to {model_save_path}")
        else:
            epochs_no_improve += 1
            print(f"  -> No validation loss improvement for {epochs_no_improve} epochs.")
            if epochs_no_improve >= early_stopping_patience:
                print("Early stopping triggered! Ending training.")
                break

    print("Training finished successfully!")

if __name__ == "__main__":
    args = parse_args()
    train(args)
