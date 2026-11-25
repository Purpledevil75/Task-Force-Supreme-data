#!/bin/bash
set -e
sudo apt-get install -y -q osmium-tool >/dev/null; pip install -q osmium numpy
mkdir -p /tmp/w; cd /tmp/w
curl -sL -o hn.pbf https://download.geofabrik.de/europe/france/haute-normandie-latest.osm.pbf
osmium tags-filter --overwrite -o hn.f.pbf hn.pbf w/waterway=river,canal,fairway,tidal_channel w/seamark:type=fairway,recommended_track,navigation_line
python3 - <<'PY'
import sys, collections, osmium
sys.path.insert(0, '/home/runner/work/Task-Force-Supreme-data/Task-Force-Supreme-data/tools/approach')
import dump
cells = dump.port_cells('/home/runner/work/Task-Force-Supreme-data/Task-Force-Supreme-data/tools/approach/ports.json')
C = collections.Counter()
class H(osmium.SimpleHandler):
    def way(self, w):
        k, weak = dump.classify(w.tags)
        p = dump.Pass(cells); r = p.keep(w)
        C[(k, weak, bool(r), w.tags.get('name') == 'La Seine')] += 1
        if w.tags.get('name') == 'La Seine' and C[('dbg',)] < 3: C[('dbg',)] += 1; print(dict(w.tags), k, weak, r, len(w.nodes))
H().apply_file('hn.f.pbf', locations=True)
for k, v in sorted(C.items(), key=str): print(k, v)
PY
