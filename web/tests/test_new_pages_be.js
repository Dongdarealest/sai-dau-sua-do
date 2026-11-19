// Kiểm thử trang mới kiểu app PeakFour: từ điển, bảng lộ trình, thư viện chủ đề,
// luyện nói, và chế độ học từng cụm trên trang bài.
// Chạy: cd web/tests && node test_new_pages_be.js
// (dùng jsdom đã cài cho test_browser_be.js)
const fs = require('fs');
const path = require('path');
const { JSDOM, VirtualConsole } = require('jsdom');

const WEB = path.join(__dirname, '..');
let pass = 0, fail = 0;
function ok(cond, name, extra) {
  if (cond) { pass++; console.log('PASS', name); }
  else { fail++; console.log('FAIL', name, extra === undefined ? '' : '=> ' + JSON.stringify(extra)); }
}

function loadPage(file, seedStorage, before, query) {
  const vc = new VirtualConsole();
  const jsErrors = [];
  vc.on('jsdomError', e => jsErrors.push('jsdomError: ' + (e.detail && e.detail.stack || e.message)));
  vc.on('error', (...a) => jsErrors.push('console.error: ' + a.join(' ')));
  const html = fs.readFileSync(path.join(WEB, file), 'utf8');
  // Tối ưu A (19/11): app.js/data.js là file ngoài, jsdom không tự nạp
  // <script src> nên nội tuyến chúng vào HTML trước khi dựng DOM.
  // Đợt hướng A: thêm skills.js và reading.js cho trang kỹ năng.
  let htmlInlined = html;
  for (const f of ['data.js', 'app.js', 'skills.js', 'reading.js']) {
    const tag = `<script src="/sai-dau-sua-do/${f}"></script>`;
    if (htmlInlined.includes(tag)) {
      const body = fs.readFileSync(path.join(WEB, f), 'utf8');
      htmlInlined = htmlInlined.replace(tag, () => `<script>\n${body}\n</script>`);
    }
  }
  const dom = new JSDOM(htmlInlined, {
    url: 'https://example.org/' + file + (query || ''),
    runScripts: 'dangerously',
    pretendToBeVisual: true,
    virtualConsole: vc,
    beforeParse(window) {
      window.matchMedia = () => ({ matches: false, addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {} });
      window.scrollTo = () => {};
      window.speechSynthesis = { getVoices: () => [], speak() {}, cancel() {}, onvoiceschanged: null };
      window.SpeechSynthesisUtterance = function () {};
      if (seedStorage) for (const [k, v] of Object.entries(seedStorage)) window.localStorage.setItem(k, v);
      if (before) before(window);
    },
  });
  return { dom, jsErrors };
}
const tick = () => new Promise(r => setTimeout(r, 0));

