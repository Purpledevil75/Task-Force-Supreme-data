#!/usr/bin/env python3
"""Collect NAVAREA / HYDRO / coastal navigational warnings in force from the official coordinators' public pages
and write one normalized JSON (navwarn/navwarn.json) + manifest entry.

Each message: {id, area, kind, ref, num, yr, dtg, t (full text), src, seen (UTC date first collected)}
  area: I, IV, X, XI, ... or HYDROLANT/HYDROPAC/HYDROARC;  kind: navarea | hydro | coastal | bulletin
If a source fails, its messages from the previous run are kept and the failure is reported in 'sources'.
Texts are official public safety broadcasts; this is NOT a substitute for SafetyNET/NAVTEX reception (SOLAS IV)."""
import hashlib, html, json, os, re, subprocess, sys, time, traceback, urllib.parse, urllib.request
H = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(H, '..', '..')
OUTD = os.path.join(ROOT, 'navwarn'); os.makedirs(OUTD, exist_ok=True)
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'
NOW = time.strftime('%Y-%m-%dT%H:%MZ', time.gmtime())
TODAY = time.strftime('%Y-%m-%d', time.gmtime())
DEBUG = os.environ.get('NW_DEBUG')

def get(url, data=None, timeout=60, binary=False, headers=None):
    hd = {'User-Agent': UA}
    if headers: hd.update(headers)
    if data is not None and not isinstance(data, bytes): data = urllib.parse.urlencode(data).encode()
    if data is not None: hd.setdefault('Content-Type', 'application/x-www-form-urlencoded')
    last = None
    for a in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=hd), timeout=timeout) as r:
                b = r.read()
                return b if binary else b.decode(r.headers.get_content_charset() or 'utf-8', 'replace')
        except Exception as ex:
            last = ex; time.sleep(5 * (a + 1))
    raise last

def text_of(h):
    h = re.sub(r'<(script|style)\b.*?</\1>', '', h, flags=re.S | re.I)
    h = re.sub(r'<br\s*/?>', '\n', h, flags=re.I)
    h = re.sub(r'</(p|div|tr|li|h\d|pre|section)>', '\n', h, flags=re.I)
    h = re.sub(r'<[^>]+>', '', h)
    t = html.unescape(h).replace('\r', '').replace('\xa0', ' ')
    return '\n'.join(l.strip() for l in t.split('\n'))

def clean(t):
    t = html.unescape(t).replace('\r', '').replace('\xa0', ' ')
    lines = [l.strip() for l in t.split('\n')]
    while lines and not lines[0]: lines.pop(0)
    while lines and not lines[-1]: lines.pop()
    out = []
    for l in lines:
        if l or (out and out[-1]): out.append(l)
    return '\n'.join(out)

ROMAN = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10, 'XI': 11, 'XII': 12, 'XIII': 13,
         'XIV': 14, 'XV': 15, 'XVI': 16, 'XVII': 17, 'XVIII': 18, 'XIX': 19, 'XX': 20, 'XXI': 21}

def msg(area, kind, ref, t, src, dtg=''):
    m = re.search(r'(\d{1,5})\s*/\s*(\d{2,4})', ref)
    num, yr = (int(m.group(1)), int(m.group(2))) if m else (0, 0)
    if 0 < yr < 100: yr += 2000
    series = re.sub(r'[^A-Z0-9]+', '', ref.split(str(num))[0].upper()) if m else re.sub(r'\W+', '', ref.upper())[:20]
    mid = f'{series}-{num}-{yr}' if m else series + '-' + hashlib.md5(t.encode()).hexdigest()[:8]
    return {'id': mid, 'area': area, 'kind': kind, 'ref': ' '.join(ref.split()), 'num': num, 'yr': yr, 'dtg': ' '.join(dtg.split()), 't': clean(t), 'src': src}

def is_bulletin(t):
    return bool(re.search(r'((?:WARNINGS?|MESSAGES?)\s+IN\s*FORCE|IN\s*FORCE\s+AS\s+OF|INFORCE\s+AT)', t[:200], re.I))

