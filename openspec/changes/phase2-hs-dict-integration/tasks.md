## 1. DictionaryMatcher: HS Code Filtering

- [x] 1.1 Thêm `hs_prefix_to_idx: Dict[str, Set[int]]` vào `_load_dict()` — map 4-digit HS prefix → list mapping indices
- [x] 1.2 Fix bug `_load_dict()` chỉ load file dict cuối cùng → giờ load tất cả dict files
- [x] 1.3 Sửa `predict(self, text)` → `predict(self, text, hs_code=None)` — nếu hs_code được cung cấp, lọc scores_by_mapping theo prefix
- [x] 1.4 Thêm `get_best_match_detail(text, hs_code=None)` để truy xuất chi tiết mapping
- [x] 1.5 Test: `matcher.predict(text, hs_code="85391010")` chỉ match trong dict rows có Mã HS 8539xxxx, "94055090" trả về None

## 2. Worker: Pass HS Code

- [x] 2.1 Sửa `process_chunk()` — nhận thêm cột `Mã HS` từ chunk_df
- [x] 2.2 Truyền `hs_code` vào `matcher.predict(text, hs_code=hs_code)` qua `input_for_ai.combine(hs_series, ...)`
- [x] 2.3 Fallback: nếu Mã HS rỗng/None → gọi `matcher.predict(text)` (không filter)

## 3. DataCleaner: Pipeline Update

- [x] 3.1 Sửa `process_async()` — include `'Mã HS'` in chunk: `chunk = df_clean[['Tên hàng raw', 'Mã HS']]`
- [x] ~~3.2 HS pre-classification~~ — BỎ do tên HS quốc tế không map được sang tên công ty

## 4. dict_generator: Cải thiện keyword extraction

- [x] 4.1 Sửa `extract_keywords_ai()`: `any()` → `all()` token validation — loại bỏ n-gram có từ không hợp lệ
- [x] 4.2 Tách single/multi words: top 8 từ đơn + top 4 cụm từ — keyword có ý nghĩa hơn
- [x] 4.3 Mở rộng `VI_STOPWORDS` và `LABEL_STOPWORDS`: thêm brand names (honda, yamaha, bawang...), từ vô nghĩa (gắn, máy, bao, gồm...)
- [x] 4.4 Test: `đèn led bulb, led bulb tròn, led tròn` thay vì n-gram rác

## 5. Integration Verification

- [x] 5.1 HS filtering hoạt động: 8539 prefix → 219 rows, 9405 prefix → 720 rows, tổng 1112 rows
- [x] 5.2 Dict matcher backward compatible: hs_code=None → match toàn bộ dict
- [x] 5.3 Keyword extraction cải thiện rõ rệt so với trước

## 6. Update task.md

- [x] 6.1 Đánh dấu Phase 2 hoàn thành trong root `task.md`
- [x] 6.2 Ghi nhận kết quả + files đã sửa
