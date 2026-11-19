# Phần nghiên cứu: API mở và mã nguồn mở cho Kho bài học Sai Đâu Sửa Đó

Ngày nghiên cứu: 19/11/2026. Mục đích: trước khi chốt đặc tả API, xem thế giới đã có gì, bộ dữ liệu của Trang lấp được khoảng trống nào, dự án nào từng được lập trình viên dùng nhiều và họ làm gì để được dùng, đi kênh nào, và API này có giúp Trang kiếm tiền sau này không hay chỉ là cho không. Mọi con số dưới đây đều lấy từ nguồn đã đọc, ghi rõ ở cuối từng mục.

## 1. API và dữ liệu mở đang có cho học tiếng Anh, và chúng thiếu gì với người Việt

### 1.1. Free Dictionary API, tên gọi khác dictionaryapi.dev

1. Chỉ có tiếng Anh, không cần khóa, không xác thực, miễn phí. Trả về phiên âm, danh sách phiên âm kèm IPA và link âm thanh, nghĩa theo từ loại kèm định nghĩa, ví dụ, từ đồng nghĩa và trái nghĩa, giấy phép và link nguồn.
2. Dữ liệu lấy từ Wiktionary, theo giấy phép CC BY-SA 3.0. Repo meetDeveloper/freeDictionaryAPI theo GPL-3.0, khoảng 2.600 sao GitHub, hơn 10 triệu lượt gọi mỗi tháng. Đã lên Product Hunt, ra mắt ngày 9/2/2026, và Show HN.
3. Điểm yếu đã ghi nhận: giới hạn khoảng 1.000 lượt gọi mỗi giờ mỗi IP theo một tài liệu so sánh, tài liệu chính không ghi rõ con số này; âm thanh đôi khi lỗi 502; thiếu cấp độ CEFR, thiếu ngữ vực, thiếu collocation, thiếu nhóm từ dễ nhầm, thiếu dạng chia của động từ; một số từ thiếu phiên âm hoặc âm thanh.
4. Với người Việt, điểm yếu lớn nhất là nghĩa chỉ có bằng tiếng Anh. Người mới học tra từ xong vẫn phải dịch nghĩa sang tiếng Việt bằng đầu óc của mình, đúng chỗ dễ sai nhất thì API không giúp.

### 1.2. Wiktionary

1. Hơn 53 triệu mục, hơn 190 phiên bản ngôn ngữ, hơn 10 triệu mục tiếng Anh. Giấy phép CC BY-SA cộng GFDL.
2. Nội dung là wikitext, tức là văn bản có đánh dấu, rất khó trích xuất sạch. Muốn dùng phải qua công cụ trung gian như Wiktextract, DBnary hay Kaikki.org. MediaWiki API giới hạn theo lượt gọi. Wikimedia Enterprise API có bản Snapshot và bản On-demand, cần tài khoản và token miễn phí, trả phí khi dùng dung lượng cao.
3. Với người Việt, Wiktionary tiếng Việt có nghĩa tiếng Việt, nhưng định nghĩa viết kiểu từ điển học, khô và dài, không gắn với lỗi người Việt hay mắc, không có câu luyện tập, không có cặp câu sai và câu đúng.

### 1.3. Tatoeba

1. Hơn 13,4 triệu câu, 429 ngôn ngữ, tính đến tháng 4/2026, hơn 1 triệu câu có âm thanh. Giấy phép CC BY, một số câu CC0. Tải về dạng cặp câu dùng được cho Anki. API chính thức không ổn định, các gói bọc của bên thứ ba thì cần khóa hoặc trả phí, ví dụ gói oanor miễn phí 3.100 lượt gọi mỗi tháng, trả phí từ 7,70 euro mỗi tháng.
2. Được Clozemaster, JMdict và OpenRussian dùng làm nguồn dữ liệu. Người sáng lập là Trang Ho, từ năm 2008. Vận hành bởi tổ chức phi lợi nhuận Association Tatoeba ở Pháp, nhận tài trợ và grant Mozilla MOSS 25.000 USD năm 2018 và 15.000 USD năm 2019.
3. Điểm yếu với người Việt: câu không tuyển chọn theo lỗi người Việt, không tổ chức theo dạng lỗi, không có sửa lỗi, không có giải thích vì sao sai, không có dịch tiếng Việt chuẩn cho từng câu.

### 1.4. Các deck Anki mở

