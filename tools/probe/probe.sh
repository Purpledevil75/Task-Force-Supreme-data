#!/bin/bash
# mirror the public inputs of the routing-network build (OSM land polygons, Natural Earth lakes, World Bank ship density)
set -e
mkdir -p /tmp/netin && cd /tmp/netin
curl -fsSL --retry 3 -o simplified.zip https://osmdata.openstreetmap.de/download/simplified-land-polygons-complete-3857.zip
curl -fsSL --retry 3 -o ne_10m_lakes.zip https://naciscdn.org/naturalearth/10m/physical/ne_10m_lakes.zip
curl -fsSL --retry 3 -m 3000 -o density.zip https://datacatalogfiles.worldbank.org/ddh-published/0037580/DR0045406/shipdensity_global.zip
ls -la
cd "$GITHUB_WORKSPACE"
gh release view netin >/dev/null 2>&1 || gh release create netin --title "Routing network inputs" --notes "Mirror of public inputs: OSM simplified land polygons (ODbL, (c) OpenStreetMap contributors), Natural Earth lakes (public domain), World Bank Global Shipping Traffic Density (CC BY 4.0)." --latest=false
gh release upload netin /tmp/netin/simplified.zip /tmp/netin/ne_10m_lakes.zip /tmp/netin/density.zip --clobber
echo uploaded
