#!/bin/bash
# NAVAREA VIII: how the site generates the current "Inforce_Navarea_Warn_*.pdf"
cd /tmp
UA="TaskForceSupreme-data/1.0 (+https://github.com/Purpledevil75/Task-Force-Supreme-data)"
curl -sSL -A "$UA" -o p.html "https://hydrobharat.gov.in/navarea-warnings"
grep -n -iE "inforce|in-force|navarea.?warn|\.pdf|jspdf|html2pdf|print|ajax|fetch\(|/o/|/api/|serveResource|p_p_resource|resourceURL" p.html | cut -c1-300 | head -60
echo "== scripts"; grep -oE '<script[^>]+src="[^"]+"' p.html | head -30
