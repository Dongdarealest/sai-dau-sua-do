// Kiểm thử độc lập nhóm B–E cho đợt nâng cấp web Sai Đâu Sửa Đó.
// B: chấm điểm/wizard · C: tiến độ/SRS · D: xuất/nhập · E: tìm kiếm.
// Chạy: cd web/tests && npm install jsdom --no-save && node test_browser_be.js
// (node_modules chỉ dùng để test, KHÔNG nằm trong danh sách deploy)
const fs = require('fs');
const path = require('path');
const { JSDOM, VirtualConsole } = require('jsdom');

const WEB = path.join(__dirname, '..'); // chạy từ web/tests/
let pass = 0, fail = 0;
function ok(cond, name, extra) {
  if (cond) { pass++; console.log('PASS', name); }
  else { fail++; console.log('FAIL', name, extra === undefined ? '' : '=> ' + JSON.stringify(extra)); }
}
function eq(a, b, name) { ok(a === b, name, { got: a, want: b }); }

const vc = new VirtualConsole();
const jsErrors = [];
vc.on('jsdomError', e => jsErrors.push('jsdomError: ' + (e.detail && e.detail.stack || e.message)));
vc.on('error', (...a) => jsErrors.push('console.error: ' + a.join(' ')));

function loadPage(file, seedStorage, query) {
  // Tối ưu A (19/11): app.js/data.js là file ngoài, jsdom không tự nạp
  // <script src> nên nội tuyến chúng vào HTML trước khi dựng DOM.
  let html = fs.readFileSync(path.join(WEB, file), 'utf8');
  for (const f of ['data.js', 'app.js']) {
    const tag = `<script src="/sai-dau-sua-do/${f}"></script>`;
    if (html.includes(tag)) {
      const body = fs.readFileSync(path.join(WEB, f), 'utf8');
      html = html.replace(tag, () => `<script>\n${body}\n</script>`);
    }
  }
  const dom = new JSDOM(html, {
    url: 'https://example.org/' + file + (query || ''),
    runScripts: 'dangerously',
    pretendToBeVisual: true,
    virtualConsole: vc,
    beforeParse(window) {
      window.matchMedia = () => ({ matches: false, addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {} });
      window.scrollTo = () => {};
      window.URL.createObjectURL = (blob) => { window.__lastBlob = blob; return 'blob:fake'; };
      window.URL.revokeObjectURL = () => {};
      window.speechSynthesis = { getVoices: () => [], speak() {}, cancel() {}, onvoiceschanged: null };
      window.SpeechSynthesisUtterance = function () {};
      // Tìm kiếm nạp lười: search-index.json đọc từ đĩa.
      window.fetch = (url) => {
        if (String(url).includes('search-index.json')) {
          return Promise.resolve({ ok: true, json: () => Promise.resolve(JSON.parse(fs.readFileSync(path.join(WEB, 'search-index.json'), 'utf8'))) });
        }
        return Promise.reject(new Error('fetch không stub: ' + url));
      };
      if (seedStorage) for (const [k, v] of Object.entries(seedStorage)) window.localStorage.setItem(k, v);
    },
  });
  return dom;
}
function dumpStorage(win) {
  const out = {};
  for (let i = 0; i < win.localStorage.length; i++) {
    const k = win.localStorage.key(i);
    out[k] = win.localStorage.getItem(k);
  }
  return out;
}

