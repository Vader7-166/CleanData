import re
import pickle
import pandas as pd
import numpy as np
import torch
import torch.nn.functional as F
import os
import asyncio

class DataCleaner:
    def __init__(self, model_path):
        self.model_path = model_path
        print(f"Loading Tokenizer from {model_path}...")
        try:
            from transformers import RobertaTokenizer
            self.tokenizer = RobertaTokenizer.from_pretrained(model_path, use_fast=False)
        except Exception as e:
            from transformers import AutoTokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=False)
        
        print("Loading Model...")
        from transformers import AutoModelForSequenceClassification
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.model.eval()

        with open(f"{model_path}/label_encoder.pkl", "rb") as f:
            self.label_encoder = pickle.load(f)

        self.THRESHOLD = 0.85
        self.MAX_CONCURRENT_CHUNKS = 4

    def clean_text_for_dict(self, text):
        text = str(text).lower()
        text = re.sub(r'[^a-z0-9àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ\s]', ' ', text)
        return ' '.join(text.split()).strip()

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

    def predict_ai_batch(self, texts, batch_size=32):
        if not texts:
            return []
            
        self.model.eval()
        predictions = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]
            inputs = self.tokenizer(batch_texts, padding=True, truncation=True, max_length=128, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                with torch.autocast('cuda') if torch.cuda.is_available() else torch.autocast('cpu', enabled=False):
                    outputs = self.model(**inputs)

            probabilities = F.softmax(outputs.logits, dim=-1)
            max_probs, pred_ids = torch.max(probabilities, dim=-1)

            for prob, pred_id in zip(max_probs.cpu().numpy(), pred_ids.cpu().numpy()):
                label = self.label_encoder.inverse_transform([pred_id])[0]
                status = "Tự động duyệt (AI)" if prob >= self.THRESHOLD else "Cần kiểm tra"
                predictions.append((label, round(float(prob) * 100, 2), status))
                
        return predictions

    async def process_async(self, df, progress_callback=None, dict_path=None):
        if progress_callback: await progress_callback("Mapping Data...")
        
        def initial_mapping():
            df_clean = pd.DataFrame()
            if 'HS_Code' in df.columns:
                df_clean['Mã HS'] = df['HS_Code']
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
            elif is_nk:
                df_clean['Công ty NK'] = df['VN_Importer'].fillna(df.get('VN_Importer_EN', ''))
                df_clean['Công ty XK'] = df.get('Foreign_Exporter', '')
                df_clean['Quốc gia'] = df.get('Origin_Country', '').fillna(df.get('Origin_Country_CN', ''))
            else:
                df_clean['Công ty XK'] = ''
                df_clean['Công ty NK'] = ''
                df_clean['Quốc gia'] = ''

            df_clean['Châu lục'] = df.get('Continent', '')
            df_clean['Incoterms'] = df.get('Incoterms', '')
            df_clean['Method_of_Payment'] = df.get('Method_of_Payment', '')
            df_clean['DVT'] = df.get('Unit_Qty', '')
            df_clean['Lượng'] = df.get('Quantity', '')
            df_clean['Giá trị'] = df.get('Total_Value_USD', '')
            df_clean['Đơn giá'] = df.get('Unit_Price_USD', '')

            if 'Date' in df.columns:
                date_series = pd.to_datetime(df['Date'], errors='coerce')
                extracted_month = date_series.dt.month.astype(str)
                month_col = df.get('Month', pd.Series(dtype=str)).astype(str).str[-2:]
                month_col = month_col.replace({'nan': np.nan, '': np.nan})
                df_clean['Ngày'] = extracted_month.fillna(month_col)
                df_clean['Ngày'] = pd.to_numeric(df_clean['Ngày'], errors='coerce').astype('Int64')
                df_clean['Ngày'] = df_clean['Ngày'].apply(lambda x: f"Tháng {x}" if pd.notna(x) else '')
            else:
                df_clean['Ngày'] = ''

            detailed_product = df.get('Detailed_Product', pd.Series(dtype=str))
            if 'Detailed_Product_EN' in df.columns:
                detailed_product = detailed_product.fillna(df['Detailed_Product_EN'])
            if 'Detailed_Product_CN' in df.columns:
                detailed_product = detailed_product.fillna(df['Detailed_Product_CN'])
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
            import concurrent.futures
            import multiprocessing
            from backend.core.worker import init_worker, process_chunk
            
            total_rows = len(df_clean)
            num_cores = multiprocessing.cpu_count()
            chunk_size = max(5000, total_rows // (num_cores * 2))
            if chunk_size == 0: chunk_size = 5000
            
            loop = asyncio.get_running_loop()
            
            with concurrent.futures.ProcessPoolExecutor(max_workers=num_cores, initializer=init_worker, initargs=(dict_path,)) as executor:
                tasks = []
                for i in range(0, total_rows, chunk_size):
                    chunk = df_clean[['Tên hàng raw']].iloc[i:i+chunk_size]
                    tasks.append(loop.run_in_executor(executor, process_chunk, chunk))
                
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
                ai_batch_size = 128
                
                if progress_callback:
                    await progress_callback(f"AI Inference... (processing {total_ai_rows} rows concurrently)")
                
                sem = asyncio.Semaphore(self.MAX_CONCURRENT_CHUNKS)
                
                async def run_ai_chunk(texts):
                    async with sem:
                        def process_ai_chunk(batch=texts):
                            return self.predict_ai_batch(batch, batch_size=ai_batch_size)
                        return await asyncio.to_thread(process_ai_chunk)

                tasks = []
                for i in range(0, total_ai_rows, ai_batch_size):
                    batch_texts = fallback_texts[i:i+ai_batch_size]
                    tasks.append(run_ai_chunk(batch_texts))
                
                ai_chunk_results = await asyncio.gather(*tasks)
                
                ai_predictions = []
                for batch_results in ai_chunk_results:
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
                    
            df_clean['Dòng SP'] = temp_cols[0]
            df_clean['Loại'] = temp_cols[1]
            df_clean['Lớp 1'] = temp_cols[2]
            df_clean['Lớp 2'] = temp_cols[3]
            
            mask = (temp_cols[4] != 'không_có') & temp_cols[4].notna() & (temp_cols[4] != '')
            df_clean['Mã HS'] = np.where(mask, temp_cols[4], df_clean['Mã HS'])

            df_clean['MDSD'] = np.nan
            df_clean['Năm'] = np.nan
            
        await asyncio.to_thread(split_and_assign)

        if progress_callback: await progress_callback("Finalizing...")
        
        def finalize():
            df_final = df_clean.drop(columns=['input_for_ai', 'Ket_Qua_Gop', 'Tên hàng raw'], errors='ignore')
            mapped_cols_set = set(['HS_Code', 'Product', 'VN_Exporter', 'VN_Exporter_EN', 'Foreign_Importer', 'Destination_Country', 'Destination_Country_CN', 'Continent', 'Incoterms', 'Method_of_Payment', 'Unit_Qty', 'Quantity', 'Total_Value_USD', 'Unit_Price_USD', 'Date', 'Month', 'Detailed_Product', 'Detailed_Product_EN', 'Detailed_Product_CN', 'VN_Importer', 'VN_Importer_EN', 'Foreign_Exporter', 'Origin_Country', 'Origin_Country_CN'])
            for col in df.columns:
                if col not in mapped_cols_set and col not in df_final.columns:
                    df_final[col] = df[col]
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
