#!/usr/bin/env python3
"""Fetch traffic separation schemes and related routeing measures from OpenStreetMap (seamark tagging)
via the Overpass API, tile by tile, compare with the previous data set and write:
  tss/tss.json         - current data (each feature has its OSM id and version)
  tss/changes.json     - change log (added / changed / removed), newest first, last 30 runs
  manifest.json        - dataset versions for the app's update check
  tools/tss/out/summary.json - for CI (changed: true/false)
(c) OpenStreetMap contributors, ODbL 1.0. Not for navigation: OSM coverage of routeing measures is incomplete."""
import hashlib, json, os, time, urllib.parse, urllib.request
H = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(H, '..', '..', 'tss'); os.makedirs(APP, exist_ok=True)
OUTD = os.path.join(H, 'out'); os.makedirs(OUTD, exist_ok=True)
EP = ['https://overpass-api.de/api/interpreter', 'https://overpass.kumi.systems/api/interpreter', 'https://maps.mail.ru/osm/tools/overpass/api/interpreter']
UA = 'TaskForceSupreme-data/0.2 (+https://github.com/Purpledevil75/Task-Force-Supreme)'
TYPES = 'separation_zone|separation_line|separation_lane|separation_boundary|separation_crossing|separation_roundabout|inshore_traffic_zone|precautionary_area|deep_water_route_part|deep_water_route_centreline|two-way_route_part|recommended_track|calling-in_point'
KEEP = {'separation_zone': 'z', 'separation_line': 'l', 'separation_lane': 'n', 'separation_boundary': 'b', 'separation_crossing': 'c', 'separation_roundabout': 'r',
        'inshore_traffic_zone': 'i', 'precautionary_area': 'p', 'deep_water_route_part': 'd', 'deep_water_route_centreline': 'D', 'two-way_route_part': 't', 'recommended_track': 'k', 'calling-in_point': 'C'}
KRU = {'z': 'зона разделения', 'l': 'линия разделения', 'n': 'полоса движения', 'b': 'граница TSS', 'c': 'зона пересечения', 'r': 'круговое движение', 'i': 'зона прибрежного плавания',
       'p': 'район осторожного плавания', 'd': 'глубоководный путь', 'D': 'ось глубоководного пути', 't': 'путь двустороннего движения', 'k': 'рекомендованный путь', 'C': 'точка доклада (VTS)'}

def q(bbox):
    s, w, n, e = bbox
    return f'[out:json][timeout:170][bbox:{s},{w},{n},{e}];(nwr["seamark:type"~"^({TYPES})$"];);out meta geom;'

def fetch(bbox):
    data = urllib.parse.urlencode({'data': q(bbox)}).encode(); last = None
    for attempt in range(4):
        url = EP[attempt % len(EP)]
        try:
            req = urllib.request.Request(url, data=data, headers={'User-Agent': UA, 'Accept': 'application/json'})
            with urllib.request.urlopen(req, timeout=200) as r:
                return json.loads(r.read().decode('utf-8'))
        except Exception as ex:
            last = ex; print('  retry', bbox, url, ex, flush=True); time.sleep(10 * (attempt + 1))
    print('  FAILED', bbox, last, flush=True); return None

def rnd(c): return [round(c['lon'], 5), round(c['lat'], 5)]

feats, seen, failed = {}, set(), []
def process(t):
    d = fetch(t)
    if d is None: failed.append(t); return
    n0 = len(feats)
    for el in d.get('elements', []):
        fid = el['type'][0] + str(el['id'])
        if fid in seen: continue
        tg = el.get('tags', {}); k = KEEP.get(tg.get('seamark:type'))
        if not k: continue
        f = {'id': fid, 'v': el.get('version', 0), 'ts': (el.get('timestamp') or '')[:10], 'k': k}
        nm = tg.get('seamark:name') or tg.get('name')
        if nm: f['n'] = nm
        for a in ('seamark:calling-in_point:channel', 'seamark:calling-in_point:callsign', 'seamark:separation_lane:orientation', 'seamark:recommended_track:orientation', 'seamark:calling-in_point:orientation'):
            if a in tg: f[a.split(':')[-1][:3]] = tg[a]
        if el['type'] == 'node': f['g'] = [round(el['lon'], 5), round(el['lat'], 5)]
        elif el['type'] == 'way' and el.get('geometry'): f['g'] = [rnd(c) for c in el['geometry'] if c]
        elif el['type'] == 'relation':
            rings = [[rnd(c) for c in m['geometry'] if c] for m in el.get('members', []) if m.get('type') == 'way' and m.get('geometry')]
            if not rings: continue
            f['m'] = rings
        else: continue
        seen.add(fid); feats[fid] = f
    if len(feats) > n0: print('tile', t, 'new', len(feats) - n0, 'total', len(feats), flush=True)

