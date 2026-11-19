# Quyết định duyệt thiết kế web mới

Ngày duyệt: 19/11/2026. Người duyệt: nhiệm vụ rà lại và tự duyệt theo lệnh của Đông: "Cái nào chưa hợp lí thì phải làm cho hợp lí rồi tự duyệt nhé".

## Quyết định mới nhất của Đông (15:03 và 15:04 ngày 19/11)

Đông xem ảnh 3 hướng, khen giao diện đẹp và thích nhất các nút ở chân trang (thanh điều hướng dưới cố định). Nhưng ông nói bản cập nhật không có gì mới cả, tức là chỉ đổi vỏ thì chưa đủ. Sau đó ông chốt thêm: các tính năng mới cũng hay, phần đầu trang chưa ổn thì sửa phần đó, còn lại cập nhật mới hết, không giữ cái cũ.

Vì vậy hướng được duyệt phải là: sửa đầu trang cho gọn, giữ các nút ở chân trang, kèm các tính năng mới cho người học (Nhiệm vụ hôm nay, điểm XP, con đường lộ trình), và thay toàn bộ vỏ cũ bằng vỏ mới trên trang chủ và trang bài, không giữ lại vỏ cũ. Chỉ giữ nguyên nội dung và dữ liệu, còn giao diện thì đổi hết sang mới.

## Cách kiểm chứng

Chromium headless trên máy này không chụp được (Chrome của hệ thống báo thiếu Hatch WebGL domain policy; Chromium của Playwright treo khi khởi động). Ảnh v2 được render bằng WeasyPrint 70 và pdftoppm, cắt đúng khung nhìn 390x844 và 1280x800. WeasyPrint không nạp được font Be Vietnam Pro woff2 nên ảnh v2 dùng font hệ thống, chỉ kiểm được bố cục (tràn chữ, ngắt dòng, thứ tự khối, kích cỡ nút), không kiểm được đúng font cuối. Lưu ý: nút "Nghe phát âm" trong ảnh WeasyPrint hiện rộng hết thẻ, nhưng đó là khác biệt của WeasyPrint, trong trình duyệt thật nút là inline-flex như ảnh v1 đã chụp bằng Chrome. Mọi điểm sửa đều đã xem bằng mắt trên ảnh v2.

Ảnh v1 (trước sửa): `huong-a-app-hoc/shots/`, `huong-b-tap-chi/shots/`, `huong-c-lo-trinh-tro-choi/shots/`.
Ảnh v2 (sau sửa): `huong-a-app-hoc/shots/v2/`, `huong-b-tap-chi/shots/v2/`, `huong-c-lo-trinh-tro-choi/shots/v2/`.
Ảnh v3 (sau khi thêm tính năng mới và gọn đầu trang): `huong-a-app-hoc/shots/v2/trang-chu-mobile-viewport.png`, `huong-a-app-hoc/shots/v2/a3-home-paged-1.png` (trang 1, thấy nút chân trang), `huong-a-app-hoc/shots/v2/a3-home-paged-2.png` (trang 2, thấy con đường lộ trình), `huong-a-app-hoc/shots/v2/trang-bai-mobile-band700.png` (gợi ý XP ở trang bài).

## Đầu trang mới gọn như thế nào

Web hiện tại có đầu trang chiếm khoảng 60% màn hình đầu tiên, nút Học nằm dưới nếp gấp. Đầu trang mới ở hướng A đã gọn lại như sau, đo thật trên ảnh render 390x844:

1. Thanh trên cao 56px, chỉ có logo, tên Trang, slogan một dòng và pill chuỗi ngày.
2. Thẻ Bài hôm nay kết thúc ở 349px, tức khoảng 41% màn hình đầu tiên, thay cho khoảng 60% của web cũ.
3. Nút Học ngay nằm ở khoảng 280 đến 325px, thấy ngay không cần cuộn.
4. Trong màn hình đầu tiên còn thấy được cả 3 ô tiến độ và đầu hộp Nhiệm vụ hôm nay, người học thấy ngay việc cần làm hôm nay.

Để gọn được như vậy, thẻ Bài hôm nay đã rút đệm từ 22px xuống 16px, tiêu đề từ 26px xuống 24px, lề giữa các dòng rút lại, chữ câu sai và câu đúng từ 17px xuống 16px. Nút Học ngay giữ nguyên cao 52px để dễ bấm, không rút nút để đổi lấy gọn.

## Tính năng mới: Nhiệm vụ hôm nay kèm XP và con đường lộ trình

