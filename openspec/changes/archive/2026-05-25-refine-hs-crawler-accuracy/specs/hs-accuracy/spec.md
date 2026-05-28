## ADDED Requirements

### Requirement: Độ chính xác của tên Lớp 1 khi tra cứu tự động
Hệ thống phải đảm bảo kết quả tra cứu tự động trả về đúng mô tả chi tiết của mã phân nhóm 8-số thay vì mô tả của Heading 4-số.

#### Scenario: Tra cứu chính xác mã HS 90012000
- **WHEN** cào hoặc dùng AI phân tích mã "90012000"
- **THEN** tên ngành (industry_name) phải là "Vật liệu phân cực dạng tấm và lá" hoặc tương đương (không được trùng với mô tả của nhóm 9001 là "Thấu kính, lăng kính...")

#### Scenario: Tra cứu chính xác mã HS 74061000
- **WHEN** cào hoặc dùng AI phân tích mã "74061000"
- **THEN** tên ngành (industry_name) phải là "Bột không cấu trúc lớp" hoặc tương đương (không được nhầm sang dạng phiến "74062000")