tiles = [(s, w, s + 10, w + 10) for s in range(-60, 80, 10) for w in range(-180, 180, 10)]
for t in tiles: process(t); time.sleep(1)
for _ in range(2):
    again, failed[:] = failed[:], []
    if not again: break
    print('retrying', len(again), 'failed tiles', flush=True); time.sleep(60)
    for t in again: process(t); time.sleep(3)
print('failed tiles left:', failed, flush=True)

def bbox_of(f):
    pts = [f['g']] if f.get('g') and not isinstance(f['g'][0], list) else (f.get('g') or [p for r in f.get('m', []) for p in r])
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return [round(min(xs), 3), round(min(ys), 3), round(max(xs), 3), round(max(ys), 3)]
def ghash(f): return hashlib.md5(json.dumps([f.get('g'), f.get('m'), f.get('n'), f.get('cha'), f.get('ori')], sort_keys=True).encode()).hexdigest()[:10]
def in_failed(bb):
    cx, cy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
    return any(s <= cy < n and w <= cx < e for s, w, n, e in failed)

# ---- compare with the previous data set ----
def load_json(path):
    return json.load(open(path, encoding='utf-8')) if os.path.exists(path) else None
prev = load_json(os.path.join(APP, 'tss.json'))
old = {f['id']: f for f in (prev or {}).get('f', []) if 'id' in f}
added, changed, removed = [], [], []
for fid, f in feats.items():
    o = old.get(fid)
    if o is None: added.append(f)
    elif o.get('v') != f.get('v') or ghash(o) != ghash(f): changed.append(f)
for fid, o in old.items():
    if fid not in feats:
        if in_failed(bbox_of(o)): feats[fid] = o      # tile not fetched this time: keep the old feature, do not report removal
        else: removed.append(o)
first_run = not old
desc = lambda f, how: {'id': f['id'], 'k': f['k'], 'what': KRU.get(f['k'], f['k']), 'n': f.get('n', ''), 'bb': bbox_of(f), 'how': how, 'ts': f.get('ts', '')}
entry = {'date': time.strftime('%Y-%m-%d'), 'total': len(feats), 'added': len(added), 'changed': len(changed), 'removed': len(removed), 'first': first_run,
         'items': ([] if first_run else [desc(f, 'new') for f in added] + [desc(f, 'changed') for f in changed] + [desc(f, 'removed') for f in removed])[:400],
         'failedTiles': len(failed)}
log = load_json(os.path.join(APP, 'changes.json')) or []
is_change = first_run or added or changed or removed
if is_change: log = [entry] + log[:29]

cnt = {}
for f in feats.values(): cnt[f['k']] = cnt.get(f['k'], 0) + 1
data = {'version': 'OSM seamark routeing measures, ' + time.strftime('%Y-%m-%d'), 'updated': time.strftime('%Y-%m-%d'), 'license': '(c) OpenStreetMap contributors, ODbL 1.0',
        'counts': cnt, 'f': sorted(feats.values(), key=lambda f: f['id'])}
if is_change or not prev:
    raw = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
    open(os.path.join(APP, 'tss.json'), 'w', encoding='utf-8').write(raw)
    open(os.path.join(APP, 'changes.json'), 'w', encoding='utf-8').write(json.dumps(log, separators=(',', ':'), ensure_ascii=False))
    mp = os.path.join(H, '..', '..', 'manifest.json'); man = load_json(mp) or {'schema': 1, 'datasets': {}}
    man['datasets']['tss'] = {'updated': data['updated'], 'count': len(feats), 'path': 'tss/tss.json', 'changes': 'tss/changes.json',
                              'sha256': hashlib.sha256(raw.encode('utf-8')).hexdigest(), 'license': 'ODbL-1.0'}
    json.dump(man, open(mp, 'w'), indent=1)
json.dump({'changed': bool(is_change), 'total': len(feats), 'added': len(added), 'changed_n': len(changed), 'removed': len(removed), 'failed_tiles': failed}, open(os.path.join(OUTD, 'summary.json'), 'w'))
print('features', len(feats), cnt, 'added', len(added), 'changed', len(changed), 'removed', len(removed))
