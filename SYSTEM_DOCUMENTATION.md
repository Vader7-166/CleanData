# Tài Liệu Hệ Thống Xây Dựng Bộ Từ Điển Phân Loại Hải Quan

> **Mục đích**: Mô tả chi tiết luồng hoạt động, logic xử lý của hệ thống `Create_Dictionary` — hỗ trợ người xây dựng hệ thống lọc, làm sạch và chuẩn hóa dữ liệu hải quan.

---

## 1. Tổng Quan Hệ Thống

### 1.1 Mục tiêu
Hệ thống tự động xây dựng **bộ từ điển phân loại** (dictionary) từ dữ liệu tờ khai hải quan thô (NK/XK). Bộ từ điển này được sử dụng bởi hệ thống **CleanData** (downstream) để lọc, làm sạch và chuẩn hóa dữ liệu hải quan thông qua thuật toán **Aho-Corasick**.

### 1.2 Kiến trúc tổng thể

```
┌─────────────────────────────────────────────────────────────────┐
│                    DỮ LIỆU ĐẦU VÀO (Raw)                       │
│  File Excel NK/XK chứa tờ khai hải quan (HS_Code, Detailed_Product) │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              BƯỚC 1: TỰ ĐỘNG PHÂN LOẠI (auto_classify.py)      │
│  NLP Pipeline: Clean Text → Tokenize → TF-IDF → DBSCAN Cluster │
│  Output: draft_phan_loai_XXXX.xlsx                              │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              REVIEW THỦ CÔNG (Con người)                        │
│  Chỉnh sửa Lớp 2, Loại (NC/LK), gộp/xóa nhóm                 │
│  Lưu: phan_loai_XXXX.xlsx                                      │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│          BƯỚC 2: TRÍCH XUẤT KEYWORD (keyword_extractor.py)      │
│  Purity-Weighted Frequency + Cross-group TF-IDF                 │
│  Output: phan_loai_co_keyword_XXXX.xlsx                         │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│          BƯỚC 3: GỘP TỪ ĐIỂN (merge_to_dict.py)                │
│  Gộp tất cả file keyword → dictv2.csv                           │
│  → Sử dụng bởi hệ thống CleanData (Aho-Corasick)               │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 Cấu trúc file trong dự án

| File | Vai trò |
|:-----|:--------|
| `run_pipeline.py` | Điều phối pipeline (entry point chính) |
| `auto_classify.py` | Bước 1 — Phân loại tự động bằng NLP Clustering |
| `keyword_extractor.py` | Bước 2 — Trích xuất keyword phân biệt |
| `merge_to_dict.py` | Bước 3 — Gộp tất cả kết quả thành từ điển CSV |
| `llm_labeler.py` | Module phụ — Dùng LLM (Groq) đặt tên cluster (tùy chọn) |
| `main.py` | Phiên bản đơn giản ban đầu (legacy, không dùng trong pipeline) |
| `DICTIONARY_SPEC.md` | Quy cách kỹ thuật của file từ điển đầu ra |
| `GUIDE_REVIEW.md` | Hướng dẫn review file draft cho người dùng |
| `Raw/` | Thư mục chứa file dữ liệu thô NK/XK |

---

## 2. Dữ Liệu Đầu Vào

### 2.1 File Raw (NK/XK)
- **Định dạng**: Excel (`.xlsx`)
- **Quy ước tên**: `{MãHS}-{NK|XK}-{Kỳ}.xlsx` (VD: `9617-NK-Th12.2025.xlsx`)
- **Cột bắt buộc**:
  - `HS_Code`: Mã hải quan (8-10 chữ số)
  - `Detailed_Product`: Mô tả chi tiết sản phẩm trên tờ khai
- **Vị trí**: Thư mục `Raw/` hoặc thư mục raw bên ngoài

### 2.2 Các dòng sản phẩm được hỗ trợ

| Mã HS | Dòng SP |
|:------|:--------|
| 9617 | SP BÌNH/PHÍCH |
| 7020 | SP THỦY TINH |
| 8539 | SP ĐÈN/BÓNG ĐÈN |
| 9405 | SP ĐÈN/THIẾT BỊ CHIẾU SÁNG |
| 85167910 | SP THIẾT BỊ ĐIỆN GIA DỤNG |

---

## 3. BƯỚC 1 — Tự Động Phân Loại (`auto_classify.py`)

### 3.1 Luồng xử lý tổng quan

```
Đọc raw → Làm sạch text → Tokenize tiếng Việt → TF-IDF vectorize
→ DBSCAN clustering → Đặt tên cluster → Phát hiện NC/LK → Xuất draft
```

### 3.2 Chi tiết từng bước

#### Bước 1/5: Đọc dữ liệu raw
- Tìm file NK/XK tự động theo mã HS trong thư mục `Raw/`
- Hàm `load_raw_file()` tự phát hiện dòng header (scan 20 dòng đầu)
- Ghép NK + XK thành 1 DataFrame duy nhất

#### Bước 2/5: Tiền xử lý văn bản
- **`clean_text()`**: Loại bỏ mã SKU trước `#&`, ký tự đặc biệt, chỉ giữ chữ và số
- **`tokenize_vi()`**: Dùng **PyVi ViTokenizer** tách từ tiếng Việt, lọc **stopwords** (40+ từ dừng tiếng Việt + từ hải quan phổ biến + mã quốc gia + brand)
- Loại bỏ dòng rỗng sau tiền xử lý

