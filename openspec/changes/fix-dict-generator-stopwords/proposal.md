## Why

Hệ thống sinh từ điển hiện tại (`dict_generator.py`) đang bị lọt các "từ khóa rác" (như `"mặt trời"`, `"hiệu"`, tên thương hiệu) vào danh sách keyword của các nhóm sản phẩm không liên quan (ví dụ: `"đèn côn trùng"`). Nguyên nhân là do các từ khóa này xuất hiện đủ nhiều trong nhóm để vượt qua ngưỡng Purity `5%` hiện tại, dẫn đến việc `DictionaryMatcher` phía sau nhận diện nhầm trầm trọng các sản phẩm đèn năng lượng mặt trời thành đèn côn trùng. Việc thay đổi ngưỡng Purity đơn thuần đã chứng minh là không hiệu quả (khiến mất keyword đặc trưng nếu tăng, và lọt keyword rác nếu giảm). Cần phải có một cơ chế lọc từ khóa ngữ cảnh (Stopwords) ngay tại thời điểm tạo từ điển.

## What Changes

- **Thêm danh sách Global Stopwords**: Loại bỏ các từ quá chung chung hoặc tên thương hiệu (`"hiệu"`, `"công suất"`, `"jindian"`, `"philips"`, `"gp"`, v.v.) khỏi mọi danh sách keyword.
- **Thêm Contextual Keywords**: Một số từ đặc thù như `"mặt trời"`, `"solar"`, `"nlmt"` sẽ bị đưa vào danh sách đen (blacklist) CHUNG, và chỉ được phép trở thành keyword nếu `Lớp 1` hoặc `Lớp 2` của sản phẩm có chứa các từ khóa liên quan đến năng lượng mặt trời.
- **Tính lại điểm hoặc phạt (Penalty)**: Những keyword nào chứa các từ rác sẽ bị loại bỏ hoàn toàn trước khi lưu vào file `TONG_THE.csv`.

## Capabilities

### New Capabilities
- `contextual-keyword-extraction`: Khả năng lọc và chặn các từ khóa rác dựa trên danh sách stopwords và ngữ cảnh của danh mục sản phẩm (Category Context) khi sinh từ điển.

### Modified Capabilities
- `dictionary-generation`: Sửa đổi logic sinh từ điển hiện tại để áp dụng Contextual Stopwords trước khi đưa vào đánh giá Purity TF-IDF.

## Impact

- **`backend/core/dict_generator.py`**: Chỉnh sửa hàm `extract_keywords_ai` để thêm danh sách chặn và logic lọc.
- **`TONG_THE.csv` (Output)**: Từ điển sinh ra sẽ sạch hơn, không còn chứa các chuỗi như `"mặt trời hiệu"` ở các dòng sản phẩm sai lệch.
- Không ảnh hưởng đến luồng chạy chính của AI hay Matching phía sau, vì thay đổi này chỉ diễn ra ở khâu tạo từ điển.
