## Context
Class `DictionaryGenerator` trong file `backend/core/dict_generator.py` đang sử dụng TF-IDF Vectorizer và DBSCAN để phân cụm sản phẩm theo từng nhóm (Mã HS). Quá trình này dùng `cosine_distances(m)` tạo ra một ma trận khoảng cách đầy đủ (dense matrix) N x N. Việc này chạy ổn định khi số dòng của 1 mã HS nhỏ (vài nghìn), nhưng gây ra lỗi Out of Memory (OOM) ở phía hệ điều hành và DB connection bị kill ngay khi xử lý các file dồn trên 10.000 dòng vào cùng một mã HS, vì ma trận vượt quá giới hạn RAM vài GB.

## Goals / Non-Goals
**Goals:**
- Loại bỏ quá trình tạo ma trận khoảng cách dense N x N trong `DBSCAN`.
- Xử lý các file raw chứa hơn 10.000 dòng ở một Mã HS duy nhất mà không bị sập bộ nhớ, tốc độ vẫn đảm bảo.
- Kết quả đầu ra thuật toán DBSCAN được giữ nguyên hoàn toàn so với phiên bản trước.

**Non-Goals:**
- Không thay đổi nghiệp vụ phân loại.
- Không đổi thư viện `scikit-learn` sang nền tảng hay framework khác.

## Decisions
**Decision:** Chuyển từ metric `precomputed` sang tính khoảng cách euclidean quy đổi (equivalent euclidean distance) trên ma trận thưa.
- **Why:** TF-IDF trong scikit-learn tự động chuẩn hóa vector ở độ dài L2-norm (`norm='l2'`). Với vector chuẩn hóa L2, Khoảng cách Cosine liên hệ trực tiếp với Khoảng cách Euclidean thông qua công thức: `Euclidean^2 = 2 * Cosine`.
- **Action:** Ta sẽ tính lại ngưỡng epsilon `eps_euclid = np.sqrt(2 * eps)`. Truyền ma trận `m` thẳng vào: `DBSCAN(eps=eps_euclid, min_samples=min_samples, metric='euclidean', algorithm='brute').fit_predict(m)`. Cú pháp này tính khoảng cách từng cặp theo lô (chunking) bên dưới C++ của scikit-learn, tránh hoàn toàn OOM. Tốc độ thậm chí còn nhanh hơn do không phải cấp phát RAM.

**Alternatives Considered:**
- Truyền `metric='cosine'` trực tiếp vào `DBSCAN` (cũng được nhưng tính hỗ trợ tuỳ thuộc vào version cụ thể của scikit-learn). Việc dùng `euclidean` trên `l2` data là an toàn nhất và phổ quát nhất.

## Risks / Trade-offs
- **Risk**: Nếu thư viện `TfidfVectorizer` bị thay đổi config `norm` từ `l2` sang thứ khác trong tương lai, công thức quy đổi sẽ sai lệch. 
- **Mitigation**: Cấu hình `norm='l2'` là mặc định và hiếm khi bị đổi. Sẽ review kỹ nếu có yêu cầu sửa TFIDF.