// ---------- B: wizard + chấm điểm ----------
{
  const dom = loadPage('loi-001/index.html');
  const { window } = dom;
  const steps = window.document.querySelectorAll('.wstep');
  ok(steps.length === 7, 'B1 loi-001 có 7 bước', steps.length);
  ok(!steps[0].hidden && steps[1].hidden, 'B1 bước đầu hiện, các bước sau ẩn');
  window.showStep(3);
  ok(steps[3].hidden === false && steps[0].hidden === true, 'B2 showStep(3) chuyển bước');
  window.showStep(6);
  const bar = window.document.querySelector('.progress-fill, .wfill, [class*=fill]');
  ok(steps[6].hidden === false, 'B3 showStep(6) tới bước hoàn thành');
  // chấm điểm: lấy widget đầu tiên có data-answer
  const box = window.document.querySelector('[data-answer]');
  ok(!!box, 'B4 tìm được widget chấm điểm');
  const answer = parseInt(box.dataset.answer, 10);
  const opts = box.querySelectorAll('.opt');
  ok(opts.length >= 2, 'B5 widget có >=2 lựa chọn', opts.length);
  // chọn SAI trước
  const wrongIdx = answer === 0 ? 1 : 0;
  window.gradeWidget(box, wrongIdx);
  const res = box.querySelector('.grade-result');
  ok(res && /sai|chưa đúng/i.test(res.textContent), 'B6 chọn sai hiện "Sai/Chưa đúng"', res && res.textContent.slice(0, 80));
  ok(res && res.textContent.length > 10, 'B6b phản hồi sai có giải thích');
  ok([...opts[wrongIdx].classList].some(c => /wrong/.test(c)), 'B7 lựa chọn sai bị tô đỏ');
  const saved = JSON.parse(window.localStorage.getItem('sdsc-progress-v1'));
  ok(saved && saved.practice && saved.practice[box.dataset.key] && saved.practice[box.dataset.key].correct === false, 'B8 chọn sai được lưu {correct:false}');
  // chọn ĐÚNG trên widget khác (nếu có) hoặc cùng widget sau khi làm lại
  const boxes = [...window.document.querySelectorAll('[data-answer]')];
  const box2 = boxes[1] || box;
  const a2 = parseInt(box2.dataset.answer, 10);
  window.gradeWidget(box2, a2);
  const r2 = box2.querySelector('.grade-result');
  ok(r2 && /đúng/i.test(r2.textContent), 'B9 chọn đúng hiện "Đúng"');
  const saved2 = JSON.parse(window.localStorage.getItem('sdsc-progress-v1'));
  ok(saved2.practice[box2.dataset.key].correct === true && saved2.practice[box2.dataset.key].choice === a2, 'B10 lựa chọn đúng được lưu {choice, correct}');
  // tải lại: restoreGrade tô lại lựa chọn đã lưu
  const dom2 = loadPage('loi-001/index.html', dumpStorage(window));
  const boxR = dom2.window.document.querySelector(`[data-key="${box.dataset.key}"]`);
  ok(!!boxR, 'B11 tìm lại widget sau tải lại');
  const optsR = boxR.querySelectorAll('.opt');
  ok([...optsR[answer].classList].some(c => /correct/.test(c)), 'B12 sau tải lại, đáp án đúng được tô xanh');
  ok(optsR[wrongIdx].disabled === true, 'B13 sau tải lại, các lựa chọn bị khóa');
  // điểm theo bài: practiceTotalsFor
  const t = dom2.window.practiceTotalsFor ? dom2.window.practiceTotalsFor('loi-001') : null;
  ok(t && t.total >= 2, 'B14 practiceTotalsFor(loi-001) đếm được câu của bài', t);
}

// ---------- B: word_order ----------
{
  const dom = loadPage('loi-003/index.html');
  const { window } = dom;
  const wo = window.document.querySelector('.grade-wo, [data-kind="word_order"], .wo-box');
  if (!wo) { console.log('SKIP B-wo: không tìm thấy widget word_order trên loi-003'); }
  else {
    const chips = wo.querySelectorAll('.wo-chip, .chip');
    ok(chips.length >= 3, 'B15 word_order có chip để xếp', chips.length);
    // bấm chip theo đúng đáp án
    const ans = JSON.parse(wo.dataset.answer || '[]');
    const opts = JSON.parse(wo.dataset.options || '[]');
    ok(Array.isArray(ans) && ans.length >= 3, 'B16 word_order có mảng answer', ans);
    // xếp đúng thứ tự
    ans.forEach(i => { const chip = [...wo.querySelectorAll('.wo-chip, .chip')].find(c => c.textContent.trim() === String(opts[i]).trim() && !c.disabled); if (chip) chip.click(); });
    const check = wo.querySelector('.wo-check');
    if (check) check.click();
    const res = wo.querySelector('.grade-result');
    ok(res && /đúng/i.test(res.textContent), 'B17 xếp đúng thứ tự hiện "Đúng"', res && res.textContent.slice(0, 80));
  }
}

