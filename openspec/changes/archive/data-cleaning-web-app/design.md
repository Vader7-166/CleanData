## Context

Do hạn chế về mặt tài nguyên trên máy cục bộ của người dùng thường và hạn chế cài đặt, việc chuyển logic làm sạch số liệu (`PhoBertmappingv2`) lên nền tảng Web sẽ hiệu quả hơn. Người dùng chỉ cần vào đường dẫn trang web, upload Excel/CSV và có được kết quả sau một nút nhấn.

## Goals / Non-Goals

**Goals:**
- Tách inference logic vào backend Python.
- Có frontend tương tác dễ dùng qua HTTP/REST.
- Thiết lập cơ chế bảo mật cơ bản (ví dụ API Keys hoặc Basic Auth) để dữ liệu lưu chuyển nội bộ không lọt ra ngoài.
- Dùng Docker và CI/CD để build & deploy tự động khi có cập nhật mô hình mới vào `/working`.

**Non-Goals:**
- Không publish ứng dụng ra Public Internet, chỉ giới hạn hạ tầng công ty.

## Decisions

- **Backend**: FastAPI - Nhanh, hỗ trợ async khi xử lý I/O hoặc file tải lên tải xuống, dễ deploy pipeline ML.
- **Frontend**: Nhanh nhất có thể xài React/Vite hoặc Vanilla HTML/CSS/JS (cần hỗ trợ Responsive UI).
- **Security & Database (Option B)**: Tích hợp SQLAlchemy + SQLite để lưu trữ `User` (chứng thực bảo mật bằng bcrypt) và bảng `ProcessingHistory` để log lại các giao dịch xử lý file. 
- **Deployment & CI/CD**: Docker Compose cho cả Web và API container. CI/CD qua GitHub Actions (hoặc Gitlab CI) để build image tự động mỗi khi merge code.

## Risks / Trade-offs

- **Bottleneck xử lý file lớn**: Một server chung xử lý các file Excel nặng liên tục có thể sinh lỗi Timeout hoặc Overload Memory. 
  *Mitigation*: Có thể tích hợp logic Queue (Celery/RabbitMQ) sau này nếu tải lớn, nhưng ở thời điểm hiện tại sẽ xài background task của FastAPI để xử lý offline và trả kết quả sau.
