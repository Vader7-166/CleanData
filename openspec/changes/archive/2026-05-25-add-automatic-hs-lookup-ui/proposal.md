## Why

Hiện tại, người dùng quản trị khi muốn thêm một mã HS mới vào cơ sở dữ liệu (HSTaxonomy) phải tự tìm kiếm và nhập thủ công tất cả các thông tin (Mã HS, Dòng sản phẩm, Lớp 1 - Ngành hàng, và Phân loại NC/LK) trên giao diện. Điều này tốn thời gian và dễ xảy ra sai sót. Mặc dù Backend đã hỗ trợ cơ chế cào dữ liệu và LLM tự động thông qua endpoint `/api/taxonomy/check-hs-codes`, tính năng này vẫn chưa được hiển thị trên giao diện người dùng để tra cứu nhanh hoặc điền nhanh thông tin.

## What Changes

- Bổ sung Card **"Tra cứu nhanh mã HS"** ở ngay đầu trang quản lý `HSTaxonomy.tsx` để người dùng có thể nhập mã HS và nhấn nút "Tra cứu". Hệ thống sẽ gọi API `/api/taxonomy/check-hs-codes` để tự động lấy dữ liệu (cào web/AI) và hiển thị thông tin trả về, đồng thời tự động lưu mã HS mới vào CSDL nếu chưa tồn tại.
- Thêm nút **"Tra cứu tự động"** bên cạnh ô nhập Mã HS trong Dialog **"Thêm mới"** của `HSTaxonomy.tsx`. Khi nhấn nút này, hệ thống sẽ tự động điền các thông tin (Dòng sản phẩm, Lớp 1, và Phân loại NC/LK) tương ứng vào form.
- Chuyển ô nhập **Dòng sản phẩm** trong Dialog "Thêm mới" thành ô nhập tự do (Input) thay vì Selectbox giới hạn cứng để hỗ trợ các dòng sản phẩm động được trả về từ Crawler/AI.

## Capabilities

### New Capabilities
- `hs-taxonomy-lookup`: Cung cấp tính năng tra cứu tự động và điền nhanh thông tin mã HS cho người dùng thông qua giao diện trực quan.

### Modified Capabilities

## Impact

- Giao diện frontend: `HSTaxonomy.tsx` (Thêm Card tra cứu nhanh, sửa Dialog thêm mới, chuyển Select thành Input cho Dòng sản phẩm).
- APIs: Tận dụng trực tiếp API `/api/taxonomy/check-hs-codes` và `/api/taxonomy`.
