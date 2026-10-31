#!/usr/bin/env python3
"""List live and stale claims on a repository (read-only, uses `gh`).
usage: python claims.py --repo owner/name
A claim is the latest [AGENT-MSG v1] type=claim comment on an issue that has no later type=release by the same author-org."""
import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone

HDR = re.compile(r'^\[AGENT-MSG v1\] type=(?P<type>[a-z\-]+) from=(?P<from>\S+) to=\S+ ref=(?P<ref>\S+)(?P<rest>.*)$')


def gh(args):
    out = subprocess.run(['gh', *args], capture_output=True, text=True, encoding='utf8')
    if out.returncode != 0:
        sys.exit('gh failed: ' + out.stderr.strip()[:300])
    return json.loads(out.stdout or '[]')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', required=True)
    a = ap.parse_args()
    issues = gh(['issue', 'list', '-R', a.repo, '--label', 'claimed', '--state', 'open', '--json', 'number,title,labels', '--limit', '200'])
    # labels are claimed:<org>; gh --label needs exact names, so also scan all open issues for claim comments
    all_open = gh(['issue', 'list', '-R', a.repo, '--state', 'open', '--json', 'number,title', '--limit', '300'])
    now = datetime.now(timezone.utc)
    rows = []
    for it in all_open:
        comments = gh(['api', f"repos/{a.repo}/issues/{it['number']}/comments?per_page=100"])
        live: dict[str, tuple[str, str]] = {}
        for c in comments:
            first = (c.get('body') or '').strip().splitlines()[:1]
            m = HDR.match(first[0]) if first else None
            if not m:
                continue
            org = m.group('from').split('/')[0]
            if m.group('type') == 'claim':
                lease = re.search(r'lease_until=(\S+)', m.group('rest'))
                live[org] = (m.group('from'), lease.group(1) if lease else '')
            elif m.group('type') == 'release':
                live.pop(org, None)
        for org, (who, lease) in live.items():
            try:
                until = datetime.fromisoformat(lease.replace('Z', '+00:00'))
                state = 'STALE' if until < now else 'live'
            except ValueError:
                state = 'no-lease'
            rows.append((it['number'], org, who, lease, state, it['title']))
    if not rows:
        print('no claims')
    for n, org, who, lease, state, title in sorted(rows):
        print(f'#{n:<5} {state:<8} {who:<24} until={lease or "-":<22} {title[:60]}')


if __name__ == '__main__':
    main()
