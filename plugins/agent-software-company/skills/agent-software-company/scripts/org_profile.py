#!/usr/bin/env python3
"""First-guess project profile for org design (read-only).
Usage: python org_profile.py [repo_path]
Prints a short JSON: languages, frameworks, deploy hints, tests, CI, data stores, risk hints, size, suggested preset.
It only reads file names and a few config files; it never prints file contents beyond detected keywords.
"""
import json, os, sys

root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else '.')
SKIP = {'.git', 'node_modules', '.next', 'dist', 'build', 'venv', '.venv', '__pycache__', 'target', 'vendor'}
EXT = {'.py': 'python', '.ts': 'typescript', '.tsx': 'typescript', '.js': 'javascript', '.jsx': 'javascript', '.go': 'go', '.rs': 'rust', '.java': 'java', '.kt': 'kotlin', '.swift': 'swift', '.cs': 'csharp', '.rb': 'ruby', '.php': 'php', '.dart': 'dart', '.sql': 'sql'}
langs, files, tests = {}, 0, 0
names = set()
for d, dirs, fs in os.walk(root):
    dirs[:] = [x for x in dirs if x not in SKIP]
    for f in fs:
        files += 1
        names.add(f)
        e = os.path.splitext(f)[1].lower()
        if e in EXT:
            langs[EXT[e]] = langs.get(EXT[e], 0) + 1
        if '.test.' in f or '.spec.' in f or f.startswith('test_') or f.endswith('_test.go'):
            tests += 1


def has(*n):
    return any(x in names for x in n)


def text(path):
    try:
        return open(os.path.join(root, path), encoding='utf8', errors='ignore').read().lower()
    except OSError:
        return ''


pkg = text('package.json') + text('requirements.txt') + text('pyproject.toml') + text('go.mod') + text('cargo.toml') + text('pubspec.yaml')
fw = [k for k in ['next', 'react', 'vue', 'svelte', 'angular', 'express', 'fastify', 'django', 'flask', 'fastapi', 'rails', 'spring', 'flutter', 'react-native', 'expo', 'electron', 'tauri'] if k in pkg]
data = [k for k in ['supabase', 'postgres', 'pg', 'mysql', 'mongodb', 'redis', 'sqlite', 'prisma', 'sqlalchemy', 'firebase'] if k in pkg]
risk = [k for k, v in {'payments': ['stripe', 'razorpay', 'paypal', 'payment'], 'auth': ['auth', 'jwt', 'oauth', 'passport', 'msal', 'session'], 'pii/hr': ['employee', 'leave', 'payroll', 'patient'], 'excel/sheets': ['xlsx', 'exceljs', 'openpyxl', 'graph']}.items() if any(w in pkg for w in v)]
deploy = [k for k, f in {'netlify': ('netlify.toml',), 'vercel': ('vercel.json',), 'docker': ('Dockerfile', 'docker-compose.yml'), 'terraform': ('main.tf',), 'github-actions': ('ci.yml', 'ci.yaml', 'main.yml'), 'app-store/play': ('Info.plist', 'AndroidManifest.xml'), 'package-registry': ('setup.py', 'pyproject.toml', 'Cargo.toml')}.items() if has(*f)]
kind = 'internal-business-app'
if has('AndroidManifest.xml', 'Info.plist', 'pubspec.yaml') or 'react-native' in fw or 'flutter' in fw:
    kind = 'mobile-or-desktop-app'
elif has('setup.py', 'Cargo.toml') and not fw:
    kind = 'library-or-api'
elif files < 60 and not data:
    kind = 'solo-internal-tool'
elif any(k in pkg for k in ['stripe', 'subscription', 'tenant']):
    kind = 'public-saas'
if 'payments' in risk or 'pii/hr' in risk:
    kind += ' (money/people data: strict change control)'
print(json.dumps({
    'path': root, 'files': files, 'test_files': tests, 'languages': dict(sorted(langs.items(), key=lambda x: -x[1])[:5]),
    'frameworks': fw, 'data_stores': data, 'risk_hints': risk, 'deploy_hints': deploy,
    'suggested_preset': kind,
    'note': 'First guess only. The Boss confirms with the owner-facing questions in references/adaptive-org.md and writes docs/team/PROFILE.md.',
}, indent=2))
