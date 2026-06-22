# CleanData - Kế hoạch cải thiện Accuracy (0.76 → 0.85-0.92)

> **Ngày tạo:** 2026-06-22
> **Mục tiêu:** Tăng accuracy phân loại `Dòng SP | Loại | Lớp 1 | Lớp 2` từ 0.76 lên 0.85-0.92
> **Ràng buộc:** CPU only
> **Dữ liệu chính:** HQ-2025.csv (train, referenced in notebook), DICT_HQ_2026.csv (dict mới 939 dòng), HSTaxonomy DB

---

## Phase 0: Chuẩn hóa naming convention ✅ HOÀN THÀNH

**Mục tiêu:** Thống nhất tên gọi giữa Dict Generator → Training Data → Output.

### Đã làm
- [x] Fix `DICT_HQ_2026.csv`: `Đèn UV`→`đèn uv`, `Sp truyền thống`→`SP truyền thống`, `Highbay`→`highbay`, `Lowbay`→`lowbay`, `Chưa phân loại`→`không_có`, `LED khác`→`led khác` (27 fixes)
- [x] Fix `dictv3.csv`: `SP LEd`→`SP LED`, `LED khác`→`led khác`, `Smart`→`smart`
- [x] Tạo `config/label_standard.json` — single source of truth cho tên gọi toàn hệ thống
- [x] Thêm `_load_label_standard()` + `_normalize_label()` vào `backend/core/dictionary_matcher.py`
- [x] Thêm `_load_label_standard()` + `_normalize_label()` vào `backend/core/dict_generator.py`
- [x] Thêm `_load_label_standard()` + `_normalize_label()` vào `backend/core/data_cleaner.py`
- [x] `dictionary_matcher.py:_load_dict()` gọi `_normalize_label()` khi load mọi dict
- [x] `dict_generator.py:generate_draft_taxonomy()` normalize output trước khi trả về
- [x] `dict_generator.py:extract_keywords_for_taxonomy()` normalize output
- [x] `data_cleaner.py:split_and_assign()` normalize label sau khi tách

### Output
- `config/label_standard.json` — single source of truth
- Mọi dict file load qua hệ thống đều được tự động normalize
- Mọi output đều qua normalize

---

## Phase 1: Phân tích lỗi chi tiết

**Mục tiêu:** Xác định chính xác model yếu ở đâu để các phase sau đi đúng hướng.

**Script cần viết:** `analysis/error_analysis.py`

### Steps
1. Load model + label_encoder từ `working/`
2. Load test set (10% từ notebook split) hoặc file `dataset/cleaned_merged_upload (6).csv`
3. Chạy predict AI + dict trên test set
4. **Breakdown accuracy từng cấp:**
   - Tách combined_label → 4 cột riêng
   - Tính accuracy cho `Dòng SP`, `Loại`, `Lớp 1`, `Lớp 2` riêng biệt
5. **Confusion matrix top-20 class** bị nhầm nhiều nhất → heatmap (matplotlib)
6. **Dict vs AI ratio:**
   - Bao nhiêu % dòng do Dict xử lý?
   - Accuracy của Dict? Accuracy của AI?
   - Overlap cases (dict + AI cùng sai, cùng đúng, khác nhau)
7. **Calibration curve:**
   - Chia confidence thành bins (0-0.5, 0.5-0.6, ..., 0.9-1.0)
   - Tính actual accuracy trong mỗi bin
   - Tìm optimal threshold (có thể 0.85 chưa tối ưu)

### Output mong đợi
- Bảng accuracy breakdown từng cấp
- Heatmap confusion matrix (lưu ảnh)
- Danh sách top-10 cặp class bị confuse nhiều nhất
- Biểu đồ calibration curve
- Report: dict accuracy %, AI accuracy %, optimal threshold

### Không cần train, chạy hoàn toàn trên CPU.

---

## Phase 2: Tích hợp DICT_HQ_2026 + HS Code filtering