Đây là tính năng mới thật sự, không chỉ đổi bố cục, lấy từ hướng C và đưa vào hướng A ngay từ lần dựng đầu tiên.

### Gồm những gì

1. Hộp Nhiệm vụ hôm nay trên trang chủ, gồm 3 nhiệm vụ mỗi ngày: học 1 bài mới (20 XP), ôn 2 bài đến hạn (10 XP), luyện nói 1 câu (20 XP). Mỗi nhiệm vụ có trạng thái riêng: đã xong (dấu tick xanh), đang làm dở (1/2, nền vàng), chưa làm (vòng tròn trống). Xong cả 3 nhiệm vụ thì thưởng thêm 50 XP. Hộp hiện số nhiệm vụ đã xong, ví dụ Đã xong 1 trên 3.
2. Điểm XP và cấp: hộp nhiệm vụ hiện tổng XP (ví dụ 120 XP) và thanh tiến độ lên cấp (ví dụ Cấp 3, 120 trên 200 XP đến Cấp 4). Mỗi mốc 200 XP lên 1 cấp, chỉ là con số khích lệ, không khóa bài nào.
3. Con đường lộ trình trên trang chủ, xem trước 3 nút gần nhất nối bằng đường nét đứt: bài đã nhớ (dấu tick), bài đang học (chấm cam, ghi rõ Bước 1 trên 7), bài tiếp theo. Không có ổ khóa, mọi bài đều mở. Nút Xem lộ trình đầy đủ dẫn tới trang Lộ trình.
4. Gợi ý XP ở trang bài: dưới thẻ bài có dòng "Xong 7 bước được 20 XP, cộng vào Nhiệm vụ hôm nay.", để người học thấy làm xong bài thì được gì, vòng học khép kín với hộp nhiệm vụ.

### Vì sao đáng làm

1. Trả lời đúng ý Đông: chỉ đổi vỏ thì chưa đủ, phải có cái mới thật sự cho người học.
2. Cho người học lý do quay lại mỗi ngày: nhiệm vụ làm mới mỗi ngày, hôm nay chưa xong thì ngày mai có nhiệm vụ mới, chuỗi ngày và XP giữ chân tốt hơn chỉ xem bài.
3. Làm tiến độ thành thứ nhìn thấy được: XP tăng sau mỗi việc làm, cấp tăng sau mỗi mốc, người học thấy công sức của mình thành con số.
4. Con đường cho người học biết học xong bài này thì tới bài nào, không còn cảm giác học xong một bài rồi không biết đi đâu.
5. Dùng lại cơ chế đã có sẵn trên web (ôn tập, luyện nói, lộ trình), chỉ thêm lớp nhiệm vụ và XP lên trên, nên rủi ro thấp.

### Dùng dữ liệu đã có hay cần dữ liệu mới

Đã đối chiếu với dữ liệu tiến độ thật trên web, khóa `sdsc-progress-v1`, gồm `lessons` (tiến độ từng bài), `practice` (câu luyện nói), `streak` (chuỗi ngày), `review` (bài đến hạn ôn, có ngày hẹn ôn lại), `history` (lịch sử học), `settings` (mục tiêu mỗi ngày). Kết luận:

1. Nhiệm vụ học 1 bài mới: dùng dữ liệu đã có, xem trong `lessons` bài hôm nay đã xong hay chưa.
2. Nhiệm vụ ôn bài đến hạn: dùng dữ liệu đã có, đếm trong `review` có bao nhiêu bài đến hạn hôm nay và đã ôn được mấy bài.
3. Nhiệm vụ luyện nói 1 câu: dùng dữ liệu đã có, xem trong `practice` hôm nay đã luyện câu nào chưa.
4. Con đường lộ trình: dùng dữ liệu đã có, lấy thứ tự bài từ `lessons.json` và trạng thái từng bài từ `lessons`.
5. Điểm XP và cấp: cần dữ liệu mới, thêm 1 trường nhỏ vào dữ liệu tiến độ, ví dụ `xp` gồm tổng điểm và cấp. XP không tính ngược được từ dữ liệu cũ vì có khoản thưởng thêm 50 XP khi xong cả 3 nhiệm vụ. Khi dựng, khởi tạo XP từ dữ liệu đã có (20 XP cho mỗi bài đã nhớ) để người học cũ không bắt đầu từ 0.
6. Trạng thái nhiệm vụ từng ngày: cần dữ liệu mới, thêm 1 trường nhỏ gồm ngày và 3 dấu đã xong hay chưa, vì nhiệm vụ làm mới mỗi ngày. Trường này chỉ lưu ngày hôm nay, hôm sau ghi đè.

