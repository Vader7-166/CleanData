## 1. Backend Core & Deployment Setup

- [x] 1.1 Tạo cấu trúc module Backend FastAPI và import Notebook logic
- [x] 1.2 Viết Dockerfile cho Backend
- [x] 1.3 Cấu hình `docker-compose.yaml` cơ bản

## 2. API & Security Integration

- [x] 2.1 Thiết lập route `/upload` trên FastAPI kết nối tới DataCleaner module
- [x] 2.2 Thêm Basic Auth middleware hoặc Token verification vào API routes

## 3. Web UI Frontend

- [x] 3.1 Khởi tạo dự án Frontend (React/Vue/HTML Vanilla tùy mức chi tiết)
- [x] 3.2 Viết giao diện Form Upload & Download Result File với các logic gọi Auth API
- [x] 3.3 Viết Dockerfile cho Frontend service (Nginx)

## 4. CI/CD & Finalization

- [x] 4.1 Thêm pipeline config file (Ví dụ: GitHub Actions `.yml`) để tự động build Docker
- [x] 4.2 Thử nghiệm End-to-end trên môi trường local Docker Compose

## 5. Option B - Architecture Pivot

- [x] 5.1 Cập nhật `frontend/style.css` để thêm Responsive layout cho module đăng nhập
- [x] 5.2 Tạo các `SQLAlchemy` model (User, ProcessingHistory) vào `backend/models.py` và setup database (`database.py`)
- [x] 5.3 Thay thế cơ chế Basic Auth cứng bằng logic query qua User DB (`backend/main.py`)
- [x] 5.4 Ghi log file xử lý vào bảng `ProcessingHistory` trong quá trình Inference
- [x] 5.5 Kiểm thử End-to-end cho luồng xác thực Database và UI Responsive
