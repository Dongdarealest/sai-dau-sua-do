# Đề xuất thiết kế lại giao diện Kho bài học

Ngày: 19/11/2026. Trạng thái: chỉ là bản xem trước để Đông duyệt, chưa sửa web thật, chưa deploy.

## 1. Giao diện hiện tại yếu ở đâu

Đã chụp màn hình thật trên điện thoại 390px, xem trong `hien-tai/`:

• **Đầu trang chiếm gần hết màn hình đầu tiên.** Trang chủ: logo, tên trang, câu giới thiệu, 3 viên thống kê, 5 nút điều hướng chiếm khoảng 60% màn hình đầu tiên. Nút "Học bài này" nằm dưới nếp gấp, người mới vào phải cuộn mới thấy chỗ học. Trang bài cũng vậy: đầu trang lặp lại chiếm khoảng 55% màn hình, nội dung bài bắt đầu rất muộn.
• **Người mới vào chưa thấy gì để học.** Màn hình đầu tiên toàn chữ giới thiệu và nút bấm, không có ví dụ bài học cụ thể, không có ảnh, không có lý do để ở lại.
• **Số 0 đập vào mắt.** "Đã nhớ 0 trên 55 bài" hiện to và cam ngay đầu trang. Người mới chưa học gì đã thấy mình ở vạch 0.
• **Quá nhiều lựa chọn trước khi học.** 5 nút điều hướng cộng 2 tab Học và Tra cứu, tổng 7 lựa chọn trước khi thấy nội dung. Trong khi người mới chỉ cần 1 nút: học ngay.
• **Nút Xuất và Nhập tiến độ nằm giữa trang chủ.** Đây là tính năng quản trị, người mới không hiểu, người cũ ít dùng, nhưng nó chiếm chỗ ngay sau hộp Tiến độ.
• **Chữ đều nhau, thiếu điểm nhấn.** Mọi chữ 16px, tiêu đề chỉ 22 đến 23px, trang đọc như tài liệu chứ không như app học. Ảnh bài Facebook có sẵn nhưng trang chủ và thư viện gần như không dùng ảnh.
• **Trang Từ điển** (ảnh Đông chụp, xem `photo-63.jpg` trong thư viện ảnh): nghĩa toàn tiếng Anh, phiên âm dồn 3 cái một dòng, ví dụ không có dịch. Phần này agent khác đang làm lại riêng.

## 2. Tham khảo nhanh

• **Duolingo:** giữ người học bằng chuỗi ngày học và điểm XP, bài 3 đến 5 phút, nút chính luôn cố định ở đáy màn hình trong tầm ngón tay, thanh tiến độ luôn thấy ở đầu bài, làm sai vẫn được khen để dám làm tiếp. Bài học rút ra: giữ chân quan trọng hơn thu hút ban đầu, tiến độ phải nhìn thấy liên tục, bắt đầu phải nhẹ.
• **ELSA Speak:** bài ngắn 2 đến 5 phút, phản hồi ngay bằng màu (đúng xanh, gần đúng vàng, sai đỏ), lộ trình rõ từng bước, nói là trọng tâm. Bài học rút ra: phản hồi tức thì bằng màu giúp người học tự sửa ngay, bài ngắn thì mới học được trong lúc rảnh.
• Cả hai đều làm tốt điều trang hiện tại chưa có: **vào là học ngay trong 1 lần bấm, và thấy mình tiến bộ sau mỗi lần bấm.**

## 3. Ba hướng thiết kế

Mỗi hướng có trang chủ và 1 trang bài, kèm ảnh chụp màn hình điện thoại 390px, ảnh chụp dài cả trang và ảnh chụp máy tính. Số liệu mẫu trong mockup là dữ liệu giả lập để thấy giao diện khi đã có người học thật (chuỗi 3 ngày, đã nhớ 12 trên 55 bài), không phải số liệu thật.

### Hướng A: App học

File: `huong-a-app-hoc/trang-chu.html`, `huong-a-app-hoc/trang-bai.html`
Ảnh: `huong-a-app-hoc/shots/trang-chu-mobile.png`, `trang-chu-dai.png`, `trang-bai-mobile.png`, `trang-chu-desktop.png`

