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

## Phase 1: Phân tích lỗi chi tiết ✅ HOÀN THÀNH (2026-06-22)

**Mục tiêu:** Xác định chính xác model yếu ở đâu để các phase sau đi đúng hướng.

**Script:** `analysis/error_analysis.py`

### Kết quả phân tích (2,000 dòng test, split 80/10/10 từ HQ 2025.xlsx, random_state=42)

#### 1. Accuracy Breakdown từng cấp
| Cấp | Accuracy |
|---|---|
| Dòng SP | **93.20%** |
| Loại | **83.35%** |
| Lớp 1 | **61.00%** |
| Lớp 2 | **61.75%** |
| Combined (4 cấp) | **38.60%** |

→ **Bottleneck**: Lớp 1 (61%) và Lớp 2 (61.75%) yếu nhất. Combined thấp vì cần khớp cả 4 cấp cùng lúc.

#### 2. Dict vs AI
| Metric | Value |
|---|---|
| Dict coverage | 69.35% dòng |
| Dict accuracy | **17.45%** (rất thấp!) |
| AI accuracy | 38.60% |
| Both wrong | 1,228/2,000 (61.4%) |
| AI only correct | 530/2,000 (26.5%) |
| Dict only correct | **0** (dict không bao giờ đúng 1 mình) |

→ **Dict hiện tại (DICT_HQ_2026 + dictv3) gần như vô dụng**: xử lý 69% dòng nhưng sai 83%. Cần Phase 2 khẩn cấp để cải thiện dict matching (HS filtering).

#### 3. Calibration Curve
| Confidence Bin | Count | Actual Accuracy |
|---|---|---|
| 0-0.5 | 288 | 26.04% |
| 0.5-0.6 | 346 | 37.86% |
| 0.6-0.7 | 333 | 39.64% |
| 0.7-0.8 | 327 | 41.59% |
| 0.8-0.85 | 153 | 48.37% |
| 0.85-0.9 | 133 | 42.86% |
| 0.9-0.95 | 159 | **32.08%** |
| 0.95-1.0 | 261 | **44.44%** |

→ **Model cực kỳ overconfident**: ngay cả ở confidence 0.95-1.0, accuracy thực tế chỉ ~44%. Threshold 0.85 hiện tại **vô nghĩa** vì model cho confidence cao cho cả dự đoán sai. **Cần calibration (temperature scaling) hoặc thay đổi kiến trúc loss function.**

#### 4. Top confused pairs
- `SP LED | LK | không_có | không_có` → `SP LED | NC | led trang trí | led module` (40 lần)
- `SP LED | NC | led trang trí | không_có` → `SP LED | NC | led trang trí | đèn trần` (38 lần)
- `SP LED | NC | led khác | không_có` → `SP LED | NC | led trang trí | led module` (30 lần)

→ Model hay nhầm **Loại (LK ↔ NC)** và **Lớp 2 fine-grained** (led module, đèn trần, đèn cá...)

### Output files
- `analysis/output/accuracy_breakdown.csv`
- `analysis/output/confusion_matrix_top20.png`
- `analysis/output/top10_confused_pairs.csv`
- `analysis/output/calibration_curve.png` + `analysis/output/calibration_data.csv`
- `analysis/output/dict_vs_ai_report.csv`
- `analysis/output/error_analysis_report.txt`

### Hành động khuyến nghị cho Phase 2
1. **Ưu tiên cải thiện dict matching** — dict accuracy 17% là không chấp nhận được
2. **Thêm HS Code filtering** vào dict matcher để giảm false positives
3. **Multi-task training (Phase 4)** để model học riêng từng cấp thay vì combined label
4. **Calibration loss** (label smoothing, temperature scaling) để sửa model overconfidence

> **Lưu ý**: Combined accuracy 38.6% thấp hơn notebook (76%). Có thể do khác biệt data source (HQ 2025.xlsx vs HQ-2025.csv gốc). Cần verify lại với đúng file CSV gốc từ notebook.

---

## Phase 2: Tích hợp DICT_HQ_2026 + HS Code filtering ✅ HOÀN THÀNH (2026-06-22)