(async () => {
  // ---------- Học từng cụm trên trang bài ----------
  {
    const { dom, jsErrors } = loadPage('loi-001/index.html');
    const { window } = dom;
    const doc = window.document;
    ok(jsErrors.length === 0, 'N1 loi-001 không lỗi JS', jsErrors.slice(0, 2));
    ok(!!doc.querySelector('#chunk-box'), 'N2 trang bài có hộp Học từng cụm');
    const en = doc.querySelector('#chunk-en');
    ok(en && en.textContent !== 'Đang tải cụm đầu tiên…' && en.textContent.length > 3, 'N3 cụm đầu tiên đã điền', en && en.textContent);
    const prog = doc.querySelector('#chunk-progress');
    ok(prog && /^Cụm 1\//.test(prog.textContent), 'N4 tiến độ hiện Cụm 1/N', prog && prog.textContent);
    const first = en.textContent;
    doc.querySelector('#chunk-next').click();
    ok(doc.querySelector('#chunk-en').textContent !== first, 'N5 bấm Cụm tiếp theo đổi câu');
    ok(/^Cụm 2\//.test(doc.querySelector('#chunk-progress').textContent), 'N6 tiến độ lên Cụm 2/N');
    doc.querySelector('#chunk-prev').click();
    ok(doc.querySelector('#chunk-en').textContent === first, 'N7 bấm Cụm trước quay lại câu đầu');
    doc.querySelector('#chunk-listen').click();
    ok(jsErrors.length === 0, 'N8 bấm Nghe câu mẫu không lỗi JS', jsErrors.slice(0, 2));
  }
  // N9: trang bài không còn thanh điều hướng trên (chỉ topbar + wiz-bottom);
  // 4 trang mới nằm ở thanh dưới trang chủ.
  {
    const { dom, jsErrors } = loadPage('index.html');
    const { window } = dom;
    const doc = window.document;
    ok(jsErrors.length === 0, 'N9 trang chủ không lỗi JS', jsErrors.slice(0, 2));
    const nav = [...doc.querySelectorAll('.bottomnav a')].map(a => a.getAttribute('href'));
    ok(nav.includes('/sai-dau-sua-do/tu-dien/') && nav.includes('/sai-dau-sua-do/luyen-noi/'), 'N9 thanh dưới trang chủ có đủ Từ điển và Luyện nói', nav);
  }

  // ---------- Từ điển ----------
  {
    const fakeEntry = [{ word: 'hello', phonetics: [{ text: '/həˈləʊ/', audio: 'https://api.dictionaryapi.dev/media/pronunciations/en/hello-uk.mp3' }, { text: '/həˈloʊ/', audio: 'https://api.dictionaryapi.dev/media/pronunciations/en/hello-us.mp3' }], meanings: [{ partOfSpeech: 'exclamation', definitions: [{ definition: 'Used as a greeting.', example: 'Hello, how are you?' }], synonyms: ['hi'] }] }];
    const { dom, jsErrors } = loadPage('tu-dien/index.html', null, (window) => {
      window.fetch = (url) => {
        if (String(url).includes('/hello')) return Promise.resolve({ ok: true, json: () => Promise.resolve(fakeEntry) });
        return Promise.resolve({ ok: false, status: 404, json: () => Promise.resolve({}) });
      };
    });
    const { window } = dom;
    const doc = window.document;
    ok(jsErrors.length === 0, 'N10 từ điển không lỗi JS khi tải', jsErrors.slice(0, 2));
    ok(/Chưa tra từ nào/.test(doc.querySelector('#dict-recent').textContent), 'N11 chưa tra từ nào thì ghi rõ');
    doc.querySelector('#dict-input').value = 'hello';
    doc.querySelector('#dict-go').click();
    await tick(); await tick();
    const res = doc.querySelector('#dict-result');
    ok(/hello/.test(res.textContent) && /həˈləʊ/.test(res.textContent), 'N12 tra hello hiện từ và phiên âm', res.textContent.slice(0, 120));
    ok(/Nghe giọng Anh/.test(res.textContent) && /Nghe giọng Mỹ/.test(res.textContent), 'N13 có nút nghe giọng Anh và giọng Mỹ');
    ok(/Used as a greeting/.test(res.textContent), 'N14 hiện nghĩa và ví dụ');
    const recent = JSON.parse(window.localStorage.getItem('sdsc-dict-recent') || '[]');
    ok(recent[0] === 'hello', 'N15 từ vừa tra lưu vào gần đây', recent);
    doc.querySelector('#dict-input').value = 'zzqqxx';
    doc.querySelector('#dict-go').click();
    await tick(); await tick();
    ok(/Không tìm thấy từ/.test(doc.querySelector('#dict-result').textContent), 'N16 từ lạ báo không tìm thấy');
  }

  // ---------- Từ điển: nghĩa tiếng Việt hiện trước (19/11) ----------
  {
    const tomorrowEntry = [{ word: 'tomorrow', phonetics: [{ text: '/təˈmɒɹəʊ/', audio: 'https://api.dictionaryapi.dev/media/pronunciations/en/tomorrow-uk.mp3' }, { text: '/təˈmɑɹoʊ/', audio: 'https://api.dictionaryapi.dev/media/pronunciations/en/tomorrow-us.mp3' }, { text: '/təˈmɒɹəʊ/', audio: 'https://api.dictionaryapi.dev/media/pronunciations/en/tomorrow-au.mp3' }], meanings: [{ partOfSpeech: 'noun', definitions: [{ definition: 'The day after the present day.' }], synonyms: ['morrow'] }, { partOfSpeech: 'adverb', definitions: [{ definition: 'On the day after the present day.', example: 'See you tomorrow.' }], synonyms: [] }] }];
    const goodEntry = [{ word: 'good', phonetics: [{ text: '/ɡʊd/', audio: 'https://api.dictionaryapi.dev/media/pronunciations/en/good-uk.mp3' }], meanings: [{ partOfSpeech: 'adjective', definitions: [{ definition: 'Of high quality.' }], synonyms: ['fine', 'great'] }] }];
    const quixoticEntry = [{ word: 'quixotic', phonetics: [], meanings: [{ partOfSpeech: 'adjective', definitions: [{ definition: 'Extremely idealistic.', example: 'a quixotic quest' }], synonyms: [] }] }];
    const { dom, jsErrors } = loadPage('tu-dien/index.html', null, (window) => {
      window.fetch = (url) => {
        const u = String(url);
        if (u.includes('dictionaryapi.dev')) {
          if (u.endsWith('/tomorrow')) return Promise.resolve({ ok: true, json: () => Promise.resolve(tomorrowEntry) });
          if (u.endsWith('/good')) return Promise.resolve({ ok: true, json: () => Promise.resolve(goodEntry) });
          if (u.endsWith('/quixotic')) return Promise.resolve({ ok: true, json: () => Promise.resolve(quixoticEntry) });
          return Promise.resolve({ ok: false, status: 404, json: () => Promise.resolve({}) });
        }
        if (u.includes('wiktionary')) {
          if (u.includes('serendipity')) return Promise.resolve({ ok: true, json: () => Promise.resolve({ query: { pages: { 123: { pageid: 123, ns: 0, title: 'serendipity', extract: '== Tiếng Anh ==\n=== Danh từ ===\nserendipity\nSự may mắn bất ngờ.' } } } }) });
          return Promise.resolve({ ok: true, json: () => Promise.resolve({ query: { pages: { 1: { missing: '' } } } }) });
        }
        if (u.includes('mymemory')) return Promise.resolve({ ok: true, json: () => Promise.resolve({ responseData: { translatedText: 'kỳ quặc' }, responseStatus: 200 }) });
        return Promise.resolve({ ok: false, status: 404, json: () => Promise.resolve({}) });
      };
    });
    const { window } = dom;
    const doc = window.document;
    ok(jsErrors.length === 0, 'N35 từ điển mới không lỗi JS khi tải', jsErrors.slice(0, 2));
    const input = doc.querySelector('#dict-input');
    const go = doc.querySelector('#dict-go');
    const res = () => doc.querySelector('#dict-result').textContent;
    input.value = 'tomorrow'; go.click();
    await tick(); await tick();
    ok(/ngày mai/.test(res()) && /trạng từ/.test(res()) && !/noun|adverb/.test(res()), 'N36 tra tomorrow hiện nghĩa tiếng Việt và nhãn từ loại tiếng Việt', res().slice(0, 200));
    ok(/giọng Anh/.test(res()) && /giọng Mỹ/.test(res()) && !/giọng Úc/.test(res()), 'N37 phiên âm tối đa 2 dòng, chỉ giọng Anh và giọng Mỹ', res().slice(0, 200));
    ok(/Hẹn gặp lại ngày mai/.test(res()), 'N38 ví dụ có dịch tiếng Việt ngay bên dưới', res().slice(0, 400));
    input.value = 'good'; go.click();
    await tick(); await tick();
    ok(/fine \(tốt, khỏe\)/.test(res()) && /great \(tuyệt vời\)/.test(res()), 'N39 từ gần nghĩa có nghĩa tiếng Việt kèm theo', res().slice(0, 400));
    input.value = 'books'; go.click();
    await tick(); await tick();
    ok(/sách/.test(res()) && /danh từ/.test(res()), 'N40 tra books (số nhiều) vẫn ra nghĩa tiếng Việt của book', res().slice(0, 200));
    input.value = 'serendipity'; go.click();
    await tick(); await tick();
    ok(/Sự may mắn bất ngờ/.test(res()) && /Wiktionary tiếng Việt/.test(res()), 'N41 từ chưa có trong bảng lấy nghĩa từ Wiktionary tiếng Việt', res().slice(0, 200));
    input.value = 'quixotic'; go.click();
    await tick(); await tick(); await tick(); await tick(); await tick(); await tick();
    ok(/kỳ quặc \(dịch máy, chưa kiểm chứng\)/.test(res()), 'N42 từ không có nghĩa tiếng Việt thì dịch máy và ghi rõ chưa kiểm chứng', res().slice(0, 400));
    input.value = 'loves'; go.click();
    await tick(); await tick();
    ok(/yêu/.test(res()) && /động từ/.test(res()), 'N43 tra loves (dạng chia) vẫn ra nghĩa tiếng Việt của love', res().slice(0, 200));
    input.value = 'going'; go.click();
    await tick(); await tick();
    ok(/đi/.test(res()) && /động từ/.test(res()), 'N44 tra going vẫn ra nghĩa tiếng Việt của go', res().slice(0, 200));
  }

  // ---------- Bảng lộ trình ----------
  {
    const seed = { 'sdsc-progress-v1': JSON.stringify({ version: 1, updatedAt: '2026-11-19T00:00:00.000Z', lessons: { 'loi-001': { done: true, doneAt: '2026-11-19' } }, practice: {}, review: {}, streak: { count: 3, lastDate: '2026-11-19', dates: ['2026-11-17', '2026-11-18', '2026-11-19'] }, history: [], settings: { dailyGoal: 1, remindReview: true } }) };
    const { dom, jsErrors } = loadPage('bang-lo-trinh/index.html', seed);
    const { window } = dom;
    const doc = window.document;
    ok(jsErrors.length === 0, 'N17 bảng lộ trình không lỗi JS', jsErrors.slice(0, 2));
    ok(/1 \/ \d+ bài/.test(doc.querySelector('#dash-done').textContent), 'N18 ô Bài đã nhớ hiện 1 / tổng số bài', doc.querySelector('#dash-done').textContent);
    ok(/3 ngày/.test(doc.querySelector('#dash-streak').textContent), 'N19 ô chuỗi ngày hiện 3 ngày');
    ok(doc.querySelectorAll('#dash-paths .progress').length === 3, 'N20 hiện tiến độ cả 3 lộ trình');
    ok(/Bài tiếp theo/.test(doc.querySelector('#dash-paths').textContent), 'N21 mỗi lộ trình gợi ý bài tiếp theo');
    ok(/Học bài này/.test(doc.querySelector('#dash-next').textContent), 'N22 có nút học bài tiếp theo');
  }

  // ---------- Thư viện chủ đề ----------
  {
    const { dom, jsErrors } = loadPage('thu-vien-chu-de/index.html');
    const { window } = dom;
    const doc = window.document;
    ok(jsErrors.length === 0, 'N23 thư viện không lỗi JS', jsErrors.slice(0, 2));
    const totalCards = doc.querySelectorAll('.lib-group .card').length;
    ok(new RegExp(totalCards + ' bài khớp').test(doc.querySelector('#lib-count').textContent), 'N24 mặc định hiện đủ số bài khớp', doc.querySelector('#lib-count').textContent);
    const chip = [...doc.querySelectorAll('#lib-chips .chip')].find(c => c.dataset.topic === 'ngữ pháp');
    ok(!!chip, 'N25 có chip lọc ngữ pháp');
    chip.click();
    const n = parseInt((doc.querySelector('#lib-count').textContent.match(/(\d+) bài khớp/) || [])[1] || '0', 10);
    const expectedNguphap = doc.querySelectorAll('.lib-group .card[data-topic="ngữ pháp"]').length;
    ok(n === expectedNguphap && n > 0, 'N26 lọc ngữ pháp còn đúng số bài ngữ pháp', n);
    const allChip = [...doc.querySelectorAll('#lib-chips .chip')].find(c => c.dataset.topic === 'Tất cả');
    allChip.click();
    const search = doc.querySelector('#lib-search');
    search.value = 'borrow';
    search.dispatchEvent(new window.Event('input', { bubbles: true }));
    await new Promise(r => setTimeout(r, 300));
    const expectedBorrow = [...doc.querySelectorAll('.lib-group .card')].filter(c => (c.dataset.search || '').includes('borrow')).length;
    ok(new RegExp(expectedBorrow + ' bài khớp').test(doc.querySelector('#lib-count').textContent), 'N27 tìm borrow còn đúng số bài khớp', doc.querySelector('#lib-count').textContent);
  }

  // ---------- Luyện nói v2 (đợt hướng A, 19/11) ----------
  {
    const { dom, jsErrors } = loadPage('luyen-noi/index.html');
    const { window } = dom;
    const doc = window.document;
    ok(jsErrors.length === 0, 'N28 luyện nói không lỗi JS', jsErrors.slice(0, 2));
    const todayCards = doc.querySelectorAll('#speak-today .speak-sentence');
    ok(todayCards.length === 3, 'N29 hàng Câu của hôm nay có 3 thẻ câu', todayCards.length);
    const topicCards = doc.querySelectorAll('#speak-topics .topic-card');
    ok(topicCards.length === 5, 'N29b hàng Luyện theo chủ đề có 5 thẻ chủ đề', topicCards.length);
    const weakCards = doc.querySelectorAll('#speak-weak .speak-sentence');
    ok(weakCards.length >= 1 && weakCards.length <= 5, 'N29c hàng Từ yếu có 1 đến 5 thẻ', weakCards.length);
    ok(doc.querySelector('#speak-today .speak-sentence .en').textContent.length > 3, 'N30 thẻ câu đầu đã hiện câu tiếng Anh');
    ok(doc.querySelector('#speak-nosupport').style.display === 'block', 'N31 trình duyệt không hỗ trợ thì hiện câu báo rõ');
    ok(doc.querySelector('#speak-start').disabled === true, 'N32 nút Bắt đầu nói bị khóa khi không hỗ trợ');
    ok(/chưa hỗ trợ nhận diện/.test(doc.querySelector('#speak-status').textContent), 'N33 trạng thái báo chưa hỗ trợ', doc.querySelector('#speak-status').textContent);
    ok(/Máy chấm theo từ, không chấm từng âm/.test(doc.body.textContent), 'N34 trang ghi rõ giới hạn chấm theo từ ở cuối trang');
    // N34b: bấm 1 thẻ câu thì vào thẳng buổi (lượt 1), không cần micro thật
    // nhờ hook __speakTest.
    const st = window.__speakTest;
    ok(!!st, 'N34c có hook kiểm thử __speakTest');
    todayCards[0].click();
    ok(doc.querySelector('#speak-card').style.display === 'block', 'N34d bấm thẻ câu mở thẻ buổi luyện nói');
    ok(/Lượt 1 trên 3/.test(doc.querySelector('#speak-round').textContent), 'N34e buổi bắt đầu ở lượt 1');
    const said = st.state().sentence;
    const r1 = st.completeRound(said);
    ok(r1 && r1.scores.length === 1 && r1.scores[0] === 100, 'N34f nói đúng câu mẫu thì lượt 1 được 100 điểm', r1);
    ok(/điểm/.test(doc.querySelector('#speak-score').textContent), 'N34g sau lượt 1 hiện điểm');
    const colored = doc.querySelector('#speak-colored').innerHTML;
    ok(/w-ok|w-miss/.test(colored), 'N34h câu tô màu từ đúng và sai', colored.slice(0, 200));
    doc.querySelector('#speak-next').click();
    ok(/Lượt 2 trên 3/.test(doc.querySelector('#speak-round').textContent), 'N34i bấm Lượt tiếp theo sang lượt 2');
    st.completeRound(st.state().sentence);
    doc.querySelector('#speak-next').click();
    ok(/Lượt 3 trên 3/.test(doc.querySelector('#speak-round').textContent), 'N34j sang lượt 3');
    const target3 = doc.querySelector('#speak-target');
    ok(target3.classList.contains('speak-hidden'), 'N34k lượt 3 ẩn câu mẫu tiếng Anh');
    st.completeRound(st.state().sentence);
    ok(doc.querySelector('#speak-done').style.display === 'block', 'N34l xong 3 lượt hiện bảng tổng kết buổi');
    ok(/20 XP/.test(doc.querySelector('#speak-done').textContent), 'N34m tổng kết buổi ghi nhận 20 XP');
    const prog = JSON.parse(window.localStorage.getItem('sdsc-progress-v1') || '{}');
    ok((prog.xpTotal || 0) >= 20, 'N34n XP cộng thật vào tiến độ', prog.xpTotal);
    const sp = JSON.parse(window.localStorage.getItem('sdsc-speaking-v1') || '{}');
    ok((sp.sessions || 0) === 1 && (sp.minutes || 0) >= 1, 'N34o thống kê ghi 1 buổi và phút thật (không 0 phút)', sp);
    // N34p: không câu nào trong ô chọn kết thúc bằng dấu chấm kép.
    const allEn = [...doc.querySelectorAll('#speak-today .speak-sentence .en, #speak-weak .speak-sentence .vi')].map(e => e.textContent);
    ok(allEn.every(t => !/\.\./.test(t)), 'N34p không câu nào có dấu chấm kép', allEn.slice(0, 3));
  }

  // ---------- Trang chủ hướng A: vỏ mới, XP, nhiệm vụ ----------
  {
    const { dom, jsErrors } = loadPage('index.html');
    const { window } = dom;
    const doc = window.document;
    ok(jsErrors.length === 0, 'N45 trang chủ hướng A không lỗi JS', jsErrors.slice(0, 2));
    const nav = [...doc.querySelectorAll('.bottomnav a')];
    ok(nav.length === 5, 'N46 thanh dưới có đúng 5 nút', nav.length);
    ok(nav[0].classList.contains('on'), 'N47 nút Học đang được tô khi ở trang chủ');
    ok(!!doc.querySelector('.appbar'), 'N48 có thanh trên gọn 56px');
    ok(/BÀI HÔM NAY/.test(doc.querySelector('#hero-box').textContent), 'N49 thẻ Bài hôm nay hiện');
    ok(/Học ngay/.test(doc.querySelector('#hero-box').textContent), 'N50 thẻ Bài hôm nay có nút Học ngay');
    ok(/Nhiệm vụ hôm nay/.test(doc.querySelector('#missions-box').textContent), 'N51 có hộp Nhiệm vụ hôm nay');
    ok(/Học 1 bài mới/.test(doc.querySelector('#missions-box').textContent), 'N52 nhiệm vụ học 1 bài mới hiện');
    ok(/Ôn 2 bài đến hạn/.test(doc.querySelector('#missions-box').textContent), 'N53 nhiệm vụ ôn 2 bài hiện');
    ok(/Luyện nói 1 câu/.test(doc.querySelector('#missions-box').textContent), 'N54 nhiệm vụ luyện nói hiện');
    ok(/XP/.test(doc.querySelector('#missions-box').textContent), 'N55 hộp nhiệm vụ hiện XP và cấp');
    ok(doc.querySelectorAll('.tools .tool').length === 6, 'N56 lưới Công cụ có 6 mục', doc.querySelectorAll('.tools .tool').length);
    const toolHrefs = [...doc.querySelectorAll('.tools .tool')].map(a => a.getAttribute('href'));
    ok(toolHrefs.includes('/sai-dau-sua-do/luyen-nghe/') && toolHrefs.includes('/sai-dau-sua-do/luyen-viet/') && toolHrefs.includes('/sai-dau-sua-do/luyen-doc/'), 'N57 lưới Công cụ có đủ Nghe, Viết, Đọc', toolHrefs);
    ok(!!doc.querySelector('#tra-cuu'), 'N58 mục Tra cứu luôn hiện cuối trang chủ');
    ok(!!doc.querySelector('#search') && !!doc.querySelector('#latest-box') && !!doc.querySelector('#latest-link'), 'N59 Tra cứu gọn trên trang chủ giữ ô tìm kiếm và 3 bài mới nhất');
  }

  // ---------- Trang thư viện bài học: toàn bộ bộ lọc cũ chuyển sang đây ----------
  {
    const { dom, jsErrors } = loadPage('thu-vien-bai-hoc/index.html');
    const { window } = dom;
    const doc = window.document;
    ok(jsErrors.length === 0, 'N59a trang thư viện bài học không lỗi JS', jsErrors.slice(0, 2));
    const ids = ['#search', '#topicChips', '#typeChips', '#btnCards', '#btnTable', '#pathFilter', '#statusFilter', '#sortFilter', '#count', '#cards', '#empty', '#tableWrap', '#tbody'];
    ok(ids.every(id => !!doc.querySelector(id)), 'N59b thư viện giữ đủ id tìm kiếm cũ', ids.filter(id => !doc.querySelector(id)));
    ok(doc.querySelectorAll('#cards .card').length >= 58, 'N59c thư viện hiện đủ thẻ bài', doc.querySelectorAll('#cards .card').length);
    ok(!!doc.querySelector('a[href="/sai-dau-sua-do/"]'), 'N59d thư viện có link về trang chủ');
  }

  // ---------- Trang Tôi: mục thống kê và xuất nhập dữ liệu chuyển sang đây ----------
  {
    const { dom, jsErrors } = loadPage('bang-lo-trinh/index.html');
    const { window } = dom;
    const doc = window.document;
    ok(jsErrors.length === 0, 'N60a trang Tôi không lỗi JS', jsErrors.slice(0, 2));
    ok(!!doc.querySelector('.practice-site-num'), 'N60 trang Tôi giữ span số câu luyện tập toàn trang');
    ok(!!doc.querySelector('#done-list') && !!doc.querySelector('#recent-list') && !!doc.querySelector('#stats-list'), 'N60b trang Tôi có đủ 3 mục đã hoàn thành, hoạt động, thống kê');
    ok(!!doc.querySelector('#btn-export') && !!doc.querySelector('#btn-import'), 'N60c trang Tôi có nút tải và nhập dữ liệu tiến độ');
  }

  // ---------- XP khởi tạo: bài đã nhớ được 20 XP mỗi bài ----------
  {
    const seed = { 'sdsc-progress-v1': JSON.stringify({ version: 1, updatedAt: '2026-11-19T00:00:00.000Z', lessons: { 'loi-001': { done: true, doneAt: '2026-11-19' }, 'loi-002': { done: true, doneAt: '2026-11-19' } }, practice: {}, review: {}, streak: { count: 1, lastDate: '2026-11-19', dates: ['2026-11-19'] }, history: [], settings: { dailyGoal: 1, remindReview: true } }) };
    const { dom, jsErrors } = loadPage('index.html', seed);
    const { window } = dom;
    const doc = window.document;
    ok(jsErrors.length === 0, 'N61 trang chủ với tiến độ cũ không lỗi JS', jsErrors.slice(0, 2));
    ok(/40 XP/.test(doc.querySelector('#missions-box').textContent), 'N62 2 bài đã nhớ được khởi tạo 40 XP', doc.querySelector('#missions-box').textContent.slice(0, 120));
    ok(/Cấp 1/.test(doc.querySelector('#missions-box').textContent), 'N63 40 XP vẫn là Cấp 1 (200 XP một cấp)');
  }

  // ---------- Trang bài: đánh dấu nhớ cộng 20 XP và nhiệm vụ mới ----------
  {
    const { dom, jsErrors } = loadPage('loi-001/index.html');
    const { window } = dom;
    const doc = window.document;
    ok(jsErrors.length === 0, 'N64 trang bài không lỗi JS', jsErrors.slice(0, 2));
    const doneBtn = doc.querySelector('#btn-done');
    ok(!!doneBtn, 'N65 trang bài có nút Tôi đã nhớ bài này');
    doneBtn.click();
    const prog = JSON.parse(window.localStorage.getItem('sdsc-progress-v1') || '{}');
    ok((prog.xpTotal || 0) === 20, 'N66 đánh dấu nhớ 1 bài cộng 20 XP', prog.xpTotal);
    ok(prog.daily && prog.daily.newDone === 1, 'N67 nhiệm vụ học bài mới đếm 1', prog.daily);
    ok(prog.review['loi-001'] && prog.review['loi-001'].skill === 'listen', 'N68 bài mới nhớ khởi tạo vòng kỹ năng bằng Nghe', prog.review['loi-001']);
    ok(/20 XP/.test(doc.querySelector('#complete-summary').textContent), 'N69 tóm tắt hoàn thành hiện XP', doc.querySelector('#complete-summary').textContent.slice(0, 200));
    ok(/Nghe/.test(doc.querySelector('#complete-summary').textContent), 'N70 tóm tắt hoàn thành ghi lần ôn tới luyện bằng Nghe', doc.querySelector('#complete-summary').textContent.slice(0, 300));
  }

  // ---------- Luyện nghe: đủ 3 dạng, XP cộng đúng ----------
  {
    const { dom, jsErrors } = loadPage('luyen-nghe/index.html');
    const { window } = dom;
    const doc = window.document;
    ok(jsErrors.length === 0, 'N71 luyện nghe không lỗi JS', jsErrors.slice(0, 2));
    const lt = window.__listenTest;
    ok(!!lt, 'N72 có hook kiểm thử __listenTest');
    doc.querySelector('#listen-begin').click();
    ok(doc.querySelector('#listen-card').style.display === 'block', 'N73 bấm Bắt đầu mở thẻ luyện nghe');
    // 6 câu: dạng pick, choose, type, pick, choose, type.
    // Trả lời đúng hay sai đều cho buổi chạy hết, điểm chỉ ảnh hưởng điểm
    // trung bình, không chặn buổi.
    for (let round = 0; round < 6; round++) {
      const st = lt.state();
      ok(st.idx === round, 'N74 câu ' + (round + 1) + ' đúng thứ tự', st.idx);
      if (st.mode === 'pick') lt.answerPick('right');
      else if (st.mode === 'choose') lt.answerChoose('0');
      else lt.answerType(st.pair.right);
      lt.next();
    }
    ok(doc.querySelector('#listen-done').style.display === 'block', 'N75 xong 6 câu hiện bảng tổng kết');
    ok(/20 XP/.test(doc.querySelector('#listen-done').textContent), 'N76 tổng kết luyện nghe ghi nhận 20 XP');
    const prog = JSON.parse(window.localStorage.getItem('sdsc-progress-v1') || '{}');
    ok((prog.xpTotal || 0) >= 20, 'N77 XP luyện nghe cộng thật vào tiến độ', prog.xpTotal);
    const sp = JSON.parse(window.localStorage.getItem('sdsc-listening-v1') || '{}');
    ok((sp.sessions || 0) === 1 && (sp.minutes || 0) >= 1, 'N78 thống kê nghe ghi 1 buổi và phút thật', sp);
    ok(/tô vàng|từ khác nhau/.test(doc.body.textContent), 'N79 trang nghe nói rõ từ khác nhau được tô vàng');
  }

  // ---------- Luyện viết: đủ 3 dạng, danh sách lỗi hay viết sai ----------
  {
    const { dom, jsErrors } = loadPage('luyen-viet/index.html');
    const { window } = dom;
    const doc = window.document;
    ok(jsErrors.length === 0, 'N80 luyện viết không lỗi JS', jsErrors.slice(0, 2));
    const wt = window.__writeTest;
    ok(!!wt, 'N81 có hook kiểm thử __writeTest');
    doc.querySelector('#write-begin').click();
    ok(doc.querySelector('#write-card').style.display === 'block', 'N82 bấm Bắt đầu mở thẻ luyện viết');
    // Câu 1 (fix): gõ sai cố ý để vào danh sách lỗi hay viết sai.
    const st1 = wt.state();
    wt.answer('totally wrong answer here');
    ok(/điểm/.test(doc.querySelector('#write-feedback').textContent), 'N83 gõ sai vẫn hiện điểm lượt');
    const wrongList = wt.wrongList();
    ok(wrongList.length === 1, 'N84 câu gõ sai vào danh sách Lỗi tôi hay viết sai', wrongList);
    wt.next();
    // Câu 2 và 3: gõ đúng.
    for (let round = 1; round < 3; round++) {
      const st = wt.state();
      if (st.mode === 'fill') {
        // Điền từ: lấy đáp án từ câu đúng bằng cách gõ cả câu đúng.
        wt.answer(st.pair.right);
      } else {
        wt.answer(st.pair.right);
      }
      wt.next();
    }
    ok(doc.querySelector('#write-done').style.display === 'block', 'N85 xong 3 câu hiện bảng tổng kết');
    ok(/20 XP/.test(doc.querySelector('#write-done').textContent), 'N86 tổng kết luyện viết ghi nhận 20 XP');
    const prog = JSON.parse(window.localStorage.getItem('sdsc-progress-v1') || '{}');
    ok((prog.xpTotal || 0) >= 20, 'N87 XP luyện viết cộng thật vào tiến độ', prog.xpTotal);
    ok(/Lỗi tôi hay viết sai/.test(doc.body.textContent), 'N88 trang viết có mục Lỗi tôi hay viết sai');
  }

  // ---------- Luyện đọc: tìm lỗi, chọn cách sửa, câu hỏi hiểu bài ----------
  {
    const { dom, jsErrors } = loadPage('luyen-doc/index.html');
    const { window } = dom;
    const doc = window.document;
    ok(jsErrors.length === 0, 'N89 luyện đọc không lỗi JS', jsErrors.slice(0, 2));
    const rt = window.__readTest;
    ok(!!rt, 'N90 có hook kiểm thử __readTest');
    doc.querySelector('#read-begin').click();
    ok(doc.querySelector('#read-card').style.display === 'block', 'N91 bấm Bắt đầu mở thẻ luyện đọc');
    ok(doc.querySelectorAll('#read-passage .read-sentence').length >= 3, 'N92 đoạn văn có ít nhất 3 câu', doc.querySelectorAll('#read-passage .read-sentence').length);
    ok(doc.querySelectorAll('#read-passage .word').length > 0, 'N93 mỗi câu tách thành từ bấm được');
    // Bấm 1 từ để xem nghĩa.
    const firstWord = doc.querySelector('#read-passage .word');
    firstWord.click();
    ok(doc.querySelector('#read-wordpop').textContent.length > 0, 'N94 bấm từ hiện nghĩa hoặc link tra từ');
    // Tìm câu lỗi: thử bấm từng câu cho tới khi tìm đúng.
    const nSent = doc.querySelectorAll('#read-passage .read-sentence').length;
    let found = false;
    for (let i = 0; i < nSent && !found; i++) {
      found = rt.pickSentence(i) === true;
    }
    ok(found, 'N95 bấm đúng câu lỗi thì tìm được lỗi');
    ok(doc.querySelectorAll('#read-fix .opt').length === 3, 'N96 tìm đúng lỗi thì hiện 3 lựa chọn sửa');
    // Thử từng lựa chọn sửa cho tới khi đúng.
    let fixed = false;
    for (let j = 0; j < 3 && !fixed; j++) {
      fixed = rt.pickFix(j) === true;
    }
    ok(fixed, 'N97 chọn đúng cách sửa thì sửa được lỗi');
    const qOpts = doc.querySelectorAll('#read-question .opt');
    ok(qOpts.length === 3, 'N98 sửa đúng thì hiện câu hỏi hiểu bài 3 lựa chọn');
    rt.pickQ(0);
    ok(/Điểm đoạn này/.test(doc.querySelector('#read-feedback').textContent), 'N99 trả lời xong hiện điểm đoạn');
    rt.next();
    ok(doc.querySelector('#read-card').style.display === 'block', 'N100 bấm Đoạn tiếp theo sang đoạn 2');
  }

  // ---------- Vòng một lỗi bốn kỹ năng: ôn Nghe xong đổi sang Viết ----------
  {
    const today = new Date();
    const iso = today.toISOString().slice(0, 10);
    const seed = { 'sdsc-progress-v1': JSON.stringify({ version: 1, updatedAt: '2026-11-19T00:00:00.000Z', lessons: { 'loi-001': { done: true, doneAt: iso } }, practice: {}, review: { 'loi-001': { interval: 1, nextDue: iso, ease: 2.5, reps: 0, skill: 'listen', skillStep: 0 } }, streak: { count: 1, lastDate: iso, dates: [iso] }, history: [], settings: { dailyGoal: 1, remindReview: true } }) };
    const { dom, jsErrors } = loadPage('luyen-nghe/index.html', seed, null, '?lesson=loi-001');
    const { window } = dom;
    const doc = window.document;
    ok(jsErrors.length === 0, 'N101 luyện nghe với ?lesson= không lỗi JS', jsErrors.slice(0, 2));
    ok(doc.querySelector('#listen-card').style.display === 'block', 'N102 ?lesson= tự bắt đầu buổi ôn bài đó');
    const lt = window.__listenTest;
    for (let round = 0; round < 6; round++) {
      const st = lt.state();
      if (st.mode === 'pick') lt.answerPick('right');
      else if (st.mode === 'choose') lt.answerChoose('0');
      else lt.answerType(st.pair.right);
      lt.next();
    }
    const prog = JSON.parse(window.localStorage.getItem('sdsc-progress-v1') || '{}');
    const rev = prog.review && prog.review['loi-001'];
    ok(rev && rev.skill === 'write', 'N103 ôn Nghe xong đổi kỹ năng thành Viết', rev);
    ok(rev && rev.skillStep === 1, 'N104 bước kỹ năng tăng lên 1', rev);
    const nextDue = rev && rev.nextDue;
    const expected = new Date(today.getTime() + 3 * 86400000).toISOString().slice(0, 10);
    ok(nextDue === expected, 'N105 lần ôn tới là hôm nay cộng 3 ngày', { got: nextDue, want: expected });
    ok(/ôn xong bằng Nghe/.test(doc.querySelector('#listen-done').textContent), 'N106 tổng kết ghi bài đã ôn xong bằng Nghe');
  }

  // ---------- Mục Cộng đồng nối API thật (19/11, fetch giả lập) ----------
  function makeCommFetch() {
    const calls = [];
    const boards = {
      weekly: { board: 'weekly', week: '2026-11-16', entries: [
        { account_id: 'acc-lan', display_name: 'Lan', level: 5, value: 320, cheers: 12, rank: 1 },
        { account_id: 'acc-bao', display_name: 'Bảo', level: 4, value: 280, cheers: 9, rank: 2 },
        { account_id: 'acc-chi', display_name: 'Chi', level: 4, value: 250, cheers: 11, rank: 3 },
      ], me: null, updated_at: '2026-11-19T00:00:00.000Z' },
      streak: { board: 'streak', week: '2026-11-16', entries: [
        { account_id: 'acc-bao', display_name: 'Bảo', level: 4, value: 12, cheers: 8, rank: 1 },
        { account_id: 'acc-lan', display_name: 'Lan', level: 5, value: 10, cheers: 6, rank: 2 },
      ], me: null, updated_at: '2026-11-19T00:00:00.000Z' },
      speaking: { board: 'speaking', week: '2026-11-16', entries: [
        { account_id: 'acc-chi', display_name: 'Chi', level: 4, value: 95, cheers: 10, rank: 1 },
        { account_id: 'acc-lan', display_name: 'Lan', level: 5, value: 92, cheers: 7, rank: 2 },
      ], me: null, updated_at: '2026-11-19T00:00:00.000Z' },
    };
    let token = null;
    const fetchStub = (url, init) => {
      const method = (init && init.method) || 'GET';
      let body = null;
      try { body = init && init.body ? JSON.parse(init.body) : null; } catch (e) {}
      calls.push({ url, method, body });
      const u = String(url);
      const respond = (status, data) => Promise.resolve({
        ok: status >= 200 && status < 300,
        status,
        text: () => Promise.resolve(JSON.stringify(data)),
      });
      if (u.includes('/api/leaderboard')) {
        const board = new URL(u).searchParams.get('board') || 'weekly';
        const data = JSON.parse(JSON.stringify(boards[board]));
        if (token) data.me = { rank: 2, value: board === 'weekly' ? 280 : 10 };
        return respond(200, data);
      }
      if (u.includes('/api/stats')) return respond(200, { accounts: 3, active_week: 2 });
      if (u.includes('/api/auth/send-code')) return respond(200, { ok: true });
      if (u.includes('/api/auth/verify')) {
        if (body && body.purpose === 'register') {
          token = 'tok-test-1234567890';
          return respond(200, { token, account: { id: 'acc-minh', display_name: 'Minh', level: 1, total_xp: 0, created_at: '2026-11-19' } });
        }
        return respond(200, { reset_token: 'reset-test-1234567890', email: body.email });
      }
      if (u.includes('/api/auth/login')) {
        token = 'tok-test-1234567890';
        return respond(200, { token, account: { id: 'acc-minh', display_name: 'Minh', level: 1, total_xp: 0, created_at: '2026-11-19' } });
      }
      if (u.includes('/api/auth/reset-password')) return respond(200, { ok: true });
      if (u.includes('/api/me')) {
        if (!token) return respond(401, { ok: false, error: 'Chưa đăng nhập.', code: 'unauthorized' });
        return respond(200, { account: { id: 'acc-minh', email: 'minh@example.com', display_name: 'Minh', level: 1, total_xp: 0, created_at: '2026-11-19', verified_at: '2026-11-19', hidden: false }, progress: null });
      }
      if (u.includes('/api/progress/sync')) {
        if (!body || !body.token) return respond(401, { ok: false, error: 'Chưa đăng nhập.', code: 'unauthorized' });
        return respond(200, { progress: body.progress });
      }
      if (u.includes('/api/cheer')) {
        const row = boards[body.board] && boards[body.board].entries.find(r => r.account_id === body.account_id);
        if (row) row.cheers += 1;
        return respond(200, { cheers: row ? row.cheers : 1 });
      }
      return respond(404, { ok: false, error: 'Không tìm thấy.', code: 'bad_request' });
    };
    fetchStub.calls = calls;
    return fetchStub;
  }
  {
    const stub = makeCommFetch();
    const { dom, jsErrors } = loadPage('cong-dong/index.html', null, w => { w.fetch = stub; });
    const { window } = dom;
    const doc = window.document;
    await window.__commTest.ready;
    await tick();
    ok(jsErrors.length === 0, 'N107 cộng đồng không lỗi JS', jsErrors.slice(0, 2));
    const xpRows = doc.querySelectorAll('#board-xp .comm-row');
    ok(xpRows.length === 3, 'N108 bảng Top XP tuần có 3 hàng từ API thật', xpRows.length);
    ok(/Lan/.test(xpRows[0].textContent) && /320 XP/.test(xpRows[0].textContent), 'N108b hàng đầu bảng XP là Lan 320 XP', xpRows[0] && xpRows[0].textContent);
    ok(doc.querySelectorAll('#board-streak .comm-row').length === 2, 'N109 bảng chuỗi ngày có 2 hàng từ API thật', doc.querySelectorAll('#board-streak .comm-row').length);
    ok(doc.querySelectorAll('#board-speak .comm-row').length === 2, 'N110 bảng điểm nói có 2 hàng từ API thật', doc.querySelectorAll('#board-speak .comm-row').length);
    ok(/Thử thách tuần/.test(doc.querySelector('#comm-challenge').textContent), 'N111 có thử thách tuần');
    ok(/Đăng nhập/.test(doc.querySelector('#comm-auth').textContent), 'N112 chưa đăng nhập thì hiện form đăng nhập');
    ok(!/bản thử/.test(doc.body.textContent), 'N113 trang không còn chữ bản thử');
    ok(!/123456/.test(doc.body.textContent), 'N113b trang không còn mã kích hoạt thử 123456');
    ok(!window.SDSC_COMM_MOCK, 'N113c không còn window.SDSC_COMM_MOCK');
    ok(/3 người đăng kí/.test(doc.querySelector('#comm-stats').textContent), 'N113d thống kê từ /api/stats', doc.querySelector('#comm-stats').textContent);
    ok(stub.calls.some(c => c.url.includes('/api/leaderboard?board=weekly')), 'N113e đã gọi GET /api/leaderboard?board=weekly');
    ok(stub.calls.some(c => c.url.includes('/api/stats')), 'N113f đã gọi GET /api/stats');
    // Quên mật khẩu: gửi mã rồi đặt mật khẩu mới.
    doc.querySelector('#comm-forgot-link').click();
    ok(doc.querySelector('#comm-reset').style.display === 'block', 'N114 quên mật khẩu hiện form đặt lại mật khẩu');
    doc.querySelector('#comm-reset-email').value = 'minh@example.com';
    doc.querySelector('#comm-reset-send').click();
    await tick(); await tick();
    ok(/Đã gửi mã/.test(doc.querySelector('#comm-reset-msg').textContent), 'N115 gửi mã đặt lại mật khẩu', doc.querySelector('#comm-reset-msg').textContent);
    doc.querySelector('#comm-reset-code').value = '654321';
    doc.querySelector('#comm-reset-pass').value = 'matkhau456';
    doc.querySelector('#comm-reset-btn').click();
    await tick(); await tick();
    ok(/Đã đặt mật khẩu mới/.test(doc.querySelector('#comm-reset-msg').textContent), 'N116 đặt mật khẩu mới xong', doc.querySelector('#comm-reset-msg').textContent);
    ok(stub.calls.some(c => c.url.includes('/api/auth/reset-password') && c.method === 'POST'), 'N116b đã gọi POST /api/auth/reset-password');
    // Đăng kí + kích hoạt bằng mã gửi qua mail (giả lập), rồi đăng nhập.
    doc.querySelector('#comm-show-register').click();
    doc.querySelector('#comm-reg-email').value = 'minh@example.com';
    doc.querySelector('#comm-reg-name').value = 'Minh';
    doc.querySelector('#comm-reg-pass').value = 'matkhau123';
    doc.querySelector('#comm-register-btn').click();
    await tick(); await tick();
    ok(doc.querySelector('#comm-activate').style.display === 'block', 'N118 đăng kí xong hiện bước nhập mã kích hoạt');
    ok(stub.calls.some(c => c.url.includes('/api/auth/send-code') && c.method === 'POST' && c.body && c.body.purpose === 'register'), 'N118b đã gọi POST /api/auth/send-code purpose register');
    doc.querySelector('#comm-code').value = '654321';
    doc.querySelector('#comm-activate-btn').click();
    for (let i = 0; i < 10; i++) await tick();
    const auth = JSON.parse(window.localStorage.getItem('sdsc-comm-auth-v1') || 'null');
    ok(auth && auth.email === 'minh@example.com' && auth.name === 'Minh' && auth.token === 'tok-test-1234567890', 'N119 kích hoạt mã thì đăng nhập được, token đã lưu', auth);
    ok(!window.localStorage.getItem('sdsc-comm-users-v1'), 'N119b không còn kho người dùng local sdsc-comm-users-v1');
    ok(/Xin chào/.test(doc.querySelector('#comm-auth').textContent), 'N120 sau khi đăng nhập hiện Xin chào');
    ok(/\(bạn\)/.test(doc.querySelector('#board-xp').textContent), 'N121 sau khi đăng nhập bảng có hàng của mình');
    ok(/Hạng 2/.test(doc.querySelector('#board-xp').textContent), 'N121b hàng của mình hiện hạng từ API thật');
    ok(/Đăng xuất/.test(doc.querySelector('#comm-auth').textContent), 'N122 có nút đăng xuất');
    ok(stub.calls.some(c => c.url.includes('/api/progress/sync') && c.method === 'POST'), 'N122b đã đồng bộ tiến trình sau khi đăng nhập');
    // Tim 1 người ở 1 bảng (đã đăng nhập).
    const heart = doc.querySelector('#board-xp .comm-heart');
    ok(!!heart, 'N114 mỗi hàng có nút tim');
    heart.click();
    await tick(); await tick();
    const hearts = JSON.parse(window.localStorage.getItem('sdsc-comm-hearts-v1') || '[]');
    ok(hearts.length === 1, 'N115 bấm tim lưu 1 lượt tim', hearts);
    ok(stub.calls.some(c => c.url.includes('/api/cheer') && c.method === 'POST' && c.body && c.body.account_id === 'acc-lan' && c.body.board === 'weekly'), 'N115b đã gọi POST /api/cheer cho Lan ở bảng weekly');
    const heart2 = doc.querySelector('#board-xp .comm-heart');
    ok(/♥ 13/.test(heart2.textContent), 'N116 sau khi tim thì nút hiện tim đỏ và số tim từ máy chủ', heart2.textContent);
    heart2.click();
    await tick();
    const hearts2 = JSON.parse(window.localStorage.getItem('sdsc-comm-hearts-v1') || '[]');
    ok(hearts2.length === 1, 'N117 bấm lại thì không tim thêm lần nữa', hearts2);
    ok(stub.calls.filter(c => c.url.includes('/api/cheer')).length === 1, 'N117b bấm lại không gọi thêm /api/cheer');
    ok(/đã tặng tim/.test(doc.querySelector('#board-xp').textContent), 'N117c bấm lại hiện thông báo đã tặng tim');
    // Thẻ Đua top trên trang chủ (dùng fetch giả lập riêng).
    const stub2 = makeCommFetch();
    const home = loadPage('index.html', null, w => { w.fetch = stub2; });
    const hdoc = home.dom.window.document;
    await home.dom.window.__commTest.ready;
    await tick();
    ok(/Đua top tuần này/.test(hdoc.querySelector('#comm-teaser').textContent), 'N123 trang chủ có thẻ Đua top tuần này');
    ok(/Lan/.test(hdoc.querySelector('#comm-teaser').textContent) && /320 XP/.test(hdoc.querySelector('#comm-teaser').textContent), 'N123b thẻ Đua top hiện top 1 từ API thật', hdoc.querySelector('#comm-teaser').textContent);
    ok(/Xem bảng đầy đủ/.test(hdoc.querySelector('#comm-teaser').textContent), 'N124 thẻ Đua top có nút xem bảng đầy đủ');
    ok(hdoc.querySelector('#comm-teaser a').getAttribute('href') === '/sai-dau-sua-do/cong-dong/', 'N125 thẻ Đua top link tới trang Cộng đồng');
  }

  console.log(`\nKẾT QUẢ TRANG MỚI: ${pass} pass, ${fail} fail`);
  process.exit(fail ? 1 : 0);
})();
