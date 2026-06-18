## Context

Hiện tại, quy trình sinh từ điển đòi hỏi hệ thống phải gom cụm (DBSCAN), gắn nhãn (LLM), sau đó người dùng tải draft file về kiểm tra, rồi upload lại để chiết xuất từ khóa. Tuy nhiên, khi đầu vào là các file nghiệp vụ của Hải Quan (ví dụ HQ 2025, HQ 2026), dữ liệu đã được gán nhãn sẵn theo `Dòng SP`, `Loại`, `Lớp 1`, `Lớp 2` và có cột `Tên hàng` phong phú. Do đó, việc chạy qua toàn bộ luồng cũ là không cần thiết, làm tốn thời gian và gây khó hiểu cho người dùng.

## Goals / Non-Goals

**Goals:**
- Tối ưu hóa quy trình tạo từ điển khi đầu vào là file HQ có nhãn (từ 1-2 tiếng xuống dưới 5 phút).
- Bổ sung tuỳ chọn trên UI cho phép upload file HQ và sinh từ điển trực tiếp trong 1 bước duy nhất (hiển thị preview trước khi lưu).
- Tận dụng logic `extract_keywords_ai` có sẵn, đảm bảo không làm gãy luồng 2 bước hiện tại.

**Non-Goals:**
- Thay đổi thuật toán trích xuất từ khóa (TF-IDF + Purity ratio) hiện tại.
- Phá vỡ quy trình 2-step cũ (giữ lại cho trường hợp upload file raw chưa có nhãn).

## Decisions

1. **Thêm Endpoint API mới (`/api/dictionaries/generate/hq-direct`)**: 
   - Thay vì sử dụng `/step1` và `/step2`, luồng xử lý file HQ sẽ có endpoint riêng để gom nhóm theo nhãn (`Mã HS`, `Dòng SP`, `Loại`, `Lớp 1`, `Lớp 2`) và ngay lập tức gọi hàm trích xuất từ khóa từ `Tên hàng` trong cùng 1 request.
2. **Preview Data Structure**: 
   - Endpoint sẽ trả về một JSON chứa danh sách các nhóm đã trích xuất từ khóa (để frontend hiển thị bảng preview) thay vì sinh ra file Excel ngay lập tức. Sau khi người dùng xác nhận, UI sẽ gọi một endpoint `/save` để lưu cấu trúc đó thành file dictionary chuẩn (hoặc download CSV).
3. **Frontend Component**: 
   - Sửa đổi Component `DictionaryGenerator` trong Vue/React để thêm một tab/nút: "Tạo từ điển trực tiếp từ file HQ". Tại đây có bảng preview Keyword vs Cấu trúc để xác nhận.
4. **Tái sử dụng hàm `extract_keywords_ai`**:
   - `dict_generator.py` sẽ thêm một hàm mới như `generate_dictionary_from_hq(self, df, ...)` để thực hiện việc nhóm theo cột và chạy vòng lặp extract_keywords.

## Risks / Trade-offs

- **Risk 1**: Out of memory nếu file HQ quá lớn khi thực hiện gom nhóm trên RAM.
  - **Mitigation**: Pandas groupby hiện tại xử lý 368k rows rất mượt, chiếm khoảng vài trăm MB RAM. Không đáng lo ngại với hạ tầng hiện tại.
- **Risk 2**: File HQ bị thiếu cột hoặc sai định dạng.
  - **Mitigation**: Hàm mới phải validate file đầu vào xem có đủ 5 cột `Mã HS, Dòng SP, Loại, Lớp 1, Lớp 2` hay không trước khi thực thi. Nếu thiếu, báo lỗi UI ngay lập tức.
