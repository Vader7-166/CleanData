## Why

Dictionary matching hiện tại có accuracy chỉ **17.45%** (sai 83% trường hợp) và "Dict only correct = 0" — nghĩa là dictionary không bao giờ đúng mà AI sai. Nguyên nhân gốc rễ: `DictionaryMatcher` sử dụng Aho-Corasick matching hoàn toàn dựa trên substring, **không hề sử dụng Mã HS** khi đối chiếu. Keyword `"mặt trời hiệu"` từ entry "đèn côn trùng" (HS 94054190) match bất kỳ sản phẩm nào chứa cụm này, bao gồm cả đèn solar (HS 94054990). Kết quả: precision "đèn côn trùng" chỉ 33.3%, hàng loạt sản phẩm bị phân loại sai. Cần sửa ngay vì dictionary đang gây hại nhiều hơn lợi cho pipeline.

## What Changes

- **Thêm HS-aware filtering vào `DictionaryMatcher`**: Khi match keyword, kiểm tra Mã HS của dòng đang xử lý có thuộc cùng nhóm HS (4-digit prefix) với dictionary entry hay không. Nếu không khớp → giảm 80% score hoặc bỏ qua match.
- **Lưu trữ Mã HS trong Aho-Corasick payload**: Mỗi keyword entry trong automaton sẽ mang theo thông tin Mã HS gốc để so sánh tại thời điểm matching.
- **Thêm fallback logic**: Nếu dòng đang xử lý không có Mã HS (hoặc HS = NaN), bỏ qua HS filtering và match bình thường như hiện tại.
- **Loại bỏ keyword rác khi load dictionary**: Thêm validation trong `_load_dict()` để skip keyword quá ngắn (< 3 ký tự) hoặc keyword chỉ chứa toàn stopword.

## Capabilities

### New Capabilities
- `hs-aware-matching`: Khả năng DictionaryMatcher sử dụng Mã HS làm context khi matching, đảm bảo keyword chỉ match các sản phẩm thuộc cùng nhóm HS code.

### Modified Capabilities
- `dictionary-filtering`: Thay đổi requirement matching — từ pure substring matching sang context-aware matching có xét đến Mã HS.

## Impact

- **`backend/core/dictionary_matcher.py`**: Sửa đổi chính — thêm HS filtering logic vào `_load_dict()` và `predict()`.
- **`backend/core/data_processor.py` hoặc `main.py`**: Cần đảm bảo Mã HS được truyền vào hàm `predict()` khi gọi dictionary matching.
- **Không ảnh hưởng**: Dictionary generation (`dict_generator.py`), Frontend UI, Database schema.
- **Backward compatible**: Nếu Mã HS không có trong dữ liệu đầu vào, hệ thống fallback về matching cũ.
