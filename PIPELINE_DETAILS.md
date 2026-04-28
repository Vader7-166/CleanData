# Chi Tiết Luồng Xử Lý Dữ Liệu (Data Processing Pipeline)

Tài liệu này mô tả chi tiết cách hệ thống CleanData xử lý một tệp dữ liệu từ lúc tải lên cho đến khi trả về kết quả cuối cùng.

---

## 1. Cấu Trúc Dữ Liệu Đầu Vào (Input Analysis)

Hệ thống hỗ trợ các tệp Excel và CSV với cấu trúc không cố định. Tuy nhiên, nó tập trung nhận diện các nhóm cột sau:

*   **Thông tin hàng hóa:** `Detailed_Product`, `Detailed_Product_EN`, `Detailed_Product_CN`.
*   **Mã phân loại:** `HS_Code`.
*   **Thông tin đối tác:** `VN_Importer`, `VN_Exporter`, `Foreign_Importer`, `Foreign_Exporter`.
*   **Thông tin địa lý:** `Origin_Country`, `Destination_Country`, `Continent`.
*   **Thông tin tài chính/vận chuyển:** `Quantity`, `Unit_Qty`, `Total_Value_USD`, `Unit_Price_USD`, `Incoterms`, `Method_of_Payment`.
*   **Thời gian:** `Date`, `Month`.

---

## 2. Các Bước Xử Lý Chi Tiết

### Bước 1: Ánh xạ Cột (Initial Mapping)
Hệ thống thực hiện ánh xạ tự động để đưa dữ liệu thô về cấu trúc làm việc nội bộ:
- **Xác định loại hình:** Nếu có cột `VN_Exporter`, hệ thống hiểu đây là dữ liệu **Xuất khẩu**. Nếu có `VN_Importer`, đây là dữ liệu **Nhập khẩu**.
- **Xử lý Thời gian:** Ưu tiên lấy Tháng từ cột `Date`. Nếu không có, sẽ bóc tách 2 ký tự cuối từ cột `Month`. Định dạng cuối cùng là `Tháng X`.
- **Hợp nhất Tên hàng:** Ưu tiên lấy từ `Detailed_Product`, nếu trống sẽ fallback (dự phòng) qua bản tiếng Anh hoặc tiếng Trung.

### Bước 2: Bóc tách Thông tin Đặc tính (Extraction Logic)
Sử dụng hàm `trich_xuat_thong_tin` để xử lý từng dòng mô tả hàng hóa:
1.  **Lọc nhiễu Hải quan:** Nếu chuỗi chứa ký tự đặc biệt `#&` (thường dùng để ngăn cách các phần trong tờ khai), hệ thống sẽ tách chuỗi và chỉ giữ lại phần có độ dài lớn nhất (phần mô tả chính).
2.  **Trích xuất Công suất:** Sử dụng Regex `(\d+(?:\.\d+)?)\s*(w|watt|hp|kw|kva|v)` để tìm các thông số kỹ thuật.
3.  **Nhận diện Hãng:** Tìm kiếm trong danh sách các thương hiệu phổ biến như `Rạng Đông`, `Philips`, `Panasonic`,... trong chuỗi văn bản.

### Bước 3: Phân loại bằng Từ điển (Dictionary Pass)
Dữ liệu được làm sạch (`input_for_ai`) sẽ đi qua bộ lọc từ điển trước:
- **Chuẩn hóa:** Chuyển về chữ thường, loại bỏ ký tự đặc biệt.
- **Thuật toán Nuốt từ (Masking):** 
    - Duyệt danh sách từ khóa từ dài đến ngắn.
    - Khi một từ khóa khớp, nó sẽ bị "xóa" khỏi chuỗi tạm thời để không bị khớp lặp lại cho các từ khóa ngắn hơn bên trong nó.
- **Tính điểm (Scoring):**
    - **Nhóm Chốt hạ (High Value):** Nếu chứa các từ đặc trưng ngành (ví dụ: `năng lượng mặt trời`, `âm trần`, `ufo`), cộng **20 điểm**.
    - **Nhóm Thường:** Điểm cộng bằng số lượng từ trong cụm từ khóa.
    - **Nhóm Rác:** Bị xóa nhưng không cộng điểm (ví dụ: `mới 100%`, `chính hãng`).
- **Kết quả:** Nếu tổng điểm >= 15, dòng đó được gán nhãn ngay lập tức.

### Bước 4: Phân loại bằng AI (AI Fallback Pass)
Những dòng không khớp từ điển hoặc điểm thấp sẽ được đẩy vào mô hình PhoBERT:
- **Input:** Chuỗi văn bản tổng hợp: `Hãng: ... - Công suất: ... - Sản phẩm: ...`
- **Xử lý Batch:** Để tăng tốc độ, AI xử lý theo từng cụm 64 dòng một lúc.
- **Độ tự tin:** Mô hình trả về xác suất cho từng nhãn. Nếu xác suất < 0.85, hệ thống vẫn gán nhãn nhưng đánh dấu trạng thái là "Cần kiểm tra".

### Bước 5: Định dạng và Reindex (Final Formatting)
- Kết quả từ 4 cấp độ (Dòng SP, Loại, Lớp 1, Lớp 2) được tách ra từ chuỗi nhãn gộp.
- Hệ thống thực hiện **Reindex** theo một tệp mẫu (`sample.csv`) để đảm bảo thứ tự cột đúng yêu cầu xuất báo cáo.
- Các cột không nằm trong danh sách chuẩn nhưng có trong file gốc vẫn được giữ lại và đẩy về phía cuối file.

---

## 3. Quy trình từng hàng (Row-level logic)

| Dữ liệu gốc (Ví dụ) | Xử lý bóc tách | Kết quả phân loại | Trạng thái |
| :--- | :--- | :--- | :--- |
| `Bộ đèn led âm trần 9W #& hiệu Philips #& mới 100%` | Hãng: Philips, CS: 9W, Tên: Bộ đèn led âm trần | Đèn Led \| NC \| Dân dụng \| Âm trần | Tự động duyệt (Từ điển) |
| `Linh kiện đèn led: Chip led SMD` | Hãng: (trống), CS: (trống), Tên: Chip led SMD | Đèn Led \| LK \| Linh kiện \| Chip Led | Tự động duyệt (AI) |

---

## 4. Các Tham số Cấu hình chính
- `THRESHOLD = 0.85`: Ngưỡng tin cậy tối thiểu của AI.
- `DICT_THRESHOLD = 15`: Ngưỡng điểm tối thiểu để chấp nhận kết quả từ điển.
- `Batch Size = 64`: Số dòng xử lý song song bởi GPU/CPU.