// ---------- C: SRS ----------
{
  const dom = loadPage('loi-001/index.html');
  const { window } = dom;
  const today = window.todayISO();
  const r0 = window.srsNew(today);
  eq(r0.interval, 1, 'C1 srsNew interval=1');
  eq(r0.ease, 2.5, 'C1 srsNew ease=2.5');
  eq(r0.reps, 0, 'C1 srsNew reps=0');
  // kho: interval về 1, ease giảm, reps 0
  const rk = window.srsUpdate({ interval: 7, ease: 2.5, reps: 5, nextDue: today }, 'kho', today);
  eq(rk.interval, 1, 'C2 kho -> interval=1');
  eq(rk.ease, 2.3, 'C2 kho -> ease 2.5-0.2');
  eq(rk.reps, 0, 'C2 kho -> reps=0');
  // de: interval giãn, ease tăng (capped 2.5)
  const rd = window.srsUpdate({ interval: 1, ease: 2.5, reps: 0, nextDue: today }, 'de', today);
  eq(rd.interval, 3, 'C3 de từ 1 -> round(1*2.5*1.3)=3');
  eq(rd.ease, 2.5, 'C3 de ease capped 2.5');
  eq(rd.reps, 1, 'C3 de reps+1');
  // vua: interval round(3*2.5)=8? kiểm tra công thức chung
  const rv = window.srsUpdate({ interval: 3, ease: 2.5, reps: 1, nextDue: today }, 'vua', today);
  eq(rv.interval, 8, 'C4 vua 3 -> round(3*2.5)=8');
  eq(rv.ease, 2.5, 'C4 vua không đổi ease');
  // trần 60 ngày + sàn ease 1.3
  const rc = window.srsUpdate({ interval: 60, ease: 2.5, reps: 9, nextDue: today }, 'de', today);
  eq(rc.interval, 60, 'C5 interval trần 60');
  let e = { interval: 1, ease: 1.3, reps: 0, nextDue: today };
  e = window.srsUpdate(e, 'kho', today);
  eq(e.ease, 1.3, 'C5 ease sàn 1.3');
  // nextDue = today + interval
  eq(rd.nextDue, window.addDays(today, 3), 'C6 nextDue = today + interval');
  // migrate từ key cũ
  const domM = loadPage('loi-001/index.html', {
    'sdsc-done-v2': JSON.stringify({ 'loi-001': '2026-11-14', 'loi-002': '2026-11-13' }),
    'sdsc-practice-v2': JSON.stringify({ 'loi-001:0': true, 'loi-001:1': false }),
    'sdsc-streak-v1': JSON.stringify({ streak: 2, last: '2026-11-14' }),
  });
  const p = domM.window.getProgress();
  ok(p.lessons['loi-001'] && p.lessons['loi-001'].done === true, 'C7 migrate: bài done cũ được giữ');
  ok(p.review['loi-001'] && p.review['loi-001'].interval === 1, 'C8 migrate: bài done cũ có SRS interval=1', p.review['loi-001']);
  ok(p.practice['loi-001:0'] && p.practice['loi-001:0'].correct === true, 'C9 migrate: practice boolean -> {correct}');
  ok(p.streak && p.streak.count === 2 && p.streak.lastDate === '2026-11-14', 'C10 migrate: streak cũ {streak,last} được giữ', p.streak);
  // tự đánh giá qua recordSelfGrade
  const domG = loadPage('loi-001/index.html');
  domG.window.markDone();
  domG.window.recordSelfGrade('de');
  const pg = domG.window.getProgress();
  ok(pg.lessons['loi-001'].selfGrade === 'de', 'C11 recordSelfGrade lưu selfGrade=de');
  ok(pg.review['loi-001'] && pg.review['loi-001'].interval === 3, 'C12 recordSelfGrade tạo SRS interval=3 (de từ 1)', pg.review['loi-001']);
}