#### Bước 3/5: Clustering theo mã HS
Với mỗi mã HS riêng biệt:

1. **TF-IDF Vectorization**: Chuyển text thành vector số
   - `max_features=5000`, `ngram_range=(1,2)`, `max_df=0.95`
2. **DBSCAN Clustering**: Nhóm sản phẩm tương tự
   - Dùng **cosine distance** (phù hợp cho text hơn euclidean)
   - `eps` (mặc định 0.65): Ngưỡng khoảng cách, càng cao → càng ít cluster
   - `min_samples` (mặc định 5): Số SP tối thiểu để tạo cluster, nhỏ hơn → OUTLIER
   - Sản phẩm không thuộc cluster nào → gán nhãn `-1` (OUTLIER)

3. **Đặt tên cluster** (hàm `get_cluster_names_tfidf()`):
   - Dùng **TF-IDF xuyên nhóm**: Mỗi cluster = 1 "tài liệu", so sánh giữa các cluster
   - Lọc token qua `_is_valid_cluster_token()`: Loại stopwords, mã SKU, token < 3 ký tự
   - Ưu tiên từ **tiếng Việt** hơn từ Latin
   - Sắp xếp từ theo tần suất xuất hiện trong cluster (đọc tự nhiên hơn)
   - Fallback: Dùng tên sản phẩm thực ngắn nhất nếu không đủ từ khóa

4. **LLM Labeling** (tùy chọn `--use-llm`):
   - Gọi **Groq API** (Llama 3.1) để đặt tên cluster có ý nghĩa hơn
   - Xử lý theo batch (15 cluster/request), retry tối đa 5 lần
   - Nếu lỗi → giữ nguyên tên TF-IDF

5. **Phát hiện Loại NC/LK** (hàm `detect_type()`):
   - Ưu tiên 1: Nếu ≥2 từ khóa LK (`linh kiện`, `nắp`, `vỏ`...) → **LK**
   - Ưu tiên 2: Tra bảng `HS_TYPE_MAP` (ánh xạ 100+ mã HS → NC/LK)
   - Ưu tiên 3: Nếu có 1 từ khóa LK (khi không có trong map) → **LK**
   - Mặc định: **NC** (Nội chính/Thành phẩm)

#### Bước 4/5: Gộp cluster trùng tên
- Hàm `merge_duplicate_clusters()`: Gộp cluster cùng (Mã HS, Lớp 2)
- Giữ cluster có nhiều SP nhất làm đại diện, cộng tổng số lượng SP

#### Bước 5/5: Xuất file Excel
File `draft_phan_loai_XXXX.xlsx` gồm 3 sheet:

| Sheet | Nội dung |
|:------|:---------|
| **Phân loại** | Bảng phân loại chính (Keyword, Mã HS, Dòng SP, Loại, Lớp 1, Lớp 2) |
| **Chi tiết Cluster** | Thêm cột Số lượng SP, Mô tả mẫu |
| **Raw + Cluster** | Toàn bộ dữ liệu gốc + Cluster_ID |

### 3.3 Cấu hình quan trọng

