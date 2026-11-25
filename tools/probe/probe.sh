#!/bin/bash
# pre-rasterise the public routing-network inputs (land 0.02 deg incl. big lakes opened, ship density on the 0.1 deg grid)
set -e
pip install -q numpy rasterio pyshp
mkdir -p /tmp/netin && cd /tmp/netin
for n in simplified.zip ne_10m_lakes.zip density.zip; do gh release download netin -R "$GITHUB_REPOSITORY" -p $n --clobber; done
unzip -o -q simplified.zip; mkdir -p lakes && unzip -o -q ne_10m_lakes.zip -d lakes; unzip -o -q density.zip
SHP=$(find . -name 'simplified_land_polygons.shp' | head -1); LK=$(find lakes -name '*.shp' | head -1); TIF=$(find . -iname '*.tif' | head -1)
python3 "$GITHUB_WORKSPACE/tools/probe/raster.py" "$SHP" "$LK" "$TIF"
ls -la *.npz
cd "$GITHUB_WORKSPACE"
gh release upload netin /tmp/netin/land.npz /tmp/netin/density.npz --clobber
echo uploaded
