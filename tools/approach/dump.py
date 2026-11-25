#!/usr/bin/env python3
"""Dump navigable waterways from an OSM extract (already tags-filtered) as JSON lines:
{"id": way id, "k": kind, "n": [node ids], "c": [[lon,lat],...], "name": ...}
kind: river | canal | fairway | tidal_channel | track (seamark recommended_track / navigation_line).
(c) OpenStreetMap contributors, ODbL 1.0."""
import sys, json, osmium

KINDS = {'river', 'canal', 'fairway', 'tidal_channel'}
SEA = {'fairway', 'recommended_track', 'navigation_line'}

class H(osmium.SimpleHandler):
    def __init__(self, out, bbox=None):
        super().__init__(); self.out = out; self.n = 0; self.bbox = bbox
    def way(self, w):
        t = w.tags; k = t.get('waterway')
        if k not in KINDS:
            s = t.get('seamark:type')
            if s not in SEA: return
            k = 'fairway' if s == 'fairway' else 'track'
        try: c = [[round(n.lon, 5), round(n.lat, 5)] for n in w.nodes]
        except osmium.InvalidLocationError: return
        if len(c) < 2: return
        if self.bbox:
            w0, s0, e0, n0 = self.bbox
            if not any(w0 <= x <= e0 and s0 <= y <= n0 for x, y in c): return
        rec = {'id': w.id, 'k': k, 'n': [n.ref for n in w.nodes], 'c': c}
        for tag in ('name', 'ship', 'CEMT', 'tidal', 'boat'):
            if t.get(tag): rec[tag] = t.get(tag)
        self.out.write(json.dumps(rec, separators=(',', ':')) + '\n'); self.n += 1

if __name__ == '__main__':
    src, dst = sys.argv[1], sys.argv[2]
    with open(dst, 'w') as f:
        h = H(f); h.apply_file(src, locations=True, idx='flex_mem')
    print('ways', h.n, file=sys.stderr)
