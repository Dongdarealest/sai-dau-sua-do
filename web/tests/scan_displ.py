# Chay tu web/: python3 tests/scan_displ.py  (quet truong hien thi lessons.json; ket qua phai = 0 hit)
import json
d = json.load(open('lessons.json', encoding='utf-8'))
disp = ["title","why","wrong","right","remember","problem","core","tip","articulation"]
n = 0
def walk(obj, path):
    global n
    if isinstance(obj, str):
        if any(c in obj for c in ('-','–','—')):
            print(path, '=>', obj[:100]); n += 1
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if k in disp or k in ("examples","compare","mistakes","practice","quiz","ipa","options","note","source","text","prompt","explanation"):
                walk(v, path + '.' + k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            walk(v, f"{path}[{i}]")
for l in d['lessons']:
    walk(l, l['slug'])
print('lessons.json display hyphen hits:', n)