**Bảng HS_TAXONOMY**: Ánh xạ 100+ mã HS chi tiết → mô tả Lớp 1 mặc định (VD: `96170010` → `Phích và bình giữ nhiệt`)

**Bảng HS_TYPE_MAP**: Ánh xạ mã HS → Loại mặc định NC/LK

**LK_KEYWORDS**: 30+ từ khóa nhận diện linh kiện (`linh kiện`, `phụ tùng`, `nắp`, `vỏ`, `lõi`, `pcba`, `mạch`...)

---

## 4. REVIEW THỦ CÔNG (Human-in-the-loop)

Đây là bước **quan trọng nhất** — chất lượng từ điển phụ thuộc vào bước này.

### 4.1 Quy trình
1. Mở `draft_phan_loai_XXXX.xlsx` bằng Excel
2. Chỉnh sửa sheet **"Phân loại"**:
   - **Lớp 2**: Viết hoa chữ cái đầu, gộp nhóm tương tự, xử lý OUTLIER
   - **Loại**: Kiểm tra NC/LK chính xác
   - **Keyword**: Để trống (Bước 2 tự điền)
3. Tham khảo sheet "Chi tiết Cluster" và "Raw + Cluster" khi cần
4. Lưu thành `phan_loai_XXXX.xlsx` (bỏ `draft_`)

### 4.2 Quy tắc vàng
- Tên Lớp 2: 2-5 từ, ngắn gọn, danh từ chính đứng đầu
- Không chứa thương hiệu, thông số kỹ thuật
- Gộp nhóm bằng cách đặt tên Lớp 2 giống nhau

---

## 5. BƯỚC 2 — Trích Xuất Keyword (`keyword_extractor.py`)

### 5.1 Luồng xử lý

```
Đọc file phân loại → Đọc raw + cluster mapping → Purity-Weighted Frequency
→ Chống trùng lặp → Lưu kết quả
```

### 5.2 Chi tiết

#### Bước 1/4: Đọc file phân loại
- Đọc `phan_loai_XXXX.xlsx` (file đã review)

#### Bước 2/4: Đọc dữ liệu raw + cluster mapping
- **Ưu tiên**: Đọc mapping `Cluster_ID` từ file draft (sheet "Raw + Cluster") → chính xác hơn
- **Fallback**: Nếu không có draft → dùng regex match theo tên Lớp 2 trên dữ liệu raw

#### Bước 3/4: Trích xuất keyword — Thuật toán Purity-Weighted Frequency

**Đây là lõi thuật toán quan trọng nhất:**

Mỗi nhóm Lớp 2 (cùng mã HS) được coi là 1 "lớp" (class). Thuật toán tìm N-gram đặc trưng nhất cho mỗi lớp:

1. **Sinh N-gram** (1-gram, 2-gram, 3-gram) từ tên sản phẩm đã tokenize
2. **Tính Document Frequency (DF)**: Đếm số lần N-gram xuất hiện trong mỗi lớp và toàn cục
3. **Tính Purity**: `purity = local_freq / global_freq`
   - Purity = 1.0: N-gram chỉ xuất hiện trong 1 lớp → rất đặc trưng
   - Purity < 0.05: N-gram quá chung → loại bỏ (score = 0)
4. **Tính điểm**:
   ```
   score = local_freq × purity² × base_score
   ```
   - `base_score` = số từ trong N-gram (ưu tiên cụm dài hơn)
   - High Value keywords (`năng lượng mặt trời`, `nlmt`, `solar`): base_score = 20
   - 1-gram: phạt 50% (`score × 0.5`)

5. **Lọc keyword hợp lệ** (`_is_valid_keyword()`):
   - Loại mã rác (regex: `phi123`, `cz45`, `350ml`)
   - Loại cụm từ junk (`mới 100`, `chính hãng`, `nhãn hiệu`...)
   - Yêu cầu ≥ 3 ký tự

6. **Chống trùng lặp**: Nếu N-gram ngắn là tập con của N-gram dài đã chọn → bỏ N-gram ngắn
7. **Chọn top-N** keyword (mặc định 15) theo điểm giảm dần

#### Bước 4/4: Lưu kết quả
- Ghi cột `Keyword` vào file `phan_loai_co_keyword_XXXX.xlsx`
- Tự động đổi tên nếu file đang mở trong Excel