# ------------------------------------------------------------------ sources
def ukho():
    """NAVAREA I + UK coastal (WZ) - UKHO Radio Navigational Warnings page."""
    h = get('https://msi.admiralty.co.uk/RadioNavigationalWarnings')
    out = []
    for m in re.finditer(r'id="Details_WarningType_(\d+)"[^>]*>(.*?)</h1>.*?id="Details_Reference_\1"[^>]*>(.*?)</h2>.*?id="Details_DateTimeGroupRnwFormat_\1"[^>]*>(.*?)</h3>.*?id="Details_Description_\1"[^>]*>(.*?)</pre>', h, re.S):
        typ, ref, dtg, desc = (html.unescape(x).strip() for x in m.group(2, 3, 4, 5))
        kind = 'navarea' if 'NAVAREA' in typ.upper() else 'coastal'
        out.append(msg('I', kind, ref, desc, 'UKHO', dtg))
    if not out: raise RuntimeError('no warnings parsed')
    return out

NGA_AREAS = {'4': ('IV', 'navarea', 'NAVAREA IV'), '12': ('XII', 'navarea', 'NAVAREA XII'), 'A': ('HYDROLANT', 'hydro', 'HYDROLANT'),
             'P': ('HYDROPAC', 'hydro', 'HYDROPAC'), 'C': ('HYDROARC', 'hydro', 'HYDROARC')}
def nga():
    """NAVAREA IV, XII, HYDROLANT, HYDROPAC, HYDROARC - NGA MSI API, or its daily in-force memos when the portal is down."""
    out, note = [], ''
    try:
        d = json.loads(get('https://msi.nga.mil/api/publications/broadcast-warn?output=json&status=active', headers={'Accept': 'application/json'}))
        for w in d.get('broadcast-warn', []):
            a = NGA_AREAS.get(str(w.get('navArea')))
            if not a: continue
            ref = f"{a[2]} {w.get('msgNumber')}/{str(w.get('msgYear'))[-2:]}" + (f" ({w['subregion']})" if w.get('subregion') else '')
            out.append(msg(a[0], a[1], ref, w.get('text', ''), 'NGA', w.get('issueDate', '')))
        note = 'api'
    except Exception as ex:
        note = 'daily memo (API: %s)' % str(ex)[:60]
        for code, f in (('4', 'IV'), ('12', 'XII'), ('A', 'LAN'), ('P', 'PAC'), ('C', 'ARC')):
            area, kind, series = NGA_AREAS[code]
            t = get(f'https://msi.nga.mil/apology_objects/DailyMem{f}.txt').replace('\r', '')
            parts = re.split(r'(?m)^(\d{6}Z [A-Z]{3} \d{2})\s*$', t)
            for i in range(1, len(parts) - 1, 2):
                dtg, body = parts[i], parts[i + 1].strip()
                first = body.split('\n', 1)[0].strip().rstrip('.')
                if not re.match(r'(NAVAREA|HYDRO)', first): continue
                out.append(msg(area, kind, first, body.split('\n', 1)[1] if '\n' in body else '', 'NGA', dtg))
    if not out: raise RuntimeError('no warnings parsed')
    return out, note

def amsa():
    """NAVAREA X + AUSCOAST - AMSA MSI publication."""
    t = text_of(get('https://www.operations.amsa.gov.au/AMSA.Web.MSIPublication/Home'))
    out = []
    for blk in re.findall(r'SECURITE\s*\n(.*?)\bNNNN', t, re.S):
        lines = [l.strip() for l in blk.strip().split('\n')]
        dtg = ''
        if lines and lines[0].startswith('FM '):
            m = re.search(r'(\d{6}Z [A-Z]{3} \d{2})', lines[0]); dtg = m.group(1) if m else ''; lines = lines[1:]
        if not lines: continue
        ref = lines[0]
        kind = 'navarea' if ref.upper().startswith('NAVAREA') else 'coastal'
        out.append(msg('X', kind, ref, '\n'.join(lines[1:]), 'AMSA', dtg))
    if not out: raise RuntimeError('no warnings parsed')
    return out

def maritimenz():
    """NAVAREA XIV + NZ coastal - Maritime NZ."""
    h = get('https://www.maritimenz.govt.nz/navigational-warnings/')
    out = []
    for g in re.finditer(r'mnz-navarea-warnings__group-title">(.*?)</h2>(.*?)(?=mnz-navarea-warnings__group-title"|$)', h, re.S):
        title = html.unescape(g.group(1)).strip()
        kind = 'navarea' if 'NAVAREA' in title.upper() else 'coastal'
        for it in re.finditer(r'__item-title">(.*?)</h3>.*?__item-body">(.*?)</div>', g.group(2), re.S):
            body = clean(text_of(it.group(2)))
            lines = body.split('\n')
            ref = lines[0] if re.search(r'\d+/\d+', lines[0]) else f"{title.split(' warn')[0]} {it.group(1).strip()}"
            body = '\n'.join(lines[1:] if lines[0] == ref else lines)
            out.append(msg('XIV', kind, ref.replace(' WARNING ', ' '), re.sub(r'\n?NNNN\s*$', '', body), 'Maritime NZ'))
    if not out: raise RuntimeError('no warnings parsed')
    return out

