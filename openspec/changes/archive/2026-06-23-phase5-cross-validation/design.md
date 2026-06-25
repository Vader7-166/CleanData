## Context

Mục tiêu của Phase 5 là triển khai phân tích đối chiếu chéo 3 chiều (3-Way Cross-Validation) bằng cách so sánh 3 nguồn dự đoán trên tập test (10%):
1. **Từ điển mới (DICT_HQ_2026)** kết hợp bộ lọc HS code (HS Code filtering).
2. **Từ điển cũ (dictv3)**.
3. **Mô hình AI mới** (PhoBERT Multi-task được huấn luyện ở Phase 4).

Thông qua việc đối chiếu chéo này với Ground Truth (nhãn thực tế), hệ thống có thể:
* Phát hiện những trường hợp từ điển mới đúng nhưng AI sai để tăng cường mẫu train (Active Learning).
* Phát hiện những trường hợp từ điển mới sai nhưng AI đúng để cải thiện/sửa từ điển mới.
* Nhận diện các "ca khó" (cả 3 đều dự đoán sai) để lọc ra cho con người review.
* Loại bỏ hoặc thay thế các cấu trúc lỗi thời trong từ điển cũ (dictv3).

## Goals / Non-Goals

**Goals:**
* Tạo script `analysis/cross_validate.py` độc lập thực hiện quy trình load tập test (10% từ `dataset/HQ 2025.xlsx`), thực hiện dự đoán chéo từ 3 nguồn.
* Phân loại chi tiết kết quả theo 5 nhóm kịch bản (Patterns) đã xác định.
* Xuất các báo cáo phân tích chi tiết dưới dạng CSV:
  - `analysis/output/cross_validation_report.csv`: Tất cả các dòng có sự bất đồng/sai sót giữa 3 nguồn và Ground Truth.
  - `analysis/output/dict_fixes_needed.csv`: Gợi ý các keyword cần sửa đổi dựa trên các ca từ điển mới đoán sai nhưng AI hoặc dictv3 đoán đúng.
  - `analysis/output/hard_cases.csv`: Các sản phẩm mà cả 3 nguồn đều đoán sai so với Ground Truth.

**Non-Goals:**
* Không cập nhật trực tiếp vào cơ sở dữ liệu hoặc tập train một cách tự động (việc retrain và merge dữ liệu thuộc về Phase 6).
* Không thay đổi API hay UI runtime trong quá trình phân tích offline này.

## Decisions

### 1. Tận dụng `DataCleaner` cho Mô hình Multi-task
* **Lựa chọn**: Sử dụng trực tiếp class `DataCleaner` từ `backend.core.data_cleaner` để load mô hình AI và chạy batch prediction.
* **Lý do**: Class `DataCleaner` trong codebase đã được cập nhật ở Phase 4 để hỗ trợ cả mô hình Multitask và Single-task, tự động tải các bộ mã hóa LabelEncoder (`label_encoder_*.pkl`) tương ứng. Việc sử dụng lại giúp tránh viết lặp code tải model và đảm bảo tính nhất quán.

### 2. Sử dụng độc lập hai bộ Matcher từ điển
* **Lựa chọn**: Khởi tạo 2 thực thể `DictionaryMatcher` riêng biệt cho từ điển mới và cũ:
  - `matcher_hq = DictionaryMatcher(dict_paths=["dataset/DICT_HQ_2026.csv"])`
  - `matcher_v3 = DictionaryMatcher(dict_paths=["dataset/dictv3.csv"])`
* **Lý do**: Điều này cho phép chúng ta so sánh độc lập hiệu suất của từ điển mới (có bộ lọc HS code) và từ điển cũ (dictv3) để phân tích chất lượng của bộ từ điển mới sinh.

### 3. Quy tắc phân loại 5 mẫu (Patterns)
Đối với mỗi dòng trong tập test, chúng ta so sánh độ chính xác của 3 bộ dự đoán:
* **Pattern 1: `Dict_HQ_correct` & `dictv3_correct` & `AI_wrong`**
  - *Ý nghĩa*: AI bỏ lỡ hoặc đoán sai các mẫu rõ ràng mà cả hai từ điển đều nhận diện được.
  - *Hành động*: Cần bổ sung mẫu này vào tập training cho AI.
* **Pattern 2: `Dict_HQ_correct` & `AI_wrong` & `dictv3_wrong`**
  - *Ý nghĩa*: Từ điển mới (DICT_HQ_2026) có độ phủ tốt hơn hẳn AI và từ điển cũ.
  - *Hành động*: Ghi nhận thế mạnh của từ điển mới, thúc đẩy sử dụng từ điển mới làm primary filter.
* **Pattern 3: `Dict_HQ_wrong` & `AI_correct` & `dictv3_wrong`**
  - *Ý nghĩa*: AI xử lý tốt hơn từ điển mới. Từ điển mới có thể chứa các keyword bị trùng lặp hoặc gán nhãn sai.
  - *Hành động*: Cần rà soát và sửa đổi các keyword trong từ điển mới (lưu vào `dict_fixes_needed.csv`).
* **Pattern 4: Cả 3 dự đoán sai (`Dict_HQ_wrong` & `AI_wrong` & `dictv3_wrong`)**
  - *Ý nghĩa*: Đây là ca khó (hard case), cấu trúc câu phức tạp hoặc nhãn ground truth bị nhiễu.
  - *Hành động*: Đưa vào `hard_cases.csv` để review thủ công.
* **Pattern 5: `Dict_HQ_correct` & `AI_correct` & `dictv3_wrong`**
  - *Ý nghĩa*: Cả từ điển mới và AI đều đúng, trong khi từ điển cũ đoán sai.
  - *Hành động*: Chứng minh từ điển cũ (dictv3) chứa entry không chính xác hoặc lỗi thời, đề xuất loại bỏ entry đó.

## Risks / Trade-offs

* **[Vấn đề OOM / Tốc độ xử lý trên CPU]** -> `DataCleaner` sẽ được chạy với tối ưu hóa dynamic quantization trên CPU và gom batch (batch_size=64) để tránh quá tải bộ nhớ và cải thiện tốc độ xử lý offline.
* **[Sự khác biệt về tiền xử lý text]** -> Tất cả 3 nguồn dự đoán phải sử dụng chung hàm tiền xử lý `clean_text` và thống nhất normalize label theo `config/label_standard.json` thông qua hàm `normalize_label` để tránh lệch nhãn do lỗi chính tả hoặc viết hoa/thường.
