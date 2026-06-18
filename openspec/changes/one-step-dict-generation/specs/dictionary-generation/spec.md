## MODIFIED Requirements

### Requirement: API sinh từ điển hỗ trợ xử lý 1 bước trực tiếp
Hệ thống backend API SHALL cung cấp các endpoint cho phép client kích hoạt quá trình sinh từ điển. Quá trình sinh từ điển SHALL hỗ trợ cả luồng 2 bước (raw file -> draft taxonomy -> dictionary) và luồng 1 bước mới (HQ labeled file -> dictionary preview).

#### Scenario: Kích hoạt luồng 1 bước qua API
- **WHEN** client gọi đến endpoint `/api/dictionaries/generate/hq-direct` với các file HQ
- **THEN** API sẽ tự động đọc file, gom nhóm dữ liệu theo các cột nhãn, trích xuất từ khóa, và trả về một JSON preview chứa thông tin từ điển để frontend hiển thị, mà không cần thông qua bước sinh file draft Excel trung gian
