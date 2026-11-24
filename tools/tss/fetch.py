#!/usr/bin/env python3
"""Fetch traffic separation schemes and related routeing measures from OpenStreetMap (seamark tagging)
via the Overpass API (one global query per seamark:type value), compare with the previous data set and write:
  tss/tss.json         - current data (each feature has its OSM id and version)
  tss/changes.json     - change log (added / changed / removed), newest first, last 30 runs
  manifest.json        - dataset versions for the app's update check
  tools/tss/out/summary.json - for CI (changed: true/false)
(c) OpenStreetMap contributors, ODbL 1.0. Not for navigation: OSM coverage of routeing measures is incomplete."""
import hashlib, json, os, time, urllib.parse, urllib.request
H = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(H, '..', '..', 'tss'); os.makedirs(APP, exist_ok=True)
OUTD = os.path.join(H, 'out'); os.makedirs(OUTD, exist_ok=True)
EP = ['https://overpass-api.de/api/interpreter', 'https://overpass.private.coffee/api/interpreter', 'https://maps.mail.ru/osm/tools/overpass/api/interpreter']
UA = 'TaskForceSupreme-data/0.2 (+https://github.com/Purpledevil75/Task-Force-Supreme)'
TYPES = 'separation_zone|separation_line|separation_lane|separation_boundary|separation_crossing|separation_roundabout|inshore_traffic_zone|precautionary_area|deep_water_route_part|deep_water_route_centreline|two-way_route_part|recommended_track|calling-in_point'
KEEP = {'separation_zone': 'z', 'separation_line': 'l', 'separation_lane': 'n', 'separation_boundary': 'b', 'separation_crossing': 'c', 'separation_roundabout': 'r',
        'inshore_traffic_zone': 'i', 'precautionary_area': 'p', 'deep_water_route_part': 'd', 'deep_water_route_centreline': 'D', 'two-way_route_part': 't', 'recommended_track': 'k', 'calling-in_point': 'C'}
KRU = {'z': 'зона разделения', 'l': 'линия разделения', 'n': 'полоса движения', 'b': 'граница TSS', 'c': 'зона пересечения', 'r': 'круговое движение', 'i': 'зона прибрежного плавания',
       'p': 'район осторожного плавания', 'd': 'глубоководный путь', 'D': 'ось глубоководного пути', 't': 'путь двустороннего движения', 'k': 'рекомендованный путь', 'C': 'точка доклада (VTS)'}

def q(t):
    return f'[out:json][timeout:600];nwr["seamark:type"="{t}"];out meta geom;'

def fetch(t, tries=12):
    """Global query for one exact seamark:type value (tag index lookup: ~30-60 s when a server accepts it).
    Overpass answers 502/504 at once when busy, so keep cycling servers with a growing pause."""
    data = urllib.parse.urlencode({'data': q(t)}).encode(); last = None
    for attempt in range(tries):
        url = EP[attempt % len(EP)]
        try:
            req = urllib.request.Request(url, data=data, headers={'User-Agent': UA, 'Accept': 'application/json'})
            with urllib.request.urlopen(req, timeout=660) as r:
                d = json.loads(r.read().decode('utf-8'))
            if 'remark' in d and 'runtime error' in str(d.get('remark')): raise RuntimeError(d['remark'][:120])
            return d
        except Exception as ex:
            last = ex; print('  retry', t, url, str(ex)[:100], flush=True); time.sleep(min(30 * (attempt + 1), 180))
    print('  FAILED', t, last, flush=True); return None

def rnd(c): return [round(c['lon'], 5), round(c['lat'], 5)]

feats, seen, failed = {}, set(), []
def process(t):
    d = fetch(t)
    if d is None: failed.append(KEEP[t]); return
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
    print('type', t, 'features', len(feats) - n0, 'total', len(feats), flush=True)

