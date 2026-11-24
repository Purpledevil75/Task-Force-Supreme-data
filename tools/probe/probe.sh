#!/bin/bash
# Chile SHOA reachability from GitHub runner (US): DNS, TCP, HTTP with long timeout, 3 attempts.
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'
getent hosts www.shoa.mil.cl; getent hosts www.shoa.cl
for u in 'https://www.shoa.mil.cl/php/radioavisos.php?idioma=es' 'http://www.shoa.mil.cl/php/radioavisos.php?idioma=es' 'https://www.shoa.cl/'; do
 for k in 1 2 3; do curl -s -o /dev/null --max-time 90 -A "$UA" -w "$u try$k: %{http_code} connect=%{time_connect}s total=%{time_total}s err=%{errormsg}\n" "$u"; done; done
echo "== Brazil (CHM) once more"; curl -s -o /dev/null -A "$UA" -w "%{http_code} %{size_download}\n" 'https://www.marinha.mil.br/chm/sites/www.marinha.mil.br.chm/files/2026-11-%5BDEV%5D/avradio_65.json'
