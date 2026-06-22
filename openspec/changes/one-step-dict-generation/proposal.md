## Why

Hiện tại quy trình tạo từ điển (Dictionary Generator) yêu cầu nhiều bước phức tạp: chạy DBSCAN, có thể gọi LLM, sau đó sinh draft, review, rồi lại upload lên để sinh từ khóa. Khi đầu vào đã là file nghiệp vụ Hải Quan (HQ 2025, HQ 2026) - vốn đã chứa sẵn cả cấu trúc phân loại (Dòng SP, Loại, Lớp 1, Lớp 2) và tên hàng thực tế để trích xuất từ khóa - thì quy trình này là quá dư thừa, mất thời gian (hàng tiếng đồng hồ cho 368k rows) và sinh ra circular dependency không cần thiết. Chúng ta cần một luồng 1 bước duy nhất, nhanh chóng, trích xuất từ khóa trực tiếp từ file HQ và xuất ra file CSV Dictionary chuẩn.

## What Changes

- Bỏ qua toàn bộ DBSCAN và LLM labeling khi nhận diện được file HQ.
- Thực hiện gom nhóm (Group By) trực tiếp theo 5 cột: `Mã HS`, `Dòng SP`, `Loại`, `Lớp 1`, `Lớp 2`.
- Trích xuất từ khóa cho mỗi nhóm bằng thuật toán TF-IDF / purity hiện tại dựa trên `Tên hàng` thực tế của tờ khai trong file HQ, với tập background là toàn bộ dữ liệu HQ khác.
- Sinh trực tiếp file CSV từ điển với đủ 6 cột chuẩn mà không cần qua bước trung gian (không sinh draft excel sheet "Raw + Cluster").
- Cập nhật giao diện (UI) để hỗ trợ luồng "Tạo từ điển trực tiếp từ file HQ" (1-step generation với preview từ khóa trước khi lưu).

## Capabilities

### New Capabilities
- `hq-direct-dict-generation`: Luồng tạo từ điển 1 bước trực tiếp từ các file HQ, gom nhóm theo các nhãn nghiệp vụ có sẵn và trích xuất từ khóa.
- `dict-generation-preview`: Giao diện (UI) hiển thị preview kết quả trích xuất từ khóa cho mỗi nhóm trước khi người dùng xác nhận lưu thành dictionary.

### Modified Capabilities
- `dictionary-generation`: Sửa đổi API hiện tại để hỗ trợ luồng 1-step (nhận file, group by, extract keyword, trả về JSON preview hoặc tải xuống CSV luôn).

## Impact

- **Backend Core**: `dict_generator.py` sẽ có thêm hàm xử lý trực tiếp một bước (gom nhóm và gọi `extract_keywords_ai`).
- **Backend API**: `main.py` sẽ thêm/sửa đổi endpoint để hỗ trợ luồng mới.
- **Frontend UI**: Thêm tuỳ chọn luồng sinh từ điển từ file HQ, có màn hình preview.
- **Hiệu suất**: Giảm thời gian sinh từ điển từ vài tiếng xuống dưới 5 phút.
