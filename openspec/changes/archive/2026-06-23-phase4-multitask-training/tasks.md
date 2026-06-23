## 1. Implement Multi-Task Training Script (Option A - Local)

- [x] 1.1 Tạo file script huấn luyện tại `training/train_multitask.py` và import các thư viện cần thiết.
- [x] 1.2 Viết logic tải dữ liệu từ `dataset/train_augmented.csv`, tách nhãn `combined_label` thành 4 cột nhãn riêng biệt và fit 4 bộ `LabelEncoder`. Lưu các encoder này dưới dạng `.pkl` tại `working/model_v2/`.
- [x] 1.3 Định nghĩa lớp mô hình PyTorch custom `PhoBertMultiTask` bọc PhoBERT-base và triển khai 4 nhánh phân loại đầu ra riêng biệt.
- [x] 1.4 Xây dựng lớp Dataset và Collator để token hóa dữ liệu văn bản với `max_length=64`.
- [x] 1.5 Thiết lập hàm Loss tổng hợp sử dụng CrossEntropy Loss với Label Smoothing ($\epsilon=0.1$) và gán trọng số (Dòng SP: 0.5, Loại: 0.5, Lớp 1: 2.0, Lớp 2: 2.0).
- [x] 1.6 Viết vòng lặp huấn luyện (training loop) tích hợp FP16, Gradient Checkpointing, batch_size = 4, gradient accumulation = 8, và Early Stopping để tối ưu trên GPU RTX 2070 Super (8GB). Lưu weights mô hình tốt nhất vào `working/model_v2/`.

## 2. Update Inference Pipeline

- [x] 2.1 Cập nhật lớp `DataCleaner` trong `backend/core/data_cleaner.py` để thay thế cơ chế load model phân loại phẳng bằng mô hình Multi-task mới.
- [x] 2.2 Viết logic khôi phục mô hình custom `PhoBertMultiTask` và load 4 bộ mã hóa nhãn từ thư mục `working/model_v2/`.
- [x] 2.3 Cập nhật phương thức suy luận (inference) trong `data_cleaner.py` để dự đoán đồng thời qua 4 heads, giải mã nhãn qua các LabelEncoder và trả về các trường nhãn chuẩn hóa.

## 3. Verify Implementation

- [x] 3.1 Chạy thử nghiệm suy luận trên một vài mẫu văn bản để kiểm tra tính ổn định của mô hình và LabelEncoder mới.
- [x] 3.2 Chạy đánh giá (evaluation) trên tập test 10% để đo lường độ chính xác (accuracy) của từng head và accuracy kết hợp của cả 4 cấp.
