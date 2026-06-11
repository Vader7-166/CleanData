## Why

Thuật toán DBSCAN hiện tại đang tạo ra ma trận khoảng cách N x N thông qua hàm `cosine_distances`. Khi hệ thống gặp các file chứa số lượng lớn sản phẩm dồn vào cùng một Mã HS (ví dụ 30,000 dòng đều thuộc mã 850440), kích thước của ma trận khoảng cách này sẽ tiêu tốn hàng GB bộ nhớ RAM, dẫn đến tràn bộ nhớ (Out of Memory - OOM). Hệ điều hành sẽ ngay lập tức kill tiến trình backend Python, làm đứt kết nối Database đột ngột (`unexpected EOF on client connection`). Chúng ta cần tối ưu hóa cách chạy DBSCAN để có thể xử lý được khối lượng dữ liệu dồn cục lớn mà không sập hệ thống.

## What Changes

- Sửa thuật toán DBSCAN từ việc tính toán trước ma trận (precomputed) sang chạy tính toán trực tiếp trên ma trận thưa (sparse matrix) `m`.
- Giữ nguyên `TfidfVectorizer` (vốn đã chuẩn hóa độ dài vector theo chuẩn L2 - l2 norm mặc định).
- Không gọi hàm `cosine_distances(m)` để tạo mảng N x N nữa.
- Thay vì gọi `DBSCAN(eps=eps, min_samples=min_samples, metric='precomputed').fit_predict(d)`, ta gọi trực tiếp: `DBSCAN(eps=np.sqrt(2 * eps), min_samples=min_samples, metric='euclidean', algorithm='brute').fit_predict(m)`. Hoặc dùng trực tiếp `metric='cosine'` trên mảng `m`. 
- Thêm import numpy nếu chưa có.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `dictionary-generator`: Sửa đổi logic gom nhóm bằng thuật toán DBSCAN bên trong class `DictionaryGenerator` (Hàm `cluster_products`). Không thay đổi requirement ở mức người dùng, chỉ thay đổi logic tối ưu bên dưới. 

## Impact

- **Affected code**: `backend/core/dict_generator.py` (cụ thể là method `cluster_products`).
- **Dependencies**: Tận dụng triệt để Scikit-learn DBSCAN chạy trên sparse matrix (brute force) giúp CPU/RAM hiệu quả hơn.
- **Systems**: Backend (không còn lo lắng bị OOM và sập kết nối Postgres). Kết quả phân cụm giống y hệt như cũ.