def kystverket():
    """NAVAREA XIX - Norwegian Coastal Administration."""
    t = text_of(get('https://kyvreports.kystverket.no/NavcoReport/navareaxixvarsler.aspx'))
    out = []
    for m in re.finditer(r'Number:\s*(\S+)\s*\n\s*Date:\s*(.*?)\n\s*Warning:\s*(.*?)(?=\n\s*Number:|\Z)', t, re.S):
        body = clean(m.group(3)).split('\n')
        ref = body[0] if body and body[0].upper().startswith('NAVAREA') else 'NAVAREA XIX ' + m.group(1)
        out.append(msg('XIX', 'navarea', ref, '\n'.join(body[1:] if body and body[0] == ref else body), 'Kystverket', m.group(2)))
    if not out: raise RuntimeError('no warnings parsed')
    return out

def ccg():
    """NAVAREA XVII, XVIII - Canadian Coast Guard NAVWARN service: in-force bulletins, then every listed message."""
    base = 'https://nis.ccg-gcc.gc.ca/public/rest/messages/en/'
    h = get(base + 'search-navareas?onlyInForce=true')
    out = []
    def one(path):
        t = text_of(get(base + 'message/' + path))
        idm = re.search(r'\nID\s*\n\s*(.+)', t); dm = re.search(r'\nDate\s*\n\s*(.+)', t)
        st = re.search(r'\nStatus\s*\n\s*(.+)', t)
        dsc = re.search(r'\nDescription\s*\n(.*?)(?:\n\s*Position\s*\n|\n\s*Date modified|\Z)', t, re.S)
        if not idm or not dsc: return None
        if st and 'cancel' in st.group(1).lower(): return None
        ref = idm.group(1).strip(); area = 'XVIII' if 'XVIII' in ref else 'XVII'
        return msg(area, 'navarea', ref, dsc.group(1), 'CCG', (dm.group(1).split(' To ')[0] if dm else ''))
    for a in re.finditer(r'message/(\d+)">\s*(NAVAREA (XVIII|XVII) \d+/\d+)\s*</a>.*?<p>(.*?)</p>', h, re.S):
        area, ref, body = a.group(3), a.group(2), clean(text_of(a.group(4)))
        out.append(msg(area, 'navarea', ref, body, 'CCG'))
        for ym in re.finditer(r'(\d{4}) SERIES:\s*([\d,\s]+)\.', body):
            yr = ym.group(1)
            for n in re.findall(r'\d+', ym.group(2)):
                if f'{int(n)}/{yr}' in ref: continue
                try:
                    m = one(f'NW-NAVAREA{area}-{int(n):04d}-{yr[-2:]}')
                    if m: out.append(m)
                except Exception as ex:
                    print('  ccg', area, n, yr, ex, flush=True)
                time.sleep(0.3)
    if not out: raise RuntimeError('no warnings parsed')
    return out

def jcg():
    """NAVAREA XI - Japan Coast Guard (XML list per year + detail pages)."""
    cgi = 'https://www1.kaiho.mlit.go.jp/TUHO/keiho/cgi/'
    out = []
    y0 = int(TODAY[:4])
    for y in range(y0, y0 - 3, -1):
        x = get(cgi + 'warnings.cgi', data={'YEAR': y, 'TYPE': 'NAVAREA11', 'LANG': 'EG'})
        if DEBUG and y == y0: print('JCG list sample:', x[:800], flush=True)
        for mm in re.finditer(r'<Member>(.*?)</Member>', x, re.S):
            f = {k: html.unescape(re.sub(r'<!\[CDATA\[|\]\]>', '', v)).strip() for k, v in re.findall(r'<(\w+)>(.*?)</\1>', mm.group(1), re.S)}
            tana = f.get('tana')
            if not tana: continue
            d = get(cgi + 'disp_warnings.cgi?' + urllib.parse.urlencode({'TYPE': 'NAVAREA11', 'TANA': tana, 'LANG': 'EG'}))
            body = clean(text_of(d))
            if DEBUG and not out: print('JCG detail sample:', body[:800], flush=True)
            m = re.search(r'NO\.\s*(\d{2})-(\d+)\s+Date:\s*(\d{4})/(\d\d)/(\d\d)\s+(\d\d)\s*UTC\s*\n(.*)', body, re.S)
            if m:
                ref = f'NAVAREA XI {int(m.group(2))}/{m.group(1)}'
                dtg = f'{m.group(5)}{m.group(6)}00 UTC ' + time.strftime('%b', time.strptime(m.group(4), '%m')).upper() + ' ' + m.group(3)[2:]
                out.append(msg('XI', 'navarea', ref, m.group(7), 'JCG', dtg))
            else:
                out.append(msg('XI', 'navarea', f"NAVAREA XI {int(f.get('number', '0') or 0)}/{str(y)[2:]}", body, 'JCG'))
            time.sleep(0.3)
    if not out: raise RuntimeError('no warnings parsed')
    return out