Như vậy tính năng mới chủ yếu dùng dữ liệu đã có, chỉ thêm 2 trường nhỏ mới, không cần tài khoản, không cần máy chủ, làm được bằng web tĩnh và localStorage như hiện tại.

## Hướng A: App học

### Điểm chưa hợp lí tìm được

1. Thanh trên thiếu slogan. Trang chủ chỉ có tên Trang, người mới vào không đọc được câu "Mỗi ngày sửa một lỗi nhỏ.".
2. Ô tiến độ giữa ghi "bài đến hạn ôn" bị ngắt dòng, đọc khó.
3. Số "120" trong thanh trên không có nhãn, người đọc không biết 120 là gì. Khi thêm nhãn "120 điểm" thì thanh trên chật, hai pill ngắt dòng và tên Trang bị che mất chữ "Đó" (thấy rõ trên ảnh v2 lần render đầu).
4. Nút "Nghe phát âm" cao 44px, hơi nhỏ so với ngón tay.
5. Ô "Đã nhớ 0 trên 55 bài" đập vào mắt, người mới thấy số 0 sẽ nản.
6. Pill "3 ngày" có thể ngắt dòng nếu font hiển thị rộng hơn.

### Đã sửa

1. Thêm slogan vào thanh trên, ngay dưới tên Trang.
2. Ô giữa đổi thành "bài cần ôn", một dòng.
3. Bỏ hẳn pill "120 điểm" khỏi thanh trên. Điểm số trong hướng A chưa có hệ thống đi kèm, bỏ đi thì thanh trên gọn và chỉ còn pill chuỗi ngày. Ảnh sau: `huong-a-app-hoc/shots/v2/trang-chu-mobile-viewport.png`, thanh trên hiện đủ tên, slogan một dòng, pill "3 ngày" một dòng.
4. Nút "Nghe phát âm" tăng lên 48px, trang bài A và trang bài B đều đã sửa.
5. Ô tiến độ đổi thành "Đã nhớ 12 trên 55 bài" (bản demo dùng số liệu có sẵn, không để số 0).
6. Thêm `white-space:nowrap` cho pill ở trang chủ và trang bài A.
7. Bản máy tính: nội dung giới hạn 720px, căn giữa. Ảnh sau: `huong-a-app-hoc/shots/v2/trang-chu-desktop-viewport.png`.

### Đánh giá theo 5 tiêu chí

1. Hiểu ngay và học được trong 1 lần bấm: tốt. Thẻ "Bài hôm nay" và nút "Học ngay" nằm ngay trong màn hình đầu tiên.
2. Tiến độ và chuỗi ngày: tốt. Ba ô số và danh sách "Học tiếp" có thanh tiến độ từng bài.
3. Bản sắc Trang: đúng. Nền navy, mint, cam, logo S kèm tick cam, slogan đầy đủ.
4. Chữ và nút: sạch sau sửa. Không tràn, không che, nút nhỏ nhất 48px.
5. Làm bằng web tĩnh và localStorage: được hoàn toàn, tính năng mới chỉ thêm 2 trường nhỏ mới.

## Hướng B: Tạp chí

### Điểm chưa hợp lí tìm được

1. Dòng mở đầu dài 2 dòng, đẩy tiêu đề chính "Mỗi ngày sửa một lỗi nhỏ." xuống thấp, màn hình đầu tiên bị dài.
2. Trang chủ không thấy tiến độ hay chuỗi ngày, người học không có lý do quay lại.
3. Thẻ "Bài mới nhất" ghi câu sai rồi ghi câu đúng, sau đó lại ghi câu đúng một lần nữa, trùng nhau.
4. Ảnh bài đặt giữa trang bài, lộ đáp án trước bước 1 của wizard.
5. Mục "Mới đăng" chưa xếp theo ngày.

### Đã sửa

