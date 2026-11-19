# Chay tu web/: python3 tests/scan_js_strings.py  (quet chuoi JS hien thi; ket qua phai = 0 hit)
import re
# Quet cac chuoi trong JS (trong <script> cua generate_site.py + chuoi Python hien thi):
# cam " — ", " – ", " - " trong chuoi hien thi; bo qua code (split("-"), key sdsc-..., sdsc-progress-v1).
src = open('generate_site.py', encoding='utf-8').read()
def check(text, where):
    bad = []
    for m in re.finditer(r'"([^"\\]*(?:\\.[^"\\]*)*)"', text):
        s = m.group(1)
        if '—' in s or '–' in s or ' - ' in s:
            bad.append((where, s[:110]))
    for m in re.finditer(r"'([^'\\]*(?:\\.[^'\\]*)*)'", text):
        s = m.group(1)
        if '—' in s or '–' in s or ' - ' in s:
            bad.append((where, s[:110]))
    return bad
hits = []
# Chi quet cac khoi JS + cac f-string HTML trong generate_site.py
for name in ('SHARED_JS', 'HOMEPAGE_JS', 'INDEX_FILTER_JS', 'LESSON_PAGE_JS',
             'CHUNK_JS', 'DICT_JS', 'DASH_JS', 'LIB_JS', 'SPEAK_JS'):
    i = src.find(name + ' = ')
    j = src.find('\n"""', i)
    hits += check(src[i:j], name)
print('JS string hits:', len(hits))
for h in hits:
    print(h)
