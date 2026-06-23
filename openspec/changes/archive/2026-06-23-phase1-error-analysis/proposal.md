## Why

Model accuracy hiện tại chỉ đạt 0.76 trên tập phân loại `Dòng SP | Loại | Lớp 1 | Lớp 2`. Trước khi đầu tư vào các phase cải thiện (tích hợp dict mới, multi-task training, synthetic data), cần phân tích chi tiết nguồn gốc lỗi để xác định chính xác model yếu ở đâu — tránh lãng phí công sức vào hướng không hiệu quả.

## What Changes

- Thêm script `analysis/error_analysis.py` để phân tích lỗi toàn diện trên test set
- Script chạy cả Dict Matcher + AI Model trên test set, so sánh với ground truth
- Output: accuracy breakdown từng cấp (Dòng SP, Loại, Lớp 1, Lớp 2), confusion matrix, calibration curve, dict-vs-AI comparison
- Không thay đổi code production, không cần train — chạy hoàn toàn trên CPU

## Capabilities

### New Capabilities

- `error-analysis`: Phân tích lỗi model classification — breakdown accuracy 4 cấp, confusion matrix, calibration curve, dict-vs-AI performance comparison, tìm optimal confidence threshold

### Modified Capabilities

<!-- Không có capability nào bị thay đổi ở spec level -->

## Impact

- Không ảnh hưởng đến API endpoints, database schema, hay pipeline production
- File mới: `analysis/error_analysis.py`, output charts/reports lưu trong `analysis/output/`
- Phụ thuộc vào: `backend/core/data_cleaner.py`, `backend/core/dictionary_matcher.py`, `config/label_standard.json`, model files trong `working/`
- Test set source: `dataset/cleaned_merged_upload (6).csv` hoặc tách từ notebook split