// ---------- D: xuất/nhập ----------
{
  const dom = loadPage('index.html');
  const { window } = dom;
  const todayD = window.todayISO();
  const yday = window.addDays(todayD, -1);
  const mkGood = (interval, nextDue) => ({
    app: 'sai-dau-sua-do', kind: 'progress-export', version: 1,
    exportedAt: todayD + 'T00:00:00+07:00',
    data: {
      version: 1, updatedAt: todayD + 'T00:00:00+07:00',
      lessons: { 'loi-001': { done: true, doneAt: yday, lastStudiedAt: yday, selfGrade: 'de', reviews: 1 } },
      practice: { 'loi-001:0': { choice: 1, correct: true, attempts: 1, lastAt: yday } },
      streak: { count: 2, lastDate: yday, dates: [window.addDays(todayD, -2), yday] },
      review: { 'loi-001': { interval, nextDue, ease: 2.5, reps: 1 } },
      history: [], settings: {},
    },
  });
  const good = mkGood(1, window.addDays(todayD, 1));
  const v = window.validateImportFile(JSON.stringify(good));
  ok(v.ok === true, 'D1 file hợp lệ validate OK', v);
  // vòng tròn xuất->nhập: bài Dễ (interval 3, nextDue +3 ngày) phải nhập lại được
  const good3 = mkGood(3, window.addDays(todayD, 3));
  const v3 = window.validateImportFile(JSON.stringify(good3));
  ok(v3.ok === true, 'D1b file có nextDue +3 ngày (interval 3) validate OK', v3);
  const good60 = mkGood(60, window.addDays(todayD, 60));
  ok(window.validateImportFile(JSON.stringify(good60)).ok === true, 'D1c nextDue +60 ngày (trần interval) validate OK');
  const bad61 = mkGood(60, window.addDays(todayD, 61));
  const v61 = window.validateImportFile(JSON.stringify(bad61));
  ok(v61.ok === false && /quá xa|60 ngày/i.test(v61.error || ''), 'D1d nextDue +61 ngày bị từ chối', v61);
  const badCases = [
    ['không phải JSON', '{oops', /JSON/],
    ['sai app', JSON.stringify({ ...good, app: 'khac' }), /không phải file tiến độ/],
    ['version mới', JSON.stringify({ ...good, data: { ...good.data, version: 99 } }), /phiên bản|version/i],
    ['slug ký tự lạ', JSON.stringify({ ...good, data: { ...good.data, lessons: { 'Bai_X': { done: true } } } }), /không có trên trang|slug/i],
    ['ngày 2026-02-30', JSON.stringify({ ...good, data: { ...good.data, lessons: { 'loi-001': { done: true, doneAt: '2026-02-30' } } } }), /ngày|không hợp lệ/i],
    ['interval 90', JSON.stringify({ ...good, data: { ...good.data, review: { 'loi-001': { interval: 90, nextDue: window.addDays(todayD, 1), ease: 2.5, reps: 1 } } } }), /interval|1.*60|60/i],
  ];
  for (const [name, text, re] of badCases) {
    const r = window.validateImportFile(text);
    ok(r.ok === false && re.test(r.error || ''), 'D2 từ chối: ' + name, r);
  }
  // nhập hỏng không ghi gì (atomic)
  const before = window.localStorage.getItem('sdsc-progress-v1');
  const rBad = window.importProgressText('{oops', 'merge');
  ok(rBad.ok === false, 'D3 import file hỏng trả lỗi');
  eq(window.localStorage.getItem('sdsc-progress-v1'), before, 'D3b import hỏng không ghi gì');
  // nhập tốt: gộp
  const rGood = window.importProgressText(JSON.stringify(good), 'merge');
  ok(rGood.ok === true, 'D4 import file tốt OK', rGood);
  const p = window.getProgress();
  ok(p.lessons['loi-001'] && p.lessons['loi-001'].done === true, 'D5 sau import, bài loi-001 done=true');
  ok(p.review && p.review['loi-001'] && p.review['loi-001'].interval === 1, 'D6 sau import, SRS interval=1 (theo file đã nhập)', p.review['loi-001']);
  // export: exportProgress tạo blob JSON hợp lệ (đọc async ở cuối file)
  const exp = window.exportProgress ? window.exportProgress() : false;
  ok(exp === true, 'D7 exportProgress chạy OK (trả true)');
  ok(!!window.__lastBlob, 'D7b export tạo blob tải về');
  global.__blobTextP = window.__lastBlob ? window.__lastBlob.text() : Promise.resolve(null);
}

