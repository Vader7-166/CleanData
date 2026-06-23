import ahocorasick
import re
import json
import pandas as pd
import os
import numpy as np

class DictionaryMatcher:
    _sbert_model = None

    def __init__(self, dict_paths=None, threshold=5, semantic_threshold=0.55):
        if not dict_paths:
            dict_paths = []
        self.dict_paths = dict_paths if isinstance(dict_paths, list) else [dict_paths]
        self.DICT_THRESHOLD = threshold
        self.SEMANTIC_THRESHOLD = semantic_threshold
        self._load_label_standard()
        self.HIGH_VALUE_KEYWORDS = [
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
        self.hs_prefix_to_idx = {}
        self.all_indices = set()
        self.dict_embeddings = None
        self.dict_keyword_texts = []
        self._load_dict()

    def _load_sbert(self):
        if DictionaryMatcher._sbert_model is not None:
            return True
        try:
            from sentence_transformers import SentenceTransformer
            model_name = "keepitreal/vietnamese-sbert"
            print(f"INFO: Loading SBERT model for semantic fallback: {model_name}...")
            DictionaryMatcher._sbert_model = SentenceTransformer(model_name)
            print(f"INFO: SBERT model loaded successfully.")
            return True
        except Exception as e:
            print(f"WARNING: Could not load SBERT model: {e}")
            print(f"WARNING: Semantic dictionary matching unavailable.")
            DictionaryMatcher._sbert_model = False
            return False

    def _build_dict_semantic_profiles(self):
        if self.dict_embeddings is not None:
            return
        if not self._load_sbert():
            self.dict_embeddings = False
            return
        print(f"INFO: Computing embeddings for {len(self.dict_mapping)} dict entries...")
        profiles = []
        indices = []
        for idx, entry in enumerate(self.dict_mapping):
            kws = entry.get('keywords', [])
            if kws:
                profile = ' '.join(kws)
            else:
                parts = entry.get('label_str', '').split(' | ')
                label_parts = [p for p in parts if p.lower() != 'không_có' and len(p) > 1]
                profile = ' '.join(label_parts) if label_parts else entry.get('label_str', '')
            profiles.append(profile)
            indices.append(idx)
            self.dict_keyword_texts.append(profile)
        try:
            embs = DictionaryMatcher._sbert_model.encode(profiles, show_progress_bar=False, normalize_embeddings=True)
            self.dict_embeddings = {}
            for idx, emb in zip(indices, embs):
                self.dict_embeddings[idx] = emb
            print(f"INFO: Computed embeddings for {len(self.dict_embeddings)} dict entries.")
        except Exception as e:
            print(f"WARNING: Failed to compute dict embeddings: {e}")
            self.dict_embeddings = False

    def _semantic_predict(self, text, allowed_indices):
        if self.dict_embeddings is None:
            self._build_dict_semantic_profiles()
        if self.dict_embeddings is False:
            return None, 0.0
        try:
            emb = DictionaryMatcher._sbert_model.encode([text], normalize_embeddings=True)[0]
        except Exception as e:
            return None, 0.0
        best_idx = None
        best_sim = -1.0
        for idx in allowed_indices:
            if idx not in self.dict_embeddings:
                continue
            sim = float(emb @ self.dict_embeddings[idx])
            if sim > best_sim:
                best_sim = sim
                best_idx = idx
        if best_idx is not None and best_sim >= self.SEMANTIC_THRESHOLD:
            return best_idx, best_sim
        return None, best_sim

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

    def _extract_hs_prefix(self, ma_hs):
        cleaned = re.sub(r'\D', '', str(ma_hs))
        if len(cleaned) >= 4:
            return cleaned[:4]
        return None

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

                so_luong_sp = 0
                raw_sl = row.get('Số lượng SP', 0)
                try:
                    so_luong_sp = int(float(str(raw_sl)))
                except (ValueError, TypeError):
                    so_luong_sp = 0

                label_str = f"{d_sp} | {loai} | {lop_1} | {lop_2} | {ma_hs}"

                hs_prefix = self._extract_hs_prefix(ma_hs)
                
                self.dict_mapping.append({
                    'label_str': label_str,
                    'idx': mapping_idx,
                    'dong_sp': d_sp,
                    'loai': loai,
                    'lop_1': lop_1,
                    'lop_2': lop_2,
                    'ma_hs': ma_hs,
                    'hs_prefix': hs_prefix,
                    'so_luong_sp': so_luong_sp,
                    'keywords': keywords,
                })

                if hs_prefix:
                    if hs_prefix not in self.hs_prefix_to_idx:
                        self.hs_prefix_to_idx[hs_prefix] = set()
                    self.hs_prefix_to_idx[hs_prefix].add(mapping_idx)

                self.all_indices.add(mapping_idx)

                for kw in keywords:
                    padded_kw = f" {kw} "
                    
                    words = kw.split()
                    score = len(words) ** 2
                    
                    if any(hv in kw for hv in self.HIGH_VALUE_KEYWORDS):
                        score = 25
                    elif any(kw == jk for jk in self.JUNK_KEYWORDS):
                        score = 0
                    
                    self.automaton.add_word(padded_kw, (mapping_idx, len(kw), score, kw))
                
                mapping_idx += 1
            
        self.automaton.make_automaton()

    def _get_allowed_indices(self, hs_code):
        if not hs_code or str(hs_code).strip() == '':
            return self.all_indices

        cleaned = re.sub(r'\D', '', str(hs_code))
        if len(cleaned) < 4:
            return self.all_indices

        prefix = cleaned[:4]
        allowed = self.hs_prefix_to_idx.get(prefix, set())
        if not allowed:
            return self.all_indices

        return allowed

    def predict(self, text, hs_code=None):
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
            allowed = self._get_allowed_indices(hs_code)
            sem_idx, sem_sim = self._semantic_predict(text_lower, allowed)
            if sem_idx is not None:
                return pd.Series([self.dict_mapping[sem_idx]['label_str'],
                                  round(sem_sim * 100, 2),
                                  f"Tự động duyệt (Ngữ nghĩa - Độ tương đồng: {sem_sim:.2f})"])
            return pd.Series([None, 0.0, "Cần kiểm tra"])
            
        matches.sort(key=lambda x: (x[1] - x[0], -x[0]), reverse=True)
        
        allowed_indices = self._get_allowed_indices(hs_code)
        
        scores_by_mapping = {}
        consumed_intervals = []
        
        def is_overlapping(start, end):
            for cs, ce in consumed_intervals:
                if max(start, cs) <= min(end, ce):
                    return True
            return False

        for start_idx, end_idx, mapping_idx, score, kw in matches:
            if mapping_idx not in allowed_indices:
                continue
            if not is_overlapping(start_idx, end_idx):
                consumed_intervals.append((start_idx, end_idx))
                scores_by_mapping[mapping_idx] = scores_by_mapping.get(mapping_idx, 0) + score
                
        if not scores_by_mapping:
            sem_idx, sem_sim = self._semantic_predict(text_lower, allowed_indices)
            if sem_idx is not None:
                return pd.Series([self.dict_mapping[sem_idx]['label_str'],
                                  round(sem_sim * 100, 2),
                                  f"Tự động duyệt (Ngữ nghĩa - Độ tương đồng: {sem_sim:.2f})"])
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

        sem_idx, sem_sim = self._semantic_predict(text_lower, allowed_indices)
        if sem_idx is not None:
            return pd.Series([self.dict_mapping[sem_idx]['label_str'],
                              round(sem_sim * 100, 2),
                              f"Tự động duyệt (Ngữ nghĩa - Độ tương đồng: {sem_sim:.2f})"])

        return pd.Series([None, 0.0, "Cần kiểm tra"])

    def get_best_match_detail(self, text, hs_code=None):
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
            return None
            
        matches.sort(key=lambda x: (x[1] - x[0], -x[0]), reverse=True)
        
        allowed_indices = self._get_allowed_indices(hs_code)
        
        scores_by_mapping = {}
        consumed_intervals = []
        
        def is_overlapping(start, end):
            for cs, ce in consumed_intervals:
                if max(start, cs) <= min(end, ce):
                    return True
            return False

        for start_idx, end_idx, mapping_idx, score, kw in matches:
            if mapping_idx not in allowed_indices:
                continue
            if not is_overlapping(start_idx, end_idx):
                consumed_intervals.append((start_idx, end_idx))
                scores_by_mapping[mapping_idx] = scores_by_mapping.get(mapping_idx, 0) + score
                
        if not scores_by_mapping:
            return None
            
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
            return {
                'mapping': self.dict_mapping[best_mapping_idx],
                'score': max_score,
            }

        return None

    def predict_batch(self, texts, hs_codes=None, batch_size=256, progress_callback=None):
        n = len(texts)
        if hs_codes is None:
            hs_codes = [None] * n
        elif len(hs_codes) != n:
            hs_codes = [hs_codes[0]] * n

        results = [None] * n
        ac_clean = [self.clean_text_for_dict(t) for t in texts]
        needs_sem = []
        needs_sem_idx = []

        for idx in range(n):
            text_lower = ac_clean[idx]
            padded_text = f" {text_lower} "
            hs = hs_codes[idx]

            raw_matches = list(self.automaton.iter(padded_text))
            if not raw_matches:
                needs_sem.append(text_lower)
                needs_sem_idx.append(idx)
                continue

            matches = []
            for end_idx, payload in raw_matches:
                mapping_idx, kw_len, score, kw = payload
                start_idx = end_idx - (kw_len + 2) + 1
                word_start = start_idx + 1
                word_end = end_idx - 1
                matches.append((word_start, word_end, mapping_idx, score, kw))

            matches.sort(key=lambda x: (x[1] - x[0], -x[0]), reverse=True)
            allowed_indices = self._get_allowed_indices(hs)
            scores_by_mapping = self._score_matches(matches, allowed_indices)

            if not scores_by_mapping:
                needs_sem.append(text_lower)
                needs_sem_idx.append(idx)
                continue

            max_score, best_idx = self._best_mapping(scores_by_mapping)
            if best_idx is not None and max_score >= self.DICT_THRESHOLD:
                results[idx] = (self.dict_mapping[best_idx]['label_str'], 100.0,
                                f"Tự động duyệt (Từ điển - Điểm: {max_score})")
            else:
                needs_sem.append(text_lower)
                needs_sem_idx.append(idx)

        if progress_callback:
            progress_callback(f"AC done. Semantic fallback for {len(needs_sem)} rows...")

        if needs_sem and self._load_sbert():
            self._build_dict_semantic_profiles()
            if self.dict_embeddings:
                emb_matrix = np.array([self.dict_embeddings[i] for i in sorted(self.dict_embeddings.keys())])
                emb_indices = sorted(self.dict_embeddings.keys())

                n_sem = len(needs_sem)
                for batch_start in range(0, n_sem, batch_size):
                    batch_end = min(batch_start + batch_size, n_sem)
                    batch_texts = needs_sem[batch_start:batch_end]
                    batch_embs = DictionaryMatcher._sbert_model.encode(
                        batch_texts, normalize_embeddings=True, show_progress_bar=False
                    )
                    sim_matrix = emb_matrix @ batch_embs.T
                    for bi in range(len(batch_texts)):
                        global_idx = needs_sem_idx[batch_start + bi]
                        hs = hs_codes[global_idx]
                        allowed = self._get_allowed_indices(hs)

                        col_sims = sim_matrix[:, bi]
                        best_sim = -1.0
                        best_di = -1
                        for ti, s in enumerate(col_sims):
                            actual_idx = emb_indices[ti]
                            if actual_idx in allowed and s > best_sim:
                                best_sim = s
                                best_di = actual_idx

                        if best_sim >= self.SEMANTIC_THRESHOLD:
                            results[global_idx] = (self.dict_mapping[best_di]['label_str'],
                                                   round(best_sim * 100, 2),
                                                   f"Tự động duyệt (Ngữ nghĩa - Độ tương đồng: {best_sim:.2f})")
                        else:
                            results[global_idx] = (None, 0.0, "Cần kiểm tra")

                    if progress_callback and (batch_start % (batch_size * 10) == 0):
                        progress_callback(f"  Semantic: {batch_end}/{n_sem} ({100*batch_end/n_sem:.0f}%)")
            else:
                for gi in needs_sem_idx:
                    results[gi] = (None, 0.0, "Cần kiểm tra")
        else:
            for gi in needs_sem_idx:
                results[gi] = (None, 0.0, "Cần kiểm tra")

        return results

    def _score_matches(self, matches, allowed_indices):
        scores_by_mapping = {}
        consumed_intervals = []

        def is_overlapping(start, end):
            for cs, ce in consumed_intervals:
                if max(start, cs) <= min(end, ce):
                    return True
            return False

        for start_idx, end_idx, mapping_idx, score, kw in matches:
            if mapping_idx not in allowed_indices:
                continue
            if not is_overlapping(start_idx, end_idx):
                consumed_intervals.append((start_idx, end_idx))
                scores_by_mapping[mapping_idx] = scores_by_mapping.get(mapping_idx, 0) + score

        return scores_by_mapping

    def _best_mapping(self, scores_by_mapping):
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
        return max_score, best_mapping_idx