1. Dòng mở đầu rút còn một dòng: "Một lỗi một ngày, đúng ngay từ câu đầu tiên. Mỗi bài chỉ 3 đến 5 phút."
2. Thêm dải tiến độ màu mint dưới phần số liệu: "Chuỗi 3 ngày. Đã nhớ 12 trên 55 bài. 2 bài đến hạn ôn. Xem lộ trình". Ảnh sau: `huong-b-tap-chi/shots/v2/trang-chu-mobile-viewport.png`.
3. Thẻ "Bài mới nhất" chỉ giữ câu sai và nút "Đọc bài", bỏ câu đúng trùng. Ảnh sau: `huong-b-tap-chi/shots/v2/trang-bai-mobile-viewport.png`.
4. Chuyển ảnh bài xuống cuối trang bài, sau nút "Tiếp tục" và thẻ "Bài tiếp theo", kèm chú thích "Ảnh bài đã đăng trên Facebook, lưu về để ôn lại.". Đã kiểm bằng mắt ở ảnh `huong-b-tap-chi/shots/v2/trang-bai-mobile-band844-2100.png`.
5. Mục "Mới đăng" xếp lại theo ngày mới nhất trước.
6. Nút "Tiếp tục" ở cuối trang bài đổi thành "Tiếp tục" kèm mũi tên, rõ hành động hơn.

### Đánh giá theo 5 tiêu chí

1. Hiểu ngay: khá, nhưng hành động học chính nằm dưới nếp gấp, người mới phải cuộn mới thấy nút học.
2. Tiến độ: đã có sau sửa, nhưng vẫn là dải phụ, không phải trọng tâm.
3. Bản sắc Trang: đúng.
4. Chữ và nút: sạch sau sửa.
5. Làm bằng web tĩnh và localStorage: được.

## Hướng C: Lộ trình trò chơi

### Điểm chưa hợp lí tìm được

1. Ổ khóa trên các nút bài sau gây cảm giác bị chặn, trong khi mọi bài đều mở và chỉ là thứ tự gợi ý.
2. Phần thưởng nhiệm vụ ghi chưa rõ, người đọc không biết làm xong 3 nhiệm vụ thì được gì.
3. Nút "Bắt đầu" cao 44px, hơi nhỏ.
4. Hộp "Nhớ" đặt trùng lời giải ở trang bài, đọc rối.
5. Pill XP "120 XP" có thể ngắt dòng.

### Đã sửa

1. Bỏ hẳn ổ khóa khỏi mọi nút trên con đường. Giữ thứ tự gợi ý bằng vị trí và trạng thái đã học, đang học. Ảnh sau: `huong-c-lo-trinh-tro-choi/shots/v2/trang-chu-mobile-viewport.png`, các nút chỉ còn dấu tick và số bài, không còn ổ khóa.
2. Dòng thưởng đổi thành "Thưởng thêm 50 XP khi xong cả 3 nhiệm vụ".
3. Nút "Bắt đầu" tăng lên 48px.
4. Hộp "Nhớ" đổi sang vị trí khác, không trùng lời giải. Ảnh sau: `huong-c-lo-trinh-tro-choi/shots/v2/trang-bai-mobile-viewport.png`.
5. Thêm `white-space:nowrap` cho pill XP ở trang bài C.
6. Bản máy tính: nội dung giới hạn 720px, căn giữa. Ảnh sau: `huong-c-lo-trinh-tro-choi/shots/v2/trang-chu-desktop-viewport.png`.

### Đánh giá theo 5 tiêu chí

1. Hiểu ngay: khá. Người dùng phải đọc hộp nhiệm vụ trước khi biết nên làm gì.
2. Tiến độ và chuỗi ngày: mạnh nhất trong 3 hướng. Cấp, XP, thanh tiến độ, nhiệm vụ hôm nay đều thấy ngay.
3. Bản sắc Trang: đúng.
4. Chữ và nút: sạch sau sửa.
5. Làm bằng web tĩnh và localStorage: làm được về mặt kỹ thuật, nhưng XP, cấp và nhiệm vụ là hệ thống mới, cần luật trước khi dựng: cách tính XP, mốc lên cấp, XP có mất khi nghỉ không, XP có đồng bộ với SRS hiện có không. Chưa có luật thì không nên dựng ngay.

## Hướng được duyệt: A, App học

### Lý do chọn A

1. A sửa đúng điểm yếu lớn nhất của web hiện tại: đầu trang chiếm khoảng 60% màn hình đầu tiên, nút Học nằm dưới nếp gấp. Ở A, thẻ "Bài hôm nay" kết thúc ở 349px trên màn hình 844px, nút "Học ngay" nằm ở khoảng 280 đến 325px, thấy ngay không cần cuộn.
2. Đường học rõ nhất cho người dùng điện thoại 18 đến 35 tuổi: một lần bấm là vào bài, danh sách "Học tiếp" cho biết học dở ở đâu.
3. A giữ các nút ở chân trang mà Đông thích nhất: 5 nút Học, Lộ trình, Từ điển, Luyện nói, Tôi, cố định dưới màn hình, mục đang xem tô cam, mỗi nút cao tối thiểu 56px.
4. A kèm tính năng mới thật sự (Nhiệm vụ hôm nay, XP, con đường lộ trình) mà vẫn dùng dữ liệu tiến độ đã có, chỉ thêm 2 trường nhỏ mới, làm được bằng web tĩnh và localStorage.
5. Giữ đúng bản sắc Trang: navy, mint, cam, logo S kèm tick cam, slogan đầy đủ.