// ---------- E: tìm kiếm ----------
{
  const dom = loadPage('index.html');
  const { window } = dom;
  eq(window.sdscNorm('mượn'), 'muon', 'E1 sdscNorm bỏ dấu: mượn -> muon');
  eq(window.sdscNorm('Đà Nẵng'), 'da nang', 'E1b sdscNorm đ -> d');
  const lessons = window.SDSC_LESSONS || {};
  const l1 = lessons['loi-001'];
  ok(!!l1, 'E2 có SDSC_LESSONS loi-001');
  const s1 = window.sdscScore(l1, ['muon']);
  ok(s1 > 0, 'E3 tìm "muon" (không dấu) trúng loi-001', s1);
  const s0 = window.sdscScore(l1, ['zzqqxx']);
  eq(s0, 0, 'E4 từ vô nghĩa cho 0 điểm');
  const tokens = window.sdscTokens ? window.sdscTokens('Mượn TIỀN') : ['muon', 'tien'];
  const sT = window.sdscScore(l1, tokens);
  ok(sT >= s1, 'E5 nhiều từ khóa không giảm điểm', sT);
  // E6: ?q=muon — chỉ mục nạp lười nên phần lọc chạy sau khi fetch xong,
  // kiểm tra ở cuối file trong khối async. Ở đây chỉ kiểm tra ô tìm kiếm
  // đồng bộ từ URL ngay khi tải.
  const domQ0 = loadPage('index.html', null, '?q=muon');
  const input0 = domQ0.window.document.querySelector('#search');
  if (input0) {
    eq(input0.value, 'muon', 'E6c ô tìm kiếm đồng bộ từ URL');
  } else console.log('SKIP E6: không có #search');
}

// ---------- lỗi JS khi tải ----------
ok(jsErrors.length === 0, 'Z0 không có lỗi JS khi tải trang (jsdomError/console.error)', jsErrors.slice(0, 3));

(async () => {
  // E6: lọc "muon" qua ?q= sau khi chỉ mục tìm kiếm nạp xong (nạp lười).
  {
    const domQ = loadPage('index.html', null, '?q=muon');
    await new Promise(r => setTimeout(r, 100));
    const input = domQ.window.document.querySelector('#search');
    if (input) {
      const cards = [...domQ.window.document.querySelectorAll('#cards .card')];
      const visible = cards.filter(r => r.style.display !== 'none' && !r.hidden);
      const countTxt = domQ.window.document.querySelector('#count') ? domQ.window.document.querySelector('#count').textContent : '';
      // Kỳ vọng theo dữ liệu thật: số bài trong chỉ mục tìm kiếm mà hàm chấm của trang cho điểm với từ khóa "muon"
      const idx = domQ.window.eval('typeof SDSC_INDEX!=="undefined"?SDSC_INDEX:[]');
      const expected = idx.filter(l => domQ.window.sdscScore(l, ['muon']) > 0).length;
      ok(visible.length === expected && expected >= 1, 'E6 lọc "muon" qua ?q= thu hẹp đúng số thẻ khớp dữ liệu', { visible: visible.length, expected, total: cards.length });
      ok(/Tìm thấy/.test(countTxt), 'E6b dòng đếm báo "Tìm thấy N bài"', countTxt);
    } else console.log('SKIP E6: không có #search');
  }
  if (global.__blobTextP) {
    try {
      const t = await global.__blobTextP;
      const env = JSON.parse(t);
      ok(env.app === 'sai-dau-sua-do' && env.kind === 'progress-export' && env.data && env.data.version === 1, 'D7c blob export là envelope tiến độ hợp lệ', env && { app: env.app, kind: env.kind });
      // vòng tròn thật: file vừa export phải validate OK
      const domX = loadPage('index.html');
      const vx = domX.window.validateImportFile(t);
      ok(vx.ok === true, 'D7d file vừa export nhập lại được (round-trip)', vx);
    } catch (e) { ok(false, 'D7c đọc blob export', String(e)); }
  }
  console.log(`\nKẾT QUẢ: ${pass} pass, ${fail} fail`);
  process.exit(fail ? 1 : 0);
})();
