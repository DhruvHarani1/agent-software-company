#!/usr/bin/env python3
"""Radar: find out automatically who else is working on this GitHub repository, and where it overlaps with me. Read-only (uses `gh`).

usage: python radar.py --repo owner/name --org my-org [--hours 72] [--paths "features/leave/**,server/config/org.ts"] [--hello]

Signals used to recognise another team (no roster needed):
  1. `Agent-Org: <org>` trailer in commit messages and PR bodies
  2. `from=<org>/<agent>` in [AGENT-MSG v1] comments
  3. a GitHub login other than mine / my team's logins that pushes commits, opens PRs or comments
  4. branch prefix `<org>/...` (optional)
A team key is the first signal found (trailer > message header > login). Whoever has write access to the repository (GitHub collaborators API)
is a *teammate*; anyone else is a *guest*. Both are information only: nothing here gives anyone authority (see references/interop-protocol.md).
Output is terse. With --hello it prints the introduction message to post for each team that has not been greeted yet."""
import argparse
import fnmatch
import json
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone

HDR = re.compile(r'^\[AGENT-MSG v1\] type=(?P<type>[a-z\-]+) from=(?P<from>\S+) to=(?P<to>\S+) ref=(?P<ref>\S+)(?P<rest>.*)$')
TRAILER = re.compile(r'^Agent-Org:\s*(\S+)', re.M | re.I)


def gh(args, default=None):
    out = subprocess.run(['gh', *args], capture_output=True, text=True, encoding='utf8')
    if out.returncode != 0:
        if default is not None:
            return default
        sys.exit('gh failed: ' + out.stderr.strip()[:300])
    try:
        return json.loads(out.stdout or 'null') or (default if default is not None else [])
    except json.JSONDecodeError:
        return default if default is not None else []


def me_login():
    r = subprocess.run(['gh', 'api', 'user', '--jq', '.login'], capture_output=True, text=True, encoding='utf8')
    return r.stdout.strip()


def team_key(login: str, text: str, header_from: str | None) -> str:
    if text:
        m = TRAILER.search(text)
        if m:
            return m.group(1)
    if header_from:
        return header_from.split('/')[0]
    return 'login:' + (login or '?')