1. Có deck học tiếng Việt như Vietnamese Vocabulary Core 1k, Core 2000, Basic Vietnamese, Xefjord's Complete Vietnamese, nhưng đó là deck học tiếng Việt, không phải học tiếng Anh cho người Việt.
2. Deck tiếng Anh cho người Việt có thật, ví dụ 4000 Essential English Words bản tiếng Việt với rating khoảng 268, 600 essential English words for the TOEIC bản tiếng Việt, English vocabulary in use bản tiếng Việt. Tất cả đều là file .apkg, không có API, không có cấu trúc sửa lỗi, giấy phép không rõ, một số không cập nhật từ năm 2019.
3. Cách phân phối rất thủ công: người ta đăng bài lên Facebook xin file, một bài đăng có 69 bình luận xin gửi qua tin nhắn riêng để lấy deck TOEIC, Destination B1 và B2, 4500 từ. Không có chỗ tải tập trung, không có cập nhật, không có kiểm chứng chất lượng.

### 1.5. Dataset sửa lỗi ngữ pháp trên Hugging Face

1. grammarly/medit: 102 nghìn mẫu. BEA-2019: FCE 26.929 câu, W và I cộng LOCNESS 68.608 câu, Lang-8 985.683 câu, chiếm 80,54 phần trăm. NUCLE: 1.400 bài luận. EFCAMDAT: 1.180.310 bài viết.
2. Đây là kho ngữ liệu nghiên cứu để huấn luyện mô hình, tức là cặp câu sai và câu đúng khô khan, không phải bài học cho người học. Không có dịch tiếng Việt, không có giải thích vì sao sai, không có câu luyện tập, không có chia theo chủ đề đời thường.
3. Dữ liệu Lang-8 không được chia sẻ lại do giới hạn giấy phép. Nghĩa là ngay cả kho ngữ liệu lớn nhất cũng không phải là dữ liệu mở dùng tự do.

### 1.6. Kiến thức về lỗi người Việt chỉ nằm trong bài báo, không có dataset

1. Nghiên cứu của Lê Thị Kim Đức, 2024, Tạp chí Khoa học và Công nghệ Đại học Thái Nguyên 229(12): 382-389, khảo sát 57 sinh viên năm nhất. Lỗi gồm thì, mạo từ, giới từ, số nhiều, hòa hợp chủ ngữ và động từ.
2. Nghiên cứu MBA của Nguyễn và Đặng, 2022, Đại học Tây Đô. Lỗi phát âm gồm ngữ điệu, âm cuối, cụm phụ âm, trọng âm. Lỗi ngữ pháp gồm mạo từ, thì, bị động, trật tự từ.
3. Nghiên cứu của Triệu Thùy Hương, 2024, thư tiếng Anh của sinh viên năm nhất Đại học Tài nguyên và Môi trường Hà Nội.
4. Tất cả đều là bài báo và file PDF. Không có dataset mở, không có API, không có bài học nào lấy ra dùng được ngay. Khoảng trống đã xác nhận: kiến thức về lỗi người Việt đang nằm trong bài báo, chưa ai biến thành dữ liệu mở cho lập trình viên.

### 1.7. Khoảng trống mà bộ dữ liệu của Trang lấp được

1. Cặp câu sai và câu đúng kèm giải thích bằng tiếng Việt, tuyển chọn đúng lỗi người Việt hay mắc. Không API nào ở trên có cặp này. Dataset sửa lỗi có cặp sai và đúng nhưng không có giải thích tiếng Việt, không chia theo lỗi người Việt.
2. Nghĩa tiếng Việt đã kiểm tra bằng tay cho 852 từ, kèm từ loại tiếng Việt, ví dụ tiếng Anh có dịch tiếng Việt ngay bên dưới. Free Dictionary API chỉ có nghĩa tiếng Anh. Wiktionary tiếng Việt có nghĩa tiếng Việt nhưng không gắn ví dụ dịch sẵn và không gắn với bài học.
3. Câu luyện tập có đáp án và giải thích, tổng cộng 208 câu, chia theo 6 dạng: chọn đáp án, điền khuyết, tìm lỗi, phân biệt, dịch câu, sắp xếp từ. Không deck Anki nào, không dataset nào ở trên có dạng này.
4. Tổ chức theo chủ đề người Việt gặp hằng ngày: giao tiếp 28 bài, ngữ pháp 15 bài, từ vựng 7 bài, phát âm 6 bài, công sở 4 bài, quiz tổng hợp 2 bài. Học theo lỗi mình hay mắc, không học lan man.
5. Dữ liệu sống, cập nhật theo lịch đăng bài của Trang, 10 bài mỗi ngày, thay vì deck Anki không cập nhật từ năm 2019 hay dataset nghiên cứu đóng băng từ năm BEA-2019.

