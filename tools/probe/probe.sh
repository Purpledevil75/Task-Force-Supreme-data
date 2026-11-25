#!/bin/bash
# New compact waterway dump on a few regions -> sample v2 (for the app's approach builder)
set -e
sudo apt-get install -y -q osmium-tool >/dev/null; pip install -q osmium numpy
mkdir -p /tmp/w tools/approach/sample2; cd /tmp/w
for r in europe/belgium europe/france/haute-normandie europe/netherlands/zeeland; do
  n=$(basename $r); curl -sL -o $n.pbf https://download.geofabrik.de/$r-latest.osm.pbf
  osmium tags-filter --overwrite -o $n.f.pbf $n.pbf w/waterway=river,canal,fairway,tidal_channel w/seamark:type=fairway,recommended_track,navigation_line
  python3 $GITHUB_WORKSPACE/tools/approach/dump.py $n.f.pbf $GITHUB_WORKSPACE/tools/approach/sample2/$n.jsonl $GITHUB_WORKSPACE/tools/approach/ports.json
done
cd $GITHUB_WORKSPACE; gzip -9f tools/approach/sample2/*.jsonl; ls -la tools/approach/sample2
git config user.name probe-bot; git config user.email ci@users.noreply.github.com
git add tools/approach/sample2; git commit -qm "approach: compact waterway samples (OSM, ODbL)"; git pull -q --rebase; git push -q
