#!/usr/bin/env python3
"""Dump navigable waterways from an OSM extract (already tags-filtered) as JSON lines:
{"id": way id, "k": kind, "n": [node ids], "c": [[lon,lat],...], "name": ...}
kind: river | canal | fairway | tidal_channel | track (seamark recommended_track / navigation_line).
(c) OpenStreetMap contributors, ODbL 1.0."""
import sys, json, osmium

KINDS = {'river', 'canal', 'fairway', 'tidal_channel'}
SEA = {'fairway', 'recommended_track', 'navigation_line'}

def port_cells(ports_js, strong_deg=4.0, weak_deg=0.5, cell=0.5):
    """0.5-degree cells near candidate ports (straight approach over land or long): navigable waterways within strong_deg,
    untagged small rivers only within weak_deg."""
    import math
    txt = open(ports_js, encoding='utf-8').read()
    if ports_js.endswith('.json'): pts = json.loads(txt)['p']          # [[lon,lat],...] candidate ports
    else:
        d = json.loads(txt[txt.index('=') + 1:txt.rindex(';')]); f = {k: i for i, k in enumerate(d['fields'])}
        pts = [(r[f['lon']], r[f['lat']]) for r in d['rows'] if r[f['snapLand']] == 1 or (r[f['snapNM']] or 0) > 3]
    strong, weak = set(), set()
    for lon, lat in pts:
        for S, deg in ((strong, strong_deg), (weak, weak_deg)):
            dl = deg / max(0.2, math.cos(math.radians(lat)))
            for x in range(math.floor((lon - dl) / cell), math.floor((lon + dl) / cell) + 1):
                for y in range(math.floor((lat - deg) / cell), math.floor((lat + deg) / cell) + 1):
                    S.add(((x + 360 * 2) % 720, y))
    return strong, weak

class H(osmium.SimpleHandler):
    def __init__(self, out, bbox=None, cells=None):
        super().__init__(); self.out = out; self.n = 0; self.bbox = bbox; self.cells = cells
    def way(self, w):
        t = w.tags; k = t.get('waterway')
        if k not in KINDS:
            s = t.get('seamark:type')
            if s not in SEA: return
            k = 'fairway' if s == 'fairway' else 'track'
        try: c = [[round(n.lon, 5), round(n.lat, 5)] for n in w.nodes]
        except osmium.InvalidLocationError: return
        if len(c) < 2: return
        if self.cells:
            weak = k == 'river' and not (t.get('CEMT') or t.get('ship') == 'yes' or t.get('boat') == 'yes' or t.get('tidal') == 'yes')
            S = self.cells[1] if weak else self.cells[0]
            if not any((((int(x // 0.5)) + 720) % 720, int(y // 0.5)) in S for x, y in c[::4] + [c[-1]]): return
        if self.bbox:
            w0, s0, e0, n0 = self.bbox
            if not any(w0 <= x <= e0 and s0 <= y <= n0 for x, y in c): return
        rec = {'id': w.id, 'k': k, 'n': [n.ref for n in w.nodes], 'c': c}
        for tag in ('name', 'ship', 'CEMT', 'tidal', 'boat'):
            if t.get(tag): rec[tag] = t.get(tag)
        self.out.write(json.dumps(rec, separators=(',', ':')) + '\n'); self.n += 1

if __name__ == '__main__':
    src, dst = sys.argv[1], sys.argv[2]
    cells = port_cells(sys.argv[3]) if len(sys.argv) > 3 else None
    if cells: print('cells near ports: strong', len(cells[0]), 'weak', len(cells[1]), file=sys.stderr)
    with open(dst, 'w') as f:
        h = H(f, cells=cells); h.apply_file(src, locations=True, idx='sparse_file_array,/tmp/nodes.idx' if cells else 'flex_mem')
    print('ways', h.n, file=sys.stderr)
