# multi-task-model-training Specification

## Purpose
TBD - created by archiving change phase4-multitask-training. Update Purpose after archive.
## Requirements
### Requirement: Data Preprocessing and Label Encoding
Bộ xử lý huấn luyện SHALL cho phép tải tập dữ liệu `dataset/train_augmented.csv`, thực hiện phân tách cột `combined_label` thành 4 cột nhãn riêng biệt (`Dòng SP`, `Loại`, `Lớp 1`, `Lớp 2`), khởi tạo và fit 4 bộ `LabelEncoder` tương ứng, và lưu trữ 4 encoder dưới dạng file pickle (`.pkl`) trong thư mục model.

#### Scenario: Preprocess dataset and save encoders
- **WHEN** chạy script huấn luyện `train_multitask.py` trên file `dataset/train_augmented.csv`
- **THEN** hệ thống tách nhãn thành 4 phần, mã hóa số hóa, và xuất ra 4 file pickle `label_encoder_*.pkl` tại thư mục `working/model_v2/`.

### Requirement: Custom Multi-Head Model Architecture
Mô hình SHALL sử dụng chung bộ mã hóa `vinai/phobert-base-v2` làm shared encoder và triển khai 4 nhánh đầu ra Linear riêng biệt (classification heads) tương ứng với số lượng class của 4 cấp nhãn.

#### Scenario: Forward pass computation
- **WHEN** đưa đầu vào đã token hóa qua mô hình
- **THEN** mô hình trả về đồng thời 4 tập logits (đại diện cho Dòng SP, Loại, Lớp 1, Lớp 2) từ các nhánh đầu ra tương ứng.

### Requirement: Weighted Loss and Label Smoothing
Bộ huấn luyện SHALL tính toán hàm loss tổng hợp dựa trên tổng loss của 4 heads có nhân trọng số (Dòng SP: 0.5, Loại: 0.5, Lớp 1: 2.0, Lớp 2: 2.0). Cả 4 nhánh loss đều SHALL được áp dụng Label Smoothing với hệ số $\epsilon=0.1$.

#### Scenario: Calculate training loss
- **WHEN** thực hiện lan truyền ngược (backward pass) trong quá trình train
- **THEN** hệ thống áp dụng label smoothing cho các nhãn mục tiêu, nhân các giá trị loss với trọng số tương ứng và cộng tổng để tối ưu hóa.

### Requirement: Local GPU VRAM Optimization
Mô hình SHALL hỗ trợ huấn luyện trực tiếp trên GPU cục bộ RTX 2070 Super (8GB VRAM) bằng cách tự động kích hoạt chế độ FP16, Gradient Checkpointing và cấu hình batch_size thấp kết hợp Gradient Accumulation để tránh lỗi hết bộ nhớ (Out-Of-Memory).

#### Scenario: Train on local GPU
- **WHEN** bắt đầu huấn luyện trên máy có GPU <= 8GB VRAM
- **THEN** hệ thống tự động thiết lập `batch_size = 4`, `gradient_accumulation_steps = 8`, bật `use_fp16 = True` và kích hoạt gradient checkpointing để huấn luyện thành công mà không bị OOM.

