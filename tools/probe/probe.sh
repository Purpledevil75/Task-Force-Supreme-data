#!/bin/bash
# Approach prototype: navigable waterways for a few regions (Tay, Scheldt, Seine, Elbe) -> committed sample for local development.
set -e
sudo apt-get install -y -q osmium-tool >/dev/null; pip install -q osmium
mkdir -p /tmp/w tools/approach/sample; cd /tmp/w
for r in europe/united-kingdom/scotland europe/belgium europe/netherlands/zeeland europe/france/haute-normandie europe/germany/hamburg europe/germany/schleswig-holstein; do
  n=$(basename $r); curl -sL -o $n.pbf https://download.geofabrik.de/$r-latest.osm.pbf; ls -la $n.pbf | awk '{print $5, $9}'
  osmium tags-filter --overwrite -o $n.f.pbf $n.pbf w/waterway=river,canal,fairway,tidal_channel w/seamark:type=fairway,recommended_track,navigation_line
  python3 $GITHUB_WORKSPACE/tools/approach/dump.py $n.f.pbf $GITHUB_WORKSPACE/tools/approach/sample/$n.jsonl
done
cd $GITHUB_WORKSPACE; gzip -9f tools/approach/sample/*.jsonl; ls -la tools/approach/sample
git config user.name probe-bot; git config user.email ci@users.noreply.github.com
git add tools/approach/sample; git commit -qm "approach prototype: waterway samples (OSM, ODbL)"; git pull -q --rebase; git push -q
# 2