def from_geofabrik(path):
    """Features extracted by geofabrik.py (osmium export, GeoJSON per line)."""
    def r5(c): return [round(c[0], 5), round(c[1], 5)]
    for line in open(path, encoding='utf-8'):
        try: ft = json.loads(line)
        except Exception: continue
        pr, gm = ft.get('properties', {}), ft.get('geometry') or {}
        k = KEEP.get(pr.get('seamark:type'))
        if not k: continue
        fid = (pr.get('@type') or 'x')[0] + str(pr.get('@id'))
        f = {'id': fid, 'v': pr.get('@version', 0), 'ts': str(pr.get('@timestamp') or '')[:10], 'k': k}
        nm = pr.get('seamark:name') or pr.get('name')
        if nm: f['n'] = nm
        for a2 in ('seamark:calling-in_point:channel', 'seamark:calling-in_point:callsign', 'seamark:separation_lane:orientation', 'seamark:recommended_track:orientation', 'seamark:calling-in_point:orientation'):
            if a2 in pr: f[a2.split(':')[-1][:3]] = pr[a2]
        t, c = gm.get('type'), gm.get('coordinates')
        if not c: continue
        if t == 'Point': f['g'] = r5(c)
        elif t == 'LineString': f['g'] = [r5(p) for p in c]
        elif t == 'Polygon' and fid[0] == 'w': f['g'] = [r5(p) for p in c[0]]
        elif t == 'Polygon': f['m'] = [[r5(p) for p in ring] for ring in c]
        elif t == 'MultiPolygon': f['m'] = [[r5(p) for p in ring] for poly in c for ring in poly]
        elif t == 'MultiLineString': f['m'] = [[r5(p) for p in ln] for ln in c]
        else: continue
        size = lambda x: len(x.get('g') or []) + sum(len(r) for r in x.get('m', []))
        o = feats.get(fid)          # border regions overlap: keep the most complete copy
        if o is None or size(f) > size(o) or f['v'] > o['v']: feats[fid] = f

GF = os.path.join(OUTD, 'geofabrik.geojsonseq')
SOURCE = os.environ.get('TSS_SOURCE', 'geofabrik' if os.path.exists(GF) else 'overpass')
failed_regions = []
if SOURCE == 'geofabrik':
    from_geofabrik(GF)
    st = json.load(open(os.path.join(OUTD, 'geofabrik-status.json'))) if os.path.exists(os.path.join(OUTD, 'geofabrik-status.json')) else {}
    failed_regions = st.get('failed', [])
    if failed_regions: failed[:] = list(set(KEEP.values()))     # some regions missing: never report removals this run
    print('geofabrik features', len(feats), 'failed regions', failed_regions, flush=True)
else:
    for t in KEEP: process(t); time.sleep(5)
    for _ in range(2):
        again = [t for t, k in KEEP.items() if k in failed]; failed[:] = []
        if not again: break
        print('retrying', again, flush=True); time.sleep(300)
        for t in again: process(t); time.sleep(5)
    print('failed types left:', failed, flush=True)

def bbox_of(f):
    pts = [f['g']] if f.get('g') and not isinstance(f['g'][0], list) else (f.get('g') or [p for r in f.get('m', []) for p in r])
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return [round(min(xs), 3), round(min(ys), 3), round(max(xs), 3), round(max(ys), 3)]
def ghash(f): return hashlib.md5(json.dumps([f.get('g'), f.get('m'), f.get('n'), f.get('cha'), f.get('ori')], sort_keys=True).encode()).hexdigest()[:10]

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
        if o.get('k') in failed: feats[fid] = o      # type not fetched this time: keep the old feature, do not report removal
        else: removed.append(o)
first_run = not old
desc = lambda f, how: {'id': f['id'], 'k': f['k'], 'what': KRU.get(f['k'], f['k']), 'n': f.get('n', ''), 'bb': bbox_of(f), 'how': how, 'ts': f.get('ts', '')}
entry = {'date': time.strftime('%Y-%m-%d'), 'total': len(feats), 'added': len(added), 'changed': len(changed), 'removed': len(removed), 'first': first_run,
         'items': ([] if first_run else [desc(f, 'new') for f in added] + [desc(f, 'changed') for f in changed] + [desc(f, 'removed') for f in removed])[:400],
         'failedTypes': [] if SOURCE == 'geofabrik' else [KRU.get(k, k) for k in failed], 'failedRegions': failed_regions, 'source': SOURCE}
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
json.dump({'changed': bool(is_change), 'total': len(feats), 'added': len(added), 'changed_n': len(changed), 'removed': len(removed), 'failed_types': failed, 'failed_regions': failed_regions, 'source': SOURCE}, open(os.path.join(OUTD, 'summary.json'), 'w'))
print('features', len(feats), cnt, 'added', len(added), 'changed', len(changed), 'removed', len(removed))