---

## 6. BƯỚC 3 — Gộp Từ Điển (`merge_to_dict.py`)

### 6.1 Luồng xử lý
1. Tìm tất cả file `phan_loai_co_keyword_*.xlsx`
2. Đọc và ghép thành 1 DataFrame
3. Loại bỏ dòng thiếu Keyword hoặc Lớp 2
4. Sắp xếp theo Mã HS → Lớp 1 → Lớp 2
5. Xuất file **`dictv2.csv`** (encoding `utf-8-sig`)

### 6.2 Output — Cấu trúc từ điển cuối cùng

| Cột | Mô tả |
|:----|:------|
| Keyword | Danh sách từ khóa phân cách bằng dấu phẩy |
| Dòng SP | Tên dòng sản phẩm |
| Loại | NC (Thành phẩm) hoặc LK (Linh kiện) |
| Lớp 1 | Phân loại cấp 1 |
| Lớp 2 | Phân loại cấp 2 |
| Mã HS | Mã hải quan |

---

## 7. Cách Hệ Thống CleanData Sử Dụng Từ Điển

File `dictv2.csv` được hệ thống CleanData downstream sử dụng với cơ chế:

1. **Aho-Corasick matching**: Tìm tất cả keyword khớp trong tên hàng
2. **Scoring**: Tính điểm cho mỗi dòng từ điển khớp
   - High Value keyword: +20 điểm
   - Keyword thường: +N điểm (N = số từ)
   - Junk keyword: 0 điểm (chỉ "nuốt" text)
3. **Consumption Logic**: Cụm dài khớp trước → "nuốt" text → cụm ngắn không khớp chồng
4. **Kết quả**: Dòng từ điển có điểm cao nhất → gán phân loại cho tên hàng

---

## 8. Hướng Dẫn Sử Dụng Pipeline

### 8.1 Chạy cho 1 mã HS

```bash
# Bước 1: Phân loại tự động
python run_pipeline.py --hs 7020 --step 1

# → Review thủ công file draft_phan_loai_7020.xlsx
# → Lưu thành phan_loai_7020.xlsx

# Bước 2: Trích xuất keyword
python run_pipeline.py --hs 7020 --step 2

# Bước 3: Gộp từ điển
python merge_to_dict.py
```

### 8.2 Chạy batch tất cả dòng SP

```bash
python run_pipeline.py --hs all --step 1
```

### 8.3 Tham số tùy chỉnh

| Tham số | Mặc định | Ý nghĩa |
|:--------|:---------|:---------|
| `--eps` | 0.65 | Ngưỡng DBSCAN (cao → ít cluster, thấp → nhiều cluster) |
| `--min-samples` | 5 | Số SP tối thiểu/cluster |
| `--use-llm` | Tắt | Dùng Groq LLM đặt tên cluster |
| `--nk` / `--xk` | Tự tìm | Chỉ định file raw thủ công |

---

## 9. Các Thuật Toán Chính

### 9.1 TF-IDF (Term Frequency — Inverse Document Frequency)
- Được dùng ở **2 chỗ**: clustering sản phẩm (Bước 1) và đặt tên cluster (Bước 1)
- Mục đích: Chuyển text thành vector số, từ càng đặc trưng → trọng số càng cao

### 9.2 DBSCAN (Density-Based Spatial Clustering)
- Không cần biết trước số cluster
- Tự phát hiện OUTLIER (sản phẩm không thuộc nhóm nào)
- Dùng cosine distance phù hợp cho dữ liệu text

### 9.3 Purity-Weighted Frequency
- Thuật toán tự phát triển để trích xuất keyword phân biệt
- Kết hợp tần suất cục bộ (local frequency) với độ tinh khiết (purity)
- Ưu tiên N-gram dài (cụ thể hơn) và từ chỉ xuất hiện trong 1 lớp

---

## 10. Dependency

| Thư viện | Vai trò |
|:---------|:--------|
| pandas | Đọc/ghi Excel, xử lý DataFrame |
| numpy | Tính toán ma trận |
| scikit-learn | TF-IDF, DBSCAN, cosine_distances |
| pyvi | Tách từ tiếng Việt (ViTokenizer) |
| openpyxl | Engine ghi file Excel |
| groq | Gọi LLM API (tùy chọn) |