Kết luận mục 1: câu trong đặc tả là "không có bộ dữ liệu mở miễn phí nào làm riêng điều này cho lỗi người Việt hay mắc" là đúng, với nghĩa chính xác là không có bộ dữ liệu mở nào hướng tới người học, có cặp câu sai và câu đúng, giải thích tiếng Việt, câu luyện tập và nghĩa tiếng Việt đã kiểm tra tay, làm riêng cho lỗi người Việt hay mắc. Dataset nghiên cứu có cặp sai và đúng nhưng không hướng tới người học và không có tiếng Việt. Deck Anki có tiếng Việt nhưng chỉ là danh sách từ, không có sửa lỗi.

## 2. Dự án nội dung học tập mở từng được lập trình viên dùng nhiều, và họ làm gì để được dùng

### 2.1. freeCodeCamp, bài học lớn nhất về nội dung học mở

1. Khoảng 459 nghìn sao GitHub tính đến tháng 11/2026, giấy phép BSD-3-Clause, khoảng 7.014 người đóng góp trong năm gần nhất, 4.122 commit trong 52 tuần gần nhất.
2. Hơn 11.000 giờ chương trình, 10 lộ trình có chứng chỉ, hơn 40.000 học viên đã có việc làm lập trình viên, 1,2 triệu người học hoạt động mỗi tháng, YouTube 11,9 triệu người đăng ký, diễn đàn 358 nghìn người dùng.
3. Tổ chức phi lợi nhuận 501(c)(3), sống bằng tài trợ, doanh thu khoảng 4,28 triệu USD tiền tài trợ năm 2022, không vốn đầu tư, không paywall, không quảng cáo, không bán thêm.
4. Tăng trưởng nhờ chương trình miễn phí thật, YouTube, diễn đàn, cộng đồng đóng góp và chứng chỉ. Đang thêm chương trình English for Developers, bản beta, tức là chính freeCodeCamp cũng thấy lập trình viên cần tiếng Anh và đang lấn sang mảng này.
5. Bài học cho Trang: miễn phí thật sự là nền tảng, chứng chỉ và lộ trình giữ chân người học, cộng đồng đóng góp làm dữ liệu lớn dần mà Trang không phải tự làm hết.

### 2.2. Anki, mô hình tiền nuôi miễn phí

1. Anki desktop miễn phí, mã nguồn mở theo AGPLv3, AnkiDroid miễn phí do tình nguyện viên duy trì, hơn 10 triệu lượt tải trên Google Play, AnkiWeb đồng bộ miễn phí. Chỉ có AnkiMobile trên iOS là trả phí, 24,99 USD trả một lần ở Mỹ, giá thay đổi theo từng cửa hàng.
2. Tiền bán AnkiMobile là nguồn thu duy nhất nuôi cả hệ sinh thái: app desktop miễn phí, AnkiWeb miễn phí, và công việc duy trì của tác giả Damien Elmes. Không quảng cáo, không gói tháng, không bán dữ liệu người dùng.
3. Tháng 2/2026, Elmes thông báo chuyển dần vận hành kinh doanh và quản lý mã nguồn mở sang AnkiHub, công ty đứng sau deck AnKing, trong khi ông vẫn tham gia ở mức bền vững. Cam kết công khai: Anki vẫn mã nguồn mở, không vốn đầu tư, không tăng giá, AnkiDroid vẫn độc lập.
4. Hệ sinh thái có hơn 1.600 add-on và thuật toán xếp lịch học máy huấn luyện trên hàng trăm triệu lượt ôn tập.
5. Bài học cho Trang: một thành phần trả phí nhỏ, đúng chỗ người dùng chịu trả, nuôi được toàn bộ phần miễn phí. Và deck Anki là kênh phân phối dữ liệu học tập lớn nhất thế giới, nhưng deck cho người Việt hiện tại phân phối lộn xộn qua tin nhắn riêng, không có nguồn chính thống.

### 2.3. Tatoeba, dữ liệu mở nuôi app thật

1. Dữ liệu mở theo CC BY, tải về tự do, được Clozemaster, JMdict và OpenRussian dùng làm nguồn. Không cần Trang phải tự xây app, app của người khác mang dữ liệu của mình đi xa.
2. Sống bằng tài trợ và grant, Mozilla MOSS 25.000 USD năm 2018 và 15.000 USD năm 2019.
3. Bài học cho Trang: giấy phép cho phép dùng lại, kể cả để kiếm tiền, là điều kiện để app thương mại dám dùng dữ liệu của mình. Nếu Trang chọn giấy phép cấm dùng thương mại thì Clozemaster kiểu Việt Nam sẽ không dám chạm vào.

