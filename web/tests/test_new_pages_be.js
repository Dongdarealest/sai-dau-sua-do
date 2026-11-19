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

function loadPage(file, seedStorage, before) {
  const vc = new VirtualConsole();
  const jsErrors = [];
  vc.on('jsdomError', e => jsErrors.push('jsdomError: ' + (e.detail && e.detail.stack || e.message)));
  vc.on('error', (...a) => jsErrors.push('console.error: ' + a.join(' ')));
  const html = fs.readFileSync(path.join(WEB, file), 'utf8');
  // Tối ưu A (19/11): app.js/data.js là file ngoài, jsdom không tự nạp
  // <script src> nên nội tuyến chúng vào HTML trước khi dựng DOM.
  let htmlInlined = html;
  for (const f of ['data.js', 'app.js']) {
    const tag = `<script src="/sai-dau-sua-do/${f}"></script>`;
    if (htmlInlined.includes(tag)) {
      const body = fs.readFileSync(path.join(WEB, f), 'utf8');
      htmlInlined = htmlInlined.replace(tag, () => `<script>\n${body}\n</script>`);
    }
  }
  const dom = new JSDOM(htmlInlined, {
    url: 'https://example.org/' + file,
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
    const nav = [...doc.querySelectorAll('.sitenav a')].map(a => a.getAttribute('href'));
    ok(nav.includes('/sai-dau-sua-do/tu-dien/') && nav.includes('/sai-dau-sua-do/luyen-noi/'), 'N9 thanh điều hướng có đủ 4 trang mới');
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

  // ---------- Luyện nói ----------
  {
    const { dom, jsErrors } = loadPage('luyen-noi/index.html');
    const { window } = dom;
    const doc = window.document;
    ok(jsErrors.length === 0, 'N28 luyện nói không lỗi JS', jsErrors.slice(0, 2));
    const sel = doc.querySelector('#speak-pick');
    ok(sel && sel.options.length > 50, 'N29 có hơn 50 câu mẫu để chọn', sel && sel.options.length);
    ok(doc.querySelector('#speak-target').textContent.length > 3, 'N30 câu mẫu đầu đã hiện');
    ok(doc.querySelector('#speak-nosupport').style.display === 'block', 'N31 trình duyệt không hỗ trợ thì hiện câu báo rõ');
    ok(doc.querySelector('#speak-start').disabled === true, 'N32 nút Bắt đầu nói bị khóa khi không hỗ trợ');
    ok(/chưa hỗ trợ nhận diện/.test(doc.querySelector('#speak-status').textContent), 'N33 trạng thái báo chưa hỗ trợ', doc.querySelector('#speak-status').textContent);
    ok(/chưa chấm được từng âm/.test(doc.body.textContent), 'N34 trang ghi rõ giới hạn không chấm từng âm');
  }

  console.log(`\nKẾT QUẢ TRANG MỚI: ${pass} pass, ${fail} fail`);
  process.exit(fail ? 1 : 0);
})();
