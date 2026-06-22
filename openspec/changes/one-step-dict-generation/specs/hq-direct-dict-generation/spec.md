## ADDED Requirements

### Requirement: Luồng tạo từ điển 1-step từ file HQ
Hệ thống SHALL hỗ trợ việc tạo file Dictionary (CSV) trực tiếp từ file dữ liệu Hải Quan (HQ) đã có nhãn (Dòng SP, Loại, Lớp 1, Lớp 2) chỉ trong 1 bước duy nhất, bỏ qua quá trình clustering (DBSCAN) và LLM labeling.

#### Scenario: Người dùng tải lên file HQ để tạo từ điển
- **WHEN** người dùng tải lên các file HQ 2025/HQ 2026 trên giao diện và chọn tạo từ điển trực tiếp
- **THEN** hệ thống sẽ tự động nhận diện các cột nhãn, gom nhóm dữ liệu theo (Mã HS, Dòng SP, Loại, Lớp 1, Lớp 2) và trích xuất từ khóa dựa trên cột 'Tên hàng' cho từng nhóm
