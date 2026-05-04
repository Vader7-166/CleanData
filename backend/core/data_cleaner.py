import re
import pickle
import pandas as pd
import numpy as np
import torch
import torch.nn.functional as F
import os
import asyncio

class DataCleaner:
    def __init__(self, model_path, dict_path="dataset/dictv2.csv"):
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
        self.DICT_THRESHOLD = 15
        self.MAX_CONCURRENT_CHUNKS = 4
        self.HIGH_VALUE_KEYWORDS = [
            "năng lượng mặt trời", "nlmt", "bán nguyệt", "tuýp bán nguyệt", "âm trần", "đèn âm trần",
            "âm nước", "đèn âm nước", "mắt cáo", "rọi ray", "đèn rọi ray", "ống bơ", "ốp trần",
            "gắn tường", "đèn tường", "đội đầu", "đèn pin", "diệt côn trùng", "bắt muỗi",
            "ngoài trời", "cảnh quan", "sân vườn", "bảng hiệu", "soi bảng", "biển quảng cáo",
            "nhà xưởng", "nhà máy", "đánh cá", "câu mực", "bàn thờ", "trang trí",
            "thoát hiểm", "sự cố", "khẩn cấp", "panel", "đèn panel", "đèn chùm", "đèn thả",
            "dây led", "led cuộn", "thanh", "hồng ngoại", "cảm biến", "tuýp", "bulb", "tube",
            "bàn", "cực tím", "halogen", "cháy", "nổ", "dây", "uv", "hồng ngoại","phát quang",
            "ufo", "công nghiệp", "highbay", "lowbay", "flood", "pha", "downlight", "spotlight",
            "tracklight", "đường phố"
        ]
        self.JUNK_KEYWORDS = [
            "chiếu sáng", "mới", "100", "hàng mới 100", "hàng mới", "hàng",
            "chính hãng", "chi tiết", "bộ phận", "công suất",
            "kích thước", "điện áp", "chất liệu", "nhôm", "nhựa", "hoạt động",
            "nsx", "co", "ltd", "industrial", "factory", "zhejiang", "zhongshan",
            "mới 100", "model", "dạng", "loại", "có", "led", "đèn led", "đèn"
        ]

        print("Loading Dictionary...")
        self.dict_mapping = self._load_dict(dict_path)

    def _load_dict(self, dict_path):
        if not os.path.exists(dict_path):
            print(f"Warning: Dictionary file not found at {dict_path}")
            return []
        try:
            df_dict = pd.read_csv(dict_path, encoding='utf-8-sig')
        except:
            df_dict = pd.read_csv(dict_path, encoding='latin1')

        dict_mapping = []
        self.word_to_mappings = {}
        mapping_idx = 0

        for _, row in df_dict.iterrows():
            kw_str = str(row.get('Keyword', '')).lower()
            keywords = [self.clean_text_for_dict(k) for k in kw_str.split(',') if self.clean_text_for_dict(k) != '']
            keywords.sort(key=lambda x: len(x), reverse=True)

            d_sp = str(row.get('Dòng SP', 'không_có'))
            d_sp = d_sp if d_sp not in ['nan', 'None', '0', ''] else 'không_có'
            loai = str(row.get('Loại', 'không_có'))
            loai = loai if loai not in ['nan', 'None', '0', ''] else 'không_có'
            lop_1 = str(row.get('Lớp 1', 'không_có'))
            lop_1 = lop_1 if lop_1 not in ['nan', 'None', '0', ''] else 'không_có'
            lop_2 = str(row.get('Lớp 2', 'không_có'))
            lop_2 = lop_2 if lop_2 not in ['nan', 'None', '0', ''] else 'không_có'
            ma_hs = str(row.get('Mã HS', 'không_có'))
            ma_hs = ma_hs if ma_hs not in ['nan', 'None', '0', ''] else 'không_có'

            # Pre-compile regular expressions for efficiency and precalculate scores
            compiled_keywords = []
            for kw in keywords:
                score = len(kw.split())
                if any(hv in kw for hv in self.HIGH_VALUE_KEYWORDS):
                    score = 20
                elif any(kw == jk for jk in self.JUNK_KEYWORDS):
                    score = 0
                
                compiled_keywords.append({
                    "text": kw,
                    "pattern": re.compile(r'\b' + re.escape(kw) + r'\b'),
                    "score": score,
                    "word_set": set(kw.split())
                })
                
                # Build inverted index
                for word in kw.split():
                    if word not in self.word_to_mappings:
                        self.word_to_mappings[word] = set()
                    self.word_to_mappings[word].add(mapping_idx)

            dict_mapping.append({
                'keywords': compiled_keywords,
                'label_str': f"{d_sp} | {loai} | {lop_1} | {lop_2} | {ma_hs}"
            })
            mapping_idx += 1

        return dict_mapping

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

    async def process_async(self, df, progress_callback=None):
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

        if progress_callback: await progress_callback("Extracting Information...")
        
        def extract_info():
            if df_clean.empty:
                df_clean['Hãng'] = ''
                df_clean['Công suất'] = ''
                df_clean['Tên hàng'] = ''
            else:
                df_clean[['Hãng', 'Công suất', 'Tên hàng']] = df_clean['Tên hàng raw'].apply(self.trich_xuat_thong_tin)
            
            df_clean['input_for_ai'] = "Hãng: " + df_clean['Hãng'].astype(str) + " - Công suất: " + df_clean['Công suất'].astype(str) + " - Sản phẩm: " + df_clean['Tên hàng'].astype(str).str.lower()
            df_clean['input_for_ai'] = df_clean['input_for_ai'].apply(self.clean_text_for_dict)
            
        await asyncio.to_thread(extract_info)

        if progress_callback: await progress_callback("Dictionary Matching (Pass 1)...")
        
        if df_clean.empty:
            df_clean['Ket_Qua_Gop'] = ''
            df_clean['Độ Tự Tin (%)'] = 0.0
            df_clean['Trạng Thái'] = ''
        else:
            total_rows = len(df_clean)
            chunk_size = 2000
            
            import concurrent.futures
            loop = asyncio.get_running_loop()
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                tasks = []
                for i in range(0, total_rows, chunk_size):
                    chunk = df_clean['input_for_ai'].iloc[i:i+chunk_size]
                    
                    def process_dict_chunk(c=chunk):
                        return c.apply(self.predict_dictionary)
                    
                    tasks.append(loop.run_in_executor(executor, process_dict_chunk))
                
                if progress_callback: 
                    await progress_callback(f"Dictionary Matching... (processing {total_rows} rows concurrently)")
                
                results_list = await asyncio.gather(*tasks)

            df_clean[['Ket_Qua_Gop', 'Độ Tự Tin (%)', 'Trạng Thái']] = pd.concat(results_list)

        if progress_callback: await progress_callback("AI Inference (Pass 2)...")
        
        if not df_clean.empty:
            # Find rows that need AI fallback
            fallback_mask = df_clean['Ket_Qua_Gop'].isnull()
            fallback_indices = df_clean[fallback_mask].index.tolist()
            fallback_texts = df_clean.loc[fallback_mask, 'input_for_ai'].tolist()
            
            if fallback_texts:
                total_ai_rows = len(fallback_texts)
                ai_batch_size = 64
                
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
        # Ensure dict_path is correct regardless of where uvicorn is run from
        default_dict_path = os.path.join(os.path.dirname(__file__), "../../dataset/dictv2.csv")
        if not os.path.exists(default_dict_path):
            default_dict_path = "dataset/dictv2.csv"

        dict_path = os.environ.get("DICT_PATH", default_dict_path)
        cleaner = DataCleaner(model_path, dict_path)
    return cleaner
