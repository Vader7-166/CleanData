# Hệ Thống Chuẩn Hóa và Phân Loại Dữ Liệu Hải Quan (CleanData)

Dự án này là một hệ thống tự động hóa quy trình làm sạch, chuẩn hóa và phân loại dữ liệu xuất nhập khẩu (Hải quan). Hệ thống kết hợp sức mạnh của quy tắc từ điển (Dictionary-based) và trí tuệ nhân tạo (AI - PhoBERT) để phân loại hàng hóa vào các nhóm ngành cụ thể một cách chính xác.

## 1. Mục tiêu dự án
- Tự động hóa việc map các cột dữ liệu thô từ nhiều nguồn khác nhau về một định dạng chuẩn.
- Trích xuất thông tin đặc tính sản phẩm (Hãng, Công suất) từ mô tả hàng hóa.
- Phân loại hàng hóa theo 4 cấp bậc: **Dòng SP | Loại | Lớp 1 | Lớp 2**.
- Cung cấp giao diện trực quan để theo dõi tiến độ và tải kết quả.

## 2. Quy trình hoạt động (Workflow)

Hệ thống hoạt động theo một đường ống (Pipeline) gồm các bước sau:

### Bước 1: Tiếp nhận và Tiền xử lý (Data Loading & Mapping)
- **Đầu vào:** File Excel (.xlsx) hoặc CSV (.csv) chứa dữ liệu thô.
- **Xử lý:** 
    - Nhận diện các cột tương ứng như `Detailed_Product`, `HS_Code`, `VN_Importer`, `VN_Exporter`,...
    - Chuyển đổi về định dạng chuẩn của hệ thống.
    - Xử lý ngày tháng và các giá trị thiếu (NaN).

### Bước 2: Trích xuất thông tin (Information Extraction)
- Sử dụng Regular Expression (Regex) để bóc tách:
    - **Công suất:** Các thông số như `10W`, `20W`, `5HP`, `220V`,...
    - **Hãng:** Nhận diện các thương hiệu phổ biến (Rạng Đông, Philips, Panasonic, LG,...).
    - **Tên hàng rút gọn:** Loại bỏ các ký tự nhiễu của Hải quan (ví dụ: `#&`).

### Bước 3: Phân loại Hybrid (Hybrid Classification Strategy)
Đây là trái tim của hệ thống, kết hợp hai phương pháp:

1.  **Giai đoạn 1 - Khớp Từ điển (Dictionary Matching):**
    - Hệ thống sử dụng bộ từ điển `dictv3.csv` chứa hàng nghìn từ khóa được gán nhãn sẵn.
    - **Thuật toán "Nuốt từ" (Keyword Consumption):** Tìm kiếm các cụm từ dài nhất trước để tránh nhầm lẫn.
    - **Chấm điểm (Scoring):** Mỗi từ khóa khớp sẽ được cộng điểm. Nếu tổng điểm vượt ngưỡng (`DICT_THRESHOLD = 15`), kết quả từ điển sẽ được chấp nhận ngay (độ tự tin 100%).
2.  **Giai đoạn 2 - Dự đoán AI (AI Inference):**
    - Nếu từ điển không tìm thấy hoặc điểm quá thấp, dữ liệu sẽ được chuyển qua mô hình **PhoBERT** (đã được fine-tune).
    - AI sẽ dự đoán nhãn dựa trên ngữ cảnh của tên hàng. 
    - Kết quả chỉ được "Tự động duyệt" nếu độ tự tin đạt trên 85%.

### Bước 4: Hậu xử lý và Xuất bản (Post-processing)
- Sắp xếp lại thứ tự cột theo yêu cầu nghiệp vụ.
- Gán nhãn trạng thái: `Tự động duyệt (AI)`, `Tự động duyệt (Từ điển)` hoặc `Cần kiểm tra`.
- **Đầu ra:** File đã làm sạch hoàn chỉnh và bản xem trước (Preview) 100 dòng đầu tiên trên giao diện.

## 3. Chi tiết Đầu vào & Đầu ra

### Đầu vào (Input)
Các tệp tin dữ liệu hải quan thường có các cột:
- `Detailed_Product`: Mô tả chi tiết hàng hóa (Tiếng Việt/Anh/Trung).
- `HS_Code`: Mã phân loại hàng hóa.
- `VN_Importer` / `VN_Exporter`: Tên công ty nhập/xuất khẩu.
- `Quantity`, `Unit_Price_USD`, `Total_Value_USD`: Thông tin về lượng và giá.

### Đầu ra (Output)
File kết quả chuẩn hóa với các cột quan trọng đã được xử lý:
| Cột | Mô tả |
| :--- | :--- |
| **Ngày** | Tháng phát sinh giao dịch |
| **Tên hàng** | Tên hàng đã được làm sạch nhiễu |
| **Hãng** | Thương hiệu trích xuất được |
| **Công suất** | Thông số kỹ thuật (W, V, HP...) |
| **Dòng SP** | Phân loại cấp 1 (Ví dụ: Đèn Led) |
| **Loại** | Phân loại cấp 2 (Ví dụ: NC - Nguyên chiếc) |
| **Lớp 1** | Phân loại cấp 3 (Ví dụ: Đèn dân dụng) |
| **Lớp 2** | Phân loại cấp 4 (Ví dụ: Đèn âm trần) |
| **Trạng thái** | Nguồn gốc phân loại (AI/Từ điển/Cần kiểm tra) |
| **Độ tự tin** | % xác suất chính xác của AI |

## 4. Công nghệ sử dụng
- **Backend:** FastAPI, Pandas, PyTorch, Transformers (HuggingFace).
- **Model:** PhoBERT (vinai/phobert-base-v2).
- **Frontend:** HTML/JS (với Server-Sent Events để cập nhật tiến độ thời gian thực).
- **Containerization:** Docker & Docker Compose.
