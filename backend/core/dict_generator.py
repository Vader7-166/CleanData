import pandas as pd
import numpy as np
import re
import os
import time
import json
import traceback
import io
from collections import Counter

# ===========================================================================
# CONSTANTS & CONFIGURATION (Full port from original repo)
# ===========================================================================

DONG_SP_MAP = {
    '9617': 'SP BÌNH/PHÍCH',
    '7020': 'SP THỦY TINH',
    '8539': 'SP LED',
    '9405': 'SP LED',
    '8516': 'SP THIẾT BỊ ĐIỆN GIA DỤNG',
    '8504': 'SP BỘ NGUỒN/BIẾN ÁP',
}

# Business-defined Dòng SP overrides per HS code (from HQ files)
# These take priority over DONG_SP_MAP 4-digit prefix lookup
DONG_SP_OVERRIDES = {
    '85394900': 'đèn uv',
    '85394100': 'đèn uv',
}

VI_STOPWORDS = {
    'của', 'và', 'các', 'có', 'là', 'được', 'cho', 'trong', 'với', 'không',
    'những', 'một', 'từ', 'cùng', 'khi', 'đó', 'thì', 'ở', 'đến', 'này',
    'bằng', 'theo', 'như', 'tại', 'vào', 'phải', 'về', 'lại', 'thêm', 'ra',
    'nếu', 'hơn', 'chưa', 'nên', 'vẫn', 'để', 'mà', 'sau', 'nào', 'chỉ',
    'loại', 'hiệu', 'mới', 'dùng', 'tên', 'chi', 'tiết', 'hàng', 'nhãn',
    'model', 'mã', 'số', 'sản', 'phẩm', 'kích', 'thước', 'xuất', 'khẩu',
    'nhập', 'nsx', 'ltd', 'co', 'corp', 'inc', 'company',
    'brand', 'new', 'the', 'for', 'and', 'vn', 'cn',
    '100', 'hàng mới', 'mới 100',
    'us', 'uk', 'kr', 'jp', 'de', 'fr', 'it', 'au', 'ca', 'eu',
    'stanley', 'owala', 'zojirushi', 'lock', 'locknlock', 'tupperware',
    'fuji', 'tyeso', 'outin', 'elemental', 'cherry', 'mkb', 'mkr', 'mcs',
    'mcz', 'mct', 'med', 'btl', 'sb',
    'pcs', 'set', 'unit', 'pc', 'oz', 'ml', 'mm', 'cm',
    'made', 'use', 'size', 'type', 'part',
}

LABEL_STOPWORDS = VI_STOPWORDS | {
    'chất', 'liệu', 'thể', 'điện', 'ngoài', 'bên', 'lớp', 'thương',
    'cách', 'giữa', 'tích', 'hoàn', 'chỉnh', 'gồm', 'kết', 'hợp',
    'mặt', 'tổng', 'dòng', 'đặc', 'chuyên', 'thông', 'dụng',
    'đầu', 'trên', 'dưới', 'trước', 'trong', 'ký', 'đê', 'phân',
    'phối', 'nhà', 'làm', 'đang', 'quốc', 'mbình',
    'cao', 'dài', 'rộng', 'dày', 'mỏng', 'nhỏ', 'lớn', 'đơn', 'kép',
    'đen', 'trắng', 'xám', 'xanh', 'đỏ', 'vàng', 'hồng', 'tím', 'nâu', 'bạc',
    'ngà', 'sẫm', 'nhạt', 'đậm', 'màu', 'sắc',
    'oz', 'ml', 'lít', 'lit', 'liter', 'litre', 'g', 'kg',
    'w', 'v', 'watt', 'volt', 'wh', 'kwh', 'ac', 'dc',
    'mới100', 'hiêu', 'slo', 'đê', 'quy', 'kiểu',
    'khôngcó', 'thươnghiệu', 'khônghiệu', 'bìnhgiữnhiệt',
    'chấtliệubằngthépkhôngrỉ', 'dungtích', 'vỏbằng',
    'vacuum', 'steel', 'stainless', 'bottle', 'cup', 'mug', 'thermos',
    'body', 'lid', 'cap', 'inner', 'outer', 'bottom', 'clear', 'logo',
    'food', 'grade', 'bpa', 'free', 'with', 'without', 'double', 'wall',
    'flask', 'tumbler', 'water', 'insulated', 'travel', 'handle',
    'worthington', 'dachengco', 'wolfpak', 'kaxifei', 'shandongco',
    'lebenlang', 'qihu', 'lhc', 'vhc', 'commerce', 'containers',
    'serial', 'allcho', 'kaiyo', 'ruby', 'elk', 'products',
    'guangzhou', 'zhejiang', 'industry', 'main', 'huizhou',
    'revomax', 'dwf', 'tresette', 'zhengzheng', 'shang',
    'shengyuan', 'inochi', 'ember', 'xile', 'hoycom',
    'adventure', 'quencher', 'rna', 'tumb', 'qnchr',
    'hankie', 'urban', 'outfitters', 'sprngblssms',
    'nonvac', 'disney', 'sports',
    'ky', 'dt', 'rb', 'db', 'wd', 'wt', 'th', 'sb', 'kr', 'us', 'jp',
    'psg', 'ign', 'ptr', 'hsymbl', 'hsty', 'ctg', 'mcx', 'mea', 'mtr',
}