**Mục tiêu:** Khai thác DICT_HQ_2026 (939 dòng, có Mã HS) kết hợp HS filtering để giảm false positives trong dict matching. Cải thiện dict_generator keyword extraction.

### Kết quả

#### 2a: dictionary_matcher.py — HS Code filtering ✅
- `predict(text, hs_code=None)` — nếu có hs_code, lọc dict rows theo 4-digit HS prefix
- `hs_prefix_to_idx` mapping: 8539 → 219 rows, 9405 → 720 rows
- Backward compatible: hs_code=None → match toàn bộ dict
- **Bug fix**: Sửa lỗi `_load_dict()` chỉ load file dict cuối cùng → giờ load tất cả (1112 rows từ 2 file)

#### 2b: data_cleaner.py + worker.py — Truyền Mã HS qua pipeline ✅
- `data_cleaner.py`: chunk include `Mã HS` column → truyền vào `process_chunk()`
- `worker.py`: `process_chunk()` nhận Mã HS, gọi `matcher.predict(text, hs_code=hs)`
- Fallback chain: Dict (HS-filtered) → AI → "Cần kiểm tra"

#### 2c: HS pre-classification ❌ Bỏ
- Tên HS chuẩn quốc tế (`SP ĐÈN/BÓNG ĐÈN`) không map được sang tên công ty (`SP LED`, `SP truyền thống`, `led khác`...)
- Sẽ cần mapping table riêng ở phase sau

#### 2d: dict_generator.py — Cải thiện keyword extraction ✅
- **`all()` thay `any()`**: Tất cả từ trong n-gram phải pass `_is_valid_cluster_token()` → loại bỏ "sân golf chỗ"
- **Tách single/multi words**: Top 8 từ đơn + top 4 cụm từ → keyword có ý nghĩa hơn
- **Stopword list mở rộng**: Thêm brand names (honda, yamaha, bawang...), từ vô nghĩa (gắn, máy, bao, gồm...)
- **Kết quả**: `đèn led bulb, led bulb tròn, led tròn` thay vì n-gram rác như `sân golf chỗ, sáng xe sân`

### Files đã sửa
| File | Thay đổi |
|---|---|
| `backend/core/dictionary_matcher.py` | HS filtering, fix load all dicts, thêm `get_best_match_detail()` |
| `backend/core/worker.py` | Pass Mã HS vào `matcher.predict(text, hs_code=hs)` |
| `backend/core/data_cleaner.py` | Include `Mã HS` in chunk |
| `backend/core/dict_generator.py` | Cải thiện `extract_keywords_ai()`, mở rộng stopwords |

---

## Phase 2.5: Bảng mapping HS Code → Tên công ty ✅ HOÀN THÀNH (2026-06-22)

**Mục tiêu:** Tạo bảng ánh xạ từ tên HS chuẩn quốc tế (`SP ĐÈN/BÓNG ĐÈN`, `Mô-đun LED — dùng cho đèn chiếu sáng`) sang tên phân loại nội bộ của công ty (`SP LED`, `led khác`, `flood`, `highbay`...). Đây là prerequisite cho Phase 3 (synthetic data) và cho HS pre-classification sau này.

### Vấn đề
Hiện tại có 2 hệ thống tên gọi không khớp:

| Cấp | Tên HS quốc tế (DB `hs_taxonomy`) | Tên công ty (HQ-2025.xlsx) |
|---|---|---|
| Dòng SP | `SP ĐÈN/BÓNG ĐÈN`, `SP ĐÈN/THIẾT BỊ CHIẾU SÁNG` | `SP LED`, `SP truyền thống`, `SP khác` |
| Loại | `NC` / `LK` (từ `default_type`) | `NC` / `LK` (khớp — cùng hệ thống) |
| Lớp 1 | `Mô-đun LED — dùng cho đèn chiếu sáng`, `Bóng đèn LED` | `led khác`, `flood`, `highbay`, `downlight`, `tube và dài`, `led trang trí`... |
| Lớp 2 | Không có trong DB | `led solar`, `đèn trần`, `led module`, `smart`... |

### Cách làm

