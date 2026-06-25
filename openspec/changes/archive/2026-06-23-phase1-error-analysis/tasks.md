## 1. Project Setup

- [x] 1.1 Tạo thư mục `analysis/` và `analysis/output/` nếu chưa tồn tại
- [x] 1.2 Kiểm tra các dependency cần thiết (matplotlib, seaborn, pandas, numpy, scikit-learn) đã có trong môi trường

## 2. Load Model & Test Data

- [x] 2.1 Viết hàm `load_model_and_encoder()` — load model PhoBERT từ `working/` (dùng MODEL_PATH env hoặc default)
- [x] 2.2 Viết hàm `load_and_split_data()` — đọc `dataset/HQ 2025.xlsx`, tái tạo split 80/10/10 giống notebook (random_state=42)
- [x] 2.3 Viết hàm `clean_text()` — làm sạch text theo đúng format notebook (đã có trong data loading)
- [x] 2.4 Viết hàm `normalize_label()` — normalize label qua `label_standard.json` cho cả ground truth và prediction

## 3. Run Predictions

- [x] 3.1 Viết hàm `run_dict_predictions()` — dùng DictionaryMatcher predict từng dòng, ghi nhận label + score
- [x] 3.2 Viết hàm `run_ai_predictions()` — dùng PhoBERT model batch inference với batch_size=64, ghi nhận label + confidence
- [x] 3.3 Viết hàm `split_combined_label()` — tách `"Dòng SP | Loại | Lớp 1 | Lớp 2"` thành 4 cột riêng, normalize
- [x] 3.4 Normalize cả ground truth lẫn prediction trước khi so sánh (dùng label_standard.json aliases)

## 4. Accuracy Breakdown

- [x] 4.1 Viết hàm `compute_accuracy_breakdown()` — tính accuracy riêng cho Dòng SP, Loại, Lớp 1, Lớp 2, và combined
- [x] 4.2 In bảng accuracy breakdown ra console + lưu CSV `analysis/output/accuracy_breakdown.csv`

## 5. Confusion Matrix

- [x] 5.1 Viết hàm `plot_confusion_heatmap()` — tính confusion matrix ở combined-label level, lấy top confused classes
- [x] 5.2 Vẽ heatmap bằng matplotlib/seaborn, lưu `analysis/output/confusion_matrix_top20.png`
- [x] 5.3 Xuất top-10 cặp confused ra CSV `analysis/output/top10_confused_pairs.csv`

## 6. Dict vs AI Comparison

- [x] 6.1 Viết hàm `compare_dict_vs_ai()` — tính: % dòng dict xử lý, dict accuracy, AI accuracy
- [x] 6.2 Tính overlap matrix: both correct, both wrong, dict-only correct, AI-only correct
- [x] 6.3 Xuất báo cáo ra `analysis/output/dict_vs_ai_report.csv`

## 7. Calibration Curve

- [x] 7.1 Viết hàm `compute_calibration_curve()` — chia confidence thành bins, tính actual accuracy mỗi bin
- [x] 7.2 Viết hàm `plot_calibration_curve()` — vẽ calibration curve + bar chart sample count, lưu `analysis/output/calibration_curve.png`
- [x] 7.3 Tìm optimal threshold dựa trên calibration data

## 8. Orchestration & Report

- [x] 8.1 Viết hàm `main()` — orchestrate toàn bộ flow: load → predict → breakdown → confusion → dict-vs-AI → calibration
- [x] 8.2 Viết hàm `generate_summary_report()` — tổng hợp tất cả kết quả vào text report `analysis/output/error_analysis_report.txt`
- [x] 8.3 Thêm CLI args: `--max-rows N`, `--dict-paths`, `--data`, `--no-dict`, `--no-ai`
- [x] 8.4 Test chạy script với `--max-rows 100` và `--max-rows 2000` thành công

## 9. Update task.md

- [x] 9.1 Đánh dấu Phase 1 hoàn thành trong root `task.md`
- [x] 9.2 Ghi nhận kết quả chính (accuracy breakdown, calibration, dict coverage) vào task.md