def nho():
    """NAVAREA VIII - Indian National Hydrographic Office (PDF of warnings in force)."""
    b = get('https://hydrobharat.gov.in/documents/d/guest/in-force-navarea-viii-warnings-2', binary=True, timeout=90)
    p = '/tmp/nw_in.pdf'; open(p, 'wb').write(b)
    t = subprocess.run(['pdftotext', '-layout', p, '-'], capture_output=True, text=True).stdout.replace('\f', '\n')
    if DEBUG: print('NHO sample:', t[:600], flush=True)
    asof = re.search(r'IN FORCE AS ON\s+(\d{1,2} [A-Z]{3} \d{4})', t)
    if asof:
        age = (time.time() - time.mktime(time.strptime(asof.group(1).title(), '%d %b %Y'))) / 86400
        if age > 60: raise RuntimeError('published list is stale (in force as on %s)' % asof.group(1))
    t = re.sub(r'(?m)^\s*-{10,}\s*$', '', t)
    t = re.sub(r'(?m)^\s*NAVAREA VIII\s*-\s*WARNINGS IN FORCE.*$', '', t)
    parts = re.split(r'(?m)^\s*(\d{6}Z/?\s?[A-Z]{3} \d{2})\s*$', t)
    out = []
    for i in range(1, len(parts) - 1, 2):
        body = parts[i + 1].strip('\n')
        lines = body.strip().split('\n')
        if not lines or not re.match(r'\s*NAVAREA\s+VIII', lines[0]): continue
        ref = re.sub(r'\s*-\s*(\d)', r' \1', lines[0].strip())
        out.append(msg('VIII', 'navarea', ref, '\n'.join(l.strip() for l in lines[1:]), 'NHO India', parts[i].replace('/', ' ')))
    note = ('list as on ' + asof.group(1)) if asof else ''
    if not out: raise RuntimeError('no warnings parsed (%d chars of text)' % len(t))
    return out, note

def shn():
    """NAVAREA VI - Servicio de Hidrografia Naval (Argentina): English version of the in-force list."""
    h = get('https://www.hidro.gob.ar/nautica/RadioavisosNauticos.asp?op=8', timeout=90)
    i = h.find('id="desplegable"'); j = h.find('</pre>', i)
    if i < 0 or j < 0: raise RuntimeError('page layout changed')
    part = h[i:j]
    upd = re.search(r'Updated on:\s*([\d/]+)', part)
    out = []
    for m in re.finditer(r'<H2>\s*NAVAREA\s*-\s*(\d+)-(\d{4})\s*-\s*(\d\d)/(\d\d)/(\d{4})\s*</H2>(.*?)(?=<H2>|$)', part, re.S | re.I):
        num, yr, dd, mo, yy, body = m.groups()
        dtg = f'{dd}0000 UTC ' + time.strftime('%b', time.strptime(mo, '%m')).upper() + ' ' + yy[2:]
        out.append(msg('VI', 'navarea', f'NAVAREA VI {int(num)}/{yr[2:]}', clean(text_of(body)), 'SHN Argentina', dtg))
    if not out: raise RuntimeError('no warnings parsed')
    return out, ('updated ' + upd.group(1)) if upd else ''

def dhn():
    """NAVAREA XVI - Direccion de Hidrografia y Navegacion (Peru): latest 'MESSAGE IN FORCE' bulletin with full texts."""
    t = text_of(get('https://www.dhn.mil.pe/portal/navarea/radioavisos-warnings', timeout=90))
    a = t.find('ZCZC'); b = t.find('NNNN', a)
    if a < 0 or b < 0: raise RuntimeError('no bulletin found')
    blk = t[a:b]
    hd = re.search(r'DATE:\s*([A-Z]{3})\s+(\d{1,2})\s+(\d{4})\s+TIME\s+(\d{4})', blk)
    dtg = f'{int(hd.group(2)):02d}{hd.group(4)} UTC {hd.group(1)} {hd.group(3)[2:]}' if hd else ''
    parts = re.split(r'(?m)^\s*(NAVAREA XVI \d+/\d+)\s*$', blk)
    out = []
    for k in range(1, len(parts) - 1, 2):
        out.append(msg('XVI', 'navarea', parts[k], parts[k + 1], 'DHN Peru'))
    if hd:
        out.append(msg('XVI', 'bulletin', 'NAVAREA XVI IN FORCE ' + dtg, clean(parts[0]), 'DHN Peru', dtg))
    if not out: raise RuntimeError('no warnings parsed')
    return out

