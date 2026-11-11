"""Updater behavior and interruption tests: local fixtures only, no Git/network."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

SPEC = importlib.util.spec_from_file_location('skill_update', Path(__file__).resolve().parents[1] / 'scripts' / 'skill_update.py')
update = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(update)


class UpdaterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='updater-test-')
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / 'installed'
        self.remote = self.base / 'remote'
        for root, version in ((self.root, '1.2.0'), (self.remote, '1.3.0')):
            root.mkdir()
            (root / 'SKILL.md').write_text('---\nname: example\ndescription: Fixture skill.\n---\n', encoding='utf8')
            (root / 'VERSION').write_text(version + '\n', encoding='utf8')
            (root / 'code.txt').write_text(version, encoding='utf8')
        (self.root / '.skill-source').write_text(json.dumps({'repo': 'owner/skill', 'path': '.', 'branch': 'main'}), encoding='utf8')
        (self.root / 'removed.txt').write_text('remove in update', encoding='utf8')
        (self.remote / 'added.txt').write_text('new file', encoding='utf8')
        self.commit = 'a' * 40

    def candidate(self):
        def fake_fetch(src, dest):
            shutil.copytree(self.remote, dest)
            (dest / '.git').mkdir()
            return dest, self.commit
        with mock.patch.object(update, 'fetch_remote', side_effect=fake_fetch), contextlib.redirect_stdout(io.StringIO()):
            result = update.fetch_candidate(self.root, self.base / 'candidates')
        meta = update.read_json(result / 'candidate.json')
        return result, update.digest(meta)

    def quiet_apply(self, candidate, reviewed):
        with contextlib.redirect_stdout(io.StringIO()):
            return update.apply_candidate(self.root, candidate, reviewed)

    def test_fetch_retains_exact_commit_and_complete_change_summary(self):
        candidate, reviewed = self.candidate()
        _, meta = update.load_candidate(candidate, self.root)
        changes = update.differences(meta['baseline'], meta['target'])
        self.assertEqual(meta['commit'], self.commit)
        self.assertEqual(changes['added'], ['added.txt'])
        self.assertEqual(changes['deleted'], ['removed.txt'])
        self.assertIn('code.txt', changes['modified'])
        self.assertEqual(update.digest(meta), reviewed)

    def test_apply_has_no_network_and_does_not_refetch_changed_remote(self):
        candidate, reviewed = self.candidate()
        (self.remote / 'code.txt').write_text('remote changed after review', encoding='utf8')
        with mock.patch.object(update, 'fetch_remote', side_effect=AssertionError('network during apply')):
            backup = self.quiet_apply(candidate, reviewed)
        self.assertEqual((self.root / 'code.txt').read_text(), '1.3.0')
        self.assertFalse((self.root / 'removed.txt').exists())
        self.assertTrue((backup / 'installation' / 'removed.txt').is_file())
        self.assertTrue(candidate.exists())

    def test_rejects_candidate_content_or_metadata_changes(self):
        candidate, reviewed = self.candidate()
        payload_file = candidate / 'payload' / 'code.txt'
        payload_file.write_text('tampered', encoding='utf8')
        with self.assertRaisesRegex(update.UpdateError, 'content changed'):
            self.quiet_apply(candidate, reviewed)
        payload_file.write_text('1.3.0', encoding='utf8')
        meta = update.read_json(candidate / 'candidate.json')
        meta['commit'] = 'b' * 40
        update.write_json(candidate / 'candidate.json', meta)
        with self.assertRaisesRegex(update.UpdateError, 'digest'):
            self.quiet_apply(candidate, reviewed)
        self.assertEqual((self.root / 'VERSION').read_text().strip(), '1.2.0')

    def test_local_drift_is_not_overwritten(self):
        candidate, reviewed = self.candidate()
        (self.root / 'code.txt').write_text('important local work', encoding='utf8')
        with self.assertRaisesRegex(update.UpdateError, 'local files changed'):
            self.quiet_apply(candidate, reviewed)
        self.assertEqual((self.root / 'code.txt').read_text(), 'important local work')

    def test_current_configuration_and_state_survive_apply_and_rollback(self):
        state = self.root / '.agent-company'
        state.mkdir()
        (state / 'state.json').write_text('{"revision": 1}', encoding='utf8')
        (self.root / '.env.local').write_text('LOCAL=fixture', encoding='utf8')
        candidate, reviewed = self.candidate()
        backup = self.quiet_apply(candidate, reviewed)
        (state / 'state.json').write_text('{"revision": 2}', encoding='utf8')
        source = self.root / '.skill-source'
        source.write_text('{"repo": "owner/changed-source"}', encoding='utf8')
        with contextlib.redirect_stdout(io.StringIO()):
            newer_backup = update.rollback(self.root, backup)
        self.assertEqual((self.root / 'VERSION').read_text().strip(), '1.2.0')
        self.assertEqual((state / 'state.json').read_text(), '{"revision": 2}')
        self.assertEqual(source.read_text(), '{"repo": "owner/changed-source"}')
        self.assertEqual((self.root / '.env.local').read_text(), 'LOCAL=fixture')
        self.assertTrue((newer_backup / 'installation').is_dir())
        self.assertTrue((backup / 'installation').is_dir())

    def test_failed_second_rename_restores_original_installation(self):
        candidate, reviewed = self.candidate()
        rename = os.rename
        calls = []
        def fail_install(src, dst):
            calls.append((Path(src), Path(dst)))
            if len(calls) == 2:
                raise PermissionError('simulated Windows file lock')
            return rename(src, dst)
        with mock.patch.object(update.os, 'rename', side_effect=fail_install):
            with self.assertRaisesRegex(update.UpdateError, 'original restored'):
                self.quiet_apply(candidate, reviewed)
        self.assertEqual((self.root / 'code.txt').read_text(), '1.2.0')
        self.assertEqual(len(calls), 3)

    def test_interrupted_swap_can_recover_missing_installation(self):
        candidate, reviewed = self.candidate()
        rename = os.rename
        calls = 0
        def interrupt_install(src, dst):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise KeyboardInterrupt()
            return rename(src, dst)
        with mock.patch.object(update.os, 'rename', side_effect=interrupt_install):
            with self.assertRaises(KeyboardInterrupt):
                self.quiet_apply(candidate, reviewed)
        self.assertFalse(self.root.exists())
        backup = next(self.base.glob('installed.backup-*'))
        with contextlib.redirect_stdout(io.StringIO()):
            update.rollback(self.root, backup)
        self.assertEqual((self.root / 'VERSION').read_text().strip(), '1.2.0')
        self.assertTrue((backup / 'installation').is_dir())

    def test_rollback_refuses_new_local_work_or_corrupted_backup(self):
        candidate, reviewed = self.candidate()
        backup = self.quiet_apply(candidate, reviewed)
        (self.root / 'new-local.txt').write_text('keep me', encoding='utf8')
        with self.assertRaisesRegex(update.UpdateError, 'installed files changed'):
            update.rollback(self.root, backup)
        (self.root / 'new-local.txt').unlink()
        (backup / 'installation' / 'code.txt').write_text('corrupted', encoding='utf8')
        with self.assertRaisesRegex(update.UpdateError, 'backup content changed'):
            update.rollback(self.root, backup)

    def test_active_writer_and_update_locks_stop_apply(self):
        candidate, reviewed = self.candidate()
        state = self.root / '.agent-company'
        state.mkdir()
        lock = state / 'write.lock'
        lock.write_text('active', encoding='utf8')
        with self.assertRaisesRegex(update.UpdateError, 'writer lock'):
            self.quiet_apply(candidate, reviewed)
        lock.unlink()
        (self.base / 'installed.update.lock').write_text('active', encoding='utf8')
        with self.assertRaisesRegex(update.UpdateError, 'update lock'):
            self.quiet_apply(candidate, reviewed)

    def test_source_rejects_traversal_injection_and_absolute_paths(self):
        for config in ({'repo': 'https://example.com/x'}, {'repo': 'owner/name', 'branch': '--upload-pack=bad'},
                       {'repo': 'owner/name', 'path': '../outside'}, {'repo': 'owner/name', 'path': 'C:/outside'},
                       {'repo': 'owner/name', 'path': '/outside'}, {'repo': 'owner/name', 'path': 'a\\b'}):
            with self.subTest(config=config):
                (self.root / '.skill-source').write_text(json.dumps(config), encoding='utf8')
                with self.assertRaises(update.UpdateError):
                    update.source(self.root)

    def test_store_must_not_overlap_installation(self):
        with self.assertRaisesRegex(update.UpdateError, 'contain each other'):
            update.fetch_candidate(self.root, self.root / 'candidates')

    def test_git_checkout_is_never_replaced(self):
        (self.root / '.git').mkdir()
        with self.assertRaisesRegex(update.UpdateError, 'Git checkouts'):
            update.fetch_candidate(self.root)

    def test_linked_candidate_rejected(self):
        candidate, reviewed = self.candidate()
        link = candidate / 'payload' / 'linked.txt'
        try:
            link.symlink_to(self.root / 'code.txt')
        except OSError as exc:
            self.skipTest(f'OS does not allow unprivileged symlinks: {exc}')
        with self.assertRaisesRegex(update.UpdateError, 'linked/reparse'):
            self.quiet_apply(candidate, reviewed)

    def test_windows_reparse_attribute_rejected_without_symlink_privilege(self):
        lstat = Path.lstat
        special = self.root / 'code.txt'
        def fake_lstat(path):
            info = lstat(path)
            if path == special:
                return SimpleNamespace(st_mode=info.st_mode, st_file_attributes=0x400)
            return info
        with mock.patch.object(Path, 'lstat', autospec=True, side_effect=fake_lstat):
            with self.assertRaisesRegex(update.UpdateError, 'linked/reparse'):
                update.manifest(self.root)

    def test_unknown_or_legacy_apply_argument_is_rejected(self):
        for args in (['pull', '--apply'], ['fetch', '--unknown'], ['apply', 'candidate']):
            with self.subTest(args=args), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as exc:
                    update.main(args)
                self.assertEqual(exc.exception.code, 2)


if __name__ == '__main__':
    unittest.main()
