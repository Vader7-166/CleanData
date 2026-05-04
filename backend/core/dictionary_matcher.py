import ahocorasick
import re
import pandas as pd
import os

class DictionaryMatcher:
    def __init__(self, dict_path="dataset/dictv2.csv", threshold=15):
        self.dict_path = dict_path
        self.DICT_THRESHOLD = threshold
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
        self.dict_mapping = []
        self.automaton = ahocorasick.Automaton()
        self._load_dict()

    def clean_text_for_dict(self, text):
        text = str(text).lower()
        text = re.sub(r'[^a-z0-9àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ\s]', ' ', text)
        return ' '.join(text.split()).strip()

    def _load_dict(self):
        if not os.path.exists(self.dict_path):
            print(f"Warning: Dictionary file not found at {self.dict_path}")
            return
            
        try:
            df_dict = pd.read_csv(self.dict_path)
        except UnicodeDecodeError:
            df_dict = pd.read_csv(self.dict_path, encoding='latin1')

        mapping_idx = 0
        for _, row in df_dict.iterrows():
            kw_str = str(row.get('Keyword', '')).lower()
            keywords = [self.clean_text_for_dict(k) for k in kw_str.split(',') if self.clean_text_for_dict(k) != '']
            
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

            label_str = f"{d_sp} | {loai} | {lop_1} | {lop_2} | {ma_hs}"
            
            self.dict_mapping.append({
                'label_str': label_str,
                'idx': mapping_idx
            })

            # Add to Aho-Corasick
            for kw in keywords:
                # Add word boundary padding to ensure we match whole words
                padded_kw = f" {kw} "
                
                score = len(kw.split())
                if any(hv in kw for hv in self.HIGH_VALUE_KEYWORDS):
                    score = 20
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
