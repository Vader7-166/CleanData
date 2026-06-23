## Context

Sau Phase 1, ta biết dict accuracy (17.45%) là bottleneck chính. DictionaryMatcher hiện tại match toàn bộ 939 row của DICT_HQ_2026 + 174 row của dictv3 cho mọi input, không phân biệt HS code. Kết quả: keyword "đèn" match với cả HS 8539 (bóng đèn) lẫn HS 9405 (đèn chiếu sáng), gây false positives.

Giải pháp: lọc dict rows theo HS prefix (4 chữ số đầu của Mã HS) trước khi Aho-Corasick match. Nếu input có Mã HS `85391010`, chỉ match trong các dict rows có Mã HS bắt đầu bằng `8539`.

## Goals / Non-Goals

**Goals:**
- DictionaryMatcher.predict(text, hs_code=None) — lọc không gian tìm kiếm theo HS prefix
- data_cleaner.py process_async() truyền Mã HS vào matcher
- HS pre-classification: tra HSTaxonomy DB → auto-fill Dòng SP, Loại nếu đủ tự tin
- Fallback chain: HS DB → Dict (HS-filtered) → AI → "Cần kiểm tra"
- Backward compatible: hs_code=None → match toàn bộ dict (giữ nguyên behavior cũ)

**Non-Goals:**
- Không thay đổi Aho-Corasick automaton (vẫn dùng 1 automaton toàn cục)
- Không train lại model
- Không thay đổi API endpoints
- Không thay đổi dict file format

## Decisions

### 1. HS filtering: prefix-based index filter (không rebuild automaton)
- Xây dựng `hs_prefix_to_idx: Dict[str, Set[int]]` trong `_load_dict()`
- Trong `predict(text, hs_code=None)`: nếu có hs_code → chỉ tính score cho mapping_idx trong set tương ứng
- **Rationale**: Đơn giản, không cần rebuild automaton. Filter xảy ra ở bước tính score, không phải bước match
- **Alternative**: Build automaton riêng cho mỗi HS prefix → quá phức tạp, tốn memory

### 2. HS pre-classification: sync DB lookup, threshold = Số lượng SP > 100
- Trong `initial_mapping()`: lookup HSTaxonomy cho mỗi Mã HS (longest-prefix)
- Nếu có exact match trong DB VÀ dict row tương ứng có `Số lượng SP > 100` → pre-fill
- Chỉ pre-fill Dòng SP + Loại (2 cấp cao nhất, độ chính xác cao nhất)
- Lớp 1 và Lớp 2 vẫn cần dict/AI xử lý (fine-grained, DB không có đủ thông tin)
- **Rationale**: Dòng SP và Loại từ HS taxonomy có độ tin cậy cao. Không nên pre-fill Lớp 1/Lớp 2 vì DB chỉ có industry_name (không ánh xạ 1-1 với Lớp 1 hiện tại)

### 3. Fallback chain mới
```
Input → [HS Taxonomy DB] → Dòng SP + Loại từ HS (nếu Số lượng SP > 100)
         ↓ 
       → [DICT_HQ_2026 + HS filter] → score >= DICT_THRESHOLD? → DONE
         ↓ không
       → [PhoBERT AI] → conf >= 0.85? → DONE
         ↓ không
       → "Cần kiểm tra"
```
- HS DB lookup được thêm vào đầu chain (trước dict)
- Dict match giờ đã được lọc theo HS → giảm false positives đáng kể
- AI vẫn là fallback cuối cùng

### 4. Truyền HS code qua pipeline
- `process_chunk()` nhận thêm cột `Mã HS` trong chunk DataFrame
- `matcher.predict(text, hs_code=hs_code)` — HS code có thể là string rỗng hoặc None → fallback toàn bộ dict
- Worker function vẫn dùng ProcessPoolExecutor → data flow không thay đổi

## Risks / Trade-offs

- [Risk] HS code trong input có thể sai hoặc thiếu → Mitigation: nếu hs_code rỗng/None → fallback toàn bộ dict (behavior cũ)
- [Risk] DB lookup trong initial_mapping() có thể chậm với file lớn → Mitigation: batch lookup 1 lần, cache kết quả theo prefix
- [Risk] `Số lượng SP` trong DICT_HQ_2026 có thể không đáng tin cậy → Mitigation: chỉ dùng threshold cao (>100) để pre-fill
