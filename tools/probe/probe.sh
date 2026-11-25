#!/bin/bash
# Russian civil sources (Rosmorport, Rosatomport/Hydrographic enterprise): do they publish NAVAREA XX/XXI warnings?
export LC_ALL=C.UTF-8
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'
mkdir -p /tmp/r; cd /tmp/r
show() { python3 - "$1" <<'PY'
import sys,re,html
s=open(sys.argv[1],'rb').read()
for enc in ('utf-8','cp1251'):
    try: s=s.decode(enc); break
    except: pass
links=sorted(set(re.findall(r'href="([^"]+)"[^>]*>([^<]{0,80})',s)))
for h,t in links:
    if re.search(r'navarea|navip|prip|navtex|предупрежд|навигацион|НАВАРЕА|NAVAREA|гмссб|gmdss|msi',h+t,re.I): print('  LINK',h,'|',t.strip())
t=html.unescape(re.sub(r'<[^>]+>',' ',re.sub(r'<(script|style)\b.*?</\1>','',s,flags=re.S)))
for m in re.finditer(r'.{0,100}(NAVAREA|НАВАРЕА|НАВИП|ПРИП|навигационн\w* предупрежд).{0,100}',t,re.I): print('  TEXT',' '.join(m.group(0).split()))
PY
}
for u in https://www.rosmorport.ru/ https://www.rosmorport.ru/sitemap/ https://rosatomport.ru/navigationservices https://rosatomport.ru/ ; do
  f=$(echo $u | md5sum | cut -c1-8).html
  r=$(curl -sL --max-time 40 -A "$UA" -o $f -w "%{http_code} %{size_download}B %{url_effective}" "$u"); echo "== $u -> $r"
  [ -s $f ] && show $f | head -25
done