### 2.4. Free Dictionary API, API nhỏ mà dev nhớ tên

1. Repo khoảng 2.600 sao, hơn 10 triệu lượt gọi mỗi tháng, đã lên Product Hunt ngày 9/2/2026 và Show HN.
2. Điểm mạnh là không cần khóa, tài liệu ngắn gọn, ví dụ chạy được ngay, dữ liệu từ Wiktionary theo CC BY-SA 3.0.
3. Bài học cho Trang: API càng ít rào cản thì càng nhiều người thử. Không khóa, không đăng ký, ví dụ fetch chạy được trong 30 giây là chuẩn phải đạt.

### 2.5. Bảy điều dự án được dùng nhiều đều làm

1. Miễn phí thật, không paywall giấu sau vài lần dùng thử.
2. Tài liệu ngắn, có ví dụ chạy được ngay, không chỉ mô tả bằng chữ.
3. Giấy phép rõ ràng và cho phép dùng thương mại, ghi rõ trong repo và trong dữ liệu trả về.
4. Có app ví dụ hoặc bản demo dùng ngay, để lập trình viên thấy dữ liệu làm được gì trong 5 phút.
5. Có kênh giới thiệu: GitHub, Product Hunt, Show HN, diễn đàn, cộng đồng.
6. Có cộng đồng đóng góp: báo lỗi dữ liệu, đề xuất thêm bài, sửa lỗi chính tả, ai cũng đóng góp được.
7. Cập nhật đều đặn và công khai nhật ký thay đổi, để lập trình viên tin rằng dữ liệu không chết sau 3 tháng.

## 3. Kênh phân phối cho lập trình viên

### 3.1. GitHub, kênh chính và bền nhất

1. Danh sách public-apis trên GitHub có hơn 325 nghìn sao, hơn 1.400 API, 52 danh mục. Điều kiện đưa vào: truy cập miễn phí hoặc có gói miễn phí, từ chối pull request mang tính marketing. API của Trang đủ điều kiện vì là file tĩnh, không khóa, không phí.
2. Awesome list theo chủ đề, ví dụ awesome list về học tiếng Anh hay về API miễn phí, cũng là kênh bền, sao GitHub tích lũy mãi, không tắt sau một ngày như Product Hunt.
3. free-apis.github.io là danh sách API miễn phí khác, cũng đáng đưa vào.
4. Repo của Trang vốn đã công khai, nên việc đưa API vào các danh sách này chỉ cần một pull request có mô tả rõ ràng, không tốn tiền.

### 3.2. Product Hunt và Show HN, cú hích một ngày

1. Product Hunt có 4,6 triệu lượt thăm mỗi tháng, nhưng hiệu ứng chỉ mạnh trong 1 ngày rồi tắt nhanh. Bài học từ các bài viết về ra mắt sản phẩm: xây sản phẩm là 50 phần trăm, để người ta tìm thấy là 50 phần trăm.
2. Show HN: bài nổi bật đạt 50 nghìn đến 100 nghìn lượt xem trở lên, phản hồi chất lượng cao, tiêu chuẩn cao, không chấp nhận bài chỉ quảng cáo.
3. DevHunt: trang miễn phí vĩnh viễn, người bình chọn là lập trình viên.
4. Thứ tự khuyên dùng: GitHub trước để có chỗ cho người ta xem, rồi Show HN, rồi Product Hunt, vì Product Hunt cần link sản phẩm hoàn chỉnh ngay trong ngày ra mắt.

### 3.3. APIs.guru và Postman API Network, kênh cho người tìm API theo chuẩn

1. APIs.guru yêu cầu định nghĩa OpenAPI ở một URL ổn định. Vì vậy đặc tả đã bổ sung file `openapi.yaml` đặt ở `/api/openapi.yaml`, xem mục giấy phép và tài liệu trong api-spec.md.
2. Postman API Network cũng là nơi lập trình viên tìm API có sẵn bộ sưu tập Postman để thử ngay.
3. RapidAPI và APILayer là chợ API, nhưng hai kênh này thiên về API trả phí, nên chỉ đưa vào sau khi đã có người dùng, không phải kênh đầu tiên.

### 3.4. Cộng đồng lập trình viên Việt Nam

