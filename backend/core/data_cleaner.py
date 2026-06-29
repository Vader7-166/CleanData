import re
import pickle
import sqlite3
import pandas as pd

def clean_text_basic(text):
    if pd.isna(text): return ""
    text = str(text).lower()
    if '#&' in text:
        parts = [p.strip() for p in text.split('#&') if p.strip()]
        if parts: text = max(parts, key=len)
    text = re.sub(r'[^a-z0-9àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ\s]', ' ', text)
    return ' '.join(text.split()).strip()

import numpy as np
import os
import asyncio

class DataCleaner:
    def __init__(self, model_path):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.model_path = os.path.join(script_dir, "../storage/classifier_model.pkl")
        self.dict_path = os.path.join(script_dir, "../storage/dict_golden.csv")
        self.ensemble_models = None
        self.exact_match_cache = {}
        
        # Load Ground Truth Cache for exact matches
        try:
            db_path = os.path.join(os.path.dirname(__file__), '../storage/ground_truth.db')
            if os.path.exists(db_path):
                print(f"Loading Historical Cache from {db_path}...")
                conn = sqlite3.connect(db_path)
                df_gt = pd.read_sql('SELECT hs_code, clean_text, "Dòng SP", "Loại", "Lớp 1", "Lớp 2" FROM ground_truth', conn)
                for _, r in df_gt.iterrows():
                    key = (str(r['hs_code']).strip(), r['clean_text'])
                    self.exact_match_cache[key] = {
                        'Dòng SP': r['Dòng SP'],
                        'Loại': r['Loại'],
                        'Lớp 1': r['Lớp 1'],
                        'Lớp 2': r['Lớp 2']
                    }
                conn.close()
                print(f"Loaded {len(self.exact_match_cache)} exact match historical entries.")
        except Exception as e:
            print(f"Failed to load historical cache: {e}")
        self.dictionary = {}
        self.THRESHOLD = 0.85
        self.STOPWORDS = {"có", "bằng", "đèn", "hàng", "mới", "100", "hiệu", "dùng", "để", "sáng", "chiếu", "của", "và", "nhựa", "bộ", "c", "với", "các", "loại", "cho", "1", "2", "3", "0", "led", "sản", "xuất", "bảng", "chiếc", "cái", "unk", "gp", "pce", "w", "v", "kg", "pcs", "set", "thùng", "hộp", "bao", "gói", "bóng", "quang", "điện", "hoạt", "động", "ống", "nước", "thông", "minh", "kích", "thước", "màu", "sắc", "chất", "liệu", "sử", "dụng", "dẫn"}
        
        self.load_resources()

    def load_resources(self):
        print(f"Loading Supervised Dictionary from {self.dict_path}...")
        if os.path.exists(self.dict_path):
            try:
                df_dict = pd.read_csv(self.dict_path)
                for _, row in df_dict.iterrows():
                    hs = str(row['Mã HS']).replace('.0', '').strip()
                    keywords = [k.strip() for k in str(row['Keyword']).split(',')]
                    
                    if hs not in self.dictionary:
                        self.dictionary[hs] = []
                        
                    entry_words = set()
                    for kw in keywords:
                        entry_words.update(kw.split())
                    entry_sig = entry_words - self.STOPWORDS
                    
                    self.dictionary[hs].append({
                        'keywords': keywords,
                        'sig': entry_sig,
                        'dong_sp': row['Dòng SP'],
                        'loai': row['Loại'],
                        'lop1': row['Lớp 1'],
                        'lop2': row['Lớp 2']
                    })
            except Exception as e:
                print(f"Error loading dictionary: {e}")
        else:
            print("WARNING: Dictionary not found!")

        print(f"Loading Ensemble Classifier Models from {self.model_path}...")
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, 'rb') as f:
                    self.ensemble_models = pickle.load(f)
            except Exception as e:
                print(f"Error loading model: {e}")
        else:
            print("WARNING: Ensemble Classifier Model not found!")

    def clean_text_for_dict(self, text):
        if pd.isna(text): return ""
        text = str(text).lower()
        if '#&' in text:
            parts = text.split('#&')
            parts = [p.strip() for p in parts if p.strip()]
            if parts:
                text = max(parts, key=len)
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
        return hang, cong_suat, raw_text

    def predict_dictionary(self, text_lower, hs_code):
        if hs_code not in self.dictionary:
            return None
            
        padded_text = f" {text_lower} "
        best_match = None
        max_kw_len = 0
        
        # 1. Exact Phrase Match
        for entry in self.dictionary[hs_code]:
            for kw in entry['keywords']:
                kw_clean = kw.strip()
                if len(kw_clean) < 3: 
                    continue
                # Check if phrase is in text
                if f" {kw_clean} " in padded_text:
                    if len(kw_clean) > max_kw_len:
                        max_kw_len = len(kw_clean)
                        best_match = entry
                        
        if best_match:
            return best_match
            
        # 2. Fallback to Overlap Score
        max_score = 0
        text_words = set(text_lower.split())
        text_sig = text_words - self.STOPWORDS
        len_text_sig = len(text_sig)
        
        if len_text_sig == 0:
            return None
            
        for entry in self.dictionary[hs_code]:
            entry_sig = entry['sig']
            len_entry_sig = len(entry_sig)
            if len_entry_sig == 0:
                continue
                
            overlap = text_sig & entry_sig
            len_overlap = len(overlap)
            
            if len_overlap >= 1:
                overlap_len = sum(len(w) for w in overlap)
                overlap_ratio = len_overlap / min(len_text_sig, len_entry_sig)
                score = overlap_ratio * overlap_len
                
                if score > max_score:
                    max_score = score
                    best_match = entry
                    
        # Fuzzy threshold >= 0.5 for dictionary coverage
        if max_score >= 0.5:
            return best_match
            
        return None

    def _process_row_pass1(self, row):
        # Determine actual description column
        prod_col = None
        for cand in ['Detailed_Product', 'Actual_Detailed_Product_LL', 'Actual_Detail_Product', 'Actual_Detailed_Product', 'Tên hàng gốc', 'Description', 'Mô tả', 'Tên hàng', 'Product']:
            if cand in row.index and pd.notna(row[cand]) and str(row[cand]).strip() != '':
                prod_col = cand
                break
                
        raw_mo_ta = row[prod_col] if prod_col else ""
        hang, cong_suat, _ = self.trich_xuat_thong_tin(raw_mo_ta)
        
        # Get HS Code
        hs_col = None
        for cand in ['HS_Code', 'Mã HS', 'HS Code', 'Mã hàng', 'HS']:
            if cand in row.index and pd.notna(row[cand]):
                hs_col = cand
                break
        hs_code = str(row[hs_col]).replace('.0', '').strip() if hs_col else ""
        
        clean_mo_ta = self.clean_text_for_dict(raw_mo_ta)

        base_res = {
            'Tên hàng': raw_mo_ta,
            'Hãng': hang,
            'Công suất': cong_suat,
            'Dòng SP': '',
            'Loại': '',
            'Lớp 1': '',
            'Lớp 2': '',
            'Trạng Thái': '',
            'Mã HS': hs_code,
            '_needs_model': False,
            '_feature': clean_mo_ta
        }

        # 0. Exact Historical Match Check
        clean_desc = clean_text_basic(raw_mo_ta)
        cache_key = (hs_code, clean_desc)
        if cache_key in self.exact_match_cache:
            base_res.update(self.exact_match_cache[cache_key])
            base_res['Trạng Thái'] = 'Tự động duyệt (Lịch sử)'
            base_res['_needs_model'] = False
            return base_res

        # 1. Dictionary Match
        dict_res = self.predict_dictionary(clean_mo_ta, hs_code)
        if dict_res:
            base_res.update({
                'Dòng SP': dict_res['dong_sp'],
                'Loại': dict_res['loai'],
                'Lớp 1': dict_res['lop1'],
                'Lớp 2': dict_res['lop2'],
                'Trạng Thái': 'Tự động duyệt (Từ điển)'
            })
            return base_res
            
        # 2. Needs Model Match
        base_res['_needs_model'] = True
        return base_res

    async def process_async(self, df, progress_callback=None, dict_paths=None, transaction_type=None):
        if progress_callback: await progress_callback("Starting Fast CPU Inference Pipeline...")
        
        def process_all():
            results = []
            
            for i, row in df.iterrows():
                res = self._process_row_pass1(row)
                
                # If needs model, do it immediately for ensemble
                if res['_needs_model'] and self.ensemble_models:
                    hs_code = res['Mã HS']
                    feature = res['_feature']
                    if hs_code in self.ensemble_models:
                        model_info = self.ensemble_models[hs_code]
                        if model_info['type'] == 'single':
                            label = model_info['label']
                            parts = [p.strip() for p in label.split(' | ')]
                            res.update({
                                'Dòng SP': parts[0] if len(parts) > 0 else '',
                                'Loại': parts[1] if len(parts) > 1 else '',
                                'Lớp 1': parts[2] if len(parts) > 2 else '',
                                'Lớp 2': parts[3] if len(parts) > 3 else '',
                                'Trạng Thái': f'Tự động duyệt (AI Fallback)'
                            })
                        else:
                            try:
                                model = model_info['model']
                                probs = model.predict_proba([feature])
                                max_idx = np.argmax(probs[0])
                                conf = probs[0][max_idx]
                                label = model.classes_[max_idx]
                                
                                if conf >= self.THRESHOLD:
                                    parts = [p.strip() for p in label.split(' | ')]
                                    res.update({
                                        'Dòng SP': parts[0] if len(parts) > 0 else '',
                                        'Loại': parts[1] if len(parts) > 1 else '',
                                        'Lớp 1': parts[2] if len(parts) > 2 else '',
                                        'Lớp 2': parts[3] if len(parts) > 3 else '',
                                        'Trạng Thái': f'Tự động duyệt (AI {conf*100:.1f}%)'
                                    })
                                else:
                                    res['Trạng Thái'] = 'Cần Nghiệp Vụ'
                            except Exception as e:
                                res['Trạng Thái'] = 'Cần Nghiệp Vụ'
                    else:
                        res['Trạng Thái'] = 'Cần Nghiệp Vụ'
                elif res['_needs_model']:
                    res['Trạng Thái'] = 'Cần Nghiệp Vụ'
                    
                res.pop('_needs_model', None)
                res.pop('_feature', None)
                results.append(res)
                
            return pd.DataFrame(results)
            
        res_df = await asyncio.to_thread(process_all)
        
        if progress_callback: await progress_callback("Finalizing...")
        
        def finalize():
            # Merge with original df
            df_final = df.copy()
            for col in ['Tên hàng', 'Hãng', 'Công suất', 'Dòng SP', 'Loại', 'Lớp 1', 'Lớp 2', 'Trạng Thái', 'Mã HS']:
                if col in res_df.columns:
                    df_final[col] = res_df[col]
            
            # Map transaction types and basic info like the old script did
            is_nk = 'VN_Importer' in df_final.columns
            is_xk = 'VN_Exporter' in df_final.columns

            if is_xk:
                df_final['Công ty XK'] = df_final['VN_Exporter'].fillna(df_final.get('VN_Exporter_EN', ''))
                df_final['Công ty NK'] = df_final.get('Foreign_Importer', '')
                df_final['Quốc gia'] = df_final.get('Destination_Country', '').fillna(df_final.get('Destination_Country_CN', ''))
                detected_type = 'Xuất khẩu'
            elif is_nk:
                df_final['Công ty NK'] = df_final['VN_Importer'].fillna(df_final.get('VN_Importer_EN', ''))
                df_final['Công ty XK'] = df_final.get('Foreign_Exporter', '')
                df_final['Quốc gia'] = df_final.get('Origin_Country', '').fillna(df_final.get('Origin_Country_CN', ''))
                detected_type = 'Nhập khẩu'
            else:
                df_final['Công ty XK'] = ''
                df_final['Công ty NK'] = ''
                df_final['Quốc gia'] = ''
                detected_type = ''
                
            final_type = transaction_type if transaction_type else detected_type
            df_final['Loại giao dịch'] = final_type
            
            df_final['Châu lục'] = df_final.get('Continent', '')
            df_final['Incoterms'] = df_final.get('Incoterms', '')
            df_final['Phương thức thanh toán'] = df_final.get('Method_of_Payment', '')
            df_final['DVT'] = df_final.get('Unit_Qty', '')
            df_final['Lượng'] = pd.to_numeric(
                df_final.get('Quantity', pd.Series(dtype=str)).astype(str).str.replace(r'[,$\s]', '', regex=True).str.replace(r'[a-zA-Z]+', '', regex=True),
                errors='coerce'
            )
            df_final['Giá trị'] = pd.to_numeric(
                df_final.get('Total_Value_USD', pd.Series(dtype=str)).astype(str).str.replace(r'[,$\s]', '', regex=True).str.replace(r'[a-zA-Z]+', '', regex=True),
                errors='coerce'
            )
            df_final['Đơn giá'] = pd.to_numeric(
                df_final.get('Unit_Price_USD', pd.Series(dtype=str)).astype(str).str.replace(r'[,$\s]', '', regex=True).str.replace(r'[a-zA-Z]+', '', regex=True),
                errors='coerce'
            )

            if 'Date' in df_final.columns:
                date_series = pd.to_datetime(df_final['Date'], errors='coerce')
                df_final['Ngày'] = date_series.dt.strftime('%Y-%m-%d')
                df_final['Ngày'] = df_final['Ngày'].fillna('')
                extracted_month = date_series.dt.month
                month_col = df_final.get('Month', pd.Series(dtype=str)).astype(str).str[-2:]
                month_col = pd.to_numeric(month_col, errors='coerce')
                df_final['Tháng'] = extracted_month.fillna(month_col).astype('Int64')
            else:
                df_final['Ngày'] = ''
                df_final['Tháng'] = pd.array([pd.NA] * len(df_final), dtype='Int64')
            
            df_final['MDSD'] = np.nan
            df_final['Năm'] = np.nan
            df_final['Công suất.1'] = np.nan
            df_final['Loại 1'] = np.nan
            df_final['Loại 2'] = np.nan

            HQ_COLUMNS = [
                'Ngày', 'Mã HS', 'Công ty NK', 'Tên hàng', 'DVT', 'Lượng', 'Giá trị', 'Đơn giá',
                'Hãng', 'Dòng SP', 'Loại', 'Lớp 1', 'Lớp 2', 'Công suất', 'Quốc gia', 'Châu lục',
                'MDSD', 'Công ty XK', 'Incoterms', 'Method_of_Payment', 'Công suất.1', 'Loại 1', 'Loại 2', 'Năm',
                'Trạng Thái'
            ]
            
            for c in HQ_COLUMNS:
                if c not in df_final.columns:
                    df_final[c] = np.nan

            return df_final[HQ_COLUMNS]

        df_final = await asyncio.to_thread(finalize)
        return df_final

cleaner = None

def get_cleaner():
    global cleaner
    if cleaner is None:
        model_path = os.environ.get("MODEL_PATH", "/working")
        cleaner = DataCleaner(model_path)
    return cleaner
