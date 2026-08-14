# coding=utf-8
# SPDX-FileCopyrightText: Copyright (c) OllisGit
# SPDX-FileCopyrightText: Copyright (c) 2026 Patryk Kurzeja
# SPDX-License-Identifier: AGPL-3.0-only

import logging
import os
import shutil
import sqlite3
import tempfile
import unittest

from octoprint_spoolmanager.DatabaseManager import DatabaseManager


FIXTURE = os.path.join(os.path.dirname(__file__), "spoolmanager_scheme_v3.db")
EXPECTED_SCHEME = 7


def _connect(db_path):
	return sqlite3.connect(db_path)


def _scheme_version(db_path):
	conn = _connect(db_path)
	try:
		row = conn.execute(
			"SELECT value FROM spo_pluginmetadatamodel WHERE key='databaseSchemeVersion'").fetchone()
		return int(row[0]) if row else None
	finally:
		conn.close()


def _column_names(db_path, table):
	conn = _connect(db_path)
	try:
		return [row[1] for row in conn.execute("PRAGMA table_info(%s)" % table).fetchall()]
	finally:
		conn.close()


def _count_spools(db_path):
	conn = _connect(db_path)
	try:
		return conn.execute("SELECT COUNT(*) FROM spo_spoolmodel").fetchone()[0]
	finally:
		conn.close()


class TestDatabaseMigrations(unittest.TestCase):

	def setUp(self):
		self._tempDir = tempfile.mkdtemp(prefix="spm-migr-")
		self._dbPath = os.path.join(self._tempDir, "spoolmanager.db")
		self._logger = logging.getLogger("test")

	def tearDown(self):
		if hasattr(self, "_database"):
			self._database.closeDatabase()
		shutil.rmtree(self._tempDir, ignore_errors=True)

	def _init_manager(self, db_path=None):
		"""Create a DatabaseManager pointed at a local sqlite file and init it."""
		db_path = db_path or self._dbPath
		settings = DatabaseManager.DatabaseSettings()
		settings.useExternal = False
		settings.baseFolder = self._tempDir
		self._database = DatabaseManager(self._logger, sqlLoggingEnabled=False)
		self._database.initDatabase(settings, self._clientOutput)
		return self._database

	def _clientOutput(self, msgType, title, message):
		self._logger.debug("[%s] %s: %s" % (msgType, title, message))

	def test_upgrade_from_v3_fixture_to_v7(self):
		self.assertTrue(os.path.exists(FIXTURE), "fixture missing: %s" % FIXTURE)
		shutil.copy(FIXTURE, self._dbPath)
		self.assertEqual(_scheme_version(self._dbPath), 3, "precondition: fixture should be scheme 3")

		self._init_manager()

		self.assertEqual(_scheme_version(self._dbPath), EXPECTED_SCHEME)
		self.assertEqual(_count_spools(self._dbPath), 5, "spools must survive the upgrade")

		# columns added by the 3->4, 4->5, 5->6, 6->7 migrations
		cols = _column_names(self._dbPath, "spo_spoolmodel")
		for col in [
			"updated", "originator", "materialCharacteristic", "isActive",
			"offsetTemperature", "offsetBedTemperature", "offsetEnclosureTemperature",
			"enclosureTemperature", "version", "remainingWeight",
		]:
			self.assertIn(col, cols, "expected column %r after migration" % col)

	def test_no_upgrade_on_reopen(self):
		self._init_manager()
		self.assertEqual(_scheme_version(self._dbPath), EXPECTED_SCHEME)
		spools_after_first = _count_spools(self._dbPath)

		# reopen - must stay at v7 and not re-run migrations
		self._database.closeDatabase()
		self._init_manager()
		self.assertEqual(_scheme_version(self._dbPath), EXPECTED_SCHEME)
		self.assertEqual(_count_spools(self._dbPath), spools_after_first)

	def test_fresh_database_created_at_v7(self):
		self._init_manager()
		self.assertEqual(_scheme_version(self._dbPath), EXPECTED_SCHEME)


if __name__ == '__main__':
	unittest.main()
