#!/usr/bin/env python3
"""Kiểm thử sinh trang — Nhóm A trong AUDIT-KYTHUAT §2.5 (điều chỉnh:
A3 theo khuôn wizard mới 7 bước Lỗi/Mẫu câu / 4 bước Quiz;
A12 theo deploy đã sửa S-05 — README lấy từ đĩa, không ghi đè bằng hằng).

Chạy:  python3 -m unittest discover -s tests -v   (từ thư mục web/)
"""
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import generate_site as gen  # noqa: E402


def load_data():
    return json.loads((ROOT / "lessons.json").read_text(encoding="utf-8"))


def visible():
    return gen.visible_lessons(load_data())


class _Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        if data.strip():
            self.parts.append(data.strip())


def visible_text(path):
    p = _Text()
    p.feed(Path(path).read_text(encoding="utf-8"))
    return " ".join(p.parts)


def sentences(text):
    out = []
    for s in re.split(r"(?<=[.!?])\s+", text):
        w = re.sub(r"\s+", " ", s.strip().lower())
        if len(w.split()) >= 4:
            out.append(w)
    return out


class TestPagesExist(unittest.TestCase):
    def test_a1_every_visible_lesson_has_page(self):
        """A1: 9 bài visible -> 9 thư mục */index.html."""
        for lesson in visible():
            page = ROOT / lesson["slug"] / "index.html"
            self.assertTrue(page.exists(), f"thiếu trang {page}")

    def test_a2_stale_page_removed_after_unpublish(self):
        """A2: gỡ loi-002 khỏi data -> chạy main() -> trang loi-002 biến mất,
        các trang lộ trình không còn link tới nó."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            shutil.copytree(ROOT, tmp / "web",
                            ignore=shutil.ignore_patterns("__pycache__", "tests", "_archive", "shots", "backup"))
            # Ảnh nguồn phải nằm NGOÀI thư mục images/ đích (main() xóa images/
            # trước khi đọc ảnh — H-05), nên copy sang src-images/ riêng.
            (tmp / "src-images").mkdir()
            for img in (tmp / "web" / "images").glob("*.jpg"):
                shutil.copy(img, tmp / "src-images" / img.name)
            data = json.loads((tmp / "web" / "lessons.json").read_text(encoding="utf-8"))
            for lesson in data["lessons"]:
                cand = f"src-images/{lesson['slug']}.jpg"
                lesson["image_src"] = cand if (tmp / cand).exists() else "src-images/loi-001.jpg"
            data["lessons"] = [l for l in data["lessons"] if l["slug"] != "loi-002"]
            (tmp / "web" / "lessons.json").write_text(
                json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "gen_under_test", tmp / "web" / "generate_site.py")
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            mod.main()
            self.assertFalse((tmp / "web" / "loi-002" / "index.html").exists(),
                             "trang loi-002 vẫn còn sau khi gỡ bài")
            for path_page in (tmp / "web" / "lo-trinh").glob("*/index.html"):
                self.assertNotIn("/loi-002/", path_page.read_text(encoding="utf-8"),
                                 f"{path_page} vẫn link tới loi-002")


class TestWizardShape(unittest.TestCase):
    def test_a3_wizard_step_counts(self):
        """A3 (điều chỉnh): Lỗi/Mẫu câu = 7 .wstep, Quiz = 4 .wstep,
        đúng 1 bước data-action='done' mỗi trang."""
        for lesson in visible():
            html = (ROOT / lesson["slug"] / "index.html").read_text(encoding="utf-8")
            n = html.count('class="wstep"')
            expected = 4 if lesson["type"] == "Quiz" else 7
            self.assertEqual(n, expected,
                             f"{lesson['slug']}: {n} bước, kỳ vọng {expected}")
            self.assertEqual(html.count('data-action="done"'), 1,
                             f"{lesson['slug']}: phải có đúng 1 bước done")

    def test_word_order_widgets_present(self):
        """Số câu word_order trong dữ liệu -> đúng từng đó widget .grade-wo trên các trang."""
        total = 0
        for lesson in visible():
            html = (ROOT / lesson["slug"] / "index.html").read_text(encoding="utf-8")
            total += html.count('class="grade-wo"')
            n_wo = sum(1 for p in lesson.get("practice", []) if p.get("kind") == "word_order")
            self.assertEqual(html.count('class="grade-wo"'), n_wo, lesson["slug"])
        expected = sum(1 for l in visible() for p in l.get("practice", []) if p.get("kind") == "word_order")
        self.assertEqual(total, expected, f"tổng widget word_order = {total}, kỳ vọng {expected}")


class TestContent(unittest.TestCase):
    def test_a4_no_duplicate_sentence_per_page(self):
        """A4: mọi câu >= 4 từ trong văn bản hiển thị mỗi trang bài <= 1 lần."""
        for lesson in visible():
            text = visible_text(ROOT / lesson["slug"] / "index.html")
            counts = {}
            for s in sentences(text):
                counts[s] = counts.get(s, 0) + 1
            dups = {k: v for k, v in counts.items() if v > 1}
            self.assertEqual(dups, {}, f"{lesson['slug']}: câu lặp {dups}")

    def test_a5_images_exist_and_jpeg(self):
        """A5: mỗi image_src -> images/<slug>.jpg tồn tại, header JPEG, <= 200 KB."""
        for lesson in visible():
            img = ROOT / "images" / f"{lesson['slug']}.jpg"
            self.assertTrue(img.exists(), f"thiếu ảnh {img}")
            head = img.read_bytes()[:3]
            self.assertEqual(head, b"\xff\xd8\xff", f"{img} không phải JPEG")
            self.assertLessEqual(img.stat().st_size, 200 * 1024,
                                 f"{img} > 200 KB")

    def test_a6_lessons_json_valid(self):
        """A6: validate_lessons(data) không lỗi; why <= 2 câu (kể cả viết tắt)."""
        errors = gen.validate_lessons(load_data(), gen.WS)
        self.assertEqual(errors, [], f"validate lỗi: {errors}")
        self.assertEqual(gen.count_sentences_why("a hay an dựa vào âm đầu, vd. university đọc là /juː/. Không dựa vào chữ cái."), 2)
        self.assertEqual(gen.count_sentences_why("Câu một. Câu hai. Câu ba."), 3)

    def test_a6b_bad_practice_answer_rejected(self):
        data = load_data()
        data["lessons"][0]["practice"][0]["answer"] = 99
        errors = gen.validate_lessons(data, gen.WS)
        self.assertTrue(any("answer ngoài khoảng" in e for e in errors),
                        f"answer=99 phải bị bắt, nhận: {errors}")

    def test_a7_og_tags_complete(self):
        """A7: mỗi trang bài có og:title/description (<=220 ký tự)/url/image đúng ảnh."""
        for lesson in visible():
            html = (ROOT / lesson["slug"] / "index.html").read_text(encoding="utf-8")
            for tag in ["og:title", "og:description", "og:url", "og:image"]:
                self.assertIn(f'property="{tag}"', html, f"{lesson['slug']}: thiếu {tag}")
            m = re.search(r'property="og:description" content="([^"]*)"', html)
            self.assertIsNotNone(m, lesson["slug"])
            self.assertLessEqual(len(m.group(1)), 220, lesson["slug"])
            self.assertIn(f"/images/{lesson['slug']}.jpg", html, lesson["slug"])

    def test_a8_no_dead_internal_links(self):
        """A8: mọi href nội bộ /sai-dau-sua-do/... trỏ tới file tồn tại trên đĩa."""
        pages = [ROOT / "index.html"]
        pages += [ROOT / l["slug"] / "index.html" for l in visible()]
        pages += list((ROOT / "lo-trinh").glob("*/index.html"))
        for page in pages:
            html = page.read_text(encoding="utf-8")
            for href in re.findall(r'href="(/sai-dau-sua-do/[^"]*)"', html):
                rel = href[len("/sai-dau-sua-do/"):]
                target = ROOT / rel if not rel.endswith("/") else ROOT / rel / "index.html"
                if rel == "":
                    target = ROOT / "index.html"
                self.assertTrue(target.exists(), f"{page.name}: link chết {href}")

    def test_a9_no_font_size_below_16(self):
        """A9: mọi font-size trong CSS sinh ra và HTML sinh ra đều >= 16px."""
        for size in re.findall(r"font-size:\s*([\d.]+)px", gen.CSS):
            self.assertGreaterEqual(float(size), 16, f"CSS có font-size {size}px")
        pages = [ROOT / "index.html"] + [ROOT / l["slug"] / "index.html" for l in visible()]
        for page in pages:
            html = page.read_text(encoding="utf-8")
            for size in re.findall(r"font-size:\s*([\d.]+)px", html):
                self.assertGreaterEqual(float(size), 16,
                                        f"{page.name}: font-size {size}px")

    def test_a10_no_empty_links_or_handlers(self):
        """A10: không có href='#', href='', onclick=''."""
        pages = [ROOT / "index.html"] + [ROOT / l["slug"] / "index.html" for l in visible()]
        pages += list((ROOT / "lo-trinh").glob("*/index.html"))
        for page in pages:
            html = page.read_text(encoding="utf-8")
            self.assertNotIn('href="#"', html, page.name)
            self.assertNotIn('href=""', html, page.name)
            self.assertNotIn('onclick=""', html, page.name)

    def test_a11_readme_counts(self):
        """A11: README sinh ra chứa đúng số liệu theo dữ liệu hiện tại."""
        data = load_data()
        readme = gen.render_readme(data)
        self.assertIn(f"{len(visible())} bài học", readme)
        self.assertIn(f"{len(data['site']['paths'])} lộ trình", readme)
        self.assertIn(f"{len(data['lessons']) - len(visible())} Reel", readme)


class TestNewPages(unittest.TestCase):
    """Trang mới kiểu app PeakFour: từ điển, bảng lộ trình, thư viện chủ đề, luyện nói."""
    NEW_PAGES = ("tu-dien", "bang-lo-trinh", "thu-vien-chu-de", "luyen-noi")

    def test_new_pages_exist(self):
        for slug in self.NEW_PAGES:
            self.assertTrue((ROOT / slug / "index.html").exists(), f"thiếu trang {slug}")

    def test_new_pages_linked_from_index(self):
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        for slug in self.NEW_PAGES:
            self.assertIn(f"/{slug}/", index, f"trang chủ chưa nối tới {slug}")

    def test_new_pages_in_sitemap(self):
        sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
        for slug in self.NEW_PAGES:
            self.assertIn(f"/{slug}/", sitemap, f"sitemap thiếu {slug}")

    def test_chunk_json_on_lesson_pages(self):
        """Mỗi trang bài có khối chunk JSON, mỗi cụm đúng 1 câu."""
        for lesson in visible():
            html = (ROOT / lesson["slug"] / "index.html").read_text(encoding="utf-8")
            m = re.search(r'<script type="application/json" id="chunk-data">(.*?)</script>', html, re.S)
            self.assertIsNotNone(m, f"{lesson['slug']}: thiếu chunk-data")
            chunks = json.loads(m.group(1))
            self.assertGreater(len(chunks), 0, f"{lesson['slug']}: không có cụm nào")
            for c in chunks:
                self.assertEqual(len(re.split(r"(?<=[.!?])\s+", c["en"].strip())), 1,
                                 f"{lesson['slug']}: cụm nhiều hơn 1 câu: {c['en']}")

    def test_speak_page_has_sentences(self):
        html = (ROOT / "luyen-noi" / "index.html").read_text(encoding="utf-8")
        raw = html.split("window.SDSC_SPEAK=", 1)[1].split(";</script>", 1)[0]
        sentences_list = json.loads(raw)
        self.assertGreater(len(sentences_list), 50, "quá ít câu luyện nói")

    def test_dict_page_has_chips(self):
        html = (ROOT / "tu-dien" / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="dict-input"', html)
        self.assertIn('id="dict-chips"', html)


class TestDeploy(unittest.TestCase):
    def test_a12_deploy_reads_disk_readme(self):
        """A12 (điều chỉnh S-05): deploy không còn hằng README cũ ghi đè;
        README trong cây push = file README.md trên đĩa."""
        deploy_src = (ROOT / "deploy_github_pages.py").read_text(encoding="utf-8")
        self.assertNotIn('raw = README.encode', deploy_src,
                         "deploy vẫn ghi đè README bằng hằng cũ")
        self.assertIn("SEED_README", deploy_src,
                      "phải giữ seed README chỉ cho repo mới hoàn toàn")
        disk_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn(f"{len(visible())} bài học", disk_readme)
        self.assertNotIn("12 bài đầu nhúng sẵn", disk_readme)
        self.assertNotIn("file duy nhất là `index.html`", disk_readme)

    def test_site_files_includes_new_assets(self):
        """favicon/sitemap/robots/fonts phải nằm trong danh sách deploy."""
        deploy_src = (ROOT / "deploy_github_pages.py").read_text(encoding="utf-8")
        for name in ["favicon.svg", "sitemap.xml", "robots.txt", "CNAME", ".nojekyll"]:
            self.assertIn(f'"{name}"', deploy_src, f"site_files thiếu {name}")
        for asset in ["favicon.svg", "sitemap.xml", "robots.txt"]:
            self.assertTrue((ROOT / asset).exists(), f"thiếu {asset} trên đĩa")

    def test_fonts_only_kept_subsets(self):
        """Chỉ giữ subset latin/latin-ext/vietnamese; mọi file là woff2 hợp lệ."""
        for f in (ROOT / "fonts").glob("*.woff2"):
            self.assertRegex(f.name, r"-(latin|latin-ext|vietnamese)\.woff2$",
                             f"subset thừa còn sót: {f.name}")
            self.assertEqual(f.read_bytes()[:4], b"wOF2", f"{f.name} không phải woff2")
            self.assertGreater(f.stat().st_size, 1024, f"{f.name} quá nhỏ, có thể hỏng")


class TestUndoLog(unittest.TestCase):
    def test_undo_log_chain(self):
        """Chuỗi hoàn tác phải liên tục theo đúng log hiện tại (không hardcode
        head — head đổi sau mỗi lần deploy): prev của dòng cuối phải là một
        sha đã xuất hiện trước đó, và lần hoàn tác sau phải lùi tiếp về
        commit trước prev (không quay lại sha hiện tại)."""
        sys.path.insert(0, str(ROOT))
        import undo_deploy as undo
        lines = [l.strip() for l in (ROOT / "DEPLOY_LOG.md").read_text(encoding="utf-8").splitlines()
                 if l.startswith("- ")]
        parsed = [undo.parse_log_line(l) for l in lines]
        self.assertTrue(all(p is not None for p in parsed), "có dòng log sai định dạng")
        sha, prev, _ = parsed[-1]
        earlier_shas = [p[0] for p in parsed[:-1]]
        self.assertIn(prev, earlier_shas,
                      "prev của dòng cuối phải là commit đã xuất hiện trước đó trong log")
        nxt = undo.find_prev_for(lines, prev)
        self.assertNotEqual(nxt, sha, "lần hoàn tác sau không được quay lại commit hiện tại")
        self.assertIn(nxt, earlier_shas + [""],
                      "commit lùi tiếp phải có trong log (hoặc rỗng khi hết lịch sử)")
        # mốc lịch sử cố định: dòng deploy b5e86c4 luôn trỏ về 2fcd5b1,
        # và 2fcd5b1 trỏ về 6280870 (chuỗi undo 2 lần không quay đầu).
        by_sha = {p[0]: p[1] for p in parsed}
        self.assertEqual(by_sha.get("b5e86c483364b53534c19680e09d9025d620a4da"),
                         "2fcd5b19092ee29603cf4ae93cc61c1764d48cd9")
        self.assertEqual(by_sha.get("2fcd5b19092ee29603cf4ae93cc61c1764d48cd9"),
                         "628087095bd737dc4b0f71a87b173bda2468e0fd")
        self.assertIsNone(undo.parse_log_line("- 2026-11-15 00:34 +07 | abc"))


class TestOptimization(unittest.TestCase):
    """Tối ưu A+B (19/11): file dùng chung, tìm kiếm nạp lười, build tăng dần."""

    def test_shared_files_exist_and_match_source(self):
        """styles.css/app.js/data.js/search-index.json tồn tại, không rỗng,
        đúng nội dung sinh từ generate_site.py."""
        css = (ROOT / "styles.css").read_text(encoding="utf-8")
        self.assertIn(".wrap", css)
        self.assertGreater(len(css), 10000)
        app = (ROOT / "app.js").read_text(encoding="utf-8")
        self.assertIn("getProgress", app)
        self.assertGreater(len(app), 10000)
        data = (ROOT / "data.js").read_text(encoding="utf-8")
        self.assertTrue(data.startswith("window.SDSC_TOTAL_GRADED="))
        self.assertIn("window.SDSC_LESSONS=", data)
        idx = json.loads((ROOT / "search-index.json").read_text(encoding="utf-8"))
        self.assertEqual({x["slug"] for x in idx}, {l["slug"] for l in visible()})

    def test_pages_link_shared_files_not_inline(self):
        """Mọi trang link tới 3 file chung, không nhúng CSS/JS/dữ liệu chung."""
        pages = [ROOT / "index.html"] + [ROOT / l["slug"] / "index.html" for l in visible()]
        for page in pages:
            html = page.read_text(encoding="utf-8")
            self.assertIn('href="/sai-dau-sua-do/styles.css"', html, page.name)
            self.assertIn('src="/sai-dau-sua-do/data.js"', html, page.name)
            self.assertIn('src="/sai-dau-sua-do/app.js"', html, page.name)
            self.assertNotIn(gen.CSS.strip(), html, f"{page.name}: vẫn nhúng CSS")
            self.assertNotIn("window.SDSC_LESSONS=", html,
                             f"{page.name}: vẫn nhúng dữ liệu bài học")

    def test_homepage_no_inline_search_index(self):
        """Trang chủ không còn nhúng chỉ mục tìm kiếm; chỉ mục ở file riêng."""
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("window.SDSC_SEARCH=[", index)
        self.assertIn("search-index.json", index)

    def test_incremental_build_noop(self):
        """Build lần 2 ngay sau lần 1 không đổi file nào (ghi tăng dần)."""
        def snap(root):
            out = {}
            for p in sorted(root.rglob("*")):
                if p.is_file():
                    out[str(p.relative_to(root))] = p.read_bytes()
            return out

        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            shutil.copytree(ROOT, tmp / "web",
                            ignore=shutil.ignore_patterns("__pycache__", "tests", "_archive", "shots", "backup"))
            (tmp / "src-images").mkdir()
            for img in (tmp / "web" / "images").glob("*.jpg"):
                shutil.copy(img, tmp / "src-images" / img.name)
            data = json.loads((tmp / "web" / "lessons.json").read_text(encoding="utf-8"))
            for lesson in data["lessons"]:
                cand = f"src-images/{lesson['slug']}.jpg"
                lesson["image_src"] = cand if (tmp / cand).exists() else "src-images/loi-001.jpg"
            (tmp / "web" / "lessons.json").write_text(
                json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "gen_under_test", tmp / "web" / "generate_site.py")
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            mod.main()
            before = snap(tmp / "web")
            mod.main()
            after = snap(tmp / "web")
            changed = [k for k in after if before.get(k) != after[k]]
            added = [k for k in after if k not in before]
            self.assertEqual(changed, [], f"build lần 2 vẫn đổi file: {changed}")
            self.assertEqual(added, [], f"build lần 2 thêm file: {added}")

    def test_deploy_includes_shared_files(self):
        """site_files phải gồm 4 file dùng chung mới."""
        deploy_src = (ROOT / "deploy_github_pages.py").read_text(encoding="utf-8")
        for name in ["styles.css", "app.js", "data.js", "search-index.json"]:
            self.assertIn(f'"{name}"', deploy_src, f"site_files thiếu {name}")
            self.assertTrue((ROOT / name).exists(), f"thiếu {name} trên đĩa")


class TestApi(unittest.TestCase):
    """API mở (19/11): file JSON tĩnh dưới api/v1/ + trang tài liệu /api/."""

    @classmethod
    def setUpClass(cls):
        cls.data = load_data()
        cls.lessons = {l["slug"]: l for l in cls.data["lessons"]}
        cls.glossary = gen.parse_vi_glossary()

    def _load(self, rel):
        return json.loads((ROOT / rel).read_text(encoding="utf-8"))

    def test_api_files_exist_and_valid_json(self):
        """Mọi file API đều tồn tại và là JSON hợp lệ."""
        expected = ["api/v1/meta.json", "api/v1/lessons.json",
                    "api/v1/dictionary.json", "api/v1/search-index.json",
                    "api/v1/paths.json", "api/openapi.yaml",
                    "api/index.html"]
        for rel in expected:
            self.assertTrue((ROOT / rel).exists(), f"thiếu {rel}")
        for rel in expected:
            if rel.endswith(".json"):
                self._load(rel)
        for slug in self.lessons:
            self._load(f"api/v1/lessons/{slug}.json")

    def test_api_lessons_count_and_fields(self):
        """lessons.json của API có đủ bài, mỗi bài đủ 13 trường, khớp gốc."""
        api = self._load("api/v1/lessons.json")
        self.assertEqual(len(api["lessons"]), len(self.data["lessons"]))
        self.assertEqual(api["meta"]["total_lessons"], len(self.data["lessons"]))
        self.assertEqual(api["meta"]["visible_lessons"], len(visible()))
        fields = {"slug", "code", "type", "topic", "title", "date", "wrong",
                  "right", "remember", "url", "fb", "image", "show_in_ui"}
        for entry in api["lessons"]:
            self.assertEqual(set(entry), fields, f"bài {entry['slug']}: sai trường")
            src = self.lessons[entry["slug"]]
            self.assertEqual(entry["wrong"], src.get("wrong", ""))
            self.assertEqual(entry["right"], src.get("right", ""))
            self.assertEqual(entry["image"], src.get("image_src", ""))
            self.assertEqual(entry["url"],
                             f"https://dongdarealest.github.io/sai-dau-sua-do/{entry['slug']}/")

    def test_api_detail_per_slug(self):
        """Mỗi slug đều có file chi tiết, đủ trường, khớp dữ liệu gốc."""
        for slug, src in self.lessons.items():
            detail = self._load(f"api/v1/lessons/{slug}.json")
            lesson = detail["lesson"]
            self.assertEqual(lesson["slug"], slug)
            self.assertEqual(lesson["wrong"], src.get("wrong", ""))
            self.assertEqual(lesson["right"], src.get("right", ""))
            self.assertEqual(lesson["why"], src.get("why", ""))
            self.assertEqual(lesson["practice"], src.get("practice", []))
            self.assertEqual(lesson["quiz"], src.get("quiz"))
            self.assertIn("source", detail["meta"])
            self.assertEqual(detail["meta"]["source"]["license"], "CC BY 4.0")

    def test_api_dictionary_counts(self):
        """Từ điển API có đủ 852 từ, mỗi nghĩa có từ loại và nghĩa tiếng Việt."""
        api = self._load("api/v1/dictionary.json")
        self.assertEqual(len(api["words"]), len(self.glossary))
        self.assertEqual(api["meta"]["total_words"], len(self.glossary))
        expected_wex = sum(1 for v in self.glossary.values()
                           if any(len(s) >= 4 for s in v))
        self.assertEqual(api["meta"]["words_with_example"], expected_wex)
        for word, entry in api["words"].items():
            self.assertTrue(entry["senses"], f"từ {word}: không có nghĩa")
            for sense in entry["senses"]:
                self.assertIn("pos", sense)
                self.assertIn("meaning", sense)
                self.assertTrue(sense["pos"] and sense["meaning"])

    def test_api_dictionary_mistakes(self):
        """Mỗi từ có trường mistakes: tối đa 5 slug bài học thật, từ đó
        xuất hiện trong cặp câu sai và câu đúng của bài (khớp ranh giới từ,
        không phân biệt hoa thường). Quét lại độc lập, không dùng chung
        code với hàm sinh."""
        api = self._load("api/v1/dictionary.json")
        slugs = {l["slug"] for l in self.data["lessons"]}
        n_with = 0
        for word, entry in api["words"].items():
            self.assertIn("mistakes", entry, f"từ {word}: thiếu trường mistakes")
            got = entry["mistakes"]
            self.assertIsInstance(got, list, f"từ {word}: mistakes không phải danh sách")
            self.assertLessEqual(len(got), 5, f"từ {word}: mistakes quá 5 slug")
            if got:
                n_with += 1
            pat = re.compile(r"\b" + re.escape(word) + r"\b", re.I)
            for slug in got:
                self.assertIn(slug, slugs, f"từ {word}: slug {slug} không có thật")
                lesson = next(l for l in self.data["lessons"] if l["slug"] == slug)
                text = (lesson.get("wrong", "") or "") + " " + (lesson.get("right", "") or "")
                self.assertTrue(pat.search(text),
                                f"từ {word}: không xuất hiện trong cặp câu sai và câu đúng của {slug}")
        self.assertGreater(n_with, 0, "không từ nào có mistakes, trường này vô nghĩa")
        print(f"dictionary mistakes: {n_with}/{len(api['words'])} từ có ít nhất 1 bài học")

    def test_api_meta_source(self):
        """Mọi file API đều có khối meta.source với tên Trang, link, giấy phép, ghi công."""
        # meta.json là chính khối meta, không bọc thêm 1 lớp meta nữa.
        meta = self._load("api/v1/meta.json")
        self._check_source(meta["source"])
        self.assertEqual(meta["total_lessons"], len(self.data["lessons"]))
        self.assertEqual(meta["visible_lessons"], len(visible()))
        self.assertEqual(meta["total_words"], len(self.glossary))
        self.assertEqual(meta["learning_paths"], len(self.data["site"]["paths"]))
        for rel in ["api/v1/lessons.json", "api/v1/dictionary.json", "api/v1/paths.json"]:
            self._check_source(self._load(rel)["meta"]["source"])

    def _check_source(self, src):
        self.assertEqual(src["name"], "Sai Đâu Sửa Đó")
        self.assertEqual(src["site"], "https://dongdarealest.github.io/sai-dau-sua-do")
        self.assertEqual(src["license"], "CC BY 4.0")
        self.assertIn("Sai Đâu Sửa Đó", src["attribution"])

    def test_api_matches_verified_samples(self):
        """File API sinh ra khớp 2 file mẫu đã kiểm chứng 291 PASS."""
        sample_dir = ROOT.parent / "api"
        sample_lessons = json.loads(
            (sample_dir / "api-v1-lessons-sample.json").read_text(encoding="utf-8"))
        api = self._load("api/v1/lessons.json")
        by_slug = {e["slug"]: e for e in api["lessons"]}
        for entry in sample_lessons["lessons"]:
            self.assertEqual(by_slug[entry["slug"]], entry)
        sample_dict = json.loads(
            (sample_dir / "api-v1-dictionary-sample.json").read_text(encoding="utf-8"))
        api_dict = self._load("api/v1/dictionary.json")
        for word, entry in sample_dict["words"].items():
            self.assertEqual(api_dict["words"][word], entry)

    def test_api_no_old_url_changed(self):
        """Sitemap vẫn giữ mọi URL bài học cũ, chỉ thêm đường dẫn API mới."""
        sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
        for lesson in visible():
            self.assertIn(f"https://dongdarealest.github.io/sai-dau-sua-do/{lesson['slug']}/",
                          sitemap, f"sitemap mất URL {lesson['slug']}")
        for url in ["/api/", "/api/v1/meta.json", "/api/v1/lessons.json",
                    "/api/v1/dictionary.json"]:
            self.assertIn(f"https://dongdarealest.github.io/sai-dau-sua-do{url}", sitemap)

    def test_api_docs_page(self):
        """Trang tài liệu /api/ tồn tại, liệt kê đủ đầu dữ liệu, có bản thử trực tiếp."""
        html = (ROOT / "api" / "index.html").read_text(encoding="utf-8")
        for path in ["/api/v1/meta.json", "/api/v1/lessons.json",
                     "/api/v1/dictionary.json", "/api/v1/search-index.json",
                     "/api/v1/paths.json", "/api/openapi.yaml"]:
            self.assertIn(path, html, f"tài liệu thiếu {path}")
        self.assertIn("api-demo-btn", html)
        self.assertIn("api-demo-dict-btn", html)
        self.assertIn("api/v1/lessons.json", html)

    def test_deploy_includes_api_files(self):
        """site_files phải gồm file API và 2 file giấy phép."""
        deploy_src = (ROOT / "deploy_github_pages.py").read_text(encoding="utf-8")
        for name in ['"LICENSE"', '"LICENSE-CONTENT.md"', '"api/openapi.yaml"']:
            self.assertIn(name, deploy_src, f"site_files thiếu {name}")
        for name in ["LICENSE", "LICENSE-CONTENT.md"]:
            self.assertTrue((ROOT / name).exists(), f"thiếu {name} trên đĩa")


if __name__ == "__main__":
    unittest.main()