### Lý do không chọn B

B đẹp cho việc khám phá và chia sẻ: tiêu đề lớn, ảnh vuông, bố cục tạp chí. Nhưng hành động học chính bị đẩy xuống dưới, người mới vào chưa biết bấm đâu để học ngay. B hợp làm giai đoạn nâng cấp trang bài hơn là vỏ chính.

### Lý do không chọn C

C giữ chân mạnh nhất về lâu dài: nhiệm vụ hôm nay, XP, cấp, con đường lộ trình. Nhưng XP và cấp cần thiết kế luật và cân bằng trước khi dựng, làm ngay sẽ kéo dài thời gian và dễ sai luật chơi. C hợp làm giai đoạn 2, sau khi A đã chạy ổn.

## Lộ trình lấy thêm theo giai đoạn

Giai đoạn 1, dựng A nguyên vẹn kèm tính năng mới ngay từ đầu: đầu trang gọn, thẻ "Bài hôm nay", 3 ô tiến độ, hộp "Nhiệm vụ hôm nay" kèm XP và cấp, danh sách "Học tiếp", con đường lộ trình xem trước 3 nút, các nút ở chân trang, trang bài có gợi ý XP. Không còn giai đoạn riêng cho tính năng mới vì Đông đã chốt cập nhật mới hết.

Giai đoạn 2, lấy từ B (làm sau, khi giai đoạn 1 đã chạy ổn): thẻ "Bài mới nhất" dạng tạp chí, tiêu đề lớn kèm ảnh vuông, cho trang chủ. Thêm dải tiến độ mint của B.

## Việc cần làm khi dựng lên web thật

Thay toàn bộ vỏ cũ bằng vỏ mới, chỉ giữ nguyên nội dung và dữ liệu:

1. Thay hết giao diện trong `generate_site.py`: thanh trên gọn, thẻ "Bài hôm nay", 3 ô tiến độ, hộp "Nhiệm vụ hôm nay" kèm XP và cấp, danh sách "Học tiếp", con đường lộ trình, các nút ở chân trang, trang bài mới. Không giữ lại bất cứ khối giao diện cũ nào trên trang chủ và trang bài.
2. Trang bài mới: thanh trên có nút quay lại, mã bài, pill chuỗi ngày; thanh bước; thẻ Sai và Đúng; nút "Nghe phát âm" cao 48px; thẻ "Vì sao"; dòng gợi ý XP; nút "Tiếp tục" cố định dưới màn hình.
3. Thêm tính năng mới: tính trạng thái 3 nhiệm vụ mỗi ngày từ dữ liệu tiến độ đã có; cộng XP khi học xong bài, ôn xong bài, luyện nói xong câu, cộng thêm 50 XP khi xong cả 3 nhiệm vụ; tính cấp theo mốc 200 XP; thêm 2 trường mới vào dữ liệu tiến độ (tổng XP và trạng thái nhiệm vụ hôm nay), khởi tạo XP từ số bài đã nhớ để người học cũ không bắt đầu từ 0.
4. Giữ nguyên nội dung và dữ liệu: mọi link (URL từng bài, `/tu-dien/`, `/luyen-noi/`, `/bang-lo-trinh/`, `/thu-vien-chu-de/`, link web trong bình luận đầu tiên trên Facebook), `lessons.json`, dữ liệu tiến độ trong localStorage với đúng khóa cũ, wizard 7 bước, ôn tập, tìm kiếm, Từ điển, Luyện nói, học từng cụm.
5. Kiểm tra sau khi dựng: xem ở 390px và 1280px, đầu trang gọn đúng số đo (thẻ Bài hôm nay kết thúc trước 360px trên màn hình 844px, nút Học ngay thấy ngay không cần cuộn), không tràn chữ, không nút nào nhỏ hơn 44px, không có gạch ngang trong chữ hiển thị, nhiệm vụ và XP tính đúng với dữ liệu thật, kiểm mắt từng ảnh sau khi dựng.
6. Deploy theo đúng quy trình: không chạy 2 lần deploy song song, không dùng pipeline che mã lỗi, kiểm tra head trên remote trước khi đẩy lại nếu gặp lỗi fast forward.