GLOBAL_STOPWORDS = {
    'hiệu', 'công suất', 'kích thước', 'jindian', 'philips', 'gp', 'rạng đông', 
    'điện quang', 'panasonic', 'samsung', 'lg', 'toshiba', 'màu sắc', 'bảo hành'
}

CONTEXT_RESTRICTED = {
    'mặt trời': ['năng lượng mặt trời', 'solar'], 
    'solar': ['năng lượng mặt trời', 'solar'], 
    'nlmt': ['năng lượng mặt trời', 'solar']
}

# HS_TAXONOMY: Maps HS code -> Lớp 1 business category
# 8539/9405 entries use HQ business terms; other groups keep technical descriptions
HS_TAXONOMY = {
    '96170010': 'Phích và bình giữ nhiệt', '96170020': 'Các bộ phận phích/bình',
    '70200011': 'Khuôn thủy tinh — sản xuất acrylic', '70200019': 'Khuôn thủy tinh — loại khác',
    '70200020': 'Ống thạch anh — lò phản ứng / bán dẫn', '70200030': 'Ruột phích / ruột bình chân không',
    '70200040': 'Ống chân không — năng lượng mặt trời', '70200090': 'Sản phẩm thủy tinh khác',
    '7020009010': 'Bình ga sợi thủy tinh', '7020009090': 'Sản phẩm thủy tinh khác (loại khác)',
    # --- 8539: HQ business categories ---
    '85391010': 'led khác', '85391090': 'led khác',
    '85392120': 'led khác', '85392130': 'led khác',
    '85392140': 'led khác', '85392190': 'led khác',
    '85392231': 'led trang trí', '85392232': 'led khác',
    '85392233': 'led tube', '85392239': 'led khác',
    '85392291': 'led trang trí', '85392293': 'led tube',
    '85392299': 'led khác',
    '85392910': 'led khác', '85392920': 'led khác',
    '85392930': 'led khác', '85392941': 'led khác',
    '85392949': 'led khác', '85392950': 'led khác',
    '85392960': 'led khác', '85392990': 'led khác',
    '85393110': 'led tube', '85393120': 'led tube',
    '85393130': 'led bán nguyệt', '85393190': 'led tube',
    '85393200': 'led khác', '85393940': 'led khác',
    '85393990': 'led khác', '8539399090': 'led khác',
    '85394100': 'led khác', '85394900': 'led khác',
    '85395100': 'led khác', '8539510010': 'led khác',
    '8539510090': 'led bulb',
    '85395210': 'led bulb', '85395290': 'led khác',
    '85399010': 'led bulb', '85399020': 'led khác',
    '85399030': 'led khác', '85399090': 'led bulb',
    # --- 9405: HQ business categories ---
    '94051110': 'led khác', '94051191': 'tracklight',
    '94051199': 'led trang trí', '94051910': 'led khác',
    '94051991': 'led downlight', '94051992': 'led tube',
    '94051999': 'led trang trí',
    '94052110': 'led khác', '94052190': 'led trang trí',
    '94052910': 'led khác', '94052990': 'led trang trí',
    '94053100': 'led trang trí', '94053900': 'led trang trí',
    '94054110': 'flood', '94054120': 'led khác',
    '94054130': 'led khác', '94054140': 'led khác',
    '94054190': 'led khác',
    '94054210': 'flood', '94054220': 'led khác',
    '94054230': 'led khác', '94054240': 'led khác',
    '94054250': 'led chiếu sáng đường', '94054260': 'led cảnh quan',
    '94054290': 'led khác',
    '94054910': 'flood', '94054920': 'led khác',
    '94054930': 'led khác', '94054940': 'led khác',
    '94054950': 'flood', '94054960': 'led khác',
    '94054990': 'led khác',
    '94055011': 'led trang trí', '94055019': 'led trang trí',
    '94055050': 'led chống cháy/ ẩm', '94055090': 'flood',
    '94056110': 'led khẩn cấp', '94056190': 'led khẩn cấp',
    '94056910': 'led khác', '94056990': 'led khác',
    '94059110': 'led khác', '94059120': 'led khác',
    '94059140': 'led trang trí', '94059150': 'flood',
    '94059190': 'led trang trí', '94059210': 'led khác',
    '94059220': 'led downlight', '94059230': 'flood',
    '94059290': 'led bulb',
    '94059910': 'led trang trí', '94059920': 'led trang trí',
    '94059930': 'flood', '94059940': 'flood',
    '94059950': 'led trang trí', '94059990': 'led trang trí',
    # --- 8516: Technical descriptions (unchanged) ---
    '85161011': 'Bình thủy điện gia dụng',
    '85161019': 'Dụng cụ đun nước nóng — loại khác', '85161030': 'Dụng cụ đun nước nóng kiểu nhúng',
    '85162100': 'Dụng cụ điện làm nóng không gian — bức xạ giữ nhiệt', '85162900': 'Dụng cụ điện làm nóng không gian — loại khác',
    '85163100': 'Máy sấy tóc', '85163200': 'Dụng cụ làm tóc khác', '85163300': 'Máy sấy khô tay',
    '85164010': 'Bàn là điện — công nghiệp', '85164090': 'Bàn là điện — loại khác',
    '85165000': 'Lò vi sóng', '85166010': 'Nồi cơm điện', '85166090': 'Lò nướng / bếp điện — loại khác',
    '85167100': 'Dụng cụ pha chè / cà phê', '85167200': 'Lò nướng bánh', '85167910': 'Ấm đun nước điện',
    '85167990': 'Dụng cụ nhiệt điện gia dụng khác', '85168010': 'Điện trở đốt nóng — công nghiệp',
    '85168030': 'Điện trở đốt nóng — gia dụng', '85168090': 'Điện trở đốt nóng — loại khác',
    '85169021': 'Bộ phận thiết bị điện — tấm toả nhiệt', '85169029': 'Bộ phận thiết bị điện — loại khác',
    '85169030': 'Bộ phận của thiết bị đun nước nóng 8516.10', '85169040': 'Bộ phận điện trở đốt nóng',
    '85169090': 'Bộ phận thiết bị điện — loại khác',
    '850410': 'Chấn lưu cho đèn phóng điện', '850421': 'Máy biến áp sử dụng dung môi lỏng cách điện ≤ 650 kVA',
    '850422': 'Máy biến áp sử dụng dung môi lỏng cách điện > 650 kVA ≤ 10000 kVA', '850423': 'Máy biến áp sử dụng dung môi lỏng cách điện > 10000 kVA',
    '850431': 'Máy biến áp loại khác ≤ 1 kVA', '850432': 'Máy biến áp loại khác > 1 kVA ≤ 16 kVA',
    '850433': 'Máy biến áp loại khác > 16 kVA ≤ 500 kVA', '850434': 'Máy biến áp loại khác > 500 kVA',
    '850440': 'Máy biến đổi tĩnh điện', '85044011': 'Bộ nguồn cấp điện liên tục (UPS)',
    '85044019': 'Máy biến đổi tĩnh điện loại khác', '85044020': 'Máy nạp ắc qui, pin công suất > 100 kVA',
    '85044030': 'Bộ chỉnh lưu khác', '85044040': 'Bộ nghịch lưu', '85044090': 'Máy biến đổi tĩnh điện loại khác',
    '850450': 'Cuộn cảm', '850490': 'Bộ phận của máy biến áp/cuộn cảm',
}

