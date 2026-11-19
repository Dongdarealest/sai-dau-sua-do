# Chay tu web/: python3 tests/scan_dash.py  (quet van ban hien thi, bo script/style; ket qua phai = 0 hit)
import re, glob, sys, html
# Quet van ban HIEN THI (bo <script>, <style>, the, thuoc tinh) trong tat ca trang da sinh.
# Gach ngang bi cam trong noi dung hien thi: "-" (hyphen tru), "–" (en dash), "—" (em dash).
# Du lieu cau truc (URL, ten file, slug) khong nam trong van ban hien thi nen khong tinh.
hits = []
for f in sorted(glob.glob('site/**/*.html', recursive=True) + glob.glob('site/*.html')):
    t = open(f, encoding='utf-8').read()
    t = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', t, flags=re.S | re.I)
    # og:description va title nam trong the meta/title: lay ca title va og content
    for m in re.finditer(r'<title>(.*?)</title>', t, flags=re.S | re.I):
        txt = html.unescape(m.group(1))
        for ch in ('-', '–', '—'):
            if ch in txt:
                hits.append((f, 'TITLE', txt))
    for m in re.finditer(r'<meta[^>]+content="([^"]*)"[^>]*>', t):
        txt = html.unescape(m.group(1))
        for ch in ('-', '–', '—'):
            if ch in txt:
                hits.append((f, 'META', txt))
    # alt text
    for m in re.finditer(r'alt="([^"]*)"', t):
        txt = html.unescape(m.group(1))
        for ch in ('-', '–', '—'):
            if ch in txt:
                hits.append((f, 'ALT', txt))
    body = re.sub(r'<[^>]+>', ' ', t)
    body = html.unescape(body)
    body = re.sub(r'\s+', ' ', body)
    for ch in ('-', '–', '—'):
        i = body.find(ch)
        while i != -1:
            hits.append((f, 'BODY', body[max(0, i-45):i+45]))
            i = body.find(ch, i+1)
print("TONG HIT:", len(hits))
for h in hits[:60]:
    print(h)
