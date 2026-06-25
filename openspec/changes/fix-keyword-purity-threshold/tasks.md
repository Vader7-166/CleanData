## 1. Update Core Dictionary Generator Logic

- [x] 1.1 Mở file `backend/core/dict_generator.py`.
- [x] 1.2 Tìm hàm `extract_keywords_ai` (dùng để trích xuất từ khóa TF-IDF).
- [x] 1.3 Trong vòng lặp tính điểm từ khóa, thêm điều kiện kiểm tra Purity (ngưỡng 0.2 hoặc 20%). Chỉ chấp nhận các n-gram có `p >= 0.2`.
- [x] 1.4 Đảm bảo code sẽ bỏ qua những từ khóa không đạt ngưỡng (dù có làm giảm tổng số từ khóa xuống dưới `top_n=12`).

## 2. Verification & Testing

- [ ] 2.1 Chạy lại quá trình sinh từ điển Direct từ HQ data (sử dụng API hoặc UI).
- [ ] 2.2 Xác minh rằng từ điển mới sinh ra KHÔNG chứa các từ khóa rác, generic như "Rạng Đông", "đèn đi ốt", "Yankon" ở những danh mục không liên quan.
- [ ] 2.3 Xác minh pipeline Clean Text để đảm bảo "Đèn đi ốt" không còn bị phân loại sai vào "đèn côn trùng".
