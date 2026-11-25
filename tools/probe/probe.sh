#!/bin/bash
cd /tmp
curl -sSL -A "TaskForceSupreme-data/1.0 (+https://github.com/Purpledevil75/Task-Force-Supreme-data)" -o p.html "https://hydrobharat.gov.in/navarea-warnings"
sed -n '5385,5480p' p.html | cut -c1-400
