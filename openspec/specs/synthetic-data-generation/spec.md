# synthetic-data-generation Specification

## Purpose
TBD - created by archiving change phase3-synthetic-data. Update Purpose after archive.
## Requirements
### Requirement: Regenerate Clean Dictionary
Quy trình SHALL cho phép tái sinh từ điển từ dữ liệu gốc `HQ 2026.xlsx` bằng cách sử dụng các thuật toán trích xuất từ khóa nâng cao đã phát triển ở Phase 2, và lưu kết quả tại `dataset/DICT_HQ_2026_v2.csv`.

#### Scenario: Successful dictionary regeneration
- **WHEN** chạy hàm `generate_dictionary_from_hq()` trên tệp `HQ 2026.xlsx`
- **THEN** hệ thống tạo ra file `dataset/DICT_HQ_2026_v2.csv` chứa các từ khóa sạch (không chứa n-gram rác, loại bỏ các stopword mở rộng và thương hiệu).

### Requirement: Generate Synthetic Training Samples
Quy trình SHALL phân tách các từ khóa từ `dataset/DICT_HQ_2026_v2.csv` và sinh ra các mẫu dữ liệu huấn luyện nhân tạo (synthetic text) theo cấu trúc định dạng `"Hãng: không_có - Sản phẩm: {keyword}"` (bỏ qua thông tin Công suất để tránh gây ra nhiễu thông tin cho mô hình).

#### Scenario: Generating synthetic text from keywords
- **WHEN** kịch bản xử lý dòng từ điển có các từ khóa `"đèn pha, gắn kín"` và nhãn `"SP LED | NC | led khác | không_có"`
- **THEN** hệ thống sinh ra các mẫu huấn luyện với trường text tương ứng là `"Hãng: không_có - Sản phẩm: đèn pha"` và `"Hãng: không_có - Sản phẩm: gắn kín"`.

### Requirement: Assign Label and Calculate Weights
Quy trình SHALL gán nhãn phân loại đầy đủ (`Dòng SP | Loại | Lớp 1 | Lớp 2`) và tính toán trọng số (sample weight) cho mỗi mẫu synthetic bằng công thức `log(1 + Số lượng SP)` từ dòng từ điển gốc. Quy trình SHALL sử dụng `config/hs_company_mapping.json` để kiểm chứng và có thể override cột `Dòng SP` nếu độ tin cậy của mapping lớn hơn hoặc bằng 0.8.

#### Scenario: Label mapping validation and weight assignment
- **WHEN** sinh mẫu synthetic từ dòng từ điển có `hs_code` và khớp với `hs_company_mapping.json` có `dong_sp_confidence >= 0.8`
- **THEN** hệ thống cập nhật `Dòng SP` theo mapping, gán nhãn đầy đủ và tính toán trọng số của mẫu dựa trên `log(1 + Số lượng SP)`.

### Requirement: Merge and Deduplicate Data
Quy trình SHALL gộp các mẫu synthetic mới sinh với tập dữ liệu huấn luyện gốc `HQ-2025`, thực hiện loại bỏ các mẫu trùng lặp theo trường `text`, và lưu tập dữ liệu cuối cùng tại `dataset/train_augmented.csv`.

#### Scenario: Merge and export augmented dataset
- **WHEN** gộp dữ liệu synthetic với `HQ-2025` và chạy lọc trùng lặp
- **THEN** hệ thống xuất ra file `dataset/train_augmented.csv` chứa cả dữ liệu gốc và dữ liệu synthetic với trường `weight` hợp lệ (dữ liệu gốc mặc định weight = 1.0).