**Mục tiêu:** Khai thác DICT_HQ_2026 (939 dòng, có Mã HS, keyword n-gram) thay thế/augment dictv3.

### 2a: Sửa `dictionary_matcher.py` để hỗ trợ HS Code filtering

```python
# Hiện tại: quét toàn bộ dict cho mọi input
# Mới: nếu input có Mã HS → lọc dict rows theo HS prefix trước khi Aho-Corasick match

# Trong _load_dict: lưu thêm dict rows grouped by Mã HS
# Trong predict(text, hs_code=None): nếu hs_code được cung cấp → chỉ match trong subset
```

### 2b: Sửa `data_cleaner.py` để dùng DICT_HQ_2026

```python
# Thay đổi default dict path từ dictv3 → DICT_HQ_2026
# Thêm HS Code vào input text: "HS: 9405 - Hãng: X - Công suất: Y - Sản phẩm: Z"
# Khi gọi matcher.predict(text, hs_code=ma_hs) → lọc theo HS
```

### 2c: Thêm rule-based pre-classification từ HS code

```python
# Trong process_async, trước khi gọi dict/AI:
# 1. Tra HSTaxonomy DB cho Mã HS
# 2. Nếu khớp chính xác + Số lượng SP trong dict > 100:
#    → Auto-fill Dòng SP, Loại, Lớp 1 (skip cả dict lẫn AI)
```

### 2d: Fallback chain mới

```
Input → [HS Code DB lookup] → có exact match? → auto-fill
        ↓ không
      → [DICT_HQ_2026 + HS filter] → score ≥ 15? → DONE
        ↓ không  
      → [PhoBERT AI] → conf ≥ 0.85? → DONE
        ↓ không
      → "Cần kiểm tra"
```

### Output
- `dictionary_matcher.py` updated với `predict(text, hs_code=None)`
- `data_cleaner.py` updated với HS-based pre-classification
- DICT_HQ_2026 làm default dict

---

## Phase 3: Sinh synthetic training data từ DICT_HQ_2026

**Mục tiêu:** Augment training set với ~9,000 mẫu mới từ keyword n-gram trong DICT_HQ_2026.

**Script cần viết:** `analysis/generate_synthetic_train.py`

### Cách làm
```python
# Mỗi dòng DICT_HQ_2026:
#   Keyword: "sân golf chỗ, sáng xe sân, xe sân golf, ..."
#   Label:   "SP truyền thống | NC | led khác | không_có"
#   HS:      85391010
#   Số lượng SP: 138
#
# Với mỗi keyword trong danh sách:
for kw in keywords:
    if len(kw.split()) >= 2:  # Chỉ lấy n-gram ≥ 2 từ (có ý nghĩa)
        text = f"HS: {hs_code} - Hãng: không_có - Công suất: không_có - Sản phẩm: {kw}"
        label = combined_label
        weight = log(1 + Số_lượng_SP)  # Trọng số theo tần suất
```

### Trọng số
- Dùng `Số lượng SP` làm sample weight:
  - Class phổ biến (Số lượng SP cao) → weight cao hơn
  - Class hiếm → weight thấp hơn nhưng vẫn được thêm vào

### Lưu ý
- Các keyword đã được làm sạch (clean_text_for_dict)
- Lớp 2 trống (80% dòng) → chỉ sinh cho Lớp 2 nếu có giá trị
- Tránh trùng lặp với training set gốc

### Output
- `dataset/synthetic_train_from_dict.csv` (~9,000 dòng)
- Merge với HQ-2025.csv → `dataset/train_augmented.csv`

---

## Phase 4: Multi-Task Hierarchical Classification

**Mục tiêu:** Thay siêu nhãn phẳng `"SP LED | NC | flood | led solar"` bằng 4 head riêng biệt.

**Script cần viết:** `training/train_multitask.py` (dựa trên notebook `PhoBertmappingv2(85%).ipynb`)

### Kiến trúc