1. Viblo: hơn 85.000 người dùng hoạt động, hơn 30.000 bài viết về công nghệ. Đây là nơi viết bài giới thiệu API bằng tiếng Việt, kèm ví dụ xây app flashcard từ dữ liệu Trang.
2. WeBuild Community: cộng đồng lập trình viên người Việt, gần 5.000 thành viên trên Slack và Discord, có tổ chức sự kiện offline WeBuildDay.
3. VietTech Group: cộng đồng người Việt làm công nghệ, hơn 10.000 thành viên.
4. Group Facebook Lập trình viên Việt Nam, VOZ, Kipalog, diễn đàn Reddit, dev.to. Group Lập trình Android Việt Nam có hơn 50.000 thành viên, là nơi tìm lập trình viên làm app học tiếng Anh trên điện thoại.
5. Lưu ý: cộng đồng Việt rất nhiệt tình nhưng cũng rất thẳng, bài giới thiệu phải có sản phẩm thật, ví dụ chạy được, không viết chung chung thì mới được chia sẻ.

### 3.5. App học tiếng Anh đang cần dữ liệu

1. Clozemaster đã chứng minh app học bằng câu có sẵn dùng dữ liệu mở Tatoeba. App kiểu này cho người Việt chưa có ai làm với lỗi người Việt.
2. Người làm deck Anki cho người Việt hiện phân phối qua tin nhắn riêng, không có nguồn dữ liệu chuẩn. Một file deck .apkg sinh từ API của Trang, cập nhật theo lịch đăng bài, là sản phẩm phụ có người cần ngay.
3. Chatbot học tiếng Anh và Zalo mini app là hai dạng app mà lập trình viên Việt hay làm, cả hai đều cần dữ liệu bài học có sẵn, có cặp sai và đúng, có câu luyện tập.
4. Thứ tự kênh khuyên dùng: GitHub và awesome list trước, Viblo và Show HN sau đó, Product Hunt khi đã có 2 đến 3 app ví dụ chạy được, APIs.guru và Postman cùng lúc với việc sinh file openapi.yaml.

## 4. Bốn góc độ

### 4.1. Góc độ người học: dùng API được gì

1. App flashcard lấy đúng lỗi mình hay mắc, không phải học 4.000 từ lan man. Ví dụ app lọc bài loại Lỗi thuộc chủ đề giao tiếp rồi biến thành thẻ học, ôn lại theo lịch.
2. Tra từ có nghĩa tiếng Việt đã kiểm tra tay, kèm ví dụ có dịch, thay vì tra từ điển tiếng Anh rồi tự dịch nghĩa trong đầu.
3. Luyện tập theo dạng mình yếu: người hay sai thì làm dạng tìm lỗi, người hay sai trật tự từ làm dạng sắp xếp từ, thay vì làm chung một dạng quiz.
4. Lộ trình học có sẵn trong API: 3 lộ trình, học lại từ đầu 7 bài, tiếng Anh đi làm 5 bài, sửa phát âm 6 bài, người học mở app là có đường đi ngay.
5. Rủi ro cho người học: app của bên thứ ba có thể hiển thị sai hoặc lỗi thời nếu không cập nhật dữ liệu. Cách giảm rủi ro: mỗi file API có trường phiên bản và ngày cập nhật, app phải hiển thị ngày dữ liệu.

### 4.2. Góc độ lập trình viên: gọi API có dễ không, có tin được không

1. Dễ: file JSON tĩnh trên GitHub Pages, không cần khóa, không đăng ký, không giới hạn lượt gọi, gọi bằng fetch một dòng, dữ liệu nhỏ, danh sách bài gọn khoảng 29 KB, toàn bộ bài khoảng 156 KB, từ điển đầy đủ khoảng 36 KB, tải một lần rồi dùng offline được.
2. Dễ: schema ổn định theo phiên bản v1, đổi schema thì lên v2, không đổi ngầm v1. Mỗi bài có slug ổn định, URL bài học không đổi, app không sợ link chết.
3. Tin được: mọi trường trong dữ liệu đều có nguồn ghi rõ, bài học do Trang tự soạn theo lịch đăng thật trên Facebook, bảng nghĩa do Trang kiểm tra bằng tay, phiên âm lấy trực tiếp từ dictionaryapi.dev lúc tra, dịch máy MyMemory luôn ghi rõ là dịch máy chưa kiểm chứng.
4. Tin được: giấy phép rõ ràng, MIT cho code, CC BY 4.0 cho nội dung, tên và logo không thuộc giấy phép mở, lập trình viên biết mình được làm gì và không được làm gì.
5. Chưa tin được hoàn toàn: chưa có nhật ký thay đổi công khai, chưa có cam kết thời gian hỗ trợ, chưa có kênh báo lỗi dữ liệu. Cả ba đều nằm trong kế hoạch dựng, xem ke-hoach-dung.md.
6. Điểm trừ cần nói thẳng: dữ liệu hiện có 62 bài, còn nhỏ so với 13,4 triệu câu của Tatoeba hay 53 triệu mục của Wiktionary. Lập trình viên xây app lớn sẽ hỏi khi nào có 500 bài. Câu trả lời nằm ở tốc độ đăng 10 bài mỗi ngày của Trang, dữ liệu lớn dần theo thời gian, và API có trường đếm số bài để app tự biết dữ liệu đã lớn tới đâu.