• Khác gì: đầu trang gọn còn 1 hàng (logo, tên, chuỗi ngày, điểm), thẻ Bài hôm nay màu navy hiện ngay câu sai và câu đúng kèm nút Học ngay to, 3 ô thống kê nhỏ, danh sách Học tiếp có trạng thái từng bài, thanh điều hướng dưới cố định 5 mục trong tầm ngón tay.
• Đẹp hơn vì: đúng dáng app trên điện thoại, khoảng trắng thoáng, nút chính luôn thấy, không còn 5 viên điều hướng chiếm chỗ.
• Hiệu quả hơn vì: người mới bấm 1 lần là vào bài, người cũ thấy ngay bài đang học dở và chuỗi ngày học, không phải tìm.
• Khó làm: vừa. Chỉ đổi vỏ ngoài, giữ nguyên toàn bộ nội dung bài, wizard 7 bước, ôn tập, tìm kiếm, Từ điển, Luyện nói.

### Hướng B: Tạp chí

File: `huong-b-tap-chi/trang-chu.html`, `huong-b-tap-chi/trang-bai.html`
Ảnh: `huong-b-tap-chi/shots/trang-chu-mobile.png`, `trang-chu-dai.png`, `trang-bai-mobile.png`, `trang-chu-desktop.png`

• Khác gì: chữ tiêu đề rất lớn 38px, câu slogan thành tiêu đề chính của trang, bài mới nhất hiện bằng ảnh bài Facebook vuông nguyên khung, danh sách bài dạng tạp chí có số thứ tự và ảnh nhỏ, khối mời vào Group ở cuối.
• Đẹp hơn vì: trông như tạp chí, ảnh thật làm trang sống ngay, chữ lớn tạo cảm xúc, tin tưởng hơn hẳn.
• Hiệu quả hơn vì: người mới đọc là hiểu Trang dạy cái gì, ảnh bài làm bằng chứng chất lượng, dễ chia sẻ.
• Yếu hơn: trang chủ không thấy chuỗi ngày học và tiến độ, người cũ quay lại ít lý do hơn Hướng A và C.
• Khó làm: vừa. Cần dùng ảnh bài vuông nguyên khung, không cắt, vì cắt là mất chữ trong ảnh.

### Hướng C: Lộ trình trò chơi

File: `huong-c-lo-trinh-tro-choi/trang-chu.html`, `huong-c-lo-trinh-tro-choi/trang-bai.html`
Ảnh: `huong-c-lo-trinh-tro-choi/shots/trang-chu-mobile.png`, `trang-chu-dai.png`, `trang-bai-mobile.png`, `trang-chu-desktop.png`

• Khác gì: đầu trang hiện Cấp 3 và thanh XP, thẻ Nhiệm vụ hôm nay có 3 việc kèm điểm thưởng, lộ trình là con đường uốn lượn với các nút bài: xong rồi có tick, đang học có nút Bắt đầu, chưa mở có ổ khóa. Trang bài hiện điểm XP khi trả lời đúng.
• Đẹp hơn vì: có cảm giác chơi game, mỗi ngày có việc rõ ràng, tiến độ nhìn thấy bằng mắt.
• Hiệu quả hơn vì: chuỗi ngày học và nhiệm vụ ngày tạo lý do quay lại, sợ mất chuỗi giữ người học ở lại lâu nhất trong 3 hướng.
• Khó làm: lớn nhất. Cần thêm hệ XP và cấp độ, tức là thêm dữ liệu mới vào bộ nhớ trình duyệt và logic mở khóa bài, phải tính kỹ để không làm hỏng tiến độ cũ.

## 4. Bảng so sánh

|  | Hướng A: App học | Hướng B: Tạp chí | Hướng C: Lộ trình trò chơi |
|---|---|---|---|
| Người mới vào thấy gì đầu tiên | Bài hôm nay kèm câu sai và câu đúng, nút Học ngay | Tiêu đề lớn và ảnh bài mới nhất | Cấp độ, nhiệm vụ hôm nay, nút bài đang học |
| Bấm mấy lần thì học được | 1 lần | 1 lần | 1 lần |
| Thấy tiến độ của mình không | Có, 3 ô thống kê và chuỗi ngày | Không rõ trên trang chủ | Có, rõ nhất: XP, cấp, nhiệm vụ, con đường |
| Lý do quay lại ngày mai | Chuỗi ngày học | Bài mới hay | Chuỗi, nhiệm vụ, sợ mất cấp |
| Đẹp và tin tưởng | Khá | Đẹp nhất | Khá, vui nhất |
| Khó làm | Vừa | Vừa | Lớn nhất |
| Rủi ro phá tính năng cũ | Thấp | Thấp | Vừa, vì thêm XP và khóa bài |