LK_KEYWORDS = [
    'linh kiện', 'phụ tùng', 'bộ phận', 'nắp', 'vòi', 'thân', 'đáy',
    'phôi', 'gioăng', 'vòng', 'đệm', 'vít', 'ốc', 'trục', 'khuôn', 'viền',
    'vỏ', 'lõi', 'tấm', 'phụ kiện', 'mảnh', 'miếng', 'nút', 'đầu',
    'tay cầm', 'ruột', 'cán', 'khung', 'mặt nạ', 'chân', 'đế',
    'ống hút', 'nút bấm', 'vòng đệm', 'đui', 'chấn lưu', 'driver', 'pcba',
    'mạch', 'bảng mạch', 'module', 'mô-đun'
]

HS_TYPE_MAP = {
    '96170010': 'NC', '96170020': 'LK',
    '70200011': 'LK', '70200019': 'LK', '70200020': 'LK',
    '70200030': 'LK', '70200040': 'LK', '70200090': 'NC',
    '85391010': 'NC', '85391090': 'NC', '85392120': 'NC', '85392130': 'NC',
    '85392140': 'NC', '85392190': 'NC', '85392231': 'NC',
    '85392232': 'NC', '85392233': 'NC', '85392239': 'NC', '85392291': 'NC',
    '85392293': 'NC', '85392299': 'NC', '85392910': 'NC', '85392920': 'NC',
    '85392930': 'NC', '85392941': 'NC', '85392949': 'NC', '85392950': 'NC',
    '85392960': 'NC', '85392990': 'NC',
    '85393110': 'NC', '85393120': 'NC', '85393130': 'NC', '85393190': 'NC',
    '85393200': 'NC', '85393940': 'NC',
    '85393990': 'NC', '8539399090': 'NC',
    '85394100': 'NC', '85394900': 'NC', '85395100': 'LK',
    '8539510010': 'NC', '8539510090': 'LK',
    '85395210': 'NC', '85395290': 'LK',
    '85399010': 'LK', '85399020': 'LK', '85399030': 'LK',
    '85399090': 'LK',
    # --- 9405: HQ-derived Loại ---
    '94051110': 'NC', '94051191': 'NC', '94051199': 'NC',
    '94051910': 'NC', '94051991': 'NC', '94051992': 'NC', '94051999': 'NC',
    '94052110': 'NC', '94052190': 'NC', '94052910': 'NC', '94052990': 'NC',
    '94053100': 'NC', '94053900': 'NC',
    '94054110': 'NC', '94054120': 'NC', '94054130': 'NC', '94054140': 'NC', '94054190': 'NC',
    '94054210': 'NC', '94054220': 'NC', '94054230': 'NC', '94054240': 'NC',
    '94054250': 'NC', '94054260': 'NC', '94054290': 'NC',
    '94054910': 'NC', '94054920': 'NC', '94054930': 'NC', '94054940': 'NC',
    '94054950': 'NC', '94054960': 'NC', '94054990': 'NC',
    '94055011': 'NC', '94055019': 'NC', '94055050': 'NC', '94055090': 'NC',
    '94056110': 'NC', '94056190': 'NC', '94056910': 'NC', '94056990': 'NC',
    '94059110': 'NC', '94059120': 'NC',
    '94059140': 'LK', '94059150': 'LK', '94059190': 'LK',
    '94059210': 'LK', '94059220': 'LK', '94059230': 'LK', '94059290': 'LK',
    '94059910': 'LK', '94059920': 'LK', '94059930': 'LK',
    '94059940': 'LK', '94059950': 'LK', '94059990': 'LK',
    # --- Other groups (unchanged) ---
    '85167910': 'NC', '85168010': 'LK', '85169090': 'LK',
    '850410': 'LK', '850421': 'NC', '850422': 'NC', '850423': 'NC',
    '850431': 'NC', '850432': 'NC', '850433': 'NC', '850434': 'NC',
    '850440': 'NC', '85044011': 'NC', '85044019': 'NC', '85044020': 'NC',
    '85044030': 'NC', '85044040': 'NC', '85044090': 'NC',
    '850450': 'NC', '850490': 'LK',
}

