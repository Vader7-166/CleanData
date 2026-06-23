import re
import pickle
import json
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import os
import asyncio
import time
from functools import lru_cache
from transformers import AutoModel

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

class DataCleaner:
    def __init__(self, model_path):
        # Check for model redirection
        model_v2_path = os.path.join(model_path, "model_v2")
        if os.path.exists(os.path.join(model_v2_path, "config.json")):
            print(f"Redirecting model path from {model_path} to {model_v2_path}")
            model_path = model_v2_path

        # Determine tokenizer path
        tokenizer_path = "vinai/phobert-base-v2"
        # Check if tokenizer files exist in model_path
        if os.path.exists(os.path.join(model_path, "vocab.txt")):
            tokenizer_path = model_path
        # Check if they exist in parent directory of model_path
        elif os.path.exists(os.path.join(os.path.dirname(model_path), "vocab.txt")):
            tokenizer_path = os.path.dirname(model_path)

        self.model_path = model_path
        self.MAX_LENGTH = 64
        print(f"Loading Tokenizer from {tokenizer_path}...")
        from transformers import AutoTokenizer
        try:
            # Use fast tokenizer for better performance on CPU
            self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_path, use_fast=True)
        except Exception as e:
            print(f"Failed to load fast AutoTokenizer: {e}. Falling back to slow...")
            self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_path, use_fast=False)
        
        # Load config
        config_file = os.path.join(model_path, "config.json")
        is_multitask = False
        config_data = {}
        if os.path.exists(config_file):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
                if config_data.get("model_type") == "phobert_multitask":
                    is_multitask = True
            except Exception as e:
                print(f"Error loading config.json: {e}")
        
        self.is_multitask = is_multitask
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Device set to: {self.device}")

        if is_multitask:
            print("Loading Custom PhoBertMultiTask Model...")
            num_dong_sp = config_data.get("num_dong_sp", 5)
            num_loai = config_data.get("num_loai", 3)
            num_lop1 = config_data.get("num_lop1", 36)
            num_lop2 = config_data.get("num_lop2", 41)
            
            base_model_name = "vinai/phobert-base-v2"
            self.model = PhoBertMultiTask(
                num_dong_sp=num_dong_sp,
                num_loai=num_loai,
                num_lop1=num_lop1,
                num_lop2=num_lop2,
                model_name=base_model_name
            )
            
            weights_path = os.path.join(model_path, "pytorch_model.bin")
            print(f"Loading state dict from {weights_path}...")
            state_dict = torch.load(weights_path, map_location="cpu")
            self.model.load_state_dict(state_dict)
            
            # Load the 4 ASCII label encoders
            self.encoders = {}
            for col_key in ['dong_sp', 'loai', 'lop1', 'lop2']:
                pkl_path = os.path.join(model_path, f"label_encoder_{col_key}.pkl")
                with open(pkl_path, "rb") as f:
                    self.encoders[col_key] = pickle.load(f)
                print(f"Loaded encoder for {col_key} with {len(self.encoders[col_key].classes_)} classes.")
        else:
            print("Loading Flat Classifier Model...")
            from transformers import AutoModelForSequenceClassification
            self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
            with open(os.path.join(model_path, "label_encoder.pkl"), "rb") as f:
                self.label_encoder = pickle.load(f)

        if self.device.type == "cpu":
            print("INFO: CUDA not available. Applying dynamic quantization for CPU optimization.")
            # Quantize the model to int8 to speed up CPU inference
            self.model = torch.quantization.quantize_dynamic(
                self.model, {torch.nn.Linear}, dtype=torch.qint8
            )
            
        self.model.to(self.device)
        self.model.eval()
        
        if torch.cuda.is_available():
            torch.backends.cudnn.benchmark = True
            print("INFO: CUDA available, enabling cuDNN benchmark.")

        self.THRESHOLD = 0.60 if is_multitask else 0.85
        # Per-head thresholds for multitask: mỗi head phải vượt ngưỡng riêng
        self.THRESHOLD_DONG_SP = 0.60
        self.THRESHOLD_LOAI = 0.60
        self.THRESHOLD_LOP1 = 0.40
        self.THRESHOLD_LOP2 = 0.60
        self.MAX_CONCURRENT_CHUNKS = 1 # Set to 1 as we move to sequential CPU batching
        
        self._load_label_standard()
        
        import concurrent.futures
        import multiprocessing
        self.executor = concurrent.futures.ProcessPoolExecutor(max_workers=multiprocessing.cpu_count())

    def clean_text_for_dict(self, text):
        text = str(text).lower()
        text = re.sub(r'[^a-z0-9àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ\s]', ' ', text)
        return ' '.join(text.split()).strip()

    _sbert_model = None
    _sbert_tokenizer = None

    def _load_sbert(self):
        if DataCleaner._sbert_model is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer
            model_name = "keepitreal/vietnamese-sbert"
            print(f"INFO: Loading SBERT model: {model_name}...")
            DataCleaner._sbert_model = SentenceTransformer(model_name)
            print(f"INFO: SBERT model loaded successfully.")
        except Exception as e:
            print(f"WARNING: Could not load SBERT model: {e}")
            print(f"WARNING: Semantic features will be unavailable.")
            DataCleaner._sbert_model = False

    def get_embedding(self, texts):
        self._load_sbert()
        if DataCleaner._sbert_model is False:
            return None
        single_input = isinstance(texts, str)
        if single_input:
            texts = [texts]
        texts = [str(t).strip() for t in texts]
        non_empty = [t for t in texts if t]
        if not non_empty:
            return np.zeros(768) if single_input else np.zeros((len(texts), 768))
        embeddings = DataCleaner._sbert_model.encode(non_empty, show_progress_bar=False, normalize_embeddings=True)
        result_map = {}
        idx = 0
        for i, t in enumerate(texts):
            if t:
                result_map[i] = embeddings[idx]
                idx += 1
            else:
                result_map[i] = np.zeros(768)
        if single_input:
            return result_map[0]
        return np.array([result_map[i] for i in range(len(texts))])

    def cosine_similarity(self, a, b):
        a = a / (np.linalg.norm(a) + 1e-10)
        b = b / (np.linalg.norm(b) + 1e-10)
        return float(np.dot(a, b))

    def _load_label_standard(self):
        config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'label_standard.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                standard = json.load(f)
            self._dong_sp_aliases = standard.get('dong_sp', {}).get('aliases', {})
            self._loai_aliases = standard.get('loai', {}).get('aliases', {})
            self._lop1_aliases = standard.get('lop1', {}).get('aliases', {})
            self._lop2_aliases = standard.get('lop2', {}).get('aliases', {})
        except Exception as e:
            print(f"Warning: Could not load label_standard.json: {e}")
            self._dong_sp_aliases = {}
            self._loai_aliases = {}
            self._lop1_aliases = {}
            self._lop2_aliases = {}

    def _normalize_label(self, dong_sp, loai, lop1, lop2):
        d_sp = str(dong_sp).strip()
        lo = str(loai).strip()
        l1 = str(lop1).strip()
        l2 = str(lop2).strip()

        d_sp = self._dong_sp_aliases.get(d_sp, d_sp)
        lo = self._loai_aliases.get(lo, lo)
        l1 = self._lop1_aliases.get(l1, l1.lower())
        l2 = self._lop2_aliases.get(l2, l2.lower())

        d_sp = d_sp if d_sp not in ['nan', 'None', '0', ''] else 'không_có'
        lo = lo if lo not in ['nan', 'None', '0', ''] else 'không_có'
        l1 = l1 if l1 not in ['nan', 'None', '0', ''] else 'không_có'
        l2 = l2 if l2 not in ['nan', 'None', '0', ''] else 'không_có'

        return d_sp, lo, l1, l2

    def trich_xuat_thong_tin(self, raw_text):
        raw_text = str(raw_text)
        if '#&' in raw_text:
            parts = raw_text.split('#&')
            parts = [p.strip() for p in parts if p.strip()]
            if parts:
                raw_text = max(parts, key=len)

        raw_text_lower = raw_text.lower()
        cong_suat = ""
        match_w = re.search(r'(\d+(?:\.\d+)?)\s*(w|watt|hp|kw|kva|v)', raw_text_lower)
        if match_w:
            cong_suat = match_w.group(0).strip()

        hang = ""
        danh_sach_hang = ['rạng đông', 'điện quang', 'panasonic', 'philips', 'lg', 'samsung', 'daikin', 'sony', 'toshiba', 'sharp', 'sino', 'cadivi']
        for h in danh_sach_hang:
            if h in raw_text_lower:
                hang = h.capitalize()
                break
        return pd.Series([hang, cong_suat, raw_text])

    def predict_with_threshold(self, text):
        if not self.is_multitask:
            inputs = self.tokenizer(text, padding="max_length", truncation=True, max_length=128, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self.model(**inputs)

            probabilities = F.softmax(outputs.logits, dim=-1)
            max_prob, pred_id = torch.max(probabilities, dim=-1)

            confidence = max_prob.item()
            label = self.label_encoder.inverse_transform([pred_id.item()])[0]

            status = "Tự động duyệt (AI)" if confidence >= self.THRESHOLD else "Cần kiểm tra"
            return pd.Series([label, round(confidence * 100, 2), status])

        # New multitask logic
        inputs = self.tokenizer(text, padding="max_length", truncation=True, max_length=self.MAX_LENGTH, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            logits_dong, logits_loai, logits_lop1, logits_lop2 = self.model(
                inputs['input_ids'], 
                inputs['attention_mask']
            )

        p_dong = F.softmax(logits_dong, dim=-1)
        p_loai = F.softmax(logits_loai, dim=-1)
        p_lop1 = F.softmax(logits_lop1, dim=-1)
        p_lop2 = F.softmax(logits_lop2, dim=-1)

        prob_dong, pred_dong = torch.max(p_dong, dim=-1)
        prob_loai, pred_loai = torch.max(p_loai, dim=-1)
        prob_lop1, pred_lop1 = torch.max(p_lop1, dim=-1)
        prob_lop2, pred_lop2 = torch.max(p_lop2, dim=-1)

        val_dong = prob_dong.item()
        val_loai = prob_loai.item()
        val_lop1 = prob_lop1.item()
        val_lop2 = prob_lop2.item()

        # Per-head thresholds: mỗi head phải vượt ngưỡng riêng
        all_pass = (
            val_dong >= self.THRESHOLD_DONG_SP and
            val_loai >= self.THRESHOLD_LOAI and
            val_lop1 >= self.THRESHOLD_LOP1 and
            val_lop2 >= self.THRESHOLD_LOP2
        )

        label_dong = self.encoders['dong_sp'].inverse_transform([pred_dong.item()])[0]
        label_loai = self.encoders['loai'].inverse_transform([pred_loai.item()])[0]
        label_lop1 = self.encoders['lop1'].inverse_transform([pred_lop1.item()])[0]
        label_lop2 = self.encoders['lop2'].inverse_transform([pred_lop2.item()])[0]

        label = f"{label_dong} | {label_loai} | {label_lop1} | {label_lop2}"
        # Confidence = head yếu nhất (min), dễ interpret hơn product
        confidence = min(val_dong, val_loai, val_lop1, val_lop2)
        status = "Tự động duyệt (AI)" if all_pass else "Cần kiểm tra"

        return pd.Series([label, round(confidence * 100, 2), status])

    def predict_dictionary(self, text):
        text_lower = self.clean_text_for_dict(text)
        best_mapping = None
        max_score = 0
        
        words = text_lower.split()
        text_words = set(words)
        candidate_indices = set()
        for w in words:
            if w in self.word_to_mappings:
                candidate_indices.update(self.word_to_mappings[w])

        for idx in candidate_indices:
            mapping = self.dict_mapping[idx]
            current_score = 0
            temp_text = text_lower

            for kw_obj in mapping['keywords']:
                if not kw_obj['word_set'].issubset(text_words):
                    continue
                
                pattern = kw_obj['pattern']
                
                if pattern.search(temp_text):
                    temp_text = pattern.sub(' ', temp_text)
                    current_score += kw_obj['score']

            if current_score > max_score:
                max_score = current_score
                best_mapping = mapping
            elif current_score == max_score and current_score > 0 and best_mapping is not None:
                current_loai = mapping['label_str'].split(' | ')[1].strip().upper() if ' | ' in mapping['label_str'] else ''
                best_loai = best_mapping['label_str'].split(' | ')[1].strip().upper() if ' | ' in best_mapping['label_str'] else ''
                if current_loai == 'NC' and best_loai == 'LK':
                    best_mapping = mapping

        if best_mapping is not None and max_score >= self.DICT_THRESHOLD:
            return pd.Series([best_mapping['label_str'], 100.0, f"Tự động duyệt (Từ điển - Điểm: {max_score})"])

        return pd.Series([None, 0.0, "Cần kiểm tra"])

    def predict_ai_batch(self, texts, batch_size=64):
        if not texts:
            return []
            
        start_total = time.time()
        self.model.eval()
        predictions = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]
            
            inputs = self.tokenizer(
                batch_texts, 
                padding=True, 
                truncation=True, 
                max_length=self.MAX_LENGTH, 
                return_tensors="pt"
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                if self.device.type == "cuda":
                    with torch.amp.autocast('cuda'):
                        if self.is_multitask:
                            logits_dong, logits_loai, logits_lop1, logits_lop2 = self.model(
                                inputs['input_ids'], 
                                inputs['attention_mask']
                            )
                        else:
                            outputs = self.model(**inputs)
                else:
                    if self.is_multitask:
                        logits_dong, logits_loai, logits_lop1, logits_lop2 = self.model(
                            inputs['input_ids'], 
                            inputs['attention_mask']
                        )
                    else:
                        outputs = self.model(**inputs)

            if self.is_multitask:
                p_dong = F.softmax(logits_dong, dim=-1)
                p_loai = F.softmax(logits_loai, dim=-1)
                p_lop1 = F.softmax(logits_lop1, dim=-1)
                p_lop2 = F.softmax(logits_lop2, dim=-1)

                prob_dong, pred_dong = torch.max(p_dong, dim=-1)
                prob_loai, pred_loai = torch.max(p_loai, dim=-1)
                prob_lop1, pred_lop1 = torch.max(p_lop1, dim=-1)
                prob_lop2, pred_lop2 = torch.max(p_lop2, dim=-1)

                p_dong_np = prob_dong.cpu().numpy()
                p_loai_np = prob_loai.cpu().numpy()
                p_lop1_np = prob_lop1.cpu().numpy()
                p_lop2_np = prob_lop2.cpu().numpy()

                id_dong_np = pred_dong.cpu().numpy()
                id_loai_np = pred_loai.cpu().numpy()
                id_lop1_np = pred_lop1.cpu().numpy()
                id_lop2_np = pred_lop2.cpu().numpy()

                lbl_dong = self.encoders['dong_sp'].inverse_transform(id_dong_np)
                lbl_loai = self.encoders['loai'].inverse_transform(id_loai_np)
                lbl_lop1 = self.encoders['lop1'].inverse_transform(id_lop1_np)
                lbl_lop2 = self.encoders['lop2'].inverse_transform(id_lop2_np)

                for idx in range(len(batch_texts)):
                    p_d = float(p_dong_np[idx])
                    p_l = float(p_loai_np[idx])
                    p_1 = float(p_lop1_np[idx])
                    p_2 = float(p_lop2_np[idx])
                    all_pass = (
                        p_d >= self.THRESHOLD_DONG_SP and
                        p_l >= self.THRESHOLD_LOAI and
                        p_1 >= self.THRESHOLD_LOP1 and
                        p_2 >= self.THRESHOLD_LOP2
                    )
                    confidence = min(p_d, p_l, p_1, p_2)
                    label = f"{lbl_dong[idx]} | {lbl_loai[idx]} | {lbl_lop1[idx]} | {lbl_lop2[idx]}"
                    status = "Tự động duyệt (AI)" if all_pass else "Cần kiểm tra"
                    predictions.append((label, round(confidence * 100, 2), status))
            else:
                probabilities = F.softmax(outputs.logits, dim=-1)
                max_probs, pred_ids = torch.max(probabilities, dim=-1)

                max_probs_numpy = max_probs.cpu().numpy()
                pred_ids_numpy = pred_ids.cpu().numpy()
                
                labels = self.label_encoder.inverse_transform(pred_ids_numpy)

                for prob, label in zip(max_probs_numpy, labels):
                    status = "Tự động duyệt (AI)" if prob >= self.THRESHOLD else "Cần kiểm tra"
                    predictions.append((label, round(float(prob) * 100, 2), status))
        
        total_time = time.time() - start_total
        print(f"INFO: AI Batch Inference of {len(texts)} rows took {total_time:.2f}s ({len(texts)/total_time:.2f} rows/s)")
                
        return predictions

    async def process_async(self, df, progress_callback=None, dict_paths=None, transaction_type=None):
        if progress_callback: await progress_callback("Mapping Data...")
        
        def initial_mapping():
            df_clean = pd.DataFrame()
            hs_col = None
            for cand in ['HS_Code', 'Mã HS', 'HS Code', 'Mã hàng', 'HS']:
                if cand in df.columns:
                    hs_col = cand
                    break
            if hs_col:
                df_clean['Mã HS'] = df[hs_col]
            else:
                df_clean['Mã HS'] = ''

            if 'Product' in df.columns:
                df_clean['Dòng SP'] = df['Product']
            else:
                df_clean['Dòng SP'] = ''

            is_nk = 'VN_Importer' in df.columns
            is_xk = 'VN_Exporter' in df.columns

            if is_xk:
                df_clean['Công ty XK'] = df['VN_Exporter'].fillna(df.get('VN_Exporter_EN', ''))
                df_clean['Công ty NK'] = df.get('Foreign_Importer', '')
                df_clean['Quốc gia'] = df.get('Destination_Country', '').fillna(df.get('Destination_Country_CN', ''))
                detected_type = 'Xuất khẩu'
            elif is_nk:
                df_clean['Công ty NK'] = df['VN_Importer'].fillna(df.get('VN_Importer_EN', ''))
                df_clean['Công ty XK'] = df.get('Foreign_Exporter', '')
                df_clean['Quốc gia'] = df.get('Origin_Country', '').fillna(df.get('Origin_Country_CN', ''))
                detected_type = 'Nhập khẩu'
            else:
                df_clean['Công ty XK'] = ''
                df_clean['Công ty NK'] = ''
                df_clean['Quốc gia'] = ''
                detected_type = ''
                
            # Use provided transaction_type or fallback to auto-detected
            final_type = transaction_type if transaction_type else detected_type
            df_clean['Loại giao dịch'] = final_type

            df_clean['Châu lục'] = df.get('Continent', '')
            df_clean['Incoterms'] = df.get('Incoterms', '')
            df_clean['Method_of_Payment'] = df.get('Method_of_Payment', '')
            df_clean['DVT'] = df.get('Unit_Qty', '')
            df_clean['Lượng'] = pd.to_numeric(
                df.get('Quantity', pd.Series(dtype=str)).astype(str).str.replace(r'[,$\s]', '', regex=True).str.replace(r'[a-zA-Z]+', '', regex=True),
                errors='coerce'
            )
            df_clean['Giá trị'] = pd.to_numeric(
                df.get('Total_Value_USD', pd.Series(dtype=str)).astype(str).str.replace(r'[,$\s]', '', regex=True).str.replace(r'[a-zA-Z]+', '', regex=True),
                errors='coerce'
            )
            df_clean['Đơn giá'] = pd.to_numeric(
                df.get('Unit_Price_USD', pd.Series(dtype=str)).astype(str).str.replace(r'[,$\s]', '', regex=True).str.replace(r'[a-zA-Z]+', '', regex=True),
                errors='coerce'
            )

            if 'Date' in df.columns:
                date_series = pd.to_datetime(df['Date'], errors='coerce')
                # Keep full date as ISO YYYY-MM-DD for BI tools
                df_clean['Ngày'] = date_series.dt.strftime('%Y-%m-%d')
                df_clean['Ngày'] = df_clean['Ngày'].fillna('')
                # Add separate integer month column for pivot analysis
                extracted_month = date_series.dt.month
                month_col = df.get('Month', pd.Series(dtype=str)).astype(str).str[-2:]
                month_col = pd.to_numeric(month_col, errors='coerce')
                df_clean['Tháng'] = extracted_month.fillna(month_col).astype('Int64')
            else:
                df_clean['Ngày'] = ''
                df_clean['Tháng'] = pd.array([pd.NA] * len(df), dtype='Int64')

            prod_col = None
            for cand in ['Detailed_Product', 'Actual_Detailed_Product_LL', 'Actual_Detail_Product', 'Actual_Detailed_Product', 'Tên hàng gốc', 'Description', 'Mô tả', 'Tên hàng', 'Product']:
                if cand in df.columns:
                    prod_col = cand
                    break
            
            detailed_product = df[prod_col].copy() if prod_col else pd.Series(dtype=str)
            for fallback_col in ['Detailed_Product', 'Actual_Detailed_Product_LL', 'Actual_Detail_Product', 'Actual_Detailed_Product', 'Tên hàng gốc', 'Detailed_Product_EN', 'Detailed_Product_CN']:
                if fallback_col in df.columns and fallback_col != prod_col:
                    detailed_product = detailed_product.fillna(df[fallback_col])
                    
            df_clean['Tên hàng raw'] = detailed_product
            return df_clean

        df_clean = await asyncio.to_thread(initial_mapping)

        if progress_callback: await progress_callback("Processing Data (Pass 1 - Parallel)...")
        
        if df_clean.empty:
            df_clean['Hãng'] = ''
            df_clean['Công suất'] = ''
            df_clean['Tên hàng'] = ''
            df_clean['input_for_ai'] = ''
            df_clean['Ket_Qua_Gop'] = ''
            df_clean['Độ Tự Tin (%)'] = 0.0
            df_clean['Trạng Thái'] = ''
        else:
            import multiprocessing
            from backend.core.worker import process_chunk
            
            total_rows = len(df_clean)
            num_cores = multiprocessing.cpu_count()
            chunk_size = max(5000, total_rows // (num_cores * 2))
            if chunk_size == 0: chunk_size = 5000
            
            loop = asyncio.get_running_loop()
            
            tasks = []
            for i in range(0, total_rows, chunk_size):
                chunk = df_clean[['Tên hàng raw', 'Mã HS']].iloc[i:i+chunk_size]
                chunk_data = (chunk, dict_paths)
                tasks.append(loop.run_in_executor(self.executor, process_chunk, chunk_data))
            
            if progress_callback: 
                await progress_callback(f"Processing Data... (processing {total_rows} rows concurrently)")
            
            results_list = await asyncio.gather(*tasks)

            processed_df = pd.concat(results_list)
            for col in processed_df.columns:
                df_clean[col] = processed_df[col]

        if progress_callback: await progress_callback("AI Inference (Pass 2)...")
        
        if not df_clean.empty:
            # Find rows that need AI fallback
            fallback_mask = df_clean['Ket_Qua_Gop'].isnull()
            fallback_indices = df_clean[fallback_mask].index.tolist()
            fallback_texts = df_clean.loc[fallback_mask, 'input_for_ai'].tolist()
            
            if fallback_texts:
                total_ai_rows = len(fallback_texts)
                # Optimized batch size for CPU sequential inference
                ai_batch_size = 64

                print(f"DEBUG: AI Inference on {total_ai_rows} rows.")
                
                ai_predictions = []
                for i in range(0, total_ai_rows, ai_batch_size):
                    batch_texts = fallback_texts[i:i+ai_batch_size]
                    
                    if progress_callback and (i % (ai_batch_size * 20) == 0 or i == 0):
                        await progress_callback(f"AI Inference... ({i}/{total_ai_rows} rows)")
                    
                    # Run batch inference in a thread to keep event loop responsive
                    batch_results = await asyncio.to_thread(self.predict_ai_batch, batch_texts, batch_size=ai_batch_size)
                    ai_predictions.extend(batch_results)
                
                # Merge AI predictions back into the main DataFrame
                for idx, (label, prob, status) in zip(fallback_indices, ai_predictions):
                    df_clean.at[idx, 'Ket_Qua_Gop'] = label
                    df_clean.at[idx, 'Độ Tự Tin (%)'] = prob
                    df_clean.at[idx, 'Trạng Thái'] = status

        def split_and_assign():
            temp_cols = df_clean['Ket_Qua_Gop'].str.split(r' \| ', expand=True)
            for i in range(5):
                if i not in temp_cols.columns:
                    temp_cols[i] = 'không_có'
            
            for idx in df_clean.index:
                d_sp, loai, lop1, lop2 = self._normalize_label(
                    temp_cols.at[idx, 0] if idx in temp_cols.index else 'không_có',
                    temp_cols.at[idx, 1] if idx in temp_cols.index else 'không_có',
                    temp_cols.at[idx, 2] if idx in temp_cols.index else 'không_có',
                    temp_cols.at[idx, 3] if idx in temp_cols.index else 'không_có'
                )
                df_clean.at[idx, 'Dòng SP'] = d_sp
                df_clean.at[idx, 'Loại'] = loai
                df_clean.at[idx, 'Lớp 1'] = lop1
                df_clean.at[idx, 'Lớp 2'] = lop2
            
            mask = (temp_cols[4] != 'không_có') & temp_cols[4].notna() & (temp_cols[4] != '')
            df_clean['Mã HS'] = np.where(mask, temp_cols[4], df_clean['Mã HS'])

            df_clean['MDSD'] = np.nan
            df_clean['Năm'] = np.nan
            
        await asyncio.to_thread(split_and_assign)

        if progress_callback: await progress_callback("Finalizing...")
        
        def finalize():
            df_final = df_clean.drop(columns=['input_for_ai', 'Ket_Qua_Gop', 'Tên hàng raw'], errors='ignore')
            mapped_cols_set = set(['HS_Code', 'Product', 'VN_Exporter', 'VN_Exporter_EN', 'Foreign_Importer', 'Destination_Country', 'Destination_Country_CN', 'Continent', 'Incoterms', 'Method_of_Payment', 'Unit_Qty', 'Quantity', 'Total_Value_USD', 'Unit_Price_USD', 'Date', 'Month', 'Detailed_Product', 'Detailed_Product_EN', 'Detailed_Product_CN', 'VN_Importer', 'VN_Importer_EN', 'Foreign_Exporter', 'Origin_Country', 'Origin_Country_CN', 'Actual_Detail_Product', 'Actual_Detailed_Product', 'Actual_Detailed_Product_LL'])
            for col in df.columns:
                if col not in mapped_cols_set and col not in df_final.columns:
                    df_final[col] = df[col]
            
            # BI-Ready: Rename English column headers to Vietnamese
            rename_map = {
                'Method_of_Payment': 'Phương thức thanh toán',
            }
            df_final = df_final.rename(columns=rename_map)
            
            # BI-Ready: Drop pandas duplicate suffix columns (e.g. "Công suất.1")
            suffix_cols = [c for c in df_final.columns if c.endswith('.1')]
            if suffix_cols:
                df_final = df_final.drop(columns=suffix_cols, errors='ignore')
            
            return df_final

        df_final = await asyncio.to_thread(finalize)
        return df_final

cleaner = None

def get_cleaner():
    global cleaner
    if cleaner is None:
        model_path = os.environ.get("MODEL_PATH", "/working")
        cleaner = DataCleaner(model_path)
    return cleaner