```
PhoBERT-base (shared encoder, int8 quantized)
    │
    ├── Head Dòng SP: Linear(768 → ~6 classes)
    ├── Head Loại:     Linear(768 → 3 classes: NC, LK, không_có)
    ├── Head Lớp 1:    Linear(768 → ~35 classes)
    └── Head Lớp 2:    Linear(768 → ~45 classes)
```

### Loss function
```
Total = α·CrossEntropy(Dòng SP) 
      + β·CrossEntropy(Loại) 
      + γ·CrossEntropy(Lớp 1) 
      + δ·CrossEntropy(Lớp 2)
```
Với `α=1.0, β=1.0, γ=1.5, δ=2.0` (ưu tiên Lớp 2 vì fine-grained nhất).

### Hierarchical variant (nếu thời gian cho phép)
```
PhoBERT encoder
    ↓
Head Dòng SP → pred Dòng SP
    ↓
[concat: pooled_embedding + Dòng SP embedding]
    ↓
Head Loại → pred Loại
    ↓
[concat: pooled_embedding + Dòng SP embedding + Loại embedding]
    ↓
Head Lớp 1 → pred Lớp 1
    ↓
[concat: ... + Lớp 1 embedding]
    ↓
Head Lớp 2 → pred Lớp 2
```

### Data preparation
- Đọc HQ-2025.csv + synthetic_train_from_dict.csv
- Tách combined_label → 4 cột
- Mỗi cột có LabelEncoder riêng
- Tokenize với max_length=64

### Training config (CPU)
```
- batch_size: 8
- gradient_accumulation_steps: 4
- max_length: 64
- epochs: 3-5
- learning_rate: 2e-5 (thấp hơn để tránh overfit với 4 heads)
- warmup_ratio: 0.1
- weight_decay: 0.01
- lr_scheduler: cosine
- early_stopping_patience: 2
- fp16: False
- quantization: dynamic int8 (đã có trong code)
```

### Output
- Model mới lưu tại `working/model_v2/`
- 4 `label_encoder_*.pkl` (cho Dòng SP, Loại, Lớp 1, Lớp 2)

---

## Phase 5: Cross-validation 3 chiều

**Mục tiêu:** Dùng DICT_HQ_2026 làm "trọng tài" để phát hiện lỗi.

**Script cần viết:** `analysis/cross_validate.py`

### Setup
```
Test set 10%
    ├── DICT_HQ_2026 predict (với HS filter)
    ├── dictv3 predict  
    └── PhoBERT AI predict (model mới từ Phase 4)
         ↓
    So sánh 3 kết quả với ground truth
```

### Patterns cần phân loại
| Pattern | Hành động |
|---|---|
| Dict_HQ đúng, AI sai, dictv3 đúng | AI cần thêm mẫu train → thêm vào training set |
| Dict_HQ đúng, AI sai, dictv3 sai | Dict_HQ vượt trội → promote lên làm primary |
| Dict_HQ sai, AI đúng, dictv3 sai | AI mạnh hơn → giữ AI cho case này |
| Cả 3 sai | Hard case → đánh dấu "Cần kiểm tra" ưu tiên cao |
| Dict_HQ + AI đúng, dictv3 sai | Deprecate dictv3 entry tương ứng |

### Output
- `analysis/cross_validation_report.csv` — toàn bộ disagreement
- `analysis/dict_fixes_needed.csv` — keyword cần sửa trong dict
- `analysis/hard_cases.csv` — mẫu cần review thủ công

---

## Phase 6: Active Learning

**Mục tiêu:** Thu thập low-confidence samples → gán nhãn → retrain.

### Chu kỳ
```
1. Predict trên unlabeled data mới
2. Lọc samples có 0.5 < confidence < 0.85 (vùng model không chắc)
3. Xuất ra file CSV để review thủ công
4. Gán nhãn (có thể dùng frontend `DictionaryGeneratorWizard.tsx`)
5. Merge vào training set
6. Retrain model (Phase 4)
```

