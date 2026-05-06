import pandas as pd
import numpy as np
import re
import os
import time
import json
import traceback
import io
from pyvi import ViTokenizer
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_distances
from groq import Groq

# ===========================================================================
# CONSTANTS & CONFIGURATION (Full port from original repo)
# ===========================================================================

DONG_SP_MAP = {
    '9617': 'SP BÌNH/PHÍCH',
    '7020': 'SP THỦY TINH',
    '8539': 'SP ĐÈN/BÓNG ĐÈN',
    '9405': 'SP ĐÈN/THIẾT BỊ CHIẾU SÁNG',
    '8516': 'SP THIẾT BỊ ĐIỆN GIA DỤNG',
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

HS_TAXONOMY = {
    '96170010': 'Phích và bình giữ nhiệt', '96170020': 'Các bộ phận phích/bình',
    '70200011': 'Khuôn thủy tinh — sản xuất acrylic', '70200019': 'Khuôn thủy tinh — loại khác',
    '70200020': 'Ống thạch anh — lò phản ứng / bán dẫn', '70200030': 'Ruột phích / ruột bình chân không',
    '70200040': 'Ống chân không — năng lượng mặt trời', '70200090': 'Sản phẩm thủy tinh khác',
    '7020009010': 'Bình ga sợi thủy tinh', '7020009090': 'Sản phẩm thủy tinh khác (loại khác)',
    '85391010': 'Đèn pha gắn kín — dùng cho xe có động cơ', '85391090': 'Đèn pha gắn kín — loại khác',
    '85392120': 'Bóng đèn ha-lo-gien vonfram — thiết bị y tế', '85392130': 'Bóng đèn ha-lo-gien vonfram — xe có động cơ',
    '85392140': 'Bóng đèn ha-lo-gien vonfram — phản xạ', '85392190': 'Bóng đèn ha-lo-gien vonfram — loại khác',
    '85392220': 'Bóng đèn dây tóc ≤200W — thiết bị y tế', '85392231': 'Bóng đèn dây tóc — chiếu sáng trang trí ≤60W',
    '85392232': 'Bóng đèn dây tóc — chiếu sáng trang trí >60W', '85392233': 'Bóng đèn dây tóc — chiếu sáng gia dụng',
    '85392239': 'Bóng đèn dây tóc ≤200W — loại khác', '85392291': 'Bóng đèn dây tóc — chiếu sáng trang trí ≤60W (nhóm khác)',
    '85392293': 'Bóng đèn dây tóc — chiếu sáng gia dụng (nhóm khác)', '85392299': 'Bóng đèn dây tóc ≤200W — loại khác (nhóm khác)',
    '85392910': 'Bóng đèn dây tóc — thiết bị y tế', '85392920': 'Bóng đèn dây tóc — xe có động cơ',
    '85392930': 'Bóng đèn dây tóc — phản xạ', '85392941': 'Bóng đèn flash / cỡ nhỏ — thiết bị y tế',
    '85392949': 'Bóng đèn flash / cỡ nhỏ — loại khác', '85392950': 'Bóng đèn dây tóc >200W ≤300W, >100V',
    '85392960': 'Bóng đèn dây tóc ≤200W, ≤100V', '8539296010': 'Bóng đèn phòng nổ hai sợi đốt — đèn thợ mỏ',
    '8539296090': 'Bóng đèn dây tóc ≤200W ≤100V — loại khác', '85392990': 'Bóng đèn dây tóc — loại khác',
    '85393110': 'Bóng đèn huỳnh quang — ống dùng cho đèn com-pắc', '85393120': 'Bóng đèn huỳnh quang — ống thẳng',
    '85393130': 'Bóng đèn huỳnh quang com-pắc có chấn lưu lắp liền', '85393190': 'Bóng đèn huỳnh quang ca-tốt nóng — loại khác',
    '85393200': 'Bóng đèn hơi thủy ngân / natri / ha-lo-gien kim loại', '85393910': 'Bóng đèn phóng điện — ống dùng cho đèn com-pắc',
    '85393920': 'Bóng đèn CCFL — màn hình dẹt', '85393940': 'Bóng đèn CCFL — loại khác',
    '85393990': 'Bóng đèn phóng điện — loại khác', '8539399010': 'Đèn ống phóng điện — trang trí / công cộng',
    '8539399020': 'Bóng đèn phóng điện — xe có động cơ / xe đạp', '8539399090': 'Bóng đèn phóng điện — loại khác',
    '85394100': 'Bóng đèn hồ quang', '85394900': 'Bóng đèn tia cực tím / hồng ngoại',
    '85395100': 'Mô-đun LED', '8539510010': 'Mô-đun LED — dùng cho đèn chiếu sáng',
    '8539510020': 'Mô-đun LED — dùng cho xe có động cơ', '8539510090': 'Mô-đun LED — loại khác',
    '85395210': 'Bóng đèn LED — đầu đèn ren xoáy', '85395290': 'Bóng đèn LED — loại khác',
    '85399010': 'Bộ phận bóng đèn — nắp / đui nhôm huỳnh quang', '85399020': 'Bộ phận bóng đèn — dùng cho xe có động cơ',
    '85399030': 'Bộ phận mô-đun LED', '8539903010': 'Bộ phận mô-đun LED — dùng cho đèn chiếu sáng',
    '8539903090': 'Bộ phận mô-đun LED — loại khác', '85399090': 'Bộ phận bóng đèn — loại khác',
    '94051110': 'Bộ đèn LED — đèn phòng mổ', '94051191': 'Bộ đèn LED — đèn rọi',
    '94051199': 'Bộ đèn LED — loại khác (trần/tường)', '94051910': 'Bộ đèn loại khác — đèn phòng mổ',
    '94051991': 'Bộ đèn loại khác — đèn rọi', '94051992': 'Bộ đèn loại khác — đèn huỳnh quang',
    '94051999': 'Bộ đèn loại khác — loại khác (trần/tường)', '94052110': 'Đèn bàn/giường/cây LED — đèn phòng mổ',
    '94052190': 'Đèn bàn/giường/cây LED — loại khác', '9405219010': 'Đèn bàn/giường/cây LED — đèn sân khấu',
    '9405219090': 'Đèn bàn/giường/cây LED — loại khác', '94052910': 'Đèn bàn/giường/cây loại khác — đèn phòng mổ',
    '94052990': 'Đèn bàn/giường/cây loại khác — loại khác', '9405299010': 'Đèn bàn/giường/cây — đèn sân khấu',
    '9405299090': 'Đèn bàn/giường/cây — loại khác', '94053100': 'Dây chiếu sáng Nô-en LED',
    '94053900': 'Dây chiếu sáng Nô-en loại khác', '94054110': 'Đèn LED — đèn pha',
    '94054120': 'Đèn LED — đèn rọi', '94054130': 'Đèn LED — tín hiệu sân bay / đường sắt / tàu thủy',
    '94054140': 'Đèn LED — chiếu sáng công cộng / ngoài trời', '94054190': 'Đèn LED — loại khác',
    '9405419010': 'Đèn LED — đèn sân khấu', '9405419090': 'Đèn LED — loại khác',
    '94054210': 'Đèn điện LED khác — đèn pha', '94054220': 'Đèn điện LED khác — đèn rọi',
    '94054230': 'Đèn điện LED khác — tín hiệu sân bay / đường sắt', '94054240': 'Đèn LED — báo hiệu thiết bị gia dụng 85.16',
    '94054250': 'Đèn điện LED khác — chiếu sáng công cộng', '94054260': 'Đèn điện LED khác — chiếu sáng ngoài trời',
    '94054290': 'Đèn điện LED khác — loại khác', '9405429010': 'Đèn điện LED khác — đèn sân khấu',
    '9405429090': 'Đèn điện LED khác — loại khác', '94054910': 'Đèn điện loại khác — đèn pha',
    '94054920': 'Đèn điện loại khác — đèn rọi', '94054930': 'Đèn điện loại khác — tín hiệu sân bay / đường sắt',
    '94054940': 'Đèn điện loại khác — báo hiệu thiết bị gia dụng', '94054950': 'Đèn điện loại khác — chiếu sáng công cộng',
    '94054960': 'Đèn điện loại khác — chiếu sáng ngoài trời', '94054990': 'Đèn điện loại khác — loại khác',
    '9405499010': 'Đèn điện loại khác — đèn sân khấu', '9405499090': 'Đèn điện loại khác — loại khác',
    '94055011': 'Đèn dầu bằng đồng — nghi lễ tôn giáo', '94055019': 'Đèn dầu — loại khác',
    '94055040': 'Đèn bão', '94055050': 'Đèn thợ mỏ / khai thác đá', '94055090': 'Đèn không điện — loại khác',
    '94056110': 'Biển hiệu LED — cảnh báo / tên đường / giao thông', '94056190': 'Biển hiệu LED — loại khác',
    '94056910': 'Biển hiệu loại khác — cảnh báo / tên đường / giao thông', '94056990': 'Biển hiệu loại khác — loại khác',
    '94059110': 'Bộ phận thủy tinh — đèn phòng mổ', '94059120': 'Bộ phận thủy tinh — đèn rọi',
    '94059140': 'Bộ phận thủy tinh — chao đèn / thông phong', '94059150': 'Bộ phận thủy tinh — đèn pha',
    '94059190': 'Bộ phận thủy tinh — loại khác', '94059210': 'Bộ phận plastic — đèn phòng mổ',
    '94059220': 'Bộ phận plastic — đèn rọi', '94059230': 'Bộ phận plastic — đèn pha',
    '94059290': 'Bộ phận plastic — loại khác', '94059910': 'Bộ phận đèn — chụp đèn vải',
    '94059920': 'Bộ phận đèn — chụp đèn vật liệu khác', '94059930': 'Bộ phận đèn — của đèn dầu 9405.50.11/9405.50.19',
    '94059940': 'Bộ phận đèn — của đèn pha / đèn rọi', '94059950': 'Bộ phận đèn — gốm / sứ / kim loại',
    '94059990': 'Bộ phận đèn — loại khác', '85161011': 'Bình thủy điện gia dụng',
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
    '85392140': 'NC', '85392190': 'NC', '85392220': 'NC', '85392231': 'NC',
    '85392232': 'NC', '85392233': 'NC', '85392239': 'NC', '85392291': 'NC',
    '85392293': 'NC', '85392299': 'NC', '85392910': 'NC', '85392920': 'NC',
    '85392930': 'NC', '85392941': 'NC', '85392949': 'NC', '85392950': 'NC',
    '85392960': 'NC', '8539296010': 'NC', '8539296090': 'NC', '85392990': 'NC',
    '85393110': 'NC', '85393120': 'NC', '85393130': 'NC', '85393190': 'NC',
    '85393200': 'NC', '85393910': 'NC', '85393920': 'NC', '85393940': 'NC',
    '85393990': 'NC', '8539399010': 'NC', '8539399020': 'NC', '8539399090': 'NC',
    '85394100': 'NC', '85394900': 'NC', '85395100': 'LK', '85395210': 'NC',
    '85395290': 'NC', '85399010': 'LK', '85399020': 'LK', '85399030': 'LK',
    '85399090': 'LK', '85167910': 'NC', '85168010': 'LK', '85169090': 'LK',
}

_VALID_TOKEN_RE = re.compile(r'[a-záàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđ]{2,}')

# ===========================================================================
# DICTIONARY GENERATOR CLASS
# ===========================================================================

class DictionaryGenerator:
    def __init__(self, groq_api_key=None):
        self.groq_api_key = groq_api_key
        self.vi_stopwords = VI_STOPWORDS
        self.label_stopwords = LABEL_STOPWORDS
        self.hs_taxonomy = HS_TAXONOMY
        self.hs_type_map = HS_TYPE_MAP
        self.dong_sp_map = DONG_SP_MAP

    def clean_text(self, text):
        if pd.isna(text): return ''
        text = str(text).lower()
        text = re.sub(r'^[^#]*#\s*&?\s*', '', text)
        text = re.sub(r'#\s*&?\s*vn\s*$', '', text)
        text = re.sub(r'[^a-záàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđ0-9\s]+', ' ', text)
        return re.sub(r'\s+', ' ', text).strip()

    def tokenize_vi(self, text, use_label_stopwords=False):
        if not text: return [] if use_label_stopwords else ''
        tokens = ViTokenizer.tokenize(text).split()
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

    def cluster_products(self, descriptions, eps=0.45, min_samples=2):
        if len(descriptions) < 2: return np.array([0] * len(descriptions))
        v = TfidfVectorizer(max_features=5000, ngram_range=(1, 2), min_df=1, max_df=0.95)
        try:
            m = v.fit_transform(descriptions)
            d = cosine_distances(m)
            return DBSCAN(eps=eps, min_samples=min_samples, metric='precomputed').fit_predict(d)
        except: return np.array([0] * len(descriptions))

    def get_cluster_name_fallback(self, products, raw_descriptions=None, top_n=4):
        words = [w for p in products for w in p.split() if self._is_valid_cluster_token(w)]
        if words:
            top = [w for w, _ in Counter(words).most_common(top_n)]
            if len(top) >= 2: return ' '.join(top).capitalize()
        if raw_descriptions:
            cands = []
            for d in raw_descriptions:
                cl = re.sub(r'^[^#]*#\s*&?\s*', '', str(d))
                cl = re.sub(r'#.*$', '', cl).strip()
                v = [w for w in cl.lower().split() if self._is_valid_cluster_token(w)]
                if len(v) >= 2: cands.append(' '.join(v[:6]))
            if cands: return min(cands, key=len)[:60].capitalize()
        return "Chưa phân loại"

    def get_cluster_names_tfidf(self, clusters_data, top_n=4):
        labels = list(clusters_data.keys())
        docs = [' '.join([t for s in clusters_data[l]['prods'] for t in s.split() if self._is_valid_cluster_token(t)]) for l in labels]
        if len(labels) <= 1: return {l: self.get_cluster_name_fallback(clusters_data[l]['prods'], clusters_data[l]['raw'], top_n) for l in labels}
        
        try:
            v = TfidfVectorizer(tokenizer=lambda x: x.split(), token_pattern=None, ngram_range=(1, 2), sublinear_tf=True, min_df=1, max_df=0.80)
            m = v.fit_transform([d if d.strip() else '.' for d in docs])
            fn = v.get_feature_names_out()
            vi_re = re.compile(r'[àáảãạăắằẳẵặâấầẩẫậèéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợùúụủũưừứựửữỳýỵỷỹđ]')
            res = {}
            for i, l in enumerate(labels):
                scores = sorted(zip(m[i].indices, m[i].data), key=lambda x: x[1], reverse=True)
                vi, lat = [], []
                for idx, _ in scores:
                    w = fn[idx]
                    if ' ' not in w and self._is_valid_cluster_token(w):
                        if vi_re.search(w): vi.append(w)
                        else: lat.append(w)
                    if len(vi) >= top_n: break
                top = (vi[:top_n] + lat)[:top_n]
                if len(top) >= 2:
                    cnt = Counter(docs[i].split())
                    top.sort(key=lambda w: cnt.get(w, 0), reverse=True)
                    res[l] = ' '.join(top).capitalize()
                else: res[l] = self.get_cluster_name_fallback(clusters_data[l]['prods'], clusters_data[l]['raw'], top_n)
            return res
        except: return {l: self.get_cluster_name_fallback(clusters_data[l]['prods'], clusters_data[l]['raw'], top_n) for l in labels}

    def detect_type(self, hs_code, name, samples):
        txt = (name + ' ' + ' '.join(samples)).lower()
        hits = sum(1 for kw in LK_KEYWORDS if kw in txt)
        if hits >= 2: return 'LK'
        if hs_code in self.hs_type_map: return self.hs_type_map[hs_code]
        return 'LK' if hits >= 1 else 'NC'

    def label_clusters_llm(self, names_tfidf, data, batch_size=15):
        if not self.groq_api_key: return names_tfidf
        try:
            client = Groq(api_key=self.groq_api_key)
            lbls = [l for l in names_tfidf.keys() if l != -1]
            res = {l: names_tfidf[l] for l in names_tfidf.keys() if l == -1}
            print(f"DEBUG: Starting LLM labeling for {len(lbls)} clusters in {len(lbls)//batch_size + 1} batches")
            for i in range(0, len(lbls), batch_size):
                batch = lbls[i:i+batch_size]
                prompt = "Bạn là chuyên gia phân loại hàng hóa hải quan. Hãy đặt TÊN DANH MỤC ngắn gọn, có ý nghĩa cho các nhóm sản phẩm sau.\n\n"
                prompt += "YÊU CẦU:\n"
                prompt += "- CHỈ trả về định dạng JSON hợp lệ, KHÔNG GIẢI THÍCH. Ví dụ: {\"0\": \"Tên danh mục 0\", \"1\": \"Tên danh mục 1\"}\n"
                prompt += "- Tên danh mục dài 2-5 từ tiếng Việt, viết hoa chữ cái đầu.\n"
                prompt += "- Tên phải phản ánh đúng BẢN CHẤT CỦA SẢN PHẨM (danh từ chính đứng trước), ví dụ: 'Bình giữ nhiệt', 'Đèn LED âm trần', 'Nắp đậy bình'.\n"
                prompt += "- TUYỆT ĐỐI KHÔNG chứa mã số (ví dụ: RS378B), tên thương hiệu (Philips), dung tích/kích thước (12oz, 15W).\n\n"
                prompt += "DỮ LIỆU CÁC NHÓM:\n"
                for l in batch:
                    prompt += f"--- Nhóm ID: {l} ---\n"
                    prompt += f"Từ khóa đặc trưng: {names_tfidf[l]}\n"
                    prompt += f"Sản phẩm mẫu:\n"
                    for s in data[l]['raw'][:3]:
                        prompt += f"- {s}\n"
                    prompt += "\n"
                try:
                    resp = client.chat.completions.create(messages=[{"role":"user","content":prompt}], model="llama-3.1-8b-instant", temperature=0.2, response_format={"type":"json_object"})
                    js = json.loads(resp.choices[0].message.content.strip())
                    print(f"DEBUG: LLM batch {i//batch_size + 1} success.")
                    for l in batch: 
                        val = js.get(str(l)) or js.get(l)
                        if isinstance(val, dict):
                            val = val.get("id") or val.get("Tên") or (list(val.values())[0] if val else None)
                        res[l] = str(val) if val else names_tfidf[l]
                except Exception as e:
                    print(f"DEBUG: LLM batch {i//batch_size + 1} failed: {e}")
                    for l in batch: res[l] = names_tfidf[l]
            return res
        except Exception as e: 
            print(f"DEBUG: LLM labeling global fail: {e}")
            return names_tfidf

    def generate_draft_taxonomy(self, raw_df, eps=0.65, min_samples=5, use_llm=True):
        raw_df = raw_df.copy()
        # Clean HS_Code column: remove dots and non-digits
        raw_df['HS_Code'] = raw_df['HS_Code'].astype(str).apply(lambda x: re.sub(r'\D', '', x))
        
        raw_df['_clean'] = raw_df['Detailed_Product'].apply(self.clean_text)
        raw_df['_tok'] = raw_df['_clean'].apply(lambda x: self.tokenize_vi(x))
        raw_df = raw_df[raw_df['_tok'].str.len() > 0].reset_index(drop=True)
        
        all_rows = []
        for hs in sorted(raw_df['HS_Code'].unique()):
            if not hs: continue
            sub = raw_df[raw_df['HS_Code'] == hs].copy()
            lbls = self.cluster_products(sub['_tok'].tolist(), eps, min_samples)
            raw_df.loc[sub.index, '_cluster'] = lbls
            
            # Now hs is guaranteed to be only digits
            lop1 = self.hs_taxonomy.get(hs)
            if not lop1:
                # Prefix matching logic
                for length in [8, 6, 4]:
                    if len(hs) >= length:
                        prefix = hs[:length]
                        if prefix in self.hs_taxonomy:
                            lop1 = self.hs_taxonomy[prefix]
                            break
            lop1 = lop1 or 'Chưa phân loại'
            
            dong = self.dong_sp_map.get(hs[:4], f'SP {hs[:4]}')
            
            c_data = {}
            for l in sorted(set(lbls)):
                m = lbls == l
                c_data[l] = {
                    'prods': sub[m]['_tok'].tolist(), 'raw': sub[m]['Detailed_Product'].tolist(),
                    'count': m.sum(), 'sample': str(sub[m]['Detailed_Product'].iloc[0])[:120]
                }
            
            non_out = {l: v for l, v in c_data.items() if l != -1}
            names = self.get_cluster_names_tfidf(non_out)
            if use_llm: names = self.label_clusters_llm(names, non_out)
            if -1 in c_data: names[-1] = f"[OUTLIER] {self.get_cluster_name_fallback(c_data[-1]['prods'], c_data[-1]['raw'], 3)}"

            for l in sorted(set(lbls)):
                all_rows.append({
                    'Mã HS': hs, 'Dòng SP': dong, 'Loại': self.detect_type(hs, names[l], c_data[l]['raw'][:5]),
                    'Lớp 1': lop1, 'Lớp 2': names[l], 'Keyword': '', 'Cluster_ID': int(l),
                    'Số lượng SP': c_data[l]['count'], 'Mô tả mẫu': c_data[l]['sample']
                })

        df = pd.DataFrame(all_rows)
        # Final merge for same Lớp 2 under same HS
        merged = []
        if not df.empty:
            for (h, l2), g in df.groupby(['Mã HS', 'Lớp 2'], sort=False):
                best = g.loc[g['Số lượng SP'].idxmax()].copy()
                best['Số lượng SP'] = g['Số lượng SP'].sum()
                merged.append(best.to_dict())
        return pd.DataFrame(merged).sort_values(['Mã HS', 'Số lượng SP'], ascending=[True, False]).reset_index(drop=True), raw_df

    def extract_keywords_ai(self, group_prods, top_n=12, fallback=None):
        indices = list(group_prods.keys())
        class_f, glob_f = {i: Counter() for i in indices}, Counter()
        def ngrams(t, n_min=1, n_max=3):
            res = []
            for n in range(n_min, n_max+1):
                for i in range(len(t)-n+1): res.append(' '.join(t[i:i+n]))
            return res
        for i, ps in group_prods.items():
            for p in ps:
                ns = ngrams(str(p).split())
                for n in set(ns): class_f[i][n] += 1; glob_f[n] += 1
        res = {}
        for i in indices:
            cands = []
            for n, lf in class_f[i].items():
                if not self._is_valid_cluster_token(n): continue
                p = lf / glob_f[n] if glob_f[n] > 0 else 0
                cands.append((n, lf * (p**2) * (len(n.split())**0.5)))
            cands.sort(key=lambda x: x[1], reverse=True)
            top = []
            for w, _ in cands:
                # Replace underscores with spaces for matcher compatibility
                clean_w = w.replace('_', ' ')
                if not any(clean_w in x or x in clean_w for x in top): 
                    top.append(clean_w)
                if len(top) >= top_n: break
            res[i] = ', '.join(top) if top else (fallback.get(i, '') if fallback else '')
        return res

    def extract_keywords_for_taxonomy(self, tax_df, raw_df):
        tax_df = tax_df.copy(); raw_df = raw_df.copy()
        tax_df.columns = [str(c).strip() for c in tax_df.columns]
        
        # Standardize raw_df columns to handle both raw files and exported draft sheets
        raw_cols = {str(c).strip(): c for c in raw_df.columns}
        
        # HS Code column mapping
        hs_col = None
        for cand in ['HS_Code', 'Mã HS', 'HS']:
            if cand in raw_cols:
                hs_col = raw_cols[cand]
                break
        if not hs_col:
            raise KeyError(f"Could not find HS Code column in raw data. Available: {list(raw_cols.keys())}")

        # Product description column mapping
        prod_col = None
        for cand in ['Detailed_Product', 'Tên hàng gốc', 'Description']:
            if cand in raw_cols:
                prod_col = raw_cols[cand]
                break
        if not prod_col:
            raise KeyError(f"Could not find Product Description column in raw data. Available: {list(raw_cols.keys())}")

        # Standardize to internal names for processing
        raw_df['HS_Code_Internal'] = raw_df[hs_col].astype(str).apply(lambda x: re.sub(r'\D', '', x))
        raw_df['Detailed_Product_Internal'] = raw_df[prod_col].astype(str)
        
        # Ensure 'Mã HS' in taxonomy is also cleaned for matching
        tax_df['Mã HS_Internal'] = tax_df['Mã HS'].astype(str).apply(lambda x: re.sub(r'\D', '', x))
        
        raw_df['_clean'] = raw_df['Detailed_Product_Internal'].apply(self.clean_text)
        raw_df['_tok'] = raw_df['_clean'].apply(lambda x: ' '.join(self.tokenize_vi(x, True)))

        c_map = {}
        # If Cluster_ID is present, we use it for precise matching
        target_cluster_col = 'Cluster_ID'
        if '_cluster' in raw_df.columns: target_cluster_col = '_cluster'

        if target_cluster_col in raw_df.columns:
            for _, r in raw_df.iterrows():
                c_val = r[target_cluster_col]
                if pd.isna(c_val) or str(c_val).strip() == '': continue
                try:
                    c_map.setdefault((str(r['HS_Code_Internal']), int(float(c_val))), []).append(r['_tok'])
                except ValueError:
                    pass

        res = [''] * len(tax_df)

        cluster_id_matches = 0
        fallback_matches = 0

        # Iterate over unique HS codes to scope purity locally
        hs_codes = tax_df['Mã HS_Internal'].unique()
        for hs in hs_codes:
            tax_mask = tax_df['Mã HS_Internal'] == hs
            tax_indices = tax_df[tax_mask].index.tolist()

            docs = {}
            fb = {}
            sub_raw = raw_df[raw_df['HS_Code_Internal'] == hs]

            for i in tax_indices:
                r = tax_df.loc[i]
                l1, l2 = str(r.get('Lớp 1','')), str(r.get('Lớp 2',''))
                fb[i] = l2 if (l2 and l2.lower() not in ('nan','0')) else l1
                cid = r.get('Cluster_ID')

                cid_int = None
                if not pd.isna(cid) and str(cid).strip() != '':
                    try:
                        cid_int = int(float(cid))
                    except ValueError:
                        pass

                if cid_int is not None and (hs, cid_int) in c_map:
                    docs[i] = c_map[(hs, cid_int)]
                    cluster_id_matches += 1
                else:
                    p = '|'.join(re.escape(s) for s in fb[i].lower().split() if len(s)>2)
                    docs[i] = sub_raw[sub_raw['Detailed_Product_Internal'].str.contains(p, case=False, na=False)]['_tok'].tolist() if p else []
                    fallback_matches += 1

            # Extract keywords scoped to this HS code
            kw_m = self.extract_keywords_ai(docs, 12, fb)
            for i, k in kw_m.items(): 
                res[i] = k

        print(f"DEBUG: Keyword extraction matches: {cluster_id_matches} via Cluster_ID, {fallback_matches} via Fallback Regex.")
        tax_df['Keyword'] = res
        return tax_df.drop(columns=['Mã HS_Internal'], errors='ignore')
