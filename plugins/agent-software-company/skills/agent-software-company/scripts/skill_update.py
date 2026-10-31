#!/usr/bin/env python3
"""Check for and fetch a newer version of this skill. Never overwrites anything without --apply.
usage:
  python skill_update.py check                       compare VERSION with the remote one, show the top of its CHANGELOG
  python skill_update.py pull [--apply]              clone the remote skill to <skill>.new and list changed files; --apply swaps it in (old kept as .bak)
Configuration: .skill-source next to this skill's SKILL.md: {"repo": "owner/name", "path": ".", "branch": "main"}"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def source():
    p = os.path.join(HERE, '.skill-source')
    if not os.path.exists(p):
        sys.exit('missing .skill-source (create it: {"repo": "owner/name", "path": ".", "branch": "main"})')
    return json.load(open(p, encoding='utf8'))


def local_version():
    return open(os.path.join(HERE, 'VERSION'), encoding='utf8').read().strip()


def clone(src, tmp):
    url = f"https://github.com/{src['repo']}.git"
    r = subprocess.run(['git', 'clone', '--depth', '1', '-b', src.get('branch', 'main'), url, tmp], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit('clone failed: ' + r.stderr.strip()[:300])
    return os.path.join(tmp, src.get('path', '.'))


def parse(v):
    return tuple(int(x) for x in v.split('.')[:3])


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'check'
    src = source()
    tmp = tempfile.mkdtemp(prefix='skill-update-')
    try:
        remote_dir = clone(src, os.path.join(tmp, 'r'))
        remote_v = open(os.path.join(remote_dir, 'VERSION'), encoding='utf8').read().strip()
        lv = local_version()
        print(f'local {lv}  remote {remote_v}')
        if parse(remote_v) <= parse(lv):
            print('up to date')
            return
        ch = os.path.join(remote_dir, 'CHANGELOG.md')
        if os.path.exists(ch):
            print('--- remote CHANGELOG (top) ---')
            print(''.join(open(ch, encoding='utf8').readlines()[:25]))
        if cmd == 'check':
            print('newer version available: run `pull` to fetch it for review')
            return
        new_dir = HERE + '.new'
        if os.path.exists(new_dir):
            shutil.rmtree(new_dir)
        shutil.copytree(remote_dir, new_dir, ignore=shutil.ignore_patterns('.git'))
        changed = []
        for d, _, fs in os.walk(new_dir):
            for f in fs:
                rel = os.path.relpath(os.path.join(d, f), new_dir)
                old = os.path.join(HERE, rel)
                if not os.path.exists(old) or open(old, 'rb').read() != open(os.path.join(d, f), 'rb').read():
                    changed.append(rel)
        print('changed files:', ', '.join(sorted(changed)) or '(none)')
        risky = [c for c in changed if 'safety-protocol' in c or 'interop-protocol' in c or c.startswith('templates')]
        if risky:
            print('READ THESE (safety / protocol rules changed):', ', '.join(risky))
        if '--apply' in sys.argv:
            bak = HERE + '.bak'
            if os.path.exists(bak):
                shutil.rmtree(bak)
            shutil.copytree(HERE, bak)
            shutil.copy(os.path.join(HERE, '.skill-source'), os.path.join(new_dir, '.skill-source'))
            shutil.rmtree(HERE)
            shutil.move(new_dir, HERE)
            print('applied; previous copy kept at', bak)
        else:
            print('review', new_dir, 'then run: python skill_update.py pull --apply')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    main()
