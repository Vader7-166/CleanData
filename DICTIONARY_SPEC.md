# Quy định về tệp Từ điển (Dictionary) cho hệ thống CleanData

Tài liệu này định nghĩa các yêu cầu kỹ thuật đối với các tệp từ điển được sử dụng trong luồng phân loại dữ liệu tự động (Pass 1). Việc tuân thủ quy định này đảm bảo độ chính xác tối đa và hiệu suất tối ưu khi sử dụng thuật toán Aho-Corasick.

## 1. Định dạng tệp và Mã hóa (Encoding)

- **Định dạng**: Giá trị phân tách bằng dấu phẩy (CSV).
- **Mã hóa (Encoding)**: `utf-8-sig` (UTF-8 có BOM).
  - *Lý do*: Mã hóa này đảm bảo các ký tự tiếng Việt hiển thị chính xác và có thể chỉnh sửa trực tiếp bằng Microsoft Excel mà không bị lỗi font.

## 2. Các cột bắt buộc

Tệp từ điển **BẮT BUỘC** phải có các cột sau:

| Cột | Mô tả | Bắt buộc |
| :--- | :--- | :--- |
| `Keyword` | Danh sách các từ khóa/cụm từ kích hoạt (phân cách bằng dấu phẩy). | Có |
| `Dòng SP` | Phân loại dòng sản phẩm. | Có |
| `Loại` | Loại hàng (ví dụ: NC - Nguyên chiếc, LK - Linh kiện). | Có |
| `Lớp 1` | Phân loại Lớp 1. | Có |
| `Lớp 2` | Phân loại Lớp 2. | Có |
| `Mã HS` | Mã HS đi kèm với phân loại này. | Có |

*Lưu ý: Nếu bất kỳ giá trị phân loại nào chưa xác định, hãy sử dụng giá trị mặc định là **`không_có`** thay vì để trống.*

## 3. Quy tắc chuẩn hóa Từ khóa

Hệ thống sẽ làm sạch tên hàng trước khi khớp. Từ khóa trong từ điển cũng cần được chuẩn hóa trước:
- **Chữ thường**: Tất cả từ khóa nên được viết thường.
- **Ký tự đặc biệt**: Loại bỏ các dấu câu (ví dụ: `.`, `/`, `-`, `(`) và thay thế bằng khoảng trắng.
- **Khoảng trắng**: Chỉ sử dụng một khoảng trắng giữa các từ. Xóa khoảng trắng thừa ở đầu và cuối.

### 3.2 Độ cụ thể của từ khóa
- Ưu tiên các cụm từ cụ thể (ví dụ: `đèn led âm trần`) hơn là các từ chung chung (ví dụ: `đèn`).
- Các từ khóa không nên bị ngắt giữa chừng (ví dụ: `năng lượng mặt trời` có thể ok nhưng `năng lượng mặt` không được).
- Từ khóa quá chung chung có thể dẫn đến nhận diện sai (false positives).

## 4. Cơ chế Chấm điểm (Scoring)

Hệ thống sử dụng hệ thống điểm trọng số để chọn kết quả khớp tốt nhất khi có nhiều hàng từ điển cùng khớp với một tên hàng.

- **Từ khóa Giá trị cao (High Value)**: Các từ khóa như `năng lượng mặt trời` hoặc `nlmt` được cộng điểm rất cao (20 điểm) và thường dẫn đến việc tự động duyệt ngay lập tức.
- **Từ khóa Thông thường**: Điểm dựa trên số lượng từ trong cụm từ (ví dụ: `đèn led panel` = 3 điểm).
- **Từ khóa Rác (Junk)**: Các từ như `mới 100%` hoặc `chính hãng` sẽ bị hệ thống "nuốt" để tránh gây nhiễu, nhưng đóng góp **0 điểm**.

## 5. Logic "Nuốt từ" (Consumption Logic)

Luồng xử lý sử dụng logic "nuốt từ":
1. Các cụm từ dài nhất và khớp tốt nhất sẽ được xác định trước.
2. Khi một phần của tên hàng đã được khớp với một từ khóa, phần đó sẽ bị "nuốt" và không thể tham gia vào các lần khớp từ khóa khác cho cùng một dòng kết quả.
3. Điều này ngăn chặn việc các từ khóa ngắn (ví dụ: `đèn`) khớp chồng lấn bên trong một cụm từ dài đã khớp (ví dụ: `đèn led`).