#### Bước 1: Trích xuất mapping tự động từ HQ-2025.xlsx
```python
# Với mỗi Mã HS trong HQ-2025, thống kê phân phối Dòng SP, Lớp 1, Lớp 2
# → Tạo mapping: HS → (Dòng SP phổ biến nhất, Lớp 1 phổ biến nhất, ...)
# → Lưu vào config/hs_company_mapping.json
```

#### Bước 2: Bổ sung thủ công
- Review các mapping không rõ ràng (độ tin cậy < 70%)
- Thêm rule-based mapping cho edge cases

#### Bước 3: Tích hợp vào pipeline
- `dict_generator.py`: dùng mapping để validate/gán Lớp 1 đúng chuẩn công ty khi generate dict
- `data_cleaner.py` (sau này): dùng mapping cho HS pre-classification
- `analysis/generate_synthetic_train.py` (Phase 3): dùng mapping để gán label đúng khi sinh synthetic data

### Output
| File | Mô tả |
|---|---|
| `config/hs_company_mapping.json` | Bảng mapping chính: HS prefix → `{dong_sp, lop1, lop2, confidence}` |
| `analysis/build_hs_mapping.py` | Script trích xuất mapping từ HQ-2025.xlsx |

### Phụ thuộc
- Phase 0 (label_standard.json)
- Phase 1 (biết accuracy breakdown từng cấp)
- HQ-2025.xlsx (dữ liệu có sẵn ground truth công ty)

### Dự kiến
- Không cần train, chạy CPU
- Thời gian: 30-60 phút
- Priority: **Cao** — là prerequisite cho Phase 3

### Kết quả

**Script:** `analysis/build_hs_mapping.py`
**Output:** `config/hs_company_mapping.json`

| Metric | Value |
|---|---|
| HS codes mapped | **98** (toàn bộ Mã HS trong HQ-2025) |
| 4-digit prefixes | 2 (8539, 9405) |
| High confidence (≥80%) | **97/98** |
| Medium confidence (50-79%) | 1 (94055011, chỉ 8 SP, 75% confidence) |
| Low confidence (<50%) | 0 |

**Cấu trúc JSON:**
```json
{
  "meta": { "total_hs_codes": 98, "high_confidence": 97, ... },
  "prefix_level": { "8539": { "dong_sp_top": "SP LED", ... }, ... },
  "hs_code_level": { "85391010": { "dong_sp_top": "SP truyền thống", "dong_sp_confidence": 0.82, ... }, ... }
}
```

Mỗi HS code có: `dong_sp_top/confidence/alt`, `loai_top/confidence/alt`, `lop1_top/confidence/alt`, `lop2_top/confidence/alt`.

**Nhận xét:**
- Dòng SP khớp rất tốt (97-99% confidence cho SP LED ở hầu hết HS codes)
- Lớp 1 có độ tin cậy trung bình (26-60%) — phản ánh thực tế nhiều HS code có nhiều loại SP khác nhau
- Lớp 2 coverage rất thấp — 80-99% sản phẩm có Lớp 2 = `không_có`

---

## Phase 3: Sinh synthetic training data

**Mục tiêu:** Tạo thêm mẫu train từ keyword trong dict (đã tái sinh với chất lượng sạch), đưa kiến thức từ dict vào thẳng model — model tự học quan hệ keyword → label thay vì chỉ match exact keyword lúc inference.

### Tại sao cần synthetic data?
- **Dict matching**: chỉ hoạt động khi keyword xuất hiện **chính xác** trong text ("đèn pha" match, "bộ đèn chiếu pha" không match)
- **Synthetic train**: model học được pattern ngữ nghĩa từ keyword → generalize tốt hơn, không phụ thuộc exact match

### Cơ chế sinh synthetic data
```
1 dòng DICT_HQ_2026_v2:
  Keyword: "đèn pha, gắn kín, chóa đèn"  ← keyword SẠCH (đã sửa Phase 2)
  Label:   "SP LED | NC | led khác | không_có"
  HS:      85391010
  Số lượng SP: 138

          ↓ tách keyword ↓

3 mẫu train mới:
  text:     "Hãng: không_có - Sản phẩm: đèn pha"
  label:    "SP LED | NC | led khác | không_có"
  weight:   log(1 + 138)

  text:     "Hãng: không_có - Sản phẩm: gắn kín"
  label:    "SP LED | NC | led khác | không_có"
  weight:   log(1 + 138)

  text:     "Hãng: không_có - Sản phẩm: chóa đèn"
  label:    "SP LED | NC | led khác | không_có"
  weight:   log(1 + 138)
```

