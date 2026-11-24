#!/usr/bin/env python3
"""Time zone data for Task Force Supreme from the IANA tz database (public domain).
Downloads tzdata-latest, compiles it with zic (-b fat: explicit transitions up to 2037) and writes
  tz/tz.json       {version, updated, z: {zone: [off0, t1, off1, t2, off2, ...]}}  minutes; t = minutes since 1970 UTC
                   (only transitions from 2000 on; off0 = offset in force on 2000-01-01)
  tz/changes.json  change log: zones whose offsets in the next 3 years differ from the previous data set
Manual corrections (country announced a change that is not in a tzdb release yet) live in tz/corrections.json
and are applied by the app on top of this data."""
import io, json, os, struct, subprocess, tarfile, tempfile, time, urllib.request, hashlib
H = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(H, '..', '..'); OUT = os.path.join(ROOT, 'tz'); os.makedirs(OUT, exist_ok=True)
UA = 'TaskForceSupreme-data/0.1 (+https://github.com/Purpledevil75/Task-Force-Supreme-data)'
T2000 = 946684800

def tzif(path):
    b = open(path, 'rb').read()
    def hdr(o):
        assert b[o:o + 4] == b'TZif', 'not TZif'
        return struct.unpack('>6l', b[o + 20:o + 44])
    isutc, isstd, leap, timecnt, typecnt, charcnt = hdr(0)
    o = 44 + timecnt * 5 + typecnt * 6 + charcnt + leap * 8 + isstd + isutc
    if b[4] >= 0x32:          # v2+: use the 64-bit block
        isutc, isstd, leap, timecnt, typecnt, charcnt = hdr(o); o += 44; tsz = 8
    else:
        o = 44; tsz = 4
    times = struct.unpack('>%d%s' % (timecnt, 'q' if tsz == 8 else 'l'), b[o:o + timecnt * tsz]); o += timecnt * tsz
    idx = b[o:o + timecnt]; o += timecnt
    types = [struct.unpack('>lBB', b[o + 6 * i:o + 6 * i + 6]) for i in range(typecnt)]
    return times, idx, types

def compile_zone(times, idx, types):
    first = next((t for t in types if not t[1]), types[0])[0]
    off = first
    for t, i in zip(times, idx):
        if t <= T2000: off = types[i][0]
    out = [off // 60]; last = off
    for t, i in zip(times, idx):
        if t <= T2000: continue
        o = types[i][0]
        if o == last: continue
        out += [t // 60, o // 60]; last = o
    return out

def main():
    req = urllib.request.Request('https://data.iana.org/time-zones/tzdata-latest.tar.gz', headers={'User-Agent': UA})
    raw = urllib.request.urlopen(req, timeout=120).read()
    tmp = tempfile.mkdtemp(); src = os.path.join(tmp, 'src'); os.makedirs(src)
    tarfile.open(fileobj=io.BytesIO(raw)).extractall(src)
    version = open(os.path.join(src, 'version')).read().strip()
    prevp = os.path.join(OUT, 'tz.json')
    prev = json.load(open(prevp)) if os.path.exists(prevp) else None
    if prev and prev.get('version') == version and not os.environ.get('TZ_FORCE'):
        print('tzdata', version, 'unchanged'); json.dump({'changed': False}, open(os.path.join(H, 'summary.json'), 'w')); return
    zdir = os.path.join(tmp, 'zi')
    files = [f for f in ('africa', 'antarctica', 'asia', 'australasia', 'europe', 'northamerica', 'southamerica', 'etcetera', 'backward') if os.path.exists(os.path.join(src, f))]
    subprocess.run(['zic', '-b', 'fat', '-d', zdir] + [os.path.join(src, f) for f in files], check=True, cwd=src)
    Z = {}
    for dp, _, fs in os.walk(zdir):
        for f in fs:
            name = os.path.relpath(os.path.join(dp, f), zdir).replace(os.sep, '/')
            if name.startswith(('posix/', 'right/')) or name in ('posixrules', 'localtime', 'Factory'): continue
            try: Z[name] = compile_zone(*tzif(os.path.join(dp, f)))
            except Exception as ex: print('skip', name, ex)
    now = int(time.time() // 60); horizon = now + 3 * 366 * 1440
    def window(z):        # offsets in force over [now, now+3y]
        if not z: return None
        out = []; off = z[0]
        for i in range(1, len(z), 2):
            if z[i] <= now: off = z[i + 1]
        out.append(off)
        for i in range(1, len(z), 2):
            if now < z[i] <= horizon: out += [z[i], z[i + 1]]
        return out
    items = []
    if prev:
        pz = prev.get('z', {})
        for name in sorted(set(Z) | set(pz)):
            a, b = window(pz.get(name)), window(Z.get(name))
            if a != b:
                items.append({'zone': name, 'how': 'new' if a is None else 'removed' if b is None else 'changed', 'before': a, 'after': b})
    data = {'version': version, 'updated': time.strftime('%Y-%m-%d'), 'source': 'IANA tz database ' + version + ' (public domain)', 'z': dict(sorted(Z.items()))}
    raw_out = json.dumps(data, separators=(',', ':'))
    open(prevp, 'w').write(raw_out)
    cp = os.path.join(OUT, 'changes.json'); log = json.load(open(cp)) if os.path.exists(cp) else []
    log = [{'date': data['updated'], 'version': version, 'from': prev.get('version') if prev else None, 'zones': len(Z), 'items': items[:300], 'first': prev is None}] + log[:29]
    json.dump(log, open(cp, 'w'), separators=(',', ':'))
    corr = os.path.join(OUT, 'corrections.json')
    if not os.path.exists(corr): json.dump([], open(corr, 'w'))
    json.dump({'changed': True, 'version': version, 'zones': len(Z), 'items': len(items)}, open(os.path.join(H, 'summary.json'), 'w'))
    print('tzdata', version, 'zones', len(Z), 'changed zones (next 3 years)', len(items), 'size', len(raw_out))

if __name__ == '__main__':
    main()