_VALID_TOKEN_RE = re.compile(r'[a-záàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđ]{2,}')

# ===========================================================================
# DICTIONARY GENERATOR CLASS
# ===========================================================================

class DictionaryGenerator:
    def __init__(self, deepseek_api_key=None, db_taxonomy=None):
        """
        Args:
            deepseek_api_key: Optional API key for DeepSeek LLM labeling.
            db_taxonomy: Optional list of dicts from DB with keys:
                         hs_code_prefix, dong_sp, industry_name, default_type.
                         If provided, overrides the hardcoded constants.
        """
        self.deepseek_api_key = deepseek_api_key
        self.vi_stopwords = VI_STOPWORDS
        self.label_stopwords = LABEL_STOPWORDS
        
        self.official_taxonomy = {}
        official_json_path = os.path.join(os.path.dirname(__file__), "..", "data", "official_hs_taxonomy.json")
        try:
            if os.path.exists(official_json_path):
                with open(official_json_path, 'r', encoding='utf-8') as f:
                    self.official_taxonomy = json.load(f)
        except Exception as e:
            print(f"DEBUG: Error loading official taxonomy: {e}")
            

        if db_taxonomy:
            # Build dynamic lookups from database records
            self.hs_taxonomy = {r['hs_code_prefix']: r['industry_name'] for r in db_taxonomy}
            self.hs_type_map = {r['hs_code_prefix']: r['default_type'] for r in db_taxonomy}
            # Build dong_sp_map from unique 4-digit prefixes
            self.dong_sp_map = {}
            for r in db_taxonomy:
                p4 = r['hs_code_prefix'][:4]
                if p4 not in self.dong_sp_map:
                    self.dong_sp_map[p4] = r['dong_sp']
        else:
            # Fallback to hardcoded constants
            self.hs_taxonomy = HS_TAXONOMY
            self.hs_type_map = HS_TYPE_MAP
            self.dong_sp_map = DONG_SP_MAP
        self.dong_sp_overrides = DONG_SP_OVERRIDES

    def clean_text(self, text):
        if pd.isna(text): return ''
        text = str(text).lower()
        text = re.sub(r'^[^#]*#\s*&?\s*', '', text)
        text = re.sub(r'#\s*&?\s*vn\s*$', '', text)
        
        # Remove mixed alphanumeric model/spec codes (e.g. RS-378B, 15W, 1.2m, 12oz)
        text = re.sub(r'\b(?=[a-z0-9.-]*\d)(?=[a-z0-9.-]*[a-z])[a-z0-9.-]+\b', ' ', text)
        
        # Remove pure numbers (e.g. 100, 2026, 1.5)
        text = re.sub(r'\b\d+(?:[.,]\d+)?\b', ' ', text)
        
        # Remove non-alphanumeric characters, keeping only letters and spaces
        text = re.sub(r'[^a-záàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợùúụủũụưứừửữựýỳỷỹỵđ\s]+', ' ', text)
        return re.sub(r'\s+', ' ', text).strip()

    def tokenize_vi(self, text, use_label_stopwords=False):
        if not text: return [] if use_label_stopwords else ''
        tokens = text.split()
        sw = self.label_stopwords if use_label_stopwords else self.vi_stopwords
        cleaned = [t.replace('_', ' ') for t in tokens if t.lower() not in sw and len(t) > 1]
        return cleaned if use_label_stopwords else ' '.join(cleaned)

    def _is_valid_cluster_token(self, token):
        t = token.lower()
        if t in self.label_stopwords: return False
        if re.match(r'^\d', t) or len(t) < 3: return False
        if re.fullmatch(r'\d+[a-z]+|[a-z]+\d+', t): return False
        if not _VALID_TOKEN_RE.search(t): return False
        return True



    def generate_draft_taxonomy(self, raw_df, eps=0.70, min_samples=8, use_llm=True, progress_callback=None):
        raw_df = raw_df.copy()
        raw_df.columns = [str(c).strip() for c in raw_df.columns]
        
        hs_col = None
        for cand in ['HS_Code', 'Mã HS', 'HS Code', 'Mã hàng', 'HS']:
            if cand in raw_df.columns:
                hs_col = cand
                break
        if not hs_col:
            raise ValueError(f"Không tìm thấy cột Mã HS (HS_Code, Mã HS, v.v.). Các cột hiện có: {list(raw_df.columns)}")
            
        raw_df['HS_Code'] = raw_df[hs_col].astype(str)
        # Clean HS_Code column: remove dots and non-digits
        raw_df['HS_Code'] = raw_df['HS_Code'].apply(lambda x: re.sub(r'\D', '', x))
        
        prod_col = None
        for cand in ['Detailed_Product', 'Actual_Detailed_Product_LL', 'Actual_Detail_Product', 'Actual_Detailed_Product', 'Tên hàng gốc', 'Description', 'Mô tả', 'Tên hàng', 'Product']:
            if cand in raw_df.columns:
                prod_col = cand
                break
        if not prod_col:
            raise ValueError(f"Không tìm thấy cột mô tả sản phẩm (Detailed_Product, Tên hàng gốc, v.v.). Các cột hiện có: {list(raw_df.columns)}")
            
        detailed_product = raw_df[prod_col].copy()
        for fallback_col in ['Detailed_Product', 'Actual_Detailed_Product_LL', 'Actual_Detail_Product', 'Actual_Detailed_Product', 'Tên hàng gốc']:
            if fallback_col in raw_df.columns and fallback_col != prod_col:
                detailed_product = detailed_product.fillna(raw_df[fallback_col])
                
        raw_df['Detailed_Product'] = detailed_product.astype(str)
        raw_df['_clean'] = raw_df['Detailed_Product'].apply(self.clean_text)
        raw_df['_tok'] = raw_df['_clean'].apply(lambda x: self.tokenize_vi(x))
        raw_df = raw_df[raw_df['_tok'].str.len() > 0].reset_index(drop=True)
        
        # === FAST PATH ONLY: Must be pre-labeled HQ data ===
        hq_cols = {'Dòng SP', 'Loại', 'Lớp 1'}
        if not hq_cols.issubset(set(raw_df.columns)):
            raise ValueError("File tải lên không hợp lệ. Vui lòng sử dụng file chuẩn của Hải quan (có chứa các cột: Dòng SP, Loại, Lớp 1).")
            
        print("DEBUG: Pre-labeled HQ data detected. Using exact grouping.")
        if progress_callback:
            progress_callback(1, 1, "Pre-labeled data detected, grouping...")
        
        lop2_col = 'Lớp 2' if 'Lớp 2' in raw_df.columns else None
        group_cols = ['HS_Code', 'Dòng SP', 'Loại', 'Lớp 1']
        if lop2_col:
            group_cols.append(lop2_col)
        
        # Clean category values
        for col in group_cols[1:]:  # skip HS_Code
            raw_df[col] = raw_df[col].fillna('0').astype(str).str.strip()
        
        all_rows = []
        cluster_counter = 0
        cluster_map = {}  # (hs, group_key) -> cluster_id
        
        for keys, grp in raw_df.groupby(group_cols, sort=False):
            hs = keys[0]
            dong_sp = keys[1]
            loai = keys[2]
            lop1 = keys[3]
            lop2 = keys[4] if lop2_col else '0'
            
            group_key = (hs, dong_sp, loai, lop1, lop2)
            if group_key not in cluster_map:
                cluster_map[group_key] = cluster_counter
                cluster_counter += 1
            cid = cluster_map[group_key]
            
            raw_df.loc[grp.index, '_cluster'] = cid
            
            all_rows.append({
                'Mã HS': hs,
                'Dòng SP': dong_sp if dong_sp != '0' else (self.dong_sp_overrides.get(hs) or self.dong_sp_map.get(hs[:4], f'SP {hs[:4]}')),
                'Loại': loai if loai != '0' else self.hs_type_map.get(hs, 'NC'),
                'Lớp 1': lop1 if lop1 != '0' else self.hs_taxonomy.get(hs, 'Chưa phân loại'),
                'Lớp 2': lop2 if lop2 != '0' else '',
                'Keyword': '',
                'Cluster_ID': int(cid),
                'Số lượng SP': len(grp),
                'Mô tả mẫu': str(grp['Detailed_Product'].iloc[0])[:120],
            })
        
        df = pd.DataFrame(all_rows)
        # Merge duplicate groups
        merged = []
        if not df.empty:
            merge_cols = ['Mã HS', 'Dòng SP', 'Loại', 'Lớp 1', 'Lớp 2']
            for _, g in df.groupby(merge_cols, sort=False):
                best = g.loc[g['Số lượng SP'].idxmax()].copy()
                best['Số lượng SP'] = g['Số lượng SP'].sum()
                merged.append(best.to_dict())
        return pd.DataFrame(merged).sort_values(['Mã HS', 'Số lượng SP'], ascending=[True, False]).reset_index(drop=True), raw_df

    def extract_keywords_ai(self, group_prods, top_n=15, fallback=None, global_freqs=None):
        indices = list(group_prods.keys())
        class_f, local_glob_f = {i: __import__('collections').Counter() for i in indices}, __import__('collections').Counter()
        def ngrams(t, n_min=1, n_max=3):
            res = []
            for n in range(n_min, n_max+1):
                for i in range(len(t)-n+1): res.append(' '.join(t[i:i+n]))
            return res
        for i, ps in group_prods.items():
            for p in ps:
                ns = ngrams(str(p).split())
                for n in set(ns): class_f[i][n] += 1; local_glob_f[n] += 1
        
        actual_glob_f = global_freqs if global_freqs is not None else local_glob_f
        
        high_value_kws = {'năng lượng mặt trời', 'solar', 'nlmt'}
        res = {}
        for i in indices:
            cands = []
            
            for n, lf in class_f[i].items():
                words = n.split()
                if not any(self._is_valid_cluster_token(w) for w in words): continue
                if any(w in GLOBAL_STOPWORDS for w in words): continue
                
                gf = actual_glob_f[n] if actual_glob_f[n] > 0 else local_glob_f[n]
                if gf == 0: gf = 1
                p = lf / gf
                
                # PURITY CHECK: Must be somewhat unique to this class
                # If a word is very generic across all HS codes, reject it
                if p < 0.05: continue 
                
                base_score = len(words)
                if any(hv in n for hv in high_value_kws):
                    base_score += 5
                
                score = (p * 50) + (lf * 2) * base_score
                cands.append((n, score, lf))
                
            cands.sort(key=lambda x: (x[1], x[2]), reverse=True)
            
            final_kws = []
            for c in cands:
                if len(final_kws) >= top_n: break
                w = c[0]
                if not any(w in ex and w != ex for ex in final_kws):
                    final_kws.append(w)
            res[i] = ', '.join(final_kws)
        return res

    def generate_dictionary_from_hq(self, raw_df, progress_callback=None):
        """
        Fast-path 1-step dictionary generation directly from HQ labeled files.
        Skips DBSCAN clustering and LLM labeling.
        """
        raw_df = raw_df.copy()
        raw_cols = {str(c).strip(): c for c in raw_df.columns}
        
        # Identify columns
        hs_col = next((raw_cols[cand] for cand in ['HS_Code', 'Mã HS', 'HS'] if cand in raw_cols), None)
        prod_col = next((raw_cols[cand] for cand in ['Detailed_Product', 'Actual_Detailed_Product_LL', 'Actual_Detail_Product', 'Actual_Detailed_Product', 'Tên hàng gốc', 'Description', 'Mô tả', 'Tên hàng', 'Product'] if cand in raw_cols), None)
        
        if not hs_col:
            raise ValueError(f"Missing HS Code column. Found: {list(raw_cols.keys())}")
        if not prod_col:
            raise ValueError(f"Missing Product description column. Found: {list(raw_cols.keys())}")
            
        group_cols = ['Dòng SP', 'Loại', 'Lớp 1']
        if not all(col in raw_df.columns for col in group_cols):
            raise ValueError(f"Missing one of required HQ columns: {group_cols}")
            
        lop2_col = 'Lớp 2' if 'Lớp 2' in raw_df.columns else None
        
        if progress_callback:
            progress_callback(1, 3, "Cleaning and tokenizing text...")
            
        raw_df['HS_Code_Internal'] = raw_df[hs_col].astype(str).apply(lambda x: re.sub(r'\D', '', x))
        raw_df['Detailed_Product_Internal'] = raw_df[prod_col].astype(str)
        raw_df['_clean'] = raw_df['Detailed_Product_Internal'].apply(self.clean_text)
        raw_df['_tok'] = raw_df['_clean'].apply(lambda x: ' '.join(self.tokenize_vi(x, True)))
        
        for col in group_cols + ([lop2_col] if lop2_col else []):
            raw_df[col] = raw_df[col].fillna('0').astype(str).str.strip()
            
        if progress_callback:
            progress_callback(2, 3, "Grouping and extracting keywords...")
            
        # --- Pre-compute global frequencies across entire dataset ---
        from collections import Counter
        def ngrams(t, n_min=1, n_max=3):
            res = []
            for n in range(n_min, n_max+1):
                for i in range(len(t)-n+1): res.append(' '.join(t[i:i+n]))
            return res
            
        global_freqs = Counter()
        for tok_str in raw_df['_tok']:
            if not isinstance(tok_str, str) or not tok_str.strip():
                continue
            ns = ngrams(tok_str.split())
            for n in set(ns):
                global_freqs[n] += 1
        # -----------------------------------------------------------
            
        results = []
        unique_hs = raw_df['HS_Code_Internal'].unique()
        
        for hs in unique_hs:
            sub_raw = raw_df[raw_df['HS_Code_Internal'] == hs]
            
            # Group by HQ labels within this HS code
            g_cols = group_cols + ([lop2_col] if lop2_col else [])
            groups = sub_raw.groupby(g_cols, sort=False)
            
            docs = {}
            fb = {}
            group_keys = []
            
            for i, (keys, grp) in enumerate(groups):
                dong_sp = keys[0]
                loai = keys[1]
                lop1 = keys[2]
                lop2 = keys[3] if lop2_col else '0'
                
                docs[i] = grp['_tok'].tolist()
                fb[i] = lop2 if (lop2 and lop2.lower() not in ('nan', '0', '')) else lop1
                group_keys.append({
                    'Dòng SP': dong_sp if dong_sp != '0' else (self.dong_sp_overrides.get(hs) or self.dong_sp_map.get(hs[:4], f'SP {hs[:4]}')),
                    'Loại': loai if loai != '0' else self.hs_type_map.get(hs, 'NC'),
                    'Lớp 1': lop1 if lop1 != '0' else self.hs_taxonomy.get(hs, 'Chưa phân loại'),
                    'Lớp 2': lop2 if lop2 != '0' else '',
                    'Mã HS': hs,
                    'Số lượng SP': len(grp)
                })
                
            kw_m = self.extract_keywords_ai(docs, 15, fb, global_freqs=global_freqs)
            
            for i, meta in enumerate(group_keys):
                extracted = kw_m.get(i, '')
                
                label_words = set()
                for k in ['Dòng SP', 'Loại', 'Lớp 1', 'Lớp 2']:
                    val = meta.get(k, '')
                    if val and val.lower() not in ('0', 'chưa phân loại', 'nc', ''):
                        cleaned_val = self.clean_text(val)
                        if cleaned_val:
                            label_words.add(cleaned_val)
                
                existing_kws = [k.strip() for k in extracted.split(',')] if extracted else []
                for lw in label_words:
                    if lw not in existing_kws:
                        existing_kws.insert(0, lw)
                        
                meta['Keyword'] = ', '.join(filter(None, existing_kws))
                results.append(meta)
                
        if progress_callback:
            progress_callback(3, 3, "Dictionary generation completed.")
            
        df_res = pd.DataFrame(results)
        # Reorder columns to standard format
        cols_order = ['Keyword', 'Dòng SP', 'Loại', 'Lớp 1', 'Lớp 2', 'Mã HS', 'Số lượng SP']
        df_res = df_res[[c for c in cols_order if c in df_res.columns]]
        return df_res.sort_values(['Mã HS', 'Số lượng SP'], ascending=[True, False]).reset_index(drop=True)

