#!/usr/bin/env python3
"""Extract OSM routeing measures (seamark:type = TSS parts, precautionary areas, VTS calling-in points ...)
from Geofabrik country extracts, one region at a time (download -> osmium tags-filter -> osmium export -> delete).
No Overpass involved. Output: tools/tss/out/geofabrik.geojsonseq (one GeoJSON feature per line, with @type/@id/@version/@timestamp)
and tools/tss/out/geofabrik-status.json (regions done / failed).
Needs: osmium-tool (apt install osmium-tool), curl.
(c) OpenStreetMap contributors, ODbL 1.0."""
import json, os, subprocess, sys, time, urllib.request
H = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(H, 'out'); os.makedirs(OUT, exist_ok=True)
WORK = os.environ.get('TSS_WORK', '/tmp/tsswork'); os.makedirs(WORK, exist_ok=True)
UA = 'TaskForceSupreme-data/0.3 (+https://github.com/Purpledevil75/Task-Force-Supreme-data)'
TYPES = ['separation_zone', 'separation_line', 'separation_lane', 'separation_boundary', 'separation_crossing', 'separation_roundabout',
         'inshore_traffic_zone', 'precautionary_area', 'deep_water_route_part', 'deep_water_route_centreline', 'two-way_route_part',
         'recommended_track', 'calling-in_point']
# aggregates that duplicate their member countries
SKIP = {'dach', 'alps', 'britain-and-ireland', 'us-midwest', 'us-northeast', 'us-pacific', 'us-south', 'us-west'}
SPLIT = {'us'}           # too big as one file: use its children (states)
LIMIT = int(os.environ.get('TSS_LIMIT', '0'))   # >0: only the first N regions (CI smoke test)

def regions():
    req = urllib.request.Request('https://download.geofabrik.de/index-v1-nogeom.json', headers={'User-Agent': UA})
    idx = json.load(urllib.request.urlopen(req, timeout=120))['features']
    P = {f['properties']['id']: f['properties'] for f in idx}
    kids = {}
    for p in P.values(): kids.setdefault(p.get('parent'), []).append(p['id'])
    tops = kids.get(None, [])
    out = []
    for t in tops:
        if t == 'russia' or not kids.get(t): out.append(t); continue      # russia: one country file; antarctica: no children
        for c in kids[t]:
            if c in SKIP: continue
            if c in SPLIT: out += kids.get(c, [])
            else: out.append(c)
    seen, res = set(), []
    for r in out:
        if r in seen or 'pbf' not in P[r].get('urls', {}): continue
        seen.add(r); res.append((r, P[r]['urls']['pbf']))
    return res

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode: raise RuntimeError(' '.join(cmd[:2]) + ': ' + (r.stderr or r.stdout)[-300:])

def main():
    regs = regions()
    if LIMIT: regs = regs[:LIMIT]
    print('regions:', len(regs), flush=True)
    dst = open(os.path.join(OUT, 'geofabrik.geojsonseq'), 'w', encoding='utf-8')
    done, failed, nfeat, t0 = [], [], 0, time.time()
    flt = ['nwr/seamark:type=' + ','.join(TYPES)]
    for i, (rid, url) in enumerate(regs):
        pbf, sub, js = os.path.join(WORK, 'r.osm.pbf'), os.path.join(WORK, 'f.osm.pbf'), os.path.join(WORK, 'f.geojsonseq')
        ok = False
        for attempt in range(3):
            try:
                run(['curl', '-sfL', '--retry', '3', '--retry-delay', '20', '-A', UA, '-o', pbf, url])
                run(['osmium', 'tags-filter', '--overwrite', '-o', sub, pbf] + flt)
                run(['osmium', 'export', '--overwrite', '-f', 'geojsonseq', '-x', 'print_record_separator=false',
                     '-a', 'type,id,version,timestamp', '-o', js, sub])
                n = 0
                for line in open(js, encoding='utf-8'):
                    line = line.strip()
                    if line: dst.write(line + '\n'); n += 1
                nfeat += n; ok = True; break
            except Exception as ex:
                print('  retry', rid, str(ex)[:200], flush=True); time.sleep(30 * (attempt + 1))
        for f in (pbf, sub, js):
            try: os.remove(f)
            except OSError: pass
        (done if ok else failed).append(rid)
        print(f'[{i+1}/{len(regs)}] {rid} {"ok" if ok else "FAILED"} total {nfeat} ({int(time.time()-t0)}s)', flush=True)
    dst.close()
    json.dump({'done': done, 'failed': failed, 'features': nfeat}, open(os.path.join(OUT, 'geofabrik-status.json'), 'w'))
    print('done', len(done), 'failed', failed, 'features', nfeat)

if __name__ == '__main__':
    main()
