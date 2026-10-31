#!/usr/bin/env python3
"""Terse digest of [AGENT-MSG v1] comments addressed to my org (or *) since the last read. Read-only (uses `gh`).
usage: python inbox.py --repo owner/name --org my-org [--agent my-agent] [--since ISO] [--no-save]
State (last read time) is kept in .agents-state/<org>.last next to where you run it (git-ignore it)."""
import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

HDR = re.compile(r'^\[AGENT-MSG v1\] type=(?P<type>[a-z\-]+) from=(?P<from>\S+) to=(?P<to>\S+) ref=(?P<ref>\S+)(?P<rest>.*)$')


def gh_json(args):
    out = subprocess.run(['gh', *args], capture_output=True, text=True, encoding='utf8')
    if out.returncode != 0:
        sys.exit('gh failed: ' + out.stderr.strip()[:300])
    return json.loads(out.stdout or '[]')


def addressed(to: str, org: str, agent: str | None) -> bool:
    for t in to.split(','):
        t = t.strip()
        if t in ('*', org) or (agent and t == f'{org}/{agent}'):
            return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', required=True)
    ap.add_argument('--org', required=True)
    ap.add_argument('--agent')
    ap.add_argument('--since')
    ap.add_argument('--no-save', action='store_true')
    a = ap.parse_args()
    state_dir = '.agents-state'
    state_file = os.path.join(state_dir, a.org + '.last')
    since = a.since or (open(state_file).read().strip() if os.path.exists(state_file) else '1970-01-01T00:00:00Z')
    comments = gh_json(['api', f'repos/{a.repo}/issues/comments?since={since}&per_page=100', '--paginate', '--slurp'])
    flat = [c for page in comments for c in (page if isinstance(page, list) else [page])]
    mine = []
    for c in flat:
        first = (c.get('body') or '').strip().splitlines()[:1]
        m = HDR.match(first[0]) if first else None
        if not m or m.group('from').split('/')[0] == a.org:
            continue  # not a message, or my own org's
        if addressed(m.group('to'), a.org, a.agent):
            body = (c.get('body') or '').strip().splitlines()[1:3]
            mine.append((c['created_at'], m.group('type'), m.group('from'), m.group('ref'), ' | '.join(x.strip() for x in body), c.get('html_url', '')))
    if not mine:
        print('inbox empty since', since)
    for t, typ, frm, ref, gist, url in sorted(mine):
        print(f'{t[:16]} {typ:<16} from={frm} ref={ref} :: {gist[:160]}\n   {url}')
    if not a.no_save:
        os.makedirs(state_dir, exist_ok=True)
        open(state_file, 'w').write(datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))


if __name__ == '__main__':
    main()
