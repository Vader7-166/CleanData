## Context

Sau Phase 0 (chuẩn hóa naming convention), hệ thống đã có pipeline phân loại ổn định với 2 tầng:
1. **DictionaryMatcher**: Aho-Corasick automaton, score threshold ≥ 5, trả về `Dòng SP | Loại | Lớp 1 | Lớp 2 | Mã HS`
2. **PhoBERT AI**: model `working/model.safetensors`, confidence threshold ≥ 0.85, fallback khi dict không match

Accuracy hiện tại chỉ đo trên combined label (`Ket_Qua_Gop`) — chưa biết model yếu ở cấp nào (Dòng SP, Loại, Lớp 1, hay Lớp 2). Cũng chưa rõ tỉ lệ dict vs AI xử lý, chưa có calibration analysis để verify threshold 0.85 có tối ưu không.

Script chạy hoàn toàn offline trên CPU, chỉ dùng để phân tích — không ảnh hưởng production.

## Goals / Non-Goals

**Goals:**
- Load model + label encoder từ `working/`, chạy predict AI + dict trên test set
- Breakdown accuracy 4 cấp riêng biệt: Dòng SP, Loại, Lớp 1, Lớp 2
- Confusion matrix top-20 class bị confuse (heatmap matplotlib)
- Dict vs AI ratio: % dòng dict xử lý, accuracy từng bên, overlap analysis
- Calibration curve: confidence bins → actual accuracy, tìm optimal threshold
- Top-10 cặp class bị confuse nhiều nhất

**Non-Goals:**
- Không train model
- Không sửa pipeline production (`data_cleaner.py`, `dictionary_matcher.py`)
- Không tạo API endpoint mới
- Không sinh dữ liệu mới

## Decisions

### 1. Test set source: `dataset/HQ 2025.xlsx` với split giống notebook
- Tái tạo chính xác split 80/10/10 từ notebook với `random_state=42`
- File có ~310K dòng với ground truth (`Dòng SP`, `Loại`, `Lớp 1`, `Lớp 2`) đã được gán nhãn thủ công
- **KHÔNG dùng `cleaned_merged_upload (6).csv`** vì đây là file output của pipeline — các cột label trong đó do chính pipeline gán, không phải ground truth thật
- Test set = 10% held-out (~31K dòng), chưa từng được model thấy trong quá trình train

### 2. Input text: dùng cột `text` đã được clean trong quá trình load data
- Text được tạo theo format: `"Hãng: {X} - Công suất: {Y} - Sản phẩm: {Z}"` + clean qua `clean_text()` (giống hệt notebook)
- Đảm bảo input cho AI và Dict match chính xác format training

### 3. Tái sử dụng code có sẵn thay vì viết lại
- Import `DataCleaner`, `DictionaryMatcher`, `_normalize_label` từ backend thay vì copy code
- Đảm bảo kết quả phân tích phản ánh đúng production behavior
- **Alternative**: Viết inference script độc lập → có thể miss edge cases trong production pipeline

### 4. Calibration bins: 0-0.5, 0.5-0.6, 0.6-0.7, 0.7-0.8, 0.8-0.85, 0.85-0.9, 0.9-0.95, 0.95-1.0
- Bin cuối cùng mịn hơn vì confidence ≥ 0.85 là vùng auto-accept hiện tại
- Tìm điểm mà actual accuracy bắt đầu giảm để xác định optimal threshold

### 5. Output lưu trong `analysis/output/`
- `accuracy_breakdown.csv` — bảng accuracy 4 cấp
- `confusion_matrix_top20.png` — heatmap
- `top10_confused_pairs.csv` — danh sách cặp confuse
- `calibration_curve.png` — biểu đồ calibration
- `dict_vs_ai_report.csv` — báo cáo dict vs AI
- `error_analysis_report.txt` — tổng hợp text report

## Risks / Trade-offs

- [Risk] File test set 30K dòng → xử lý lâu trên CPU (dict matching theo từng dòng) → Mitigation: dùng Aho-Corasick batch không hỗ trợ sẵn, nhưng 30K dòng là khả thi; chạy AI batch 64 để tăng tốc
- [Risk] Một số dòng trong test set không có đủ cột `Hãng`/`Công suất` → input text thiếu → Mitigation: fill `không_có` cho các cột thiếu để khớp format pipeline
- [Risk] Ground truth có thể có label không chuẩn (chưa qua normalize) → Mitigation: normalize cả ground truth lẫn prediction trước khi so sánh

## Open Questions

- File test set có column `Tên hàng` không, hay cần reconstruct từ cột khác? → Kiểm tra khi implement
- Có nên sample 5K-10K dòng thay vì full 30K để chạy nhanh hơn không? → Mặc định full, thêm param `--max-rows` tùy chọn
