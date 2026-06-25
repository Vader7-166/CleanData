# multi-task-model-inference Specification

## Purpose
TBD - created by archiving change phase4-multitask-training. Update Purpose after archive.
## Requirements
### Requirement: Load Multi-Task Model and Encoders
Pipeline suy luận SHALL cho phép tải trọng số của mô hình Multi-task đã huấn luyện từ thư mục `working/model_v2/` và khôi phục (load) 4 bộ mã hóa nhãn từ các file pickle tương ứng.

#### Scenario: Successful model loading
- **WHEN** khởi tạo đối tượng phân loại trong `data_cleaner.py`
- **THEN** hệ thống load thành công checkpoint mô hình và 4 file `label_encoder_*.pkl` vào bộ nhớ.

### Requirement: Multi-Head Inference and Decoding
Hàm suy luận SHALL nhận văn bản đã tiền xử lý, thực hiện forward pass qua mô hình để lấy logits của 4 heads, chạy argmax để lấy chỉ mục dự đoán có xác suất cao nhất, giải mã các chỉ mục này bằng các LabelEncoder tương ứng, và trả về kết quả phân loại chuẩn hóa.

#### Scenario: Predict labels for product text
- **WHEN** nhận được đầu vào là mô tả sản phẩm đã chuẩn hóa
- **THEN** hệ thống trả về kết quả dự đoán đồng thời cho cả 4 cấp: `Dòng SP`, `Loại`, `Lớp 1`, và `Lớp 2` dưới dạng các giá trị chuỗi đã được giải mã.

