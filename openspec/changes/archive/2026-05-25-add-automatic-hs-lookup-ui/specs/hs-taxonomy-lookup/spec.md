## ADDED Requirements

### Requirement: Tra cứu nhanh mã HS tại trang quản lý
Hệ thống phải cung cấp một ô tìm kiếm mã HS độc lập ở đầu trang HSTaxonomy để tra cứu nhanh thông tin.

#### Scenario: Tra cứu thành công mã HS có sẵn trong hệ thống hoặc cào thành công
- **WHEN** người dùng nhập mã HS hợp lệ (ví dụ: "85395210") vào ô tra cứu nhanh và bấm nút "Tra cứu"
- **THEN** hệ thống hiển thị Card thông tin chi tiết gồm: Mã HS, Dòng sản phẩm, Lớp 1 (Ngành hàng), Phân loại NC/LK, và Nguồn gốc (cào hoặc CSDL)

#### Scenario: Tra cứu thất bại mã HS không hợp lệ hoặc không tìm thấy thông tin
- **WHEN** người dùng nhập mã HS không thể giải nghĩa và bấm nút "Tra cứu"
- **THEN** hệ thống hiển thị thông báo lỗi "Không tìm thấy thông tin cho mã HS này. Hãy tự thêm thủ công."

### Requirement: Tra cứu và tự động điền thông tin trong Dialog Thêm mới
Trong Dialog "Thêm mới" mã HS, hệ thống phải cho phép tra cứu tự động và điền nhanh thông tin dựa trên mã HS nhập vào.

#### Scenario: Auto-fill thành công khi bấm nút Tra cứu
- **WHEN** người dùng nhập mã HS vào ô nhập trong Dialog Thêm mới và nhấn nút "Tra cứu tự động"
- **THEN** hệ thống gọi API và điền tự động các giá trị tìm được vào các ô nhập: Dòng sản phẩm, Lớp 1 (Ngành hàng), Phân loại (NC/LK)

#### Scenario: Không tìm thấy thông tin khi bấm nút Tra cứu
- **WHEN** người dùng nhấn nút "Tra cứu tự động" cho một mã HS hoàn toàn không tồn tại và không cào được
- **THEN** hệ thống hiển thị cảnh báo "Không tìm thấy thông tin tự động, vui lòng tự nhập tay." và giữ nguyên các trường nhập