SOURCES = [('UKHO', 'I + UK coastal', ukho), ('NGA', 'IV, XII, HYDROLANT/PAC/ARC', nga), ('AMSA', 'X + AUSCOAST', amsa),
           ('JCG', 'XI', jcg), ('Maritime NZ', 'XIV + NZ coastal', maritimenz), ('CCG', 'XVII, XVIII', ccg),
           ('Kystverket', 'XIX', kystverket), ('SHN Argentina', 'VI', shn), ('DHN Peru', 'XVI', dhn), ('NHO India', 'VIII', nho)]

def main():
    only = set(sys.argv[1:])
    prev_path = os.path.join(OUTD, 'navwarn.json')
    prev = json.load(open(prev_path, encoding='utf-8')) if os.path.exists(prev_path) else {'m': [], 'sources': {}}
    prev_by_src = {}
    for m in prev.get('m', []): prev_by_src.setdefault(m['src'], []).append(m)
    seen = {m['id']: m.get('seen', TODAY) for m in prev.get('m', [])}
    allm, srcs = [], {}
    for name, covers, fn in SOURCES:
        if only and name not in only:
            allm += prev_by_src.get(name, []); srcs[name] = prev.get('sources', {}).get(name, {}); continue
        t0 = time.time()
        try:
            r = fn(); note = ''
            if isinstance(r, tuple): r, note = r
            srcs[name] = {'covers': covers, 'ok': True, 'n': len(r), 'at': NOW, 'note': note}
            allm += r
            print(f'{name}: {len(r)} messages ({int(time.time()-t0)}s) {note}', flush=True)
        except Exception as ex:
            old = prev_by_src.get(name, [])
            ps = prev.get('sources', {}).get(name, {})
            srcs[name] = {'covers': covers, 'ok': False, 'n': len(old), 'at': ps.get('at', ''), 'error': str(ex)[:200], 'failedAt': NOW}
            allm += old
            print(f'{name}: FAILED {ex} - kept {len(old)} old', flush=True)
            if DEBUG: traceback.print_exc()
    uniq = {}
    for m in allm:
        if is_bulletin(m['t']) and m['kind'] != 'coastal': m['kind'] = 'bulletin'
        m['seen'] = seen.get(m['id'], TODAY)
        uniq[m['id']] = m
    msgs = sorted(uniq.values(), key=lambda m: (m['area'], -m['yr'], -m['num']))
    core = json.dumps(msgs, sort_keys=True, ensure_ascii=False)
    changed = core != json.dumps(sorted(prev.get('m', []), key=lambda m: (m['area'], -m['yr'], -m['num'])), sort_keys=True, ensure_ascii=False)
    data = {'updated': NOW if changed else prev.get('updated', NOW), 'checked': NOW, 'sources': srcs, 'm': msgs,
            'note': 'Official public navigational warnings collected from NAVAREA co-ordinators. Not a substitute for SafetyNET/NAVTEX reception.'}
    raw = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
    open(prev_path, 'w', encoding='utf-8').write(raw)
    mp = os.path.join(ROOT, 'manifest.json')
    man = json.load(open(mp)) if os.path.exists(mp) else {'schema': 1, 'datasets': {}}
    man['datasets']['navwarn'] = {'updated': data['updated'], 'count': len(msgs), 'path': 'navwarn/navwarn.json',
                                  'sha256': hashlib.sha256(raw.encode('utf-8')).hexdigest(), 'license': 'official public broadcasts'}
    json.dump(man, open(mp, 'w'), indent=1)
    os.makedirs(os.path.join(H, 'out'), exist_ok=True)
    json.dump({'changed': changed, 'count': len(msgs), 'sources': {k: (v.get('ok'), v.get('n')) for k, v in srcs.items()}}, open(os.path.join(H, 'out', 'summary.json'), 'w'))
    print('total', len(msgs), 'changed', changed)

if __name__ == '__main__':
    main()
