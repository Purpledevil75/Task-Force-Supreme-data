# Task Force Supreme — open data

Open data sets used by the **Task Force Supreme** navigation planning app, published here so they can be
updated independently of the app and as required by the Open Database License.

| Path | What | Source / licence | Updated |
|---|---|---|---|
| `tss/tss.json` | Traffic separation schemes and other routeing measures (zones, lines, lanes, precautionary areas, deep-water routes, VTS calling-in points) | © OpenStreetMap contributors, [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/) | weekly (Mondays), automatic |
| `tss/changes.json` | Change log: added / changed / removed objects with OSM ids | same | with every change |
| `manifest.json` | Versions and checksums of the data sets (read by the app's update check) | — | with every change |

**Not for navigation.** OpenStreetMap coverage of routeing measures is incomplete and is not checked against official
charts or IMO *Ships' Routeing*. Always use official ENC/ECDIS and nautical publications.

## Format of `tss/tss.json`
`{"updated": "YYYY-MM-DD", "license": "...", "counts": {...}, "f": [feature, ...]}` where a feature is
`{"id": "w123", "v": version, "ts": "last edit date", "k": kind, "n": name?, "g": [lon,lat] | [[lon,lat],...], "m": [[[lon,lat],...],...]?, "cha"/"cal"/"ori": channel/callsign/orientation?}`.
Kinds: `z` separation zone, `l` separation line, `n` lane, `b` boundary, `c` crossing, `r` roundabout, `i` inshore traffic zone,
`p` precautionary area, `d` deep-water route part, `D` deep-water route centreline, `t` two-way route part, `k` recommended track, `C` calling-in point.

Data are fetched with `tools/tss/fetch.py` (Overpass API) by the workflow in `.github/workflows/tss.yml`.
