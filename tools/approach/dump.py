#!/usr/bin/env python3
"""Dump navigable waterways near candidate ports from an OSM extract (already tags-filtered) as JSON lines:
{"k": kind, "c": [[lon,lat],...] (simplified), "j": [[pos, node id], ...] graph nodes (way ends and nodes shared with other ways)}
kind: river | canal | fairway | tidal_channel | track (seamark recommended_track / navigation_line); w=1: weak (untagged river/canal,
kept only close to ports). Two passes: (1) which nodes are shared between kept ways, (2) write.
Usage: dump.py ways.pbf out.jsonl ports.json     (c) OpenStreetMap contributors, ODbL 1.0."""
import sys, json, math, array, osmium
import numpy as np

KINDS = {'river', 'canal', 'fairway', 'tidal_channel'}
SEA = {'fairway', 'recommended_track', 'navigation_line'}
CELL = 0.5

def port_cells(path, strong_deg=4.0, weak_deg=0.5):
    pts = json.load(open(path))['p']
    strong, weak = set(), set()
    for lon, lat in pts:
        for S, deg in ((strong, strong_deg), (weak, weak_deg)):
            dl = deg / max(0.2, math.cos(math.radians(lat)))
            for x in range(math.floor((lon - dl) / CELL), math.floor((lon + dl) / CELL) + 1):
                for y in range(math.floor((lat - deg) / CELL), math.floor((lat + deg) / CELL) + 1):
                    S.add(((x + 1440) % 720, y))
    return strong, weak

def classify(t):
    k = t.get('waterway')
    if k in KINDS:
        nav = t.get('CEMT') or t.get('ship') == 'yes' or t.get('boat') == 'yes' or t.get('motorboat') == 'yes' or t.get('tidal') == 'yes'
        weak = k in ('river', 'canal') and not nav
        return k, weak
    s = t.get('seamark:type')
    if s in SEA: return ('fairway' if s == 'fairway' else 'track'), False
    return None, None

class Pass(osmium.SimpleHandler):
    def __init__(self, cells, write=None, shared=None):
        super().__init__(); self.cells = cells; self.write = write; self.shared = shared; self.refs = array.array('q'); self.n = 0
    def keep(self, w):
        k, weak = classify(w.tags)
        if not k: return None
        S = self.cells[1] if weak else self.cells[0]
        nodes = w.nodes; L = len(nodes)
        if L < 2: return None
        for i in list(range(0, L, 4)) + [L - 1]:
            n = nodes[i]
            if not n.location.valid(): continue
            if ((int(math.floor(n.lon / CELL)) + 1440) % 720, int(math.floor(n.lat / CELL))) in S: return k, weak
        return None
    def way(self, w):
        r = self.keep(w)
        if not r: return
        k, weak = r
        if self.write is None:
            self.refs.extend(n.ref for n in w.nodes); return
        try: c = [(n.lon, n.lat) for n in w.nodes]
        except osmium.InvalidLocationError: return
        ids = np.fromiter((n.ref for n in w.nodes), dtype=np.int64, count=len(w.nodes))
        pos = np.searchsorted(self.shared, ids); pos[pos >= len(self.shared)] = 0
        isj = self.shared[pos] == ids; isj[0] = isj[-1] = True
        jpos = np.nonzero(isj)[0]
        keepc = simplify(c, set(int(p) for p in jpos))
        remap = {p: i for i, p in enumerate(keepc)}
        rec = {'k': k, 'c': [[round(c[p][0], 5), round(c[p][1], 5)] for p in keepc], 'j': [[remap[int(p)], int(ids[p])] for p in jpos]}
        if weak: rec['w'] = 1
        self.write.write(json.dumps(rec, separators=(',', ':')) + '\n'); self.n += 1

def simplify(c, must, tol=0.0002):    # ~20 m Douglas-Peucker in degrees, keeping graph nodes
    n = len(c); keep = [False] * n
    for p in must: keep[p] = True
    order = sorted(must)
    for s, e in zip(order, order[1:]):
        st = [(s, e)]
        while st:
            a, b = st.pop()
            if b <= a + 1: continue
            ax, ay = c[a]; bx, by = c[b]; dx, dy = bx - ax, by - ay; L = dx * dx + dy * dy
            best, bd = -1, tol
            for i in range(a + 1, b):
                px, py = c[i]; t = ((px - ax) * dx + (py - ay) * dy) / L if L else 0; t = max(0, min(1, t))
                d = math.hypot(px - ax - t * dx, py - ay - t * dy)
                if d > bd: bd, best = d, i
            if best > 0: keep[best] = True; st += [(a, best), (best, b)]
    return [i for i in range(n) if keep[i]]

if __name__ == '__main__':
    src, dst, ports = sys.argv[1], sys.argv[2], sys.argv[3]
    cells = port_cells(ports)
    print('cells near ports: strong', len(cells[0]), 'weak', len(cells[1]), file=sys.stderr, flush=True)
    idx = 'sparse_file_array,/tmp/nodes.idx'
    p1 = Pass(cells); p1.apply_file(src, locations=True, idx=idx)
    refs = np.frombuffer(p1.refs, dtype=np.int64)
    u, cnt = np.unique(refs, return_counts=True); shared = u[cnt > 1]; del refs, u, cnt; p1.refs = None
    print('pass 1: shared nodes', len(shared), file=sys.stderr, flush=True)
    with open(dst, 'w') as f:
        p2 = Pass(cells, f, shared); p2.apply_file(src, locations=True, idx=idx)
    print('ways', p2.n, file=sys.stderr)
