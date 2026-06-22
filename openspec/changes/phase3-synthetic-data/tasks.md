## 1. Regenerate Clean Dictionary

- [x] 1.1 Chạy script sinh từ điển để tạo lại tệp `dataset/DICT_HQ_2026_v2.csv` với các từ khóa sạch (từ Phase 2).

## 2. Implement Synthetic Data Generator Script

- [x] 2.1 Tạo file kịch bản `analysis/generate_synthetic_train.py` và import các thư viện cần thiết (`pandas`, `numpy`, `json`, `os`, `math`).
- [x] 2.2 Đọc bảng cấu hình `config/hs_company_mapping.json` và file tiêu chuẩn nhãn `config/label_standard.json` để phục vụ xác thực nhãn.
- [x] 2.3 Viết hàm phân tách từ khóa từ cột `Từ khóa` của từ điển `DICT_HQ_2026_v2.csv` (tách theo dấu phẩy, strip khoảng trắng, chỉ giữ lại các cụm có độ dài từ tương ứng).
- [x] 2.4 Thực hiện gán nhãn đầy đủ cho mỗi từ khóa synthetic và kiểm chứng chéo `Dòng SP` bằng mã HS. Nếu mã HS tồn tại trong `hs_company_mapping.json` và độ tin cậy >= 0.8, override cột `Dòng SP`.
- [x] 2.5 Tính toán trọng số cho mỗi mẫu synthetic bằng công thức `log(1 + Số lượng SP)`.
- [x] 2.6 Định dạng trường text của mẫu synthetic thành `"Hãng: không_có - Sản phẩm: {keyword}"`.
- [x] 2.7 Gộp các mẫu synthetic thành DataFrame và lưu ra file `dataset/synthetic_train_v2.csv`.
- [x] 2.8 Load tập dữ liệu gốc `HQ-2025` (đã clean), gán trọng số mặc định `1.0` cho dữ liệu gốc.
- [x] 2.9 Hợp nhất tập dữ liệu gốc và dữ liệu synthetic, thực hiện loại bỏ các dòng trùng lặp (deduplicate) dựa trên cột `text` (hoặc cột đầu vào của mô hình) và lưu kết quả tại `dataset/train_augmented.csv`.

## 3. Verify Output

- [x] 3.1 Chạy script `analysis/generate_synthetic_train.py` để tạo các file output.
- [x] 3.2 Kiểm tra sự tồn tại và tính hợp lệ của `dataset/synthetic_train_v2.csv` và `dataset/train_augmented.csv` (số dòng, định dạng cột, giá trị trọng số).
