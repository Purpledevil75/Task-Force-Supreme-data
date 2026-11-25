#!/bin/bash
# Russian civil sources for NAVAREA XIII/XX/XXI: reachability from abroad and whether they publish warnings.
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'
mkdir -p /tmp/r; cd /tmp/r
for u in https://www.rosmorport.ru/ https://www.rosmorport.ru/filials/navarea/ https://nsr.rosatom.ru/ https://nsr.rosatom.ru/navigatsionnaya-obstanovka/ http://www.hydro-state.ru/ https://structure.mil.ru/structure/forces/hydrographic/info/navwar.htm https://www.ccdcm.ru/ ; do
  f=$(echo $u | md5sum | cut -c1-8).html
  r=$(curl -sL --max-time 40 -A "$UA" -o $f -w "%{http_code} %{size_download}B %{url_effective}" "$u" 2>&1); echo "== $u -> $r"
  [ -s $f ] && iconv -f $(file -bi $f | sed -n 's/.*charset=//p' | grep -qi 1251 && echo cp1251 || echo utf-8) -t utf-8 $f 2>/dev/null | grep -oiE '.{0,80}(navarea|навареа|навип|прип|навигационн[а-я]* предупрежд)[^<]{0,80}' | head -6
  [ -s $f ] && grep -oiE 'href="[^"]*(navarea|navip|prip|nav-?warn|predupr|preduprezhd|navigation)[^"]*"' $f | sort -u | head -8
done
