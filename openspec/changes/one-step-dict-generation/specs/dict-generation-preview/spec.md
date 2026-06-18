## ADDED Requirements

### Requirement: Hiển thị preview cho luồng tạo từ điển trực tiếp
Giao diện người dùng SHALL cung cấp một bước preview dữ liệu từ điển (sau khi đã gom nhóm và trích xuất từ khóa) trước khi lưu lại thành file CSV.

#### Scenario: Xem trước và xác nhận kết quả tạo từ điển
- **WHEN** hệ thống hoàn thành việc nhóm và trích xuất từ khóa từ file HQ
- **THEN** một bảng danh sách các nhóm kèm theo Từ khóa, Dòng SP, Loại, Lớp 1, Lớp 2, Mã HS sẽ được hiển thị trên giao diện để người dùng có thể tải về file dictionary CSV
