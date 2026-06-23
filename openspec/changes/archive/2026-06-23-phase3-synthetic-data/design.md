## Context

Trong Phase 1 (Error Analysis), chúng ta xác định mô hình PhoBERT hiện tại bị thắt nút cổ chai (bottleneck) ở Lớp 1 (accuracy 61%) và Lớp 2 (accuracy 61.75%), đồng thời bị overconfidence nặng. 

Trong Phase 2, chúng ta đã tích hợp lọc HS Code vào dictionary matching và cải thiện thuật toán trích xuất từ khóa của `dict_generator.py`. Tuy nhiên, dictionary matching chỉ có thể hoạt động khi từ khóa khớp chính xác tuyệt đối (exact match) trong văn bản mô tả.

Phase 3 thiết lập quy trình sinh dữ liệu huấn luyện nhân tạo (synthetic training data) từ các từ khóa sạch của từ điển mới (`DICT_HQ_2026_v2.csv`). Bằng cách đưa các từ khóa này trực tiếp vào tập huấn luyện dưới dạng các mẫu synthetic, mô hình PhoBERT có thể học mối tương quan ngữ nghĩa giữa từ khóa và nhãn, giúp tăng khả năng tổng quát hóa (generalization) với các biến thể mô tả thực tế khi chạy suy luận (inference).

## Goals / Non-Goals

**Goals:**
- Tái sinh tự động bộ từ điển sạch `dataset/DICT_HQ_2026_v2.csv` từ tệp dữ liệu `HQ 2026.xlsx` dùng thuật toán trích xuất nâng cao ở Phase 2.
- Viết kịch bản `analysis/generate_synthetic_train.py` để tự động hóa quy trình sinh và trộn dữ liệu huấn luyện.
- Sinh khoảng 5,000 - 9,000 mẫu dữ liệu nhân tạo từ từ khóa trong từ điển, có gán nhãn đầy đủ.
- Áp dụng trọng số mẫu (sample weight) dạng logarit `log(1 + Số lượng SP)` để cân bằng tầm quan trọng của các lớp.
- Sử dụng `config/hs_company_mapping.json` (Phase 2.5) để kiểm chứng chéo và tự động override cột `Dòng SP` nếu độ tin cậy của mapping >= 0.8.
- Trộn dữ liệu nhân tạo với tập dữ liệu sạch gốc `HQ-2025`, lọc trùng lặp và lưu thành `dataset/train_augmented.csv`.

**Non-Goals:**
- Huấn luyện mô hình PhoBERT (việc này thuộc về Phase 4).
- Thay đổi logic chạy suy luận (inference pipeline) hoặc cơ chế lọc HS code trong code chạy thực tế.
- Viết lại từ đầu thuật toán trích xuất từ khóa (chúng ta tái sử dụng code của `dict_generator.py` đã cải tiến ở Phase 2).

## Decisions

### Quyết định 1: Định dạng trường văn bản (text) cho các mẫu synthetic
- **Lựa chọn:** Cấu trúc dạng `"Hãng: không_có - Sản phẩm: {keyword}"`.
- **Lý do:** Văn bản huấn luyện gốc có dạng `"Hãng: {brand} - Công suất: {power} - Sản phẩm: {product_desc}"`. Mẫu synthetic không có thông tin hãng và công suất thật. Nếu dùng `"Công suất: không_có"`, mô hình có thể học sai mối liên hệ giữa cụm từ `"không_có"` ở vị trí công suất với một số nhãn sản phẩm nhất định. Loại bỏ hẳn cụm công suất giúp mô hình tập trung vào từ khóa sản phẩm mà vẫn giữ nguyên tiền tố `"Hãng: không_có - Sản phẩm: ..."` khớp với cách tiền xử lý của pipeline.
- **Giải pháp thay thế đã xem xét:**
  - `"Hãng: không_có - Công suất: không_có - Sản phẩm: {keyword}"`: Bị từ chối vì có thể gây nhiễu/bias cho trường công suất.
  - Chỉ dùng `{keyword}` thô: Bị từ chối vì cấu trúc câu không đồng bộ với tập huấn luyện gốc khiến mô hình khó học.

### Quyết định 2: Điều chỉnh Dòng SP bằng bảng ánh xạ HS Mapping
- **Lựa chọn:** Nếu mã HS của từ điển khớp với `hs_company_mapping.json` và độ tin cậy của dòng SP >= 0.8, sẽ ghi đè (override) `Dòng SP` của mẫu synthetic bằng giá trị từ mapping.
- **Lý do:** Nhãn trong từ điển tự sinh đôi khi chứa nhiễu hoặc sai lệch nhỏ do ghi chép thủ công. Bảng HS Mapping đại diện cho sự đồng thuận thống kê trên toàn bộ tập dữ liệu gốc, giúp chuẩn hóa lại dòng sản phẩm một cách chính xác trước khi đưa vào huấn luyện mô hình.
- **Giải pháp thay thế đã xem xét:** Giữ nguyên nhãn từ từ điển gốc. Bị từ chối vì có thể mang nhãn nhiễu vào dữ liệu huấn luyện mới.

### Quyết định 3: Cách tính trọng số mẫu (Sample Weighting)
- **Lựa chọn:** Gán `weight = log(1 + Số lượng SP)` cho dữ liệu synthetic và mặc định `1.0` cho dữ liệu huấn luyện gốc `HQ-2025`.
- **Lý do:** Những dòng từ điển có số lượng sản phẩm lớn tương ứng với các từ khóa phổ biến và quan trọng trong thực tế. Nếu không gán trọng số, mô hình sẽ coi các từ khóa hiếm gặp và từ khóa phổ biến như nhau. Nếu gán trọng số tuyến tính trực tiếp theo số lượng, các từ khóa cực kỳ phổ biến sẽ chiếm tỷ trọng quá lớn đè bẹp các từ khóa khác. Hàm logarit là giải pháp trung hòa tốt nhất.
- **Giải pháp thay thế đã xem xét:** Gán trọng số bằng nhau (1.0) cho tất cả. Bị từ chối vì mất đi thông tin phân phối tần suất thực tế của sản phẩm.

## Risks / Trade-offs

- **[Risk] Mô hình bị overfitting vào cấu trúc câu synthetic** → **[Mitigation]** Thực hiện lọc trùng lặp và giữ số lượng mẫu synthetic vừa phải (~5,000-9,000 mẫu) so với tập dữ liệu gốc (~40,000 mẫu) để tránh làm loãng tập dữ liệu thực tế. Dữ liệu gốc vẫn giữ trọng số mặc định `1.0`.
- **[Risk] Sai lệch nhãn do override nhầm Dòng SP** → **[Mitigation]** Chỉ thực hiện override khi độ tin cậy trong `hs_company_mapping.json` đạt tối thiểu 80% (`dong_sp_confidence >= 0.8`).
