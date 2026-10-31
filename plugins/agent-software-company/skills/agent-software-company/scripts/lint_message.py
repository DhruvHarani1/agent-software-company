#!/usr/bin/env python3
"""Lint an [AGENT-MSG v1] comment before posting it.
usage: python lint_message.py < message.txt        (or: python lint_message.py message.txt)
exit 0 = ok, 1 = problems printed."""
import re
import sys

HEADER = re.compile(r'^\[AGENT-MSG v1\] type=(?P<type>[a-z\-]+) from=(?P<from>[\w\-./]+) to=(?P<to>[\w\-./:,*]+) ref=(?P<ref>#\d+|\S+)(?P<rest>.*)$')
REQUIRED = {
    'claim': ['Task:', 'Plan:'],
    'release': ['Task:', 'State left:', 'Why released:'],
    'handover': ['Goal:', 'Current state:', 'Confirmed facts:', 'Next:', 'Blockers/decisions:', 'Done means:'],
    'question': ['Question:', 'Why it matters:', 'Recommendation:', 'Needed by:'],
    'answer': ['Answer:', 'Source:'],
    'review': ['Verdict:', 'Commit SHA:', 'Checks:', 'Red proof:', 'Problems:'],
    'status': ['Doing:', 'Done:', 'Blocked:', 'Next:'],
    'decision-request': ['Decision needed:', 'Options:', 'Recommendation:', 'Risk:'],
    'hello': ['Who:', 'How to talk:', 'Areas we touch:', 'Trust:'],
    'heads-up': ['Touching:', 'Why:', 'Overlap:', 'Proposal:'],
}
NEEDS_ATTR = {'claim': ['lease_until='], 'review': ['sha='], 'handover': ['sha=']}
FILLER = re.compile(r'\b(i would like to|please note that|basically|just|really|simply|i think that)\b', re.I)


def lint(text: str) -> list[str]:
    problems: list[str] = []
    lines = text.strip().splitlines()
    if not lines:
        return ['empty message']
    m = HEADER.match(lines[0])
    if not m:
        return ['line 1 is not a valid header: [AGENT-MSG v1] type=<type> from=<org>/<agent> to=... ref=#N']
    t = m.group('type')
    if t not in REQUIRED:
        problems.append(f'unknown type "{t}" (known: {", ".join(sorted(REQUIRED))}); readers will ignore it')
        return problems
    for attr in NEEDS_ATTR.get(t, []):
        if attr not in m.group('rest'):
            problems.append(f'header for type={t} needs {attr}<value>')
    body = '\n'.join(lines[1:])
    for sec in REQUIRED[t]:
        if sec not in body:
            problems.append(f'missing section "{sec}"')
    if t == 'review':
        v = re.search(r'Verdict:\s*(\w+)', body)
        if v and v.group(1).upper() not in ('PASS', 'CHANGES'):
            problems.append('Verdict must be PASS or CHANGES')
        sha = re.search(r'sha=([0-9a-f]{7,40})', m.group('rest'))
        if not sha:
            problems.append('review header sha= must be a commit hash (7-40 hex)')
    if len(body) > 1800:
        problems.append(f'long ({len(body)} chars): terse mode wants a short message; move detail to the issue body or a file')
    if FILLER.search(body):
        problems.append('filler words found (terse mode): ' + ', '.join(sorted({x.group(0).lower() for x in FILLER.finditer(body)})))
    return problems


if __name__ == '__main__':
    data = open(sys.argv[1], encoding='utf8').read() if len(sys.argv) > 1 else sys.stdin.read()
    probs = lint(data)
    if probs:
        print('\n'.join('- ' + p for p in probs))
        sys.exit(1)
    print('ok')
