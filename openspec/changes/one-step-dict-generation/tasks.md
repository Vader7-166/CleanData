## 1. Backend Core Logic

- [x] 1.1 Thêm hàm `generate_dictionary_from_hq` trong `dict_generator.py`
- [x] 1.2 Implement logic gom nhóm (groupby) file HQ theo 5 cột (`Mã HS`, `Dòng SP`, `Loại`, `Lớp 1`, `Lớp 2`) trong hàm mới
- [x] 1.3 Tích hợp thuật toán `extract_keywords_ai` vào hàm mới để sinh từ khóa dựa trên cột `Tên hàng` và trả về danh sách kết quả từ khóa

## 2. Backend API

- [x] 2.1 Thêm endpoint `/api/dictionaries/generate/hq-direct` vào `main.py`
- [x] 2.2 Cập nhật endpoint để nhận file tải lên, gọi hàm `generate_dictionary_from_hq`, định dạng lại kết quả dạng JSON và gửi về cho frontend
- [x] 2.3 Thêm tính năng export CSV trực tiếp từ JSON data nếu cần (tuỳ chọn API `/save`)

## 3. Frontend UI

- [x] 3.1 Cập nhật màn hình `DictionaryGenerator` (hoặc view tương ứng) thêm lựa chọn luồng "Tạo từ điển trực tiếp từ file HQ"
- [x] 3.2 Tích hợp tính năng upload file và gọi endpoint `/api/dictionaries/generate/hq-direct`
- [x] 3.3 Xây dựng bảng hiển thị (Preview Table) để duyệt trước danh sách từ khóa vừa sinh ra
- [x] 3.4 Thêm nút "Xác nhận & Tải xuống", xử lý xuất file CSV chuẩn 6 cột trực tiếp trên trình duyệt hoặc qua backend