### Công cụ hỗ trợ
- Frontend `DictionaryGeneratorWizard.tsx` đã có sẵn
- Có thể export low-confidence samples → import vào wizard để gán nhãn

---

## Tổng kết lộ trình

| Phase | Cần train? | Dự kiến tăng acc | Thời gian (CPU) | Phụ thuộc |
|---|---|---|---|---|
| 0. Naming | Không | Gián tiếp | Đã xong | - |
| 1. Error Analysis | Không | - | 1-2h | Phase 0 |
| 2. DICT_HQ_2026 + HS | Không | +2-4% | 2-3h | Phase 0 |
| 3. Synthetic Data | Không | +2-5% | 1h | Phase 0,2 |
| 4. Multi-Task | Có | +5-10% | 4-8h train | Phase 1,3 |
| 5. Cross-validation | Không | +1-3% | 1-2h | Phase 2,4 |
| 6. Active Learning | Có | +3-7% | Theo chu kỳ | Phase 4 |

**Tổng dự kiến:** 0.76 → 0.85-0.92

---

## Ghi chú kỹ thuật

### Các file quan trọng
| File | Vai trò |
|---|---|
| `backend/core/data_cleaner.py` | AI inference pipeline (PhoBERT) |
| `backend/core/dictionary_matcher.py` | Aho-Corasick matcher cho từ điển |
| `backend/core/dict_generator.py` | TF-IDF + DBSCAN dict generator |
| `backend/models.py` | DB schema (HSTaxonomy, HSCustomsReference) |
| `PhoBertmappingv2(85%).ipynb` | Notebook train PhoBERT gốc (reference) |
| `config/label_standard.json` | Chuẩn tên gọi toàn hệ thống |
| `dataset/DICT_HQ_2026.csv` | Dict mới 939 dòng, auto-gen từ file kết quả |
| `dataset/dictv3.csv` | Dict cũ 174 dòng (SP LED) |
| `dataset/dictv2.csv` | Dict legacy 1533 dòng (đa HS) |
| `dataset/cleaned_merged_upload (6).csv` | File output mẫu (30K dòng) |

### API endpoints liên quan
| Endpoint | Chức năng |
|---|---|
| `GET /api/taxonomy` | Lấy toàn bộ HSTaxonomy |
| `POST /api/taxonomy` | Thêm taxonomy record mới |
| `POST /api/taxonomy/check-hs-codes` | Tra cứu HS code (longest prefix) |
| `POST /api/dictionaries/generate/step1` | Tạo dict draft từ raw data |

### Environment variables
| Variable | Dùng ở đâu |
|---|---|
| `MODEL_PATH` | `data_cleaner.py` — path đến model PhoBERT |
| `GROQ_API_KEY` | `dict_generator.py` — LLM labeling |
| `DEEPSEEK_API_KEY` | `dict_generator.py` — DeepSeek LLM labeling |

### Keyword đặc biệt trong dict
- **HIGH_VALUE_KEYWORDS**: `năng lượng mặt trời`, `nlmt`, `âm trần`, `downlight`, `highbay`, ... → score = 25
- **JUNK_KEYWORDS**: `chiếu sáng`, `mới 100`, `hàng mới`, ... → score = 0 (bị nuốt)
- **DICT_THRESHOLD**: 15 — điểm tối thiểu để dict auto-accept

### DICT_HQ_2026 vs dictv3
| | dictv3 | DICT_HQ_2026 |
|---|---|---|
| Số dòng | 174 | 939 |
| Keyword style | Từ đơn, nhiều junk | N-gram 2-4 từ, sát thực tế |
| Mã HS | Gần như không có | 100% có (91 mã khác nhau) |
| Phạm vi HS | Chỉ 9405 | 9405 + 8539 |
| Số lượng SP | Không có | Có (min=1, max=8297) |
| Lớp 2 | Đầy đủ | 80% trống |