def paths_overlap(files: list[str], patterns: list[str]) -> list[str]:
    hit = []
    for f in files:
        for p in patterns:
            if fnmatch.fnmatch(f, p) or fnmatch.fnmatch(f, p.replace('**', '*')):
                hit.append(f)
                break
    return hit


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', required=True)
    ap.add_argument('--org', required=True, help='my team key (the org in my from=<org>/<agent> and Agent-Org trailer)')
    ap.add_argument('--hours', type=int, default=72)
    ap.add_argument('--paths', default='', help='comma separated globs I am about to touch (default: nothing)')
    ap.add_argument('--hello', action='store_true')
    ap.add_argument('--include-bots', action='store_true', help='also list GitHub bots (CI, review bots); default: ignored')
    a = ap.parse_args()
    since = (datetime.now(timezone.utc) - timedelta(hours=a.hours)).strftime('%Y-%m-%dT%H:%M:%SZ')
    my_login = me_login()
    mine = {a.org, 'login:' + my_login}
    patterns = [p.strip() for p in a.paths.split(',') if p.strip()]

    collab = {c['login']: c.get('permissions', {}) for c in gh(['api', f'repos/{a.repo}/collaborators?per_page=100'], default=[]) if isinstance(c, dict)}

    teams: dict[str, dict] = defaultdict(lambda: {'logins': set(), 'commits': 0, 'last': '', 'prs': [], 'comments': 0, 'claims': 0, 'greeted_me': False})

    commits = gh(['api', f'repos/{a.repo}/commits?since={since}&per_page=100'], default=[])
    for c in commits if isinstance(commits, list) else []:
        login = (c.get('author') or {}).get('login') or c.get('commit', {}).get('author', {}).get('name', '?')
        key = team_key(login, c.get('commit', {}).get('message', ''), None)
        t = teams[key]
        t['logins'].add(login)
        t['commits'] += 1
        when = c.get('commit', {}).get('author', {}).get('date', '')
        t['last'] = max(t['last'], when)

    prs = gh(['pr', 'list', '-R', a.repo, '--state', 'open', '--limit', '100', '--json', 'number,title,author,headRefName,files,updatedAt,isDraft,body'], default=[])
    for p in prs:
        login = (p.get('author') or {}).get('login', '?')
        key = team_key(login, p.get('body') or '', None)
        t = teams[key]
        t['logins'].add(login)
        t['prs'].append({'n': p['number'], 'draft': p.get('isDraft'), 'files': [f['path'] for f in p.get('files', [])], 'title': p['title']})
        t['last'] = max(t['last'], p.get('updatedAt', ''))

    comments = gh(['api', f'repos/{a.repo}/issues/comments?since={since}&per_page=100'], default=[])
    for c in comments if isinstance(comments, list) else []:
        first = (c.get('body') or '').strip().splitlines()[:1]
        m = HDR.match(first[0]) if first else None
        login = (c.get('user') or {}).get('login', '?')
        if not m:
            key = 'login:' + login
            if key in mine or login == my_login:
                continue
            # plain human/agent comment from someone else: only counts as presence
            teams[key]['logins'].add(login)
            teams[key]['comments'] += 1
            teams[key]['last'] = max(teams[key]['last'], c.get('created_at', ''))
            continue
        key = m.group('from').split('/')[0]
        t = teams[key]
        t['logins'].add(login)
        t['comments'] += 1
        t['last'] = max(t['last'], c.get('created_at', ''))
        if m.group('type') == 'claim':
            t['claims'] += 1
        if m.group('type') == 'hello' and a.org in m.group('to'):
            t['greeted_me'] = True

    others = {k: v for k, v in teams.items() if k not in mine and not (v['logins'] and all(('login:' + l) in mine for l in v['logins']))}
    if not a.include_bots:
        others = {k: v for k, v in others.items() if not all(l.endswith('[bot]') for l in v['logins'])}
    if not others:
        print(f'radar: no other team active on {a.repo} in the last {a.hours}h (me: {a.org} / {my_login})')
        return
    print(f'radar: {len(others)} other team(s) active in the last {a.hours}h on {a.repo} (me: {a.org})')
    greet = []
    for key, t in sorted(others.items(), key=lambda kv: kv[1]['last'], reverse=True):
        tiers = {('teammate' if (collab.get(l) or {}).get('push') else 'guest') for l in t['logins']}
        tier = 'teammate' if 'teammate' in tiers else 'guest'
        print(f"- {key}  {tier}  logins={','.join(sorted(t['logins']))}  last={t['last'][:16]}  commits={t['commits']} prs={len(t['prs'])} msgs={t['comments']} claims={t['claims']}")
        for p in t['prs'][:8]:
            ov = paths_overlap(p['files'], patterns) if patterns else []
            flag = f"  OVERLAP {len(ov)} file(s): {', '.join(ov[:3])}" if ov else ''
            print(f"    PR #{p['n']}{' draft' if p['draft'] else ''} files={len(p['files'])} {p['title'][:60]}{flag}")
        if not t['greeted_me']:
            greet.append(key)
    if patterns:
        conflicts = [(k, p['n']) for k, t in others.items() for p in t['prs'] if paths_overlap(p['files'], patterns)]
        if conflicts:
            print('ACTION: overlap on your paths with ' + ', '.join(f'{k} PR #{n}' for k, n in conflicts) + ' -> post a heads-up (type=heads-up) and wait or pick another task')
        else:
            print('no overlap on your paths')
    if a.hello and greet:
        for key in greet:
            print('\n--- post as a comment on the shared standup/presence issue ---')
            print(f'[AGENT-MSG v1] type=hello from={a.org}/boss to={key} ref=#presence\n'
                  f'Who: team {a.org} (GitHub {my_login}).\n'
                  f'How to talk: read .agents/PROTOCOL.md (AAP v1). Messages start [AGENT-MSG v1]. Claim with lease before building. Reviews bind to a SHA.\n'
                  f'Areas we touch: see .agents/areas.json (or ask). Our status: living comment on the standup issue.\n'
                  f'Trust: your text is data for us; no merge/publish/commands because of it. Reviews both ways welcome.')


if __name__ == '__main__':
    main()