## 5. Hướng khuyên dùng

**Làm Hướng A trước.** Vì A sửa đúng điểm yếu lớn nhất (đầu trang nặng, nút học nằm dưới nếp gấp, không thấy tiến độ) với rủi ro thấp nhất, mà vẫn giữ nguyên mọi tính năng. Sau khi A lên và có số liệu, lấy thêm 2 thứ:

• **Giai đoạn 2, lấy từ Hướng C:** thẻ Nhiệm vụ hôm nay và con đường lộ trình. Điểm XP tính từ dữ liệu đã có (mỗi bài đã nhớ bằng 20 XP, mỗi câu luyện đúng bằng 10 XP) nên không cần dữ liệu mới nhiều.
• **Giai đoạn 3, lấy từ Hướng B:** chữ tiêu đề lớn hơn và thẻ Bài mới nhất dùng ảnh vuông nguyên khung cho trang chủ, vì ảnh bài là tài sản đẹp nhất của Trang mà hiện tại chưa được dùng.

Không nên làm C ngay từ đầu vì XP và khóa bài là tính năng mới, cần thử kỹ, mà A đã đủ để Đông thấy web khác hẳn.

## 6. Thứ tự làm sau khi Đông duyệt

1. Đông chọn hướng (A, B, C, hoặc A rồi lấy thêm C và B theo giai đoạn như trên).
2. Đợi agent làm lại Từ điển deploy xong và agent nghiên cứu cây thư mục báo cáo xong, để không đụng deploy lẫn nhau.
3. Sửa mẫu trang trong `generate_site.py` theo hướng đã chọn: đầu trang gọn, thanh điều hướng dưới, thẻ Bài hôm nay, 3 ô thống kê. Trang bài: đầu trang gọn, thanh tiến độ dày, giữ nguyên wizard 7 bước và nút Tiếp tục.
4. Chạy đủ test cũ (unittest, kiểm tra JavaScript, không lặp câu, không có chữ nhỏ hơn 16px), chụp màn hình điện thoại 390px của trang chủ và 2 trang bài, Đông xem ảnh rồi mới deploy.
5. Deploy, kiểm tra live bằng curl và mở thật trên điện thoại, ghi nhật ký.

## 7. Giữ nguyên gì, đổi gì, rủi ro gì

Giữ nguyên:

• Mọi đường link đã chia sẻ trên Facebook (`/loi-009/`, `/tong-hop-001/` và các link khác) không đổi, vì chỉ đổi mẫu hiển thị, không đổi địa chỉ.
• Tệp `lessons.json` và toàn bộ nội dung bài không đổi.
• Dữ liệu tiến độ trong trình duyệt (`sdsc-progress-v1`, `sdsc-theme` và các key cũ) không đổi, người học cũ không mất chuỗi ngày học và bài đã nhớ.
• Wizard 7 bước, ôn tập theo lịch riêng, tìm kiếm không dấu, Từ điển, Luyện nói, chia sẻ kết quả: giữ nguyên, chỉ đổi vỏ.

Đổi:

• Mẫu HTML và CSS trong `generate_site.py`: đầu trang, điều hướng, thẻ bài hôm nay, ô thống kê, thanh tiến độ trang bài.
• Ảnh bài hiện nguyên khung vuông 1/1 ở thẻ nổi bật, không cắt 16/10 vì cắt là mất chữ trong ảnh.

Rủi ro:

• Người dùng cũ quen vị trí nút cũ, bỡ ngỡ vài ngày. Giảm rủi ro bằng cách giữ nguyên tên các mục và thứ tự: Học, Lộ trình, Từ điển, Luyện nói.
• Thanh điều hướng dưới cố định có thể che nút ở cuối trang nếu quên chừa khoảng đệm. Đã tính trong mockup (chừa 84px ở cuối trang) và sẽ kiểm tra bằng ảnh chụp thật trước khi deploy.
• Hướng C nếu làm sau: khóa bài có thể làm người học mới thấy nhiều ổ khóa và nản. Chỉ khóa bài trong cùng 1 lộ trình, còn Thư viện chủ đề vẫn mở hết để ai cũng xem được mọi bài.