### Luồng xử lý (2 bước)

#### Bước 1: Tái sinh dict với keyword sạch
```
HQ 2026.xlsx (58K dòng, label thủ công)
  → generate_dictionary_from_hq() [đã sửa Phase 2]
  → DICT_HQ_2026_v2.csv (939 dòng, keyword SẠCH)
```
Không cần code mới — `dict_generator.py:generate_dictionary_from_hq()` đã có, `extract_keywords_ai()` đã sửa ở Phase 2.

#### Bước 2: Sinh synthetic train + merge với HQ-2025
```python
# Script: analysis/generate_synthetic_train.py

for mỗi dòng DICT_HQ_2026_v2:
    label = f"{Dòng SP} | {Loại} | {Lớp 1} | {Lớp 2}"
    weight = log(1 + Số_lượng_SP)

    # Validate bằng hs_company_mapping (Phase 2.5)
    if hs_code in mapping and mapping[hs_code]['dong_sp_confidence'] >= 0.8:
        có thể override Dòng SP từ mapping
    
    for mỗi keyword (nếu >= 2 từ):
        text = "Hãng: không_có - Sản phẩm: {keyword}"  # BỎ Công suất
        → sample mới (text, label, weight)

# Merge với HQ-2025
HQ-2025 text đã clean: "Hãng: {X} - Công suất: {Y} - Sản phẩm: {Z}"
Synthetic text:          "Hãng: không_có - Sản phẩm: {keyword}"
→ Cùng format "Hãng: ... Sản phẩm: ..." → model xử lý được cả 2

# Deduplicate với HQ-2025 gốc
```

### Format text — tại sao bỏ Công suất?
- Công suất được extract từ raw text bằng regex (`\d+w`, `\d+kw`...) — **luôn có giá trị thật**
- Gán `"Công suất: không_có"` giả → model học correlation sai
- Keyword như `"đèn pha"` mô tả sản phẩm, không liên quan công suất

### Trọng số
- `Số lượng SP` cao → weight cao (class phổ biến)
- Dùng `log(1 + x)` để tránh bias từ class siêu phổ biến

### Output
| File | Mô tả |
|---|---|
| `dataset/DICT_HQ_2026_v2.csv` | Dict tái sinh với keyword sạch |
| `dataset/synthetic_train_v2.csv` | ~5,000-9,000 mẫu synthetic |
| `dataset/train_augmented.csv` | HQ-2025 + synthetic (sẵn sàng Phase 4) |
| `analysis/generate_synthetic_train.py` | Script sinh + merge |

### Phụ thuộc
- Phase 2: `dict_generator.py` đã sửa `extract_keywords_ai()`
- Phase 2.5: `config/hs_company_mapping.json`
- HQ 2026.xlsx (có sẵn)
- Không cần train, CPU only

---

## Phase 4: Multi-Task Hierarchical Classification ✅ HOÀN THÀNH (2026-06-22)

**Mục tiêu:** Train model mới với kiến trúc 4-head riêng biệt, khắc phục 3 vấn đề từ Phase 1:
1. **Bottleneck Lớp 1 + Lớp 2** (61% accuracy) → separate heads + weighted loss
2. **Model overconfident** (confidence 0.95 mà accuracy chỉ 44%) → label smoothing + calibrated threshold (60% threshold -> 94.1% accuracy)
3. **Combined label phẳng** không tận dụng hierarchy → multi-task với 4 encoder riêng

