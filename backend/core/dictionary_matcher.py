import ahocorasick
import re
import json
import pandas as pd
import os

class DictionaryMatcher:
    def __init__(self, dict_paths=None, threshold=5):
        if not dict_paths:
            dict_paths = []
        self.dict_paths = dict_paths if isinstance(dict_paths, list) else [dict_paths]
        self.DICT_THRESHOLD = threshold
        self._load_label_standard()
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
            "mới 100", "model", "dạng", "loại"
        ]
        self.dict_mapping = []
        self.automaton = ahocorasick.Automaton()
        self._load_dict()

    def clean_text_for_dict(self, text):
        text = str(text).lower()
        text = re.sub(r'[^a-z0-9àáạảãâầấậẩẫăằắẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ\s]', ' ', text)
        return ' '.join(text.split()).strip()

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
        loai = str(loai).strip()
        lop_1 = str(lop1).strip()
        lop_2 = str(lop2).strip()

        d_sp = self._dong_sp_aliases.get(d_sp, d_sp)
        loai = self._loai_aliases.get(loai, loai)
        lop_1 = self._lop1_aliases.get(lop_1, lop_1.lower())
        lop_2 = self._lop2_aliases.get(lop_2, lop_2.lower())

        for val in [d_sp, loai, lop_1, lop_2]:
            if val in ['', 'nan', 'None', '0']:
                val = 'không_có'

        d_sp = d_sp if d_sp not in ['nan', 'None', '0', ''] else 'không_có'
        loai = loai if loai not in ['nan', 'None', '0', ''] else 'không_có'
        lop_1 = lop_1 if lop_1 not in ['nan', 'None', '0', ''] else 'không_có'
        lop_2 = lop_2 if lop_2 not in ['nan', 'None', '0', ''] else 'không_có'

        return d_sp, loai, lop_1, lop_2

    def _load_dict(self):
        mapping_idx = 0
        for path in self.dict_paths:
            if not os.path.exists(path):
                print(f"Warning: Dictionary file not found at {path}")
                continue
                
            try:
                df_dict = pd.read_csv(path, encoding='utf-8-sig')
            except Exception as e:
                print(f"Notice: Failed to load dictionary with utf-8-sig, trying latin1. Error: {e}")
                try:
                    df_dict = pd.read_csv(path, encoding='latin1')
                except Exception as e2:
                    print(f"Error: Could not load dictionary file {path}. Error: {e2}")
                    continue

            mandatory_cols = ['Keyword', 'Dòng SP', 'Loại', 'Lớp 1', 'Lớp 2', 'Mã HS']
            missing_cols = [col for col in mandatory_cols if col not in df_dict.columns]
            if missing_cols:
                print(f"Error: Dictionary file is missing mandatory columns: {missing_cols}")
                for col in missing_cols:
                    df_dict[col] = 'không_có'

        for _, row in df_dict.iterrows():
            kw_str = str(row.get('Keyword', '')).lower()
            keywords = [self.clean_text_for_dict(k) for k in kw_str.split(',') if self.clean_text_for_dict(k) != '']
            
            d_sp, loai, lop_1, lop_2 = self._normalize_label(
                row.get('Dòng SP', 'không_có'),
                row.get('Loại', 'không_có'),
                row.get('Lớp 1', 'không_có'),
                row.get('Lớp 2', 'không_có')
            )
            ma_hs = str(row.get('Mã HS', 'không_có'))
            ma_hs = ma_hs if ma_hs not in ['nan', 'None', '0', ''] else 'không_có'

            label_str = f"{d_sp} | {loai} | {lop_1} | {lop_2} | {ma_hs}"
            
            self.dict_mapping.append({
                'label_str': label_str,
                'idx': mapping_idx
            })

            # Add to Aho-Corasick
            for kw in keywords:
                # Add word boundary padding to ensure we match whole words
                padded_kw = f" {kw} "
                
                # Dynamic scoring: longer phrases are exponentially more valuable
                # 1 word = 1 pt, 2 words = 4 pts, 3 words = 9 pts
                words = kw.split()
                score = len(words) ** 2
                
                if any(hv in kw for hv in self.HIGH_VALUE_KEYWORDS):
                    score = 25
                elif any(kw == jk for jk in self.JUNK_KEYWORDS):
                    score = 0
                
                # Payload: mapping_idx, kw length, score, kw string
                self.automaton.add_word(padded_kw, (mapping_idx, len(kw), score, kw))
            
            mapping_idx += 1
            
        self.automaton.make_automaton()

    def predict(self, text):
        text_lower = self.clean_text_for_dict(text)
        padded_text = f" {text_lower} "
        
        matches = []
        for end_idx, payload in self.automaton.iter(padded_text):
            mapping_idx, kw_len, score, kw = payload
            start_idx = end_idx - (kw_len + 2) + 1
            word_start = start_idx + 1
            word_end = end_idx - 1
            matches.append((word_start, word_end, mapping_idx, score, kw))
            
        if not matches:
            return pd.Series([None, 0.0, "Cần kiểm tra"])
            
        # Sort matches by length descending, then start_idx ascending
        matches.sort(key=lambda x: (x[1] - x[0], -x[0]), reverse=True)
        
        scores_by_mapping = {}
        consumed_intervals = []
        
        def is_overlapping(start, end):
            for cs, ce in consumed_intervals:
                if max(start, cs) <= min(end, ce):
                    return True
            return False

        for start_idx, end_idx, mapping_idx, score, kw in matches:
            if not is_overlapping(start_idx, end_idx):
                consumed_intervals.append((start_idx, end_idx))
                scores_by_mapping[mapping_idx] = scores_by_mapping.get(mapping_idx, 0) + score
                
        if not scores_by_mapping:
            return pd.Series([None, 0.0, "Cần kiểm tra"])
            
        max_score = 0
        best_mapping_idx = None
        
        for mapping_idx, current_score in scores_by_mapping.items():
            if current_score > max_score:
                max_score = current_score
                best_mapping_idx = mapping_idx
            elif current_score == max_score and current_score > 0 and best_mapping_idx is not None:
                mapping = self.dict_mapping[mapping_idx]
                best_mapping = self.dict_mapping[best_mapping_idx]
                current_loai = mapping['label_str'].split(' | ')[1].strip().upper() if ' | ' in mapping['label_str'] else ''
                best_loai = best_mapping['label_str'].split(' | ')[1].strip().upper() if ' | ' in best_mapping['label_str'] else ''
                if current_loai == 'NC' and best_loai == 'LK':
                    best_mapping_idx = mapping_idx

        if best_mapping_idx is not None and max_score >= self.DICT_THRESHOLD:
            return pd.Series([self.dict_mapping[best_mapping_idx]['label_str'], 100.0, f"Tự động duyệt (Từ điển - Điểm: {max_score})"])

        return pd.Series([None, 0.0, "Cần kiểm tra"])
