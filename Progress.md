# Hiện tại
Đã đáp ứng quy trình xử lý ở mức ok
Đã chia nhỏ các cụm dữ liệu để xử lý -> tối ưu tốc độ
Đã có UI ở mức cơ bản, tuy nhiên thiết kế vẫn còn rất đơn sơ

# Cần làm
[x]Cho phép upload dict và lưu trữ các bộ từ điển đó để sử dụng
[ ]Nghiên cứu tối ưu việc lưu trữ model việc cập nhật model không cần compose lại trên docker giúp tiết kiệm thời gian.
[x]Tạo tính năng tạo dict dựa trên code base của Thế. Cho phép người dùng tạo bộ dict dựa trên file raw.

# Chi tiết tính năng dashboard
[x]Cho phép xem preview các file đã upload
[x]Cho phép tải các file đã upload
[x]Cho phép xem thông tin chi tiết(số dòng, số cột, sử dụng bộ từ điển nào, số file đã xử lý, số file chưa xử lý, số file lỗi, thời gian xử lý)
[ ]Thêm websocket để đưa ra số lượng dòng đang xử lý theo thời gian thực.
[ ]Sửa lỗi xem chi tiết file bị tràn màn hình, font chữ trắng cùng với nền trắng, không tắt được.
[ ]Cải thiện tính năng preview(hiển thị nhiều hơn 100 dòng, cho phép xem tất cả các cột, sử dụng preview chuẩn excel)
[ ]Tiếp tục chỉnh sửa thiết kế lại front-end(cố gắng thêm cho nó 1 file thiết kế vd như figma hoặc canva)
[x]Gỡ bỏ việc hover khiến widget nảy lên(THIẾT KẾ RẤT NGU).
[ ]Sử dụng công nghệ để tránh việc f5 lại trang mất hết session xử lý.

# Chi tiết tính năng upload dict
[x]Cho phép upload dict và lưu trữ các bộ từ điển đó để sử dụng
[x]Cho phép xem danh sách các bộ từ điển đã upload
[x]Cho phép chọn bộ từ điển để sử dụng(Bộ từ điển được sắp xếp tùy theo từng loại sản phẩm, việc chọn trước sẽ giúp tốc độ xử lý nhanh hơn)
[x]Thống kê các file đã sử dụng