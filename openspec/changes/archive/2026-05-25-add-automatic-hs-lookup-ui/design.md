## Context

Hiện tại CSDL mã HS (HSTaxonomy) đã hỗ trợ API `/api/taxonomy/check-hs-codes` trên backend để tra cứu, tự động cào và điền thông tin (Dòng sản phẩm, Lớp 1, và Phân loại). Tuy nhiên, trang quản trị `HSTaxonomy.tsx` ở frontend chưa được cập nhật giao diện để tận dụng API này, bắt buộc người dùng khi thêm mã HS mới phải nhập tay toàn bộ thông tin.

## Goals / Non-Goals

**Goals:**
- Thêm giao diện Tra cứu nhanh (Quick Lookup) mã HS bằng cách gọi API `/api/taxonomy/check-hs-codes`.
- Thêm nút Tra cứu tự động (Auto-fill) trong form Thêm mới mã HS.
- Thay đổi selectbox Dòng sản phẩm (hiện tại bị fix cứng 5 giá trị) thành ô Input nhập tự do để tương thích với kết quả trả về từ Crawler/AI.

**Non-Goals:**
- Sửa đổi hoặc tối ưu hóa thêm thuật toán Crawler/Clustering trên Backend (đã hoàn thành ở phần trước).

## Decisions

### 1. Vị trí hiển thị tính năng Tra cứu nhanh (Quick Lookup)
- **Quyết định**: Đặt một card tra cứu nhanh ngay trên đầu bảng quản lý của `HSTaxonomy.tsx`.
- **Lý do**: Giúp người dùng thực hiện nhanh thao tác tra cứu mà không cần mở bất kỳ Modal/Dialog nào.
- **Giải pháp thay thế**: Tạo một trang route riêng `/taxonomy/lookup` (loại bỏ vì gây chia cắt trải nghiệm quản lý).

### 2. Auto-fill trong Modal "Thêm mới"
- **Quyết định**: Thêm nút "Tra cứu tự động" cạnh ô nhập Mã HS trong Dialog.
- **Lý do**: Khi gõ xong Mã HS, bấm nút này sẽ tự động gọi API và điền các trường Dòng sản phẩm, Lớp 1, Phân loại NC/LK, tiết kiệm tối đa thời gian nhập liệu.

### 3. Thay đổi ô nhập Dòng sản phẩm
- **Quyết định**: Chuyển component Select thành Input cho trường `dong_sp`.
- **Lý do**: Tên dòng sản phẩm hiện tại đã được crawler cào động từ web hải quan (Heading) hoặc sinh từ DeepSeek, không còn giới hạn cứng ở 5 danh mục như trước.

## Risks / Trade-offs

- **Risk**: API check-hs-codes có thể phản hồi chậm (từ 5-15 giây) nếu phải chạy crawler trực tiếp và gọi DeepSeek LLM.
- **Mitigation**: Thêm trạng thái loading rõ ràng và disable nút bấm trong khi đang gọi API để ngăn chặn click liên tiếp của người dùng.