### 4.3. Góc độ Trang: API kéo người về Trang bằng cách nào

1. Ghi công nằm trong dữ liệu, không nằm ngoài lề. Mọi file trả về đều có khối meta.source ghi tên Trang, link web, link Facebook, giấy phép và câu ghi công. App nào dùng API cũng mang theo khối này, và điều khoản ghi công bắt buộc app hiển thị ở nơi người học thấy được.
2. Mọi bài học trong API đều có link về bài gốc trên web và link bài đăng Facebook. Người học thấy bài hay trong app thì bấm về web của Trang để đọc thêm, rồi từ web bấm sang Facebook.
3. App ví dụ do Trang tự làm mẫu, như app flashcard và app ôn tập SRS, đều dẫn về Trang. Lập trình viên fork app ví dụ thì link về Trang đi theo.
4. Cộng đồng lập trình viên biết tới Trang qua GitHub, Viblo, Show HN, Product Hunt. Đây là nhóm người mà Trang chưa từng tiếp cận qua Facebook, vì vậy API mở ra một kênh người biết tới Trang hoàn toàn mới.
5. Dữ liệu càng được dùng nhiều thì Trang càng có uy tín để nói chuyện với đối tác, ví dụ trung tâm tiếng Anh muốn dùng dữ liệu, hay nhà xuất bản muốn hợp tác làm sách.
6. Rủi ro cho Trang: app khác dùng dữ liệu mà không ghi công, hoặc ghi công sai, hoặc dùng logo Trang làm thương hiệu riêng. Cách giảm rủi ro: giấy phép CC BY 4.0 cho phép Trang yêu cầu gỡ nội dung vi phạm, logo và slogan không thuộc giấy phép mở, và Trang giữ quyền đổi giấy phép cho phiên bản dữ liệu mới.

### 4.4. Góc độ tiền: API mở có giúp bán sản phẩm số sau này không, hay chỉ là cho không

1. Câu trả lời ngắn: API mở là phễu, không phải sản phẩm bán. Nó cho không dữ liệu miễn phí đã đăng, để đổi lấy người biết tới Trang, rồi bán sản phẩm mới, chưa từng đăng, hay và hấp dẫn hơn giá tiền.
2. Mô hình Anki chứng minh được: desktop miễn phí, AnkiWeb miễn phí, chỉ AnkiMobile trên iOS trả 24,99 USD một lần, và tiền đó nuôi cả hệ sinh thái. Một thành phần trả phí nhỏ, đúng chỗ người dùng chịu trả, nuôi được toàn bộ phần miễn phí.
3. Mô hình freeCodeCamp chứng minh được: chương trình miễn phí thật, sống bằng tài trợ 4,28 triệu USD năm 2022, không paywall, không quảng cáo, không bán thêm. Tài trợ đến vì có 1,2 triệu người học mỗi tháng và 40.000 người đã có việc nhờ học ở đó.
4. Mô hình open core chứng minh được: lõi mở, tính năng doanh nghiệp trả phí. GitLab mở lõi và bán tính năng bảo mật, tuân thủ, xác thực doanh nghiệp. Chatwoot mở lõi theo MIT, khoảng 40.000 sao, 9.700 fork, hơn 15.000 doanh nghiệp dùng, và bán tính năng AI, gọi thoại, SSO trong thư mục enterprise riêng. Quy tắc vẽ ranh giới được nhiều bài viết nhắc lại: miễn phí là phần tạo ra nhận biết, trả phí là phần tạo ra giá trị ở quy mô lớn.
5. Áp vào Trang, ranh giới đúng là: miễn phí là bài học đã đăng và API dữ liệu đó, trả phí là sản phẩm mới chưa từng đăng, ví dụ sổ tay luyện sửa lỗi theo lộ trình 14 ngày làm mới hoàn toàn, app ôn tập SRS trả phí nhỏ dùng chính dữ liệu API nhưng thêm nhắc lịch, thống kê và lộ trình cá nhân, hay deck Anki cập nhật tự động theo lịch đăng bài.
6. Luật chất lượng sản phẩm bán của Trang vẫn đứng: tài liệu trả phí phải mới, chưa từng đăng, tự nó hay và hấp dẫn, sức hấp dẫn vượt giá tiền, chính Đông phải thấy đáng bỏ tiền mua, không gói lại đồ miễn phí để bán. API mở không được làm mờ luật này. Nếu sản phẩm trả phí chỉ là gói lại dữ liệu API thì người mua sẽ thấy ngay và không mua lần hai.
7. Rủi ro lớn nhất: cho không mà không có đường về tiền. Xảy ra khi Trang mở API nhưng không giữ ranh giới, ví dụ đưa cả sản phẩm trả phí vào API, hoặc không có sản phẩm trả phí mới nào để bán, hoặc app bên thứ ba hút hết người học mà không ai quay về Trang. Cách tránh: giữ sản phẩm trả phí ngoài API, ghi công bắt buộc có link về Trang trong mọi app, và chỉ mở bán khi có sản phẩm mới thật sự hay.
8. Đường tiền khuyên thử theo thứ tự: trước hết bán sản phẩm số mới, vì Trang đã có cộng đồng Facebook và Group, không cần chờ API. Sau đó làm app ôn tập SRS trả phí nhỏ dùng dữ liệu API, vì đây là thứ API mở không có mà người học sẵn sàng trả. Cuối cùng mới nghĩ tới tài trợ kiểu freeCodeCamp, khi đã có vài nghìn người dùng API mỗi tháng và có con số để gọi tài trợ.

