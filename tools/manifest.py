#!/usr/bin/env python3
"""Recompute manifest.json entries from the data files (used right before committing, after git pull, so parallel
workflows never conflict on manifest.json).  Usage: python tools/manifest.py tss navwarn"""
import hashlib, json, os, sys
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
mp = os.path.join(ROOT, 'manifest.json')
man = json.load(open(mp)) if os.path.exists(mp) else {'schema': 1, 'datasets': {}}
for ds in sys.argv[1:]:
    if ds == 'tss':
        raw = open(os.path.join(ROOT, 'tss', 'tss.json'), encoding='utf-8').read(); d = json.loads(raw)
        man['datasets']['tss'] = {'updated': d['updated'], 'count': len(d['f']), 'path': 'tss/tss.json', 'changes': 'tss/changes.json',
                                  'sha256': hashlib.sha256(raw.encode('utf-8')).hexdigest(), 'license': 'ODbL-1.0'}
    elif ds == 'navwarn':
        raw = open(os.path.join(ROOT, 'navwarn', 'navwarn.json'), encoding='utf-8').read(); d = json.loads(raw)
        man['datasets']['navwarn'] = {'updated': d['updated'], 'count': len(d['m']), 'path': 'navwarn/navwarn.json',
                                      'sha256': hashlib.sha256(raw.encode('utf-8')).hexdigest(), 'license': 'official public broadcasts'}
    elif ds == 'tz':
        raw = open(os.path.join(ROOT, 'tz', 'tz.json'), encoding='utf-8').read(); d = json.loads(raw)
        craw = open(os.path.join(ROOT, 'tz', 'corrections.json'), encoding='utf-8').read()
        man['datasets']['tz'] = {'updated': d['updated'], 'version': d['version'], 'count': len(d['z']), 'path': 'tz/tz.json', 'changes': 'tz/changes.json',
                                 'corrections': 'tz/corrections.json', 'corrections_sha256': hashlib.sha256(craw.encode('utf-8')).hexdigest(),
                                 'sha256': hashlib.sha256(raw.encode('utf-8')).hexdigest(), 'license': 'public domain (IANA tz database)'}
    elif ds == 'approach':
        raw = open(os.path.join(ROOT, 'approach', 'approach.json'), encoding='utf-8').read(); d = json.loads(raw)
        man['datasets']['approach'] = {'updated': d['built'], 'count': len(d['approaches']), 'path': 'approach/approach.json',
                                       'sha256': hashlib.sha256(raw.encode('utf-8')).hexdigest(), 'license': 'ODbL-1.0'}
json.dump(man, open(mp, 'w'), indent=1)
print('manifest:', {k: v.get('updated') for k, v in man['datasets'].items()})
