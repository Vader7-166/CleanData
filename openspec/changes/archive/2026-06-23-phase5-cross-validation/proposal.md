## Why

Hiện tại, độ chính xác (Accuracy) của hệ thống phân loại 4 cấp (Dòng SP | Loại | Lớp 1 | Lớp 2) đã được nâng cấp đáng kể thông qua mô hình học máy Multi-task mới (Phase 4). Tuy nhiên, để liên tục kiểm soát chất lượng, tối ưu hóa các tập từ điển (DICT_HQ_2026, dictv3) và mô hình AI, chúng ta cần một công cụ tự động đối chiếu chéo (Cross-validation) 3 chiều giữa kết quả từ điển mới (DICT_HQ_2026), từ điển cũ (dictv3) và mô hình PhoBERT AI. Việc này giúp phát hiện ra các vùng dữ liệu mà AI hoặc Từ điển dự đoán sai, từ đó có cơ sở cập nhật tập train cho AI hoặc sửa các keyword trong từ điển.

## What Changes

- Thêm script phân tích đối chiếu chéo `analysis/cross_validate.py`.
- Tạo cơ chế tự động đánh giá chéo 3 chiều trên tập test (10%): dự đoán của DICT_HQ_2026 (có bộ lọc HS), dự đoán của dictv3 và dự đoán của mô hình PhoBERT AI mới.
- Phân tích và phân loại các mẫu dữ liệu theo 5 kịch bản (disagreement / agreement patterns) để đưa ra hành động tương ứng.
- Xuất các báo cáo dạng CSV phục vụ cho việc cập nhật từ điển và tái huấn luyện mô hình:
  - `analysis/output/cross_validation_report.csv` (toàn bộ các điểm không khớp)
  - `analysis/output/dict_fixes_needed.csv` (các keyword cần sửa/bổ sung trong từ điển)
  - `analysis/output/hard_cases.csv` (các ca khó cần con người review thủ công)

## Capabilities

### New Capabilities
- `cross-validation-analysis`: Cung cấp script phân tích đối chiếu chéo 3 chiều giữa các nguồn dự đoán để phát hiện lỗi và tối ưu từ điển/mô hình AI.

### Modified Capabilities

## Impact

- Thêm thư mục đầu ra và các file báo cáo phân tích mới trong `analysis/output/`.
- Không ảnh hưởng trực tiếp đến API runtime hoặc database schema hiện tại vì đây là script phân tích offline.