## 5. Test mẫu thật: mọi trường trong mẫu đều có thật, mọi ví dụ đều khớp dữ liệu gốc

### 5.1. Phương pháp

1. Script kiểm tra `verify_samples.py`, lưu cùng thư mục api, đọc dữ liệu gốc là `web/lessons.json` và bảng `VI_GLOSSARY` trong `web/generate_site.py`, rồi đối chiếu từng trường trong hai file mẫu.
2. Với mẫu bài học, script kiểm tra từng bài có thật trong lessons.json theo slug, từng trường code, type, topic, title, date, wrong, right, remember, fb, image và show_in_ui khớp y hệt trường gốc tương ứng, trường url khớp base_url cộng slug, và không có trường lạ nào ngoài danh sách cho phép.
3. Với mẫu từ điển, script kiểm tra từng từ có thật trong VI_GLOSSARY, số nghĩa khớp, từng nghĩa có từ loại và nghĩa tiếng Việt khớp y hệt, nghĩa nào gốc có ví dụ thì mẫu phải có ví dụ tiếng Anh và dịch tiếng Việt khớp y hệt, nghĩa nào gốc không có ví dụ thì mẫu không được bịa ví dụ.
4. Script còn kiểm tra các con số trong khối meta của mẫu: tổng số bài, số bài hiện trong giao diện, tổng số từ, số từ có ví dụ, và câu ghi chú số lượng mẫu.

### 5.2. Kết quả lần chạy đầu, và lỗi tìm được

1. Lần chạy đầu: 289 PASS, 2 FAIL.
2. Lỗi 1: meta.total_lessons trong mẫu bài học ghi 63, dữ liệu gốc có 62 bài.
3. Lỗi 2: meta.visible_lessons trong mẫu bài học ghi 57, dữ liệu gốc có 56 bài hiện trong giao diện, vì 6 bài Reels có show_in_ui bằng false.
4. Cả hai lỗi đều là lỗi đếm trong khối meta, không phải lỗi dữ liệu bài học. Đã sửa mẫu: total_lessons thành 62, visible_lessons thành 56. Câu ghi chú trong mẫu đã ghi đúng 3 trong 62 bài nên không cần sửa.

### 5.3. Kết quả lần chạy lại sau khi sửa

1. Lần chạy lại: 291 PASS, 0 FAIL.
2. Toàn bộ 3 bài mẫu, gồm loi-001, quiz-001 và mau-cau-001, khớp y hệt dữ liệu gốc ở mọi trường, không có trường lạ, url suy ra đúng.
3. Toàn bộ 30 từ mẫu, gồm actually, agree, answer, arrive, ask, beautiful, because, book, borrow, child, children, comfortable, debt, didn't, doesn't, don't, go, good, hello, i'd, important, lend, live, love, said, ship, think, tomorrow, very và went, khớp y hệt bảng VI_GLOSSARY ở mọi nghĩa, kể cả nghĩa thứ hai của answer, love và tomorrow.
4. Các con số meta đã đúng: tổng số bài 62, số bài hiện trong giao diện 56, tổng số từ 852, số từ có ví dụ 112. Lưu ý: bảng gốc có 114 mục nghĩa có ví dụ, nhưng chỉ 112 từ có ví dụ, vì 2 từ có 2 nghĩa kèm ví dụ.
5. Kết luận: hai file mẫu không bịa trường nào, không bịa ví dụ nào, mọi giá trị đều truy về được dữ liệu gốc. Script kiểm tra giữ lại trong thư mục api để lần dựng thật chạy lại sau mỗi lần sinh file.

