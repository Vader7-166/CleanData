## Why

Phase 1 phân tích lỗi cho thấy dict hiện tại (DICT_HQ_2026 + dictv3) gần như vô dụng: coverage 69% nhưng accuracy chỉ 17.45%, 0 dòng dict tự đúng 1 mình. Nguyên nhân chính: Aho-Corasick match trên toàn bộ dict không phân biệt HS code, dẫn đến false positives hàng loạt. Cần tích hợp HS code filtering để dict match chính xác theo ngữ cảnh sản phẩm.

## What Changes

- **dictionary_matcher.py**: Thêm `predict(text, hs_code=None)` — lọc dict rows theo HS prefix trước khi match
- **data_cleaner.py**: Truyền Mã HS vào dict matcher, thêm HS-based pre-classification từ HSTaxonomy DB
- **worker.py**: Cập nhật `process_chunk()` để truyền HS code qua pipeline
- **Fallback chain mới**: HS DB lookup → Dict (HS-filtered) → AI → "Cần kiểm tra"

## Capabilities

### New Capabilities

- `hs-code-dict-filtering`: DictionaryMatcher hỗ trợ lọc theo HS code prefix để giảm false positives
- `hs-pre-classification`: Tra cứu HSTaxonomy DB để pre-fill Dòng SP, Loại từ Mã HS trước khi chạy dict/AI

### Modified Capabilities

<!-- Không có capability nào bị thay đổi ở spec level -->

## Impact

- **dictionary_matcher.py**: Thay đổi signature `predict()` — backward compatible (hs_code=None mặc định)
- **data_cleaner.py**: Thay đổi `process_async()` — thêm HS lookup step, pass HS code vào dict
- **worker.py**: Thay đổi `process_chunk()` — nhận thêm Mã HS, truyền vào matcher
- **API**: Không thay đổi endpoint nào
- **Performance**: HS lookup là sync DB query, có thể cache; dict HS-filtering giảm không gian tìm kiếm → nhanh hơn
