## MODIFIED Requirements

### Requirement: Tra cứu nhanh mã HS tại trang quản lý
Hệ thống phải cung cấp một ô tìm kiếm mã HS độc lập ở đầu trang HSTaxonomy để tra cứu nhanh thông tin.

#### Scenario: Tra cứu thành công mã HS có sẵn trong hệ thống hoặc cào thành công
- **WHEN** người dùng nhập mã HS hợp lệ (ví dụ: "01012100") vào ô tra cứu nhanh và bấm nút "Tra cứu"
- **THEN** hệ thống hiển thị Card thông tin chi tiết gồm: Mã HS, Dòng sản phẩm (được tự động lấy từ mô tả của nhóm 4 số đầu tiên trong database ví dụ "SP NGỰA" thay vì "SP 0101"), Lớp 1 (Ngành hàng), Phân loại NC/LK, và Nguồn gốc ("offline_cache")
