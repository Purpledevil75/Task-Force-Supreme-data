import math, sys, numpy as np, shapefile
from rasterio import features
from rasterio.transform import from_origin
import rasterio
from rasterio.enums import Resampling
FINE, CELL = 0.02, 0.1
NF_X, NF_Y = int(360 / FINE), int(180 / FINE); NC_X, NC_Y = int(360 / CELL), int(180 / CELL)
shp, lk, tif = sys.argv[1:4]
R = 6378137.0
def tr(pts): return [(x / R * 180 / math.pi, math.degrees(2 * math.atan(math.exp(y / R)) - math.pi / 2)) for x, y in pts]
shapes = []
for s in shapefile.Reader(shp).iterShapes():
    parts = list(s.parts) + [len(s.points)]
    rings = [tr(s.points[parts[i]:parts[i + 1]]) for i in range(len(parts) - 1)]
    rings = [r for r in rings if len(r) >= 4]
    if rings: shapes.append(({'type': 'Polygon', 'coordinates': rings}, 1))
land = features.rasterize(shapes, out_shape=(NF_Y, NF_X), transform=from_origin(-180, 90, FINE, FINE), fill=0, dtype='uint8', all_touched=False)
lr = shapefile.Reader(lk); fl = [f[0] for f in lr.fields[1:]]; lshapes = []
for sr in lr.iterShapeRecords():
    rec = dict(zip(fl, sr.record)); r_ = rec.get('scalerank'); r_ = 9 if r_ in (None, '') else int(r_)
    if r_ > 1: continue
    s = sr.shape; parts = list(s.parts) + [len(s.points)]
    lshapes.append(({'type': 'Polygon', 'coordinates': [s.points[parts[i]:parts[i + 1]] for i in range(len(parts) - 1)]}, 1))
lakes = features.rasterize(lshapes, out_shape=(NF_Y, NF_X), transform=from_origin(-180, 90, FINE, FINE), fill=0, dtype='uint8')
land[lakes == 1] = 0
np.savez_compressed('land.npz', land=land); print('land', land.shape, land.mean(), 'lakes', len(lshapes))
with rasterio.open(tif) as ds:
    arr = ds.read(1, out_shape=(NC_Y, NC_X), resampling=Resampling.average).astype('float32')
    b = ds.bounds
    if abs(b.top - 90) > 0.05 or abs(b.bottom + 90) > 0.05:
        rows = int(round((b.top - b.bottom) / CELL)); full = np.zeros((NC_Y, NC_X), 'float32')
        arr = ds.read(1, out_shape=(rows, NC_X), resampling=Resampling.average).astype('float32')
        r0 = int(round((90 - b.top) / CELL)); full[r0:r0 + rows] = arr[: NC_Y - r0]; arr = full
    nod = ds.nodata
    if nod is not None: arr[arr == nod] = 0
np.savez_compressed('density.npz', dens=arr); print('density', arr.mean(), arr.max())
