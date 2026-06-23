## Context

Phân tích lỗi ở Phase 1 chỉ ra rằng mô hình cũ (phân loại phẳng) gặp nút cổ chai lớn về độ chính xác ở Lớp 1 (61%) và Lớp 2 (61.75%), đồng thời bị overconfidence rất nặng (ở độ tin cậy >0.95, accuracy thực tế chỉ đạt 44%).

Để giải quyết các vấn đề này, chúng ta cần huấn luyện một mô hình Multi-task Hierarchical Classification thay thế. Mô hình mới sẽ sử dụng chung bộ mã hóa PhoBERT để chia sẻ đặc trưng giữa các cấp nhãn và triển khai 4 classification heads độc lập. Để khắc phục hiện tượng overconfidence, chúng ta sẽ áp dụng Label Smoothing. Để tập trung sửa lỗi ở Lớp 1 và Lớp 2, chúng ta sẽ áp dụng trọng số Loss lớn hơn cho hai nhánh này.

Theo yêu cầu từ người dùng, chúng ta sẽ **chỉ tập trung vào Phương án A (huấn luyện cục bộ trên GPU RTX 2070 Super 8GB)** bằng cách tạo file script `training/train_multitask.py`. Việc sửa đổi Jupyter Notebook chạy trên Colab (Phương án B) hoàn toàn nằm ngoài phạm vi thực hiện.

## Goals / Non-Goals

**Goals:**
- Tạo script huấn luyện local `training/train_multitask.py` tối ưu hóa cho card đồ họa RTX 2070 Super (8GB VRAM).
- Xây dựng lớp mô hình PyTorch custom `PhoBertMultiTask` tích hợp PhoBERT-base và 4 nhánh Linear phân loại đầu ra riêng biệt.
- Cấu hình hàm Loss CrossEntropy áp dụng Label Smoothing ($\epsilon=0.1$) và trọng số loss (Dòng SP: 0.5, Loại: 0.5, Lớp 1: 2.0, Lớp 2: 2.0).
- Áp dụng các kỹ thuật tối ưu hóa bộ nhớ GPU VRAM: batch size = 4, gradient accumulation = 8, mixed precision FP16 và gradient checkpointing để tránh lỗi Out-Of-Memory (OOM).
- Xuất mô hình huấn luyện tốt nhất và 4 file LabelEncoder dạng pickle vào thư mục `working/model_v2/`.
- Cập nhật logic suy luận trong `backend/core/data_cleaner.py` để sử dụng mô hình Multi-task mới này.

**Non-Goals:**
- Cập nhật file Jupyter Notebook `PhoBertmappingv2(85%).ipynb` phục vụ chạy trên Google Colab.
- Thay đổi cấu trúc cơ sở dữ liệu hoặc giao diện frontend.

## Decisions

### Quyết định 1: Kiến trúc mô hình PyTorch Custom thay vì Hugging Face AutoModel
- **Lựa chọn:** Xây dựng một class kế thừa `torch.nn.Module` bọc `AutoModel.from_pretrained("vinai/phobert-base-v2")` và định nghĩa 4 lớp Linear làm classification heads.
- **Lý do:** Các lớp AutoModel của Hugging Face (như `AutoModelForSequenceClassification`) chỉ hỗ trợ một đầu ra phân loại duy nhất. Để phân loại đồng thời 4 cấp nhãn phân cấp, mô hình custom cho phép đưa văn bản qua PhoBERT đúng 1 lần, lấy vector đặc trưng của token `[CLS]` (hoặc qua pooling layer) và đưa vào 4 đầu phân loại Linear độc lập. Giải pháp này giúp tiết kiệm thời gian tính toán và cho phép mô hình học các biểu diễn dùng chung giữa các tác vụ phân loại.

### Quyết định 2: Tối ưu hóa bộ nhớ VRAM cho GPU RTX 2070 Super (8GB)
- **Lựa chọn:** Thiết lập `batch_size = 4`, `gradient_accumulation_steps = 8` (tương đương effective batch size = 32), kích hoạt chế độ Mixed Precision (FP16) bằng `torch.cuda.amp.autocast` và bật Gradient Checkpointing cho encoder PhoBERT.
- **Lý do:** Bộ nhớ 8GB của RTX 2070 Super không thể chứa được mô hình PhoBERT-base khi train với batch size lớn (ví dụ 32) do lượng kích hoạt lưu trữ khổng lồ. Việc giảm batch size xuống 4 giúp giảm tải tức thời bộ nhớ, kết hợp tích lũy gradient 8 bước giúp cập nhật trọng số chính xác như batch size 32. FP16 và Gradient Checkpointing giúp giảm thêm ~40% lượng VRAM tiêu thụ, đảm bảo chương trình chạy mượt mà không bị OOM.

### Quyết định 3: Thiết lập hàm Loss dồn trọng số và Label Smoothing
- **Lựa chọn:** Sử dụng CrossEntropyLoss với `label_smoothing = 0.1` cho cả 4 nhánh. Trọng số nhân của loss tổng hợp là $\alpha_{dong\_sp}=0.5, \beta_{loai}=0.5, \gamma_{lop1}=2.0, \delta_{lop2}=2.0$.
- **Lý do:** Trọng số loss cao ở Lớp 1 và Lớp 2 bắt buộc mô hình phải ưu tiên tối ưu hóa độ chính xác ở hai cấp này (vùng đang bị bottleneck). Label smoothing buộc mô hình không được phép gán xác suất quá gần với 1.0 cho nhãn đúng, từ đó giảm thiểu độ tự tin thái quá (overconfidence) của mô hình.

## Risks / Trade-offs

- **[Risk] Lỗi Out-Of-Memory (OOM) trên GPU RTX 2070 Super** $\rightarrow$ **[Mitigation]** Tự động phát hiện dung lượng VRAM của GPU khi khởi chạy script và bật cứng chế độ tối ưu hóa bộ nhớ (batch size = 4, Gradient Checkpointing, FP16).
- **[Risk] Không tương thích định dạng file checkpoints với server API** $\rightarrow$ **[Mitigation]** Viết logic load model đồng bộ trong `data_cleaner.py` đảm bảo dựng lại đúng cấu trúc lớp `PhoBertMultiTask` trước khi `load_state_dict` và verify đầu ra với dữ liệu test.
