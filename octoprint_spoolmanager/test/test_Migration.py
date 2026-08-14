# coding=utf-8
# SPDX-FileCopyrightText: Copyright (c) OllisGit
# SPDX-FileCopyrightText: Copyright (c) 2026 Patryk Kurzeja
# SPDX-License-Identifier: AGPL-3.0-only

import logging
import os
import shutil
import tempfile
import unittest

from octoprint_spoolmanager import SpoolManagerPlugin


class _FakeSettings(object):
	"""
	Minimal stand-in for OctoPrint's settings object that supports the
	global_get/global_set/global_remove/save API used by _migrateLegacyData.
	"""

	def __init__(self):
		# mimics the octoprint tree: {"plugins": {"SpoolManager": {...}}}
		self._store = {"plugins": {}}

	def global_get(self, path, default=None):
		cur = self._store
		for key in path:
			if isinstance(cur, dict) and key in cur:
				cur = cur[key]
			else:
				return default
		return cur

	def global_set(self, path, value):
		cur = self._store
		for key in path[:-1]:
			cur = cur.setdefault(key, {})
		cur[path[-1]] = value

	def global_remove(self, path):
		cur = self._store
		for key in path[:-1]:
			cur = cur.get(key, {})
		cur.pop(path[-1], None)

	def save(self):
		pass


class TestMigration(unittest.TestCase):

	def setUp(self):
		self._tempDir = tempfile.mkdtemp(prefix="spm-migr-")
		self._logger = logging.getLogger("test-migration")
		self._plugin = SpoolManagerPlugin()
		self._plugin._logger = self._logger
		self._settings = _FakeSettings()
		self._plugin._settings = self._settings

	def tearDown(self):
		shutil.rmtree(self._tempDir, ignore_errors=True)

	def _new_data_folder(self):
		"""The plugin data folder for the new (lowercase) identifier."""
		folder = os.path.join(self._tempDir, "data", "spoolmanager")
		os.makedirs(folder, exist_ok=True)
		return folder

	def _old_data_folder(self):
		"""The legacy plugin data folder for the old (uppercase) identifier."""
		folder = os.path.join(self._tempDir, "data", "SpoolManager")
		os.makedirs(folder, exist_ok=True)
		return folder

	def test_settings_are_migrated_from_legacy_identifier(self):
		# legacy settings present, new settings absent -> migrate
		self._settings.global_set(["plugins", "SpoolManager"], {"installed_version": "1.7.1"})

		self._plugin._settings = self._settings
		self._plugin.get_plugin_data_folder = lambda: self._new_data_folder()

		self._plugin._migrateLegacyData()

		self.assertEqual(
			self._settings.global_get(["plugins", "spoolmanager"]),
			{"installed_version": "1.7.1"},
		)
		self.assertIsNone(self._settings.global_get(["plugins", "SpoolManager"]))

	def test_settings_not_overwritten_when_new_already_exists(self):
		# both present -> keep the new, do not clobber it
		self._settings.global_set(["plugins", "SpoolManager"], {"legacy": True})
		self._settings.global_set(["plugins", "spoolmanager"], {"installed_version": "2.0.0"})

		self._plugin.get_plugin_data_folder = lambda: self._new_data_folder()

		self._plugin._migrateLegacyData()

		self.assertEqual(self._settings.global_get(["plugins", "spoolmanager"]), {"installed_version": "2.0.0"})

	def test_data_files_are_migrated(self):
		old_folder = self._old_data_folder()
		# a database file plus a nested backup subfolder
		with open(os.path.join(old_folder, "spoolmanager.db"), "w") as f:
			f.write("sqlite-version-7")
		backup_dir = os.path.join(old_folder, "backups")
		os.makedirs(backup_dir)
		with open(os.path.join(backup_dir, "backup-1.db"), "w") as f:
			f.write("backup-content")

		new_folder = self._new_data_folder()
		self._plugin.get_plugin_data_folder = lambda: new_folder

		self._plugin._migrateLegacyData()

		self.assertTrue(os.path.isfile(os.path.join(new_folder, "spoolmanager.db")))
		self.assertTrue(os.path.isfile(os.path.join(new_folder, "backups", "backup-1.db")))
		# the source still exists (we copy, we do not delete)
		self.assertTrue(os.path.isfile(os.path.join(old_folder, "spoolmanager.db")))

	def test_no_op_when_nothing_to_migrate(self):
		new_folder = self._new_data_folder()
		self._plugin.get_plugin_data_folder = lambda: new_folder

		# should not raise and leave settings untouched
		self._plugin._migrateLegacyData()

		self.assertIsNone(self._settings.global_get(["plugins", "spoolmanager"]))
		self.assertTrue(os.path.isdir(new_folder))


if __name__ == "__main__":
	unittest.main()