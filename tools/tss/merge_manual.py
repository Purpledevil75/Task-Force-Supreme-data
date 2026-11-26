"""Merge hand-entered routeing measures (tss/manual/*.json: official coordinates of schemes missing from OSM, ids 'm-...')
into a tss.json data set. Used by fetch.py after every update; can be run alone: python3 tools/tss/merge_manual.py [tss.json]"""
import json, os, sys, glob
H = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def manual_features():
    out = []
    for p in sorted(glob.glob(os.path.join(H, 'tss', 'manual', '*.json'))):
        out += json.load(open(p, encoding='utf-8'))['f']
    return out
def merge(data):
    keep = [f for f in data['f'] if not str(f.get('id', '')).startswith('m-')]
    man = manual_features(); data['f'] = sorted(keep + man, key=lambda f: f['id'])
    cnt = {}
    for f in data['f']: cnt[f['k']] = cnt.get(f['k'], 0) + 1
    data['counts'] = cnt
    if man and 'manual' not in data.get('license', ''): data['license'] += '; manual additions from official national regulations (tss/manual)'
    return data
if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(H, 'tss', 'tss.json')
    d = merge(json.load(open(path, encoding='utf-8')))
    open(path, 'w', encoding='utf-8').write(json.dumps(d, separators=(',', ':'), ensure_ascii=False)); print('manual features', sum(1 for f in d['f'] if f['id'].startswith('m-')))
