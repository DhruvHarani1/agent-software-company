#!/usr/bin/env python3
"""Reviewable updates: check, fetch/pull, diff, apply --reviewed DIGEST, rollback.

Only check/fetch access the network. Candidate code is never executed.
"""
from __future__ import annotations
import argparse
import ast
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import uuid

HERE = Path(__file__).resolve().parent.parent
SCHEMA = 1
PRESERVE = {'.skill-source', '.agents-state', '.agent-company'}
INTERNAL = {'.skill-install.json'}
IGNORE = {'__pycache__', '.pytest_cache'}
REPO = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*$')
VERSION = re.compile(r'^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$')

class UpdateError(Exception):
    """Cannot proceed while preserving review and recovery guarantees."""


def now():
    return datetime.now(timezone.utc).isoformat()


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding='utf8'))
    except (OSError, ValueError) as exc:
        raise UpdateError(f'cannot read valid JSON: {path}: {exc}') from exc


def write_json(path, value):
    path = Path(path)
    tmp = path.with_name(path.name + '.tmp-' + uuid.uuid4().hex)
    try:
        with tmp.open('x', encoding='utf8') as handle:
            json.dump(value, handle, sort_keys=True, indent=2)
            handle.write('\n')
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def reject_links(path):
    """Reject symbolic links and Windows junctions before resolving paths."""
    path = Path(os.path.abspath(path))
    for item in [path, *path.parents]:
        if item.exists() or item.is_symlink():
            info = item.lstat()
            if item.is_symlink() or getattr(info, 'st_file_attributes', 0) & 0x400:
                raise UpdateError(f'symlink or reparse point is not an update path: {item}')
    return path


def directory(path):
    path = reject_links(path)
    if not path.is_dir():
        raise UpdateError(f'directory does not exist: {path}')
    return path


def separate(a, b):
    a, b = reject_links(a), reject_links(b)
    if a == b or a in b.parents or b in a.parents:
        raise UpdateError(f'paths must not contain each other: {a} and {b}')


def local_name(name):
    return name in PRESERVE or name == '.env' or name.startswith('.env.')


