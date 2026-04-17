## Why

Hiện tại, logic làm sạch dữ liệu dựa trên mô hình NLP (TF-IDF + model `/working` cũ) gặp hạn chế nếu người dùng tự chạy hoặc chạy trên máy cá nhân chậm. Chúng ta cần thiết lập một Web App nội bộ có Backend mạnh mẽ để xử lý, cùng giao diện Web thân thiện. Đồng thời, do là Web App nên hệ thống cần tích hợp các giải pháp bảo mật dữ liệu và chuẩn hóa quy trình deploy (CI/CD) để sau này dễ nâng cấp và duy trì.

## What Changes

- Xây dựng Backend API (FastAPI hoặc Flask) để chứa logic Inference/NLP.
- Xây dựng Frontend Web UI cho người dùng (có thể là React, Vue, hoặc Next.js).
- Bổ sung xác thực (Authentication) hoặc cơ chế bảo vệ API để tránh truy cập trái phép.
- Đóng gói ứng dụng bằng Docker và thiết lập pipeline CI/CD cơ bản để deploy server nội bộ dễ dàng.

## Capabilities

### New Capabilities
- `data-cleaning-api`: Backend API nhận file, làm sạch dữ liệu và trả về kết quả.
- `web-ui`: Giao diện ứng dụng người dùng chạy trên trình duyệt.
- `security-deployment`: Khả năng bảo mật (Auth/Rate-limit) và quy trình CI/CD/Dockerization.

### Modified Capabilities

## Impact

- Cần server có đủ tài nguyên RAM/CPU để chạy backend liên tục.
- Yêu cầu cấu hình Docker và Server Web nội bộ (Nginx/Traefik).