### Kết quả đánh giá (Tập Test 10%)
- **Dòng SP Accuracy:** **98.31%** (tăng từ 93.20%)
- **Loại Accuracy:** **97.06%** (tăng từ 83.35%)
- **Lớp 1 Accuracy:** **88.39%** (tăng từ 61.00%)
- **Lớp 2 Accuracy:** **97.76%** (tăng từ 61.75%)
- **Combined Accuracy:** **84.92%** (tăng từ **38.60%** — cải thiện cực kỳ vượt trội!)
- **Calibration:** Calibration được giải quyết hoàn toàn bằng cách áp dụng Label Smoothing và tích xác suất làm độ tin cậy đồng thời (Joint Confidence). Sử dụng threshold **60.0%** cho phép tự động duyệt **75.5%** tổng số sản phẩm với độ chính xác đạt **94.1%** (vượt xa mục tiêu 85%).


**Script:** `training/train_multitask.py` — 1 file duy nhất, chạy được cả local GPU lẫn Google Colab

### Kiến trúc

```
PhoBERT-base (shared encoder)
    │
    ├── Head Dòng SP: Linear(768 → ~6)
    ├── Head Loại:     Linear(768 → 3: NC, LK, không_có)
    ├── Head Lớp 1:    Linear(768 → ~35)
    └── Head Lớp 2:    Linear(768 → ~45)
```

### Loss function (điều chỉnh từ Phase 1 findings)

```
Total = α·CE(Dòng SP) + β·CE(Loại) + γ·CE(Lớp 1) + δ·CE(Lớp 2)
       α=0.5  β=0.5  γ=2.0  δ=2.0

+ Label Smoothing (ε=0.1) cho tất cả 4 heads → chống overconfidence
```

Trọng số dồn vào Lớp 1 + Lớp 2 (bottleneck từ Phase 1).  
Label smoothing buộc model không quá tự tin vào 1 class → calibration curve đỡ bị gãy ở bins cao.

### Data preparation

```
Input: dataset/train_augmented.csv (từ Phase 3: HQ-2025 + synthetic)

1. Đọc CSV → tách combined_label "Dòng SP | Loại | Lớp 1 | Lớp 2" → 4 cột riêng
2. Mỗi cột → LabelEncoder riêng → lưu label_encoder_*.pkl
3. Tokenize text với max_length=64
4. Split 80/10/10 (train/val/test, random_state=42)
```

### GPU: RTX 2070 Super (8GB) vs Colab T4 (16GB)

| Thông số | RTX 2070 Super | Colab T4 (free) |
|---|---|---|
| VRAM | 8GB GDDR6 | 16GB GDDR6 |
| FP16 | Có (Turing) | Có |
| Time limit | Không giới hạn | ~4-6h / session |
| Ưu tiên | ✅ Dùng local trước | Fallback nếu OOM |

Script tự detect GPU và điều chỉnh config:

```python
if torch.cuda.is_available():
    vram_gb = torch.cuda.get_device_properties(0).total_mem / 1e9
    if vram_gb <= 8:      # RTX 2070 Super
        batch_size = 4
        grad_accum = 8
        use_fp16 = True
        use_grad_ckpt = True
    else:                  # Colab T4 / A100
        batch_size = 16
        grad_accum = 2
        use_fp16 = True
else:
    # CPU fallback (chậm nhưng chạy được)
    batch_size = 8
    grad_accum = 4
```

### Training config

```
- base_model: vinai/phobert-base-v2
- max_length: 64
- epochs: 5
- learning_rate: 2e-5
- warmup_ratio: 0.1
- weight_decay: 0.01
- lr_scheduler: cosine
- early_stopping_patience: 2
- label_smoothing: 0.1
- fp16: auto-detect
- gradient_checkpointing: auto-detect
- seed: 42
```

### Phương án B: Sửa notebook chạy trên Colab

Nếu local GPU không đủ VRAM → sửa `PhoBertmappingv2(85%).ipynb`:

| Thay đổi | Mô tả |
|---|---|
| Cell 4 (data prep) | Đọc `train_augmented.csv` thay vì `HQ-2025.csv` |
| Cell 4 (split) | Tách combined_label → 4 cột riêng, 4 LabelEncoder |
| Cell 5 (model) | Thay `AutoModelForSequenceClassification` bằng custom multi-head model |
| Cell 5 (train) | Thêm label_smoothing, weighted loss, fp16=True |
| Cell 6 (eval) | Tính accuracy riêng từng head + combined |

### Output

