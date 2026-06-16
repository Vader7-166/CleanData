# Hệ thống Làm Sạch & Chuẩn Hóa Dữ Liệu HS (Excel Data Cleaner)

Hệ thống bán tự động hỗ trợ doanh nghiệp và chuyên viên xử lý khối lượng lớn dữ liệu xuất nhập khẩu (Excel/CSV). Bằng việc kết hợp các tập luật cố định (Từ điển tra cứu), dữ liệu chuẩn (Biểu thuế XNK Chính thức) và trí tuệ nhân tạo (NLP - TF-IDF & PhoBERT), hệ thống giúp tự động hóa quá trình phân loại mã HS, gán nhãn Dòng Sản Phẩm và làm sạch dữ liệu với độ chính xác cao.

## ✨ Tính Năng Nổi Bật

- **Xử lý Hàng Loạt (Batch Processing):** Hỗ trợ kéo thả và xử lý cùng lúc hàng chục file Excel/CSV, giúp tiết kiệm thời gian gom nhóm và chuẩn hóa.
- **Tạo Từ Điển Tự Động (Dictionary Generator):** Tự động phân tích các tập dữ liệu lịch sử để trích xuất các quy tắc phân loại, kết hợp với NLP (TF-IDF) để gợi ý tên sản phẩm ngắn gọn, dễ hiểu.
- **Hệ Sinh Thái Biểu Thuế (HS Taxonomy):** Được tích hợp sẵn cơ sở dữ liệu Biểu Thuế XNK chính thức, đảm bảo các mã HS và Lớp phân loại luôn tuân thủ tiêu chuẩn hải quan.
- **Kiểm Tra Trực Quan (Data Preview & Insights):** Giao diện thống kê sinh động giúp người dùng dễ dàng xem biểu đồ phân bổ hàng hóa, đối soát lỗi và xuất báo cáo (Excel/ZIP).
- **AI Fallback:** Với những dữ liệu chưa từng xuất hiện trong từ điển, mô hình học sâu **PhoBERT** sẽ dự đoán ngữ cảnh và tự động đề xuất nhãn phân loại tối ưu nhất.

## 🚀 Công Nghệ Sử Dụng

- **Frontend:** React, TypeScript, TailwindCSS, Vite, Radix UI.
- **Backend:** Python, FastAPI, Pandas, Scikit-learn, SQLAlchemy.
- **Deployment:** Docker, Docker Compose.

## 📥 Tải Dữ Liệu & Mô Hình

> [!IMPORTANT]
> Để hệ thống có thể chạy phần AI (PhoBERT) và nạp dữ liệu gốc, bạn cần tải tập dataset và model weights về trước.

**Link tải Dataset và Model:** [Google Drive Link](https://drive.google.com/drive/folders/1lugdcMKvvc8eayBwSQQWD6XzrBzO9ouG?usp=sharing)

Sau khi tải về, vui lòng giải nén và đặt vào các thư mục cấu hình tương ứng trong source code (theo tài liệu hướng dẫn nội bộ) trước khi khởi động server.

## ⚙️ Hướng Dẫn Cài Đặt (Sử dụng Docker)

Cách nhanh nhất để khởi chạy toàn bộ hệ thống là sử dụng Docker.

1. **Clone repository:**
   ```bash
   git clone <repository_url>
   cd CleanData
   ```

2. **Khởi chạy bằng Docker Compose:**
   ```bash
   docker-compose up -d --build
   ```

3. **Truy cập Ứng Dụng:**
   - **Frontend UI:** `http://localhost:5173`
   - **Backend API Docs:** `http://localhost:8000/docs`

## 📚 Hướng Dẫn Sử Dụng Nhanh

1. Truy cập trang **Dictionary Generator**, upload file Excel lịch sử để hệ thống tự động học và tạo ra từ điển quy tắc (Dictionary).
2. Chuyển sang trang **Clean Data**, kéo thả các file Excel dữ liệu thô mới vào để hệ thống bắt đầu quá trình làm sạch và gán mã HS.
3. Khi hoàn tất, nhấn **View Insights & Preview** để kiểm tra các dòng "Cần kiểm tra" (bị thiếu hoặc sai thông tin) và tải file kết quả đã gộp.

---
*Dự án nội bộ - Vui lòng không chia sẻ mã nguồn và dữ liệu ra ngoài khi chưa được phép.*
