## Why

Hiện tại, việc khớp từ khóa (dict matching) chỉ hoạt động khi từ khóa xuất hiện chính xác tuyệt đối trong mô tả sản phẩm (ví dụ: "đèn pha" khớp, còn "bộ đèn chiếu pha" thì không). Điều này làm giảm đáng kể khả năng phân loại chính xác khi từ mô tả thực tế có sự biến thể. 

Việc sinh dữ liệu huấn luyện nhân tạo (synthetic training data) từ bộ từ điển sạch (đã cải tiến ở Phase 2) giúp mô hình PhoBERT học được các pattern ngữ nghĩa và mối liên quan giữa các từ khóa với nhãn tương ứng. Từ đó, mô hình có khả năng tổng quát hóa (generalize) tốt hơn và không còn phụ thuộc hoàn toàn vào so khớp từ khóa chính xác tại thời điểm suy luận (inference).

## What Changes

- **Tái sinh từ điển sạch**: Chạy quy trình sinh từ điển hiện có để cập nhật file từ điển `dataset/DICT_HQ_2026_v2.csv` (keyword sạch nhờ các cải tiến thuật toán trích xuất ở Phase 2).
- **Phát triển Script sinh dữ liệu**: Xây dựng script `analysis/generate_synthetic_train.py` để trích xuất các keyword từ `DICT_HQ_2026_v2.csv`, gán nhãn phân loại, kiểm chứng chéo bằng `config/hs_company_mapping.json` (Phase 2.5) và tạo các mẫu dữ liệu huấn luyện mới.
- **Tạo tập dữ liệu Synthetic**: Xuất file dữ liệu `dataset/synthetic_train_v2.csv` chứa khoảng 5,000 - 9,000 mẫu dữ liệu nhân tạo với định dạng chuẩn hóa `"Hãng: không_có - Sản phẩm: {keyword}"` và trọng số điều chỉnh bằng hàm logarit.
- **Tăng cường dữ liệu huấn luyện**: Hợp nhất tập dữ liệu gốc `HQ-2025` và tập dữ liệu nhân tạo, sau khi lọc trùng lặp, để tạo ra tập dữ liệu tăng cường `dataset/train_augmented.csv` sẵn sàng làm đầu vào cho Phase 4 (Multi-task training).

## Capabilities

### New Capabilities
- `synthetic-data-generation`: Tự động sinh dữ liệu huấn luyện nhân tạo chất lượng từ từ điển kết hợp ánh xạ HS Code → Company, và thực hiện tăng cường (augmentation) tập dữ liệu huấn luyện gốc.

### Modified Capabilities
*(Không có)*

## Impact

- **Mã nguồn**: Thêm script mới `analysis/generate_synthetic_train.py` không ảnh hưởng tới code chạy production hiện tại.
- **Dữ liệu**: Tạo ra các file dữ liệu mới `dataset/DICT_HQ_2026_v2.csv`, `dataset/synthetic_train_v2.csv` và `dataset/train_augmented.csv`.
- **Dependencies**: Không thêm thư viện ngoài mới.