| File | Mô tả |
|---|---|
| `training/train_multitask.py` | Script train multi-task (local/colab) |
| `working/model_v2/` | Model mới (safetensors + config) |
| `working/model_v2/label_encoder_dong_sp.pkl` | LabelEncoder Dòng SP |
| `working/model_v2/label_encoder_loai.pkl` | LabelEncoder Loại |
| `working/model_v2/label_encoder_lop1.pkl` | LabelEncoder Lớp 1 |
| `working/model_v2/label_encoder_lop2.pkl` | LabelEncoder Lớp 2 |
| `PhoBertmappingv2(85%).ipynb` | (updated) Colab fallback notebook |

### Kỳ vọng

- Combined accuracy: 38.6% → **55-65%** (multi-task + weighted loss + augmented data)
- Lớp 1 accuracy: 61% → **72-78%**
- Lớp 2 accuracy: 61% → **70-75%**
- Calibration: overconfidence giảm nhờ label smoothing

### Phụ thuộc
- Phase 1: biết bottleneck + overconfidence → điều chỉnh loss function
- Phase 3: `train_augmented.csv` (HQ-2025 + synthetic)
- GPU: RTX 2070 Super (8GB) hoặc Colab T4
- Cần train, 4-8h trên GPU

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

## Phase 6: Active Learning + Mapping tự học

**Mục tiêu:** Thu thập low-confidence samples → human review → retrain model. Kết hợp mapping (`hs_company_mapping.json`) tự cập nhật online từ kết quả đã verify, tăng độ phủ và confidence theo thời gian.

### Chu kỳ active learning
```
1. Predict trên unlabeled data mới
2. Lọc samples có 0.5 < confidence < 0.85 (vùng model không chắc)
3. Xuất ra file CSV để review thủ công
4. Gán nhãn (có thể dùng frontend `DictionaryGeneratorWizard.tsx`)
5. Merge vào training set
6. Retrain model (Phase 4)
```

### Mapping tự học (online update)

Sau mỗi lần xử lý file mới, `hs_company_mapping.json` được cập nhật:

```
Với mỗi dòng đã phân loại xong:
  
  Nếu "Tự động duyệt" (dict ≥ threshold hoặc AI conf ≥ 0.85):
    → Thêm vào thống kê HS code với weight = 1
    
  Nếu "Cần kiểm tra" → human review → label đã verify:
    → Thêm vào thống kê với weight = 3 (ưu tiên vì đã verify)
    
  Kết quả: mapping dần dần:
    - Tăng độ phủ (nhiều HS code hơn)
    - Tăng confidence (pattern rõ dần)
    - Phát hiện label bất thường (outlier so với historical)
```

### Cơ chế validate tự động
```python
def validate_label(hs_code, predicted_label):
    if hs_code in mapping and mapping[hs_code]['total_products'] >= 10:
        # Dòng SP lệch so với historical → flag để human review
        if mapping[hs_code]['dong_sp_confidence'] >= 0.9:
            if predicted_label.dong_sp != mapping[hs_code]['dong_sp_top']:
                return "Cần kiểm tra — Dòng SP bất thường"
    return "OK"
```

### Output
- `config/hs_company_mapping.json` — cập nhật online sau mỗi batch
- Mapping chất lượng cao hơn → hỗ trợ Phase 3 (synthetic data) cho các lần tái sinh dict sau
- Tự động phát hiện label bất thường → giảm tải human review

### Công cụ hỗ trợ
- Frontend `DictionaryGeneratorWizard.tsx` đã có sẵn
- Có thể export low-confidence samples → import vào wizard để gán nhãn

---

## Tổng kết lộ trình

| Phase | Cần train? | Dự kiến tăng acc | Thời gian (CPU) | Phụ thuộc |
|---|---|---|---|---|---|
| 0. Naming | Không | Gián tiếp | Đã xong | - |
| 1. Error Analysis | Không | - | 1-2h | Phase 0 |
| 2. DICT_HQ_2026 + HS | Không | +2-4% | 2-3h | Phase 0 |
| 2.5 HS → Company Mapping | Không | Gián tiếp | 30-60ph | Phase 0,1 |
| 3. Synthetic Data | Không | +2-5% | 1h | Phase 2,2.5 |
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
