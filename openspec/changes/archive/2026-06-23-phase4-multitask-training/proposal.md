## Why

Kết quả phân tích lỗi ở Phase 1 cho thấy mô hình phân loại hiện tại đang gặp vấn đề nghiêm trọng về độ chính xác ở các cấp chi tiết (Lớp 1 đạt 61%, Lớp 2 đạt 61.75%) và hiện tượng overconfidence cực kỳ nặng (ở vùng confidence 0.95-1.0, độ chính xác thực tế chỉ đạt ~44%). 

Nguyên nhân chính là mô hình cũ xử lý bài toán dưới dạng phân loại phẳng (flat classification) bằng cách gộp cả 4 cấp thành một nhãn chuỗi duy nhất. Điều này làm mất đi tính phân cấp (hierarchy) và ngăn cản mô hình chia sẻ đặc trưng giữa các bài toán con (ví dụ: việc nhận diện Lớp 1 giúp định hướng phân loại Lớp 2). Do đó, chúng ta cần đề xuất kiến trúc mô hình Multi-task Hierarchical Classification sử dụng chung bộ mã hóa PhoBERT kết hợp 4 đầu ra (head) độc lập cho 4 cấp nhãn, áp dụng label smoothing để hiệu chỉnh độ tự tin (calibration) và loss weighting để tập trung giải quyết các nút cổ chai ở Lớp 1 & Lớp 2.

## What Changes

- **Phát triển script huấn luyện mới**: Viết script `training/train_multitask.py` hỗ trợ huấn luyện Multi-task trên cả GPU cá nhân (RTX 2070 Super) lẫn Google Colab (T4), tự động tối ưu batch size và các kỹ thuật giảm RAM (gradient checkpointing, FP16).
- **Kiến trúc Loss Weighting & Label Smoothing**: Thiết lập hàm loss tổng hợp có trọng số dồn vào Lớp 1 và Lớp 2 (trọng số loss lần lượt là Dòng SP: 0.5, Loại: 0.5, Lớp 1: 2.0, Lớp 2: 2.0). Tích hợp Label Smoothing ($\epsilon=0.1$) cho cả 4 heads để chống mô hình quá tự tin.
- **Xuất Model & Encoder**: Lưu trữ mô hình sau huấn luyện cùng 4 bộ mã hóa nhãn (`label_encoder_dong_sp.pkl`, `label_encoder_loai.pkl`, `label_encoder_lop1.pkl`, `label_encoder_lop2.pkl`) tại thư mục `working/model_v2/`.
- **Cập nhật Pipeline suy luận (Inference)**: Cập nhật file `backend/core/data_cleaner.py` để thay thế cơ chế dự đoán phẳng cũ bằng cơ chế load mô hình Multi-task mới, thực hiện dự đoán đồng thời 4 heads, decode nhãn và trả về nhãn chuẩn hóa.

## Capabilities

### New Capabilities
- `multi-task-model-training`: Huấn luyện mô hình phân loại Multi-task với 4 nhánh đầu ra độc lập trên tập dữ liệu tăng cường, sử dụng Weighted Loss và Label Smoothing để tối ưu hóa độ chính xác và calibration.
- `multi-task-model-inference`: Thực hiện suy luận (inference) bằng mô hình Multi-task 4 heads trong pipeline tiền xử lý và phân loại dữ liệu, tự động giải mã kết quả thành nhãn phân loại chuẩn.

### Modified Capabilities
*(Không có)*

## Impact

- **Mã nguồn**: 
  - Tạo mới script huấn luyện tại `training/train_multitask.py`.
  - Thay đổi logic suy luận trong [data_cleaner.py](file:///d:/Code/CleanData/backend/core/data_cleaner.py).
- **Lưu trữ & Dữ liệu**: 
  - Tạo thư mục lưu model mới tại `working/model_v2/` chứa file weights và các file pickle encoder.
- **Tương thích**: Không làm thay đổi định dạng dữ liệu đầu ra của pipeline (vẫn trả về cấu trúc phân loại 4 cấp chuẩn hóa), đảm bảo tương thích ngược hoàn toàn với hệ thống frontend và database.