def manifest(root, *, include_local=False):
    """Hash regular files; refuse links/special files anywhere in the tree."""
    root = directory(root)
    result = {}
    for current, dirs, files in os.walk(root, followlinks=False):
        for name in dirs + files:
            path = Path(current) / name
            info = path.lstat()
            if path.is_symlink() or getattr(info, 'st_file_attributes', 0) & 0x400:
                raise UpdateError(f'linked/reparse content is not allowed: {path}')
            if not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode)):
                raise UpdateError(f'special file is not allowed: {path}')
        if any(name.casefold() == '.git' for name in dirs + files):
            raise UpdateError('Git checkouts are not replaced; use their normal Git review workflow')
        dirs[:] = [d for d in dirs if d not in IGNORE]
        for name in files:
            path = Path(current) / name
            rel = path.relative_to(root).as_posix()
            top = PurePosixPath(rel).parts[0]
            if top in INTERNAL or (local_name(top) and not include_local):
                continue
            result[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def source(root):
    src = read_json(directory(root) / '.skill-source')
    if not isinstance(src, dict) or not REPO.fullmatch(str(src.get('repo', ''))):
        raise UpdateError('.skill-source repo must be owner/name on github.com')
    branch = src.get('branch', 'main')
    if (not isinstance(branch, str) or not branch or branch.startswith(('-', '/'))
            or branch.endswith(('/', '.', '.lock')) or '..' in branch or '@{' in branch
            or any(ord(c) < 33 or c in '~^:?*[\\' for c in branch)):
        raise UpdateError('source branch must be a safe branch or tag name')
    subdir = src.get('path', '.')
    if (not isinstance(subdir, str) or not subdir or '\\' in subdir or ':' in subdir
            or PurePosixPath(subdir).is_absolute() or '..' in PurePosixPath(subdir).parts):
        raise UpdateError('source path must be a relative subdirectory without traversal')
    return {'repo': src['repo'], 'branch': branch, 'path': subdir}


def version(root):
    try:
        value = (Path(root) / 'VERSION').read_text(encoding='utf8').strip()
    except OSError as exc:
        raise UpdateError(f'candidate requires VERSION: {exc}') from exc
    if not VERSION.fullmatch(value):
        raise UpdateError('VERSION must be a semantic version such as 1.3.0')
    return value


def validate_payload(root):
    files = manifest(root)
    for item in Path(root).iterdir():
        if local_name(item.name) or item.name in INTERNAL:
            raise UpdateError(f'candidate must not ship local configuration: {item.name}')
    try:
        skill = (Path(root) / 'SKILL.md').read_text(encoding='utf8')
    except OSError as exc:
        raise UpdateError(f'candidate requires SKILL.md: {exc}') from exc
    if not skill.startswith('---\n') or not re.search(r'^name:\s*\S+', skill, re.M) or not re.search(r'^description:\s*\S+', skill, re.M):
        raise UpdateError('candidate SKILL.md requires frontmatter with name and description')
    scripts = Path(root) / 'scripts'
    for path in scripts.rglob('*.py') if scripts.exists() else []:
        try:
            ast.parse(path.read_text(encoding='utf8'), filename=str(path))
        except (SyntaxError, UnicodeError) as exc:
            raise UpdateError(f'candidate Python syntax invalid: {path}: {exc}') from exc
    version(root)
    return files


def run_git(args):
    try:
        run = subprocess.run(['git', *args], capture_output=True, text=True, encoding='utf8', timeout=45)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise UpdateError(f'git unavailable or timed out: {exc}') from exc
    if run.returncode:
        raise UpdateError('git failed: ' + run.stderr.strip()[:300])
    return run.stdout.strip()


def fetch_remote(src, destination):
    run_git(['clone', '--depth', '1', '--branch', src['branch'], '--',
             f"https://github.com/{src['repo']}.git", str(destination)])
    commit = run_git(['-C', str(destination), 'rev-parse', 'HEAD'])
    if not re.fullmatch(r'[0-9a-f]{40,64}', commit):
        raise UpdateError('git did not return an immutable commit ID')
    payload = reject_links(Path(destination) / src['path'])
    if payload != Path(destination) and Path(destination) not in payload.parents:
        raise UpdateError('source subdirectory escaped the clone')
    return payload, commit


def copy_payload(src, dest):
    shutil.copytree(src, dest, ignore=shutil.ignore_patterns('.git', '__pycache__', '.pytest_cache'))


def remote_snapshot(root, callback):
    src = source(root)
    with tempfile.TemporaryDirectory(prefix='skill-fetch-') as tmp:
        checkout = Path(tmp) / 'checkout'
        payload, commit = fetch_remote(src, checkout)
        # Verify before copytree can follow a link. Only checkout-root .git is exempt.
        for current, dirs, files in os.walk(payload, followlinks=False):
            if Path(current) == checkout and '.git' in dirs:
                dirs.remove('.git')
            for name in dirs + files:
                item = reject_links(Path(current) / name)
                mode = item.lstat().st_mode
                if not (stat.S_ISDIR(mode) or stat.S_ISREG(mode)):
                    raise UpdateError(f'special file is not a skill payload: {item}')
                if name.casefold() == '.git':
                    raise UpdateError('nested Git metadata is not a skill payload')
        return callback(src, payload, commit)


def differences(before, after):
    return {'added': sorted(set(after) - set(before)),
            'modified': sorted(k for k in before.keys() & after.keys() if before[k] != after[k]),
            'deleted': sorted(set(before) - set(after))}


def report_changes(changes):
    for kind, paths in changes.items():
        for rel in paths:
            sensitive = rel.startswith(('scripts/', 'templates/')) or rel in ('SKILL.md', 'references/safety-protocol.md', 'references/interop-protocol.md')
            print(f'{kind}: {rel}' + (' [code/policy: review]' if sensitive else ''))
    if not any(changes.values()):
        print('no managed file differences')


def fetch_candidate(root, dest=None):
    root = directory(root)
    baseline = manifest(root)
    store = reject_links(dest or root.parent / (root.name + '.updates'))
    separate(root, store)
    store.mkdir(parents=True, exist_ok=True)

    def retain(src, payload, commit):
        candidate = store / ('candidate-' + uuid.uuid4().hex)
        candidate.mkdir()
        copy_payload(payload, candidate / 'payload')
        target = validate_payload(candidate / 'payload')
        metadata = {'schema': SCHEMA, 'kind': 'candidate', 'created_at': now(),
                    'root': str(root), 'source': src, 'commit': commit,
                    'local_version': version(root), 'candidate_version': version(candidate / 'payload'),
                    'baseline': baseline, 'target': target}
        write_json(candidate / 'candidate.json', metadata)
        print('candidate:', candidate)
        print(f"local {metadata['local_version']}  candidate {metadata['candidate_version']}  commit {commit}")
        report_changes(differences(baseline, target))
        print('review digest:', digest(metadata))
        print('Review files and diff; apply never fetches again.')
        return candidate
    return remote_snapshot(root, retain)


def load_candidate(candidate, root=None):
    candidate = directory(candidate)
    meta = read_json(candidate / 'candidate.json')
    if not isinstance(meta, dict) or meta.get('schema') != SCHEMA or meta.get('kind') != 'candidate':
        raise UpdateError('unsupported candidate metadata')
    if not re.fullmatch(r'[0-9a-f]{40,64}', str(meta.get('commit', ''))):
        raise UpdateError('candidate has no immutable commit')
    if root is not None and reject_links(root) != reject_links(meta.get('root', '')):
        raise UpdateError('candidate was fetched for a different installation')
    if validate_payload(candidate / 'payload') != meta.get('target'):
        raise UpdateError('candidate content changed since fetch; fetch a new candidate for review')
    if not isinstance(meta.get('baseline'), dict):
        raise UpdateError('candidate baseline is missing')
    return candidate, meta


@contextmanager
def update_lock(root):
    lock = reject_links(Path(root).parent / (Path(root).name + '.update.lock'))
    try:
        handle = lock.open('x', encoding='utf8')
    except FileExistsError as exc:
        raise UpdateError(f'update lock exists: {lock}; verify no updater is active before removing a stale lock') from exc
    try:
        with handle:
            handle.write(f'pid={os.getpid()}\n')
        yield
    finally:
        lock.unlink()


def active_writers(root):
    for name in ('.agent-company', '.agents-state'):
        state = Path(root) / name
        if state.exists():
            for item in state.rglob('*'):
                if item.is_file() and (item.name == 'write.lock' or item.name.endswith('.lock')):
                    raise UpdateError(f'active or stale state writer lock exists: {item}')


def copy_local(current, staged):
    for item in Path(current).iterdir():
        if local_name(item.name):
            target = Path(staged) / item.name
            if target.exists():
                raise UpdateError(f'candidate conflicts with preserved local data: {item.name}')
            if item.is_dir():
                shutil.copytree(item, target)
            else:
                shutil.copy2(item, target)


def swap(root, stage, before, after):
    """Two same-volume renames; restore the original if the second rename fails."""
    root, stage = directory(root), directory(stage)
    separate(root, stage)
    if root.parent != stage.parent:
        raise UpdateError('staged installation must be a sibling on the same volume')
    backup = root.parent / (root.name + '.backup-' + uuid.uuid4().hex)
    reject_links(backup)
    backup.mkdir()
    write_json(backup / 'backup.json', {'schema': SCHEMA, 'kind': 'backup', 'created_at': now(),
                                       'root': str(root), 'before': before, 'after': after})
    os.rename(root, backup / 'installation')
    try:
        os.rename(stage, root)
    except OSError as exc:
        try:
            os.rename(backup / 'installation', root)
        except OSError as restore:
            raise UpdateError(f'install and restore failed. Recover {backup / "installation"} to {root}. Cause: {restore}') from exc
        raise UpdateError(f'install failed; original restored. Stage retained at {stage}: {exc}') from exc
    return backup


def apply_candidate(root, candidate, reviewed):
    root = directory(root)
    candidate, meta = load_candidate(candidate, root)
    separate(root, candidate)
    if reviewed != digest(meta):
        raise UpdateError('review digest does not match candidate; inspect diff before applying')
    with update_lock(root):
        active_writers(root)
        if manifest(root) != meta['baseline']:
            raise UpdateError('local files changed since fetch; preserve changes and fetch/review again')
        local_before = manifest(root, include_local=True)
        stage = root.parent / (root.name + '.stage-' + uuid.uuid4().hex)
        reject_links(stage)
        shutil.copytree(candidate / 'payload', stage)
        copy_local(root, stage)
        write_json(stage / '.skill-install.json', {'schema': SCHEMA, 'commit': meta['commit'],
                                                  'source': meta['source'], 'manifest': meta['target']})
        active_writers(root)
        if manifest(root, include_local=True) != local_before:
            raise UpdateError(f'installation changed during staging; nothing replaced; stage retained at {stage}')
        if manifest(stage) != meta['target']:
            raise UpdateError('staged content differs from reviewed candidate')
        backup = swap(root, stage, meta['baseline'], meta['target'])
    print('applied exact candidate commit:', meta['commit'])
    print('backup:', backup)
    return backup


def rollback(root, backup):
    root, backup = reject_links(root), directory(backup)
    directory(root.parent)
    separate(root, backup)
    meta = read_json(backup / 'backup.json')
    if (not isinstance(meta, dict) or meta.get('schema') != SCHEMA or meta.get('kind') != 'backup'
            or reject_links(meta.get('root', '')) != root):
        raise UpdateError('backup does not belong to this installation')
    with update_lock(root):
        original = directory(backup / 'installation')
        if manifest(original) != meta.get('before'):
            raise UpdateError('backup content changed; refusing rollback')
        if not root.exists():
            # A process kill between the two swap renames leaves the original here.
            stage = root.parent / (root.name + '.stage-' + uuid.uuid4().hex)
            reject_links(stage)
            shutil.copytree(original, stage)
            if manifest(stage) != meta['before']:
                raise UpdateError('recovery stage differs from backup')
            os.rename(stage, root)
            print('recovered missing installation from backup; backup retained:', backup)
            return backup
        active_writers(root)
        before = manifest(root)
        if before != meta.get('after'):
            raise UpdateError('installed files changed after update; preserve them before rollback')
        current_full = manifest(root, include_local=True)
        stage = root.parent / (root.name + '.stage-' + uuid.uuid4().hex)
        reject_links(stage)
        # Restore code, but keep CURRENT local state rather than a stale backup copy.
        shutil.copytree(original, stage, ignore=lambda path, names: [n for n in names if Path(path) == original and local_name(n)])
        copy_local(root, stage)
        active_writers(root)
        if manifest(root, include_local=True) != current_full:
            raise UpdateError(f'installation changed during staging; stage retained at {stage}')
        after = manifest(stage)
        newer_backup = swap(root, stage, before, after)
    print('rolled back; current local configuration/state preserved')
    print('replaced version also backed up at:', newer_backup)
    return newer_backup


def check(root):
    root = directory(root)
    def inspect(src, payload, commit):
        with tempfile.TemporaryDirectory(prefix='skill-inspect-') as tmp:
            dest = Path(tmp) / 'payload'
            copy_payload(payload, dest)
            validate_payload(dest)
            print(f'local {version(root)}  remote {version(dest)}  commit {commit}')
            print('same version' if version(root) == version(dest) else 'different version; fetch to review')
    remote_snapshot(root, inspect)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=HERE, help='installed skill directory (default: this skill)')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('check', help='read remote version without installation')
    for name in ('fetch', 'pull'):
        fetch = commands.add_parser(name, help='fetch a unique candidate for review')
        fetch.add_argument('--dest', type=Path, help='candidate store outside installation')
    diff = commands.add_parser('diff', help='verify candidate and list added/modified/deleted files')
    diff.add_argument('candidate', type=Path)
    apply = commands.add_parser('apply', help='install exact reviewed candidate without network')
    apply.add_argument('candidate', type=Path)
    apply.add_argument('--reviewed', required=True, help='review digest from diff/fetch')
    undo = commands.add_parser('rollback', help='restore backup, keeping current local state')
    undo.add_argument('backup', type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == 'check':
            check(args.root)
        elif args.command in ('fetch', 'pull'):
            fetch_candidate(args.root, args.dest)
        elif args.command == 'diff':
            candidate, meta = load_candidate(args.candidate, args.root)
            report_changes(differences(meta['baseline'], meta['target']))
            print('candidate:', candidate)
            print('review digest:', digest(meta))
        elif args.command == 'apply':
            apply_candidate(args.root, args.candidate, args.reviewed)
        elif args.command == 'rollback':
            rollback(args.root, args.backup)
    except (UpdateError, OSError, UnicodeError) as exc:
        print('update stopped:', exc, file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