## 6. Thay đổi đã làm vào đặc tả nhờ nghiên cứu này

1. Bổ sung lưu ý giấy phép của nguồn nghĩa bên ngoài vào mục giấy phép trong api-spec.md: dữ liệu API chỉ chứa phần Trang tự soạn nên CC BY 4.0 áp dụng trọn, nhưng phiên âm và nghĩa tiếng Anh tra trực tiếp từ dictionaryapi.dev theo CC BY-SA 3.0, nếu sau này có lưu phần đó vào file API thì phải ghi rõ nguồn và giữ giấy phép CC BY-SA cho đúng phần đó.
2. Bổ sung file `openapi.yaml` ở `/api/openapi.yaml` vào trang tài liệu trong api-spec.md, vì APIs.guru yêu cầu định nghĩa OpenAPI ở một URL ổn định, và Postman API Network cũng dùng định nghĩa này.
3. Làm rõ câu wow trong đặc tả theo nghĩa chính xác ở mục 1.7: khoảng trống là bộ dữ liệu mở hướng tới người học, có cặp câu sai và câu đúng, giải thích tiếng Việt, câu luyện tập và nghĩa tiếng Việt đã kiểm tra tay, làm riêng cho lỗi người Việt hay mắc.

## Nguồn đã đọc

1. Free Dictionary API, tài liệu chính: https://dictionaryapi.dev
2. Repo Free Dictionary API: https://github.com/meetDeveloper/freeDictionaryAPI
3. Free Dictionary API trên Product Hunt: https://www.producthunt.com/products/free-dictionary-api
4. Tatoeba, trang chính và trang Wikipedia: https://tatoeba.org và https://en.wikipedia.org/wiki/Tatoeba
5. Wiktionary, trang chính và trang Wikipedia: https://www.wiktionary.org và https://en.wikipedia.org/wiki/Wiktionary
6. Deck Anki tiếng Việt trên AnkiWeb: https://ankiweb.net/shared/decks
7. Bài viết về deck Anki tiếng Anh cho người Việt và cách phân phối qua Facebook, đọc qua tìm kiếm ngày 19/11/2026.
8. Dataset sửa lỗi ngữ pháp, bài tổng quan về GEC và BEA-2019, đọc qua tìm kiếm ngày 19/11/2026.
9. Nghiên cứu lỗi người Việt: Lê Thị Kim Đức 2024, Tạp chí Khoa học và Công nghệ Đại học Thái Nguyên 229(12): 382-389; Nguyễn và Đặng 2022, Đại học Tây Đô; Triệu Thùy Hương 2024, Đại học Tài nguyên và Môi trường Hà Nội, đọc qua tìm kiếm ngày 19/11/2026.
10. freeCodeCamp, repo và bài viết kỷ niệm 10 năm: https://github.com/freeCodeCamp/freeCodeCamp
11. Anki, trang chính và tài liệu: https://apps.ankiweb.net
12. Bài viết về giá AnkiMobile và mô hình kinh doanh Anki: https://www.mintdeck.app/blog/is-anki-free-on-iphone
13. Bài viết về mô hình open core: https://www.repoloot.com/guides/open-core-business-model và https://dev.to/whoffagents/how-to-monetize-an-open-source-project-freemium-open-core-and-license-gating-4il6
14. Bài viết về Chatwoot và mô hình open core: https://automata.sale/en/blog/development/chatwoot-open-source-helpdesk/
15. Danh sách public-apis: https://github.com/public-apis/public-apis
16. Bài viết về ra mắt Product Hunt và Show HN, đọc qua tìm kiếm ngày 19/11/2026.
17. Cộng đồng lập trình viên Việt Nam trên Viblo: https://viblo.asia/p/cong-dong-danh-cho-lap-trinh-vien-5-hoi-nhom-khong-the-bo-qua-GAWVpeyP405 và https://viblo.asia/p/top-10-noi-pho-bien-de-tham-khao-y-tuong-code-ung-dung-cho-dan-it-startup-va-dac-biet-la-freelancer-BQyJKE6wVMe
18. Dữ liệu gốc của Trang: `web/lessons.json` với 62 bài và bảng `VI_GLOSSARY` với 852 từ trong `web/generate_site.py`, đọc trực tiếp ngày 19/11/2026.
