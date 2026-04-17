import re
import pickle
import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

class DataCleaner:
    def __init__(self, model_path):
        self.model_path = model_path
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
        with open(f"{model_path}/label_encoder.pkl", "rb") as f:
            self.label_encoder = pickle.load(f)
            
    def clean_text(self, text):
        text = str(text).lower()
        text = re.sub(r'[^a-z0-9àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ\s]', ' ', text)
        return ' '.join(text.split()).strip()
        
    def process(self, df):
        if 'Tên hàng' not in df.columns:
            return df 
            
        for col in ['Hãng', 'Công suất', 'Tên hàng']:
            if col not in df.columns:
                df[col] = ''
                
        df.fillna('', inplace=True)
        texts = "Hãng: " + df['Hãng'].astype(str) + " - Công suất: " + df['Công suất'].astype(str) + " - Sản phẩm: " + df['Tên hàng'].astype(str)
        texts = texts.apply(self.clean_text).tolist()
        
        batch_size = 16
        predictions = []
        self.model.eval()
        with torch.no_grad():
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i+batch_size]
                inputs = self.tokenizer(batch_texts, padding=True, truncation=True, max_length=256, return_tensors="pt")
                outputs = self.model(**inputs)
                logits = outputs.logits
                preds = torch.argmax(logits, dim=-1).cpu().numpy()
                predictions.extend(preds)
                
        decoded = self.label_encoder.inverse_transform(predictions)
        
        dong_sps, loais, lop1s, lop2s = [], [], [], []
        for label in decoded:
            parts = [p.strip() for p in label.split("|")]
            if len(parts) == 4:
                dong_sps.append(parts[0])
                loais.append(parts[1])
                lop1s.append(parts[2])
                lop2s.append(parts[3])
            else:
                dong_sps.append("")
                loais.append("")
                lop1s.append("")
                lop2s.append("")
                
        df['Dòng SP'] = dong_sps
        df['Loại'] = loais
        df['Lớp 1'] = lop1s
        df['Lớp 2'] = lop2s
        
        return df

import os

cleaner = None

def get_cleaner():
    global cleaner
    if cleaner is None:
        model_path = os.environ.get("MODEL_PATH", "D:/Code/CleanData/working")
        cleaner = DataCleaner(model_path)
    return cleaner
