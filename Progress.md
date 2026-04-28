# Hiện tại
Đã đáp ứng quy trình xử lý ở mức ok
Đã chia nhỏ các cụm dữ liệu để xử lý -> tối ưu tốc độ

# Cần làm
- Cho phép upload dict và lưu trữ các bộ từ điển đó để sử dụng
- Làm trang dashboard
- Nghiên cứu tối ưu việc lưu trữ model việc cập nhật model không cần compose lại trên docker giúp tiết kiệm thời gian.
- Tạo tính năng tạo dict dựa trên code base của Thế. Cho phép người dùng tạo bộ dict dựa trên file raw.

# Chi tiết tính năng dashboard
- Hiển thị danh sách các file đã upload
- Cho phép xem preview các file đã upload
- Cho phép tải các file đã upload
- Cho phép xem thông tin chi tiết(số dòng, số cột, sử dụng bộ từ điển nào, số file đã xử lý, số file chưa xử lý, số file lỗi, thời gian xử lý)
- Giới hạn số file lưu trữ mỗi người người để đảm bảo phần cứng(10 file gần nhất)
- Cải thiện tính năng preview(hiển thị nhiều hơn 100 dòng, cho phép xem tất cả các cột, sử dụng preview chuẩn excel)

# Chi tiết tính năng upload dict
- Cho phép upload dict và lưu trữ các bộ từ điển đó để sử dụng
- Cho phép xem danh sách các bộ từ điển đã upload
- Cho phép chọn bộ từ điển để sử dụng(Bộ từ điển được sắp xếp tùy theo từng loại sản phẩm, việc chọn trước sẽ giúp tốc độ xử lý nhanh hơn)
- Thống kê các file đã sử dụng

