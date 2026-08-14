# coding=utf-8
# SPDX-FileCopyrightText: Copyright (c) OllisGit
# SPDX-FileCopyrightText: Copyright (c) 2026 Patryk Kurzeja
# SPDX-License-Identifier: AGPL-3.0-only

import logging
import os
import shutil
import tempfile
import unittest

from octoprint_spoolmanager.DatabaseManager import DatabaseManager
from octoprint_spoolmanager.models.SpoolModel import SpoolModel


def _env(key, default=None):
	"""Return the environment variable value, or the default when unset."""
	value = os.environ.get(key)
	return value if value is not None else default


class TestDatabase(unittest.TestCase):

	@classmethod
	def setUpClass(cls):
		cls._tempFolder = tempfile.mkdtemp(prefix="spoolmanager-test-")
		logging.basicConfig(level=logging.INFO)

	@classmethod
	def tearDownClass(cls):
		shutil.rmtree(cls._tempFolder, ignore_errors=True)

	def _clientOutput(self, type, title, message):
		print("CLIENT-MESSAGE [%s] %s: %s" % (type, title, message))

	def _newDatabaseManager(self):
		return DatabaseManager(logging.getLogger("test"), sqlLoggingEnabled=False)

	def _buildSqliteSettings(self):
		settings = DatabaseManager.DatabaseSettings()
		settings.useExternal = False
		settings.baseFolder = self._tempFolder
		return settings

	def _buildPostgresSettings(self):
		settings = DatabaseManager.DatabaseSettings()
		settings.useExternal = True
		settings.type = "postgres"
		settings.host = _env("SPOOLMANAGER_TEST_PG_HOST", "localhost")
		settings.port = int(_env("SPOOLMANAGER_TEST_PG_PORT", "5432"))
		settings.name = _env("SPOOLMANAGER_TEST_PG_NAME", "spoolmanagerdb")
		settings.user = _env("SPOOLMANAGER_TEST_PG_USER", "Olli")
		settings.password = _env("SPOOLMANAGER_TEST_PG_PASSWORD", "illO")
		return settings

	def _buildMysqlSettings(self):
		settings = DatabaseManager.DatabaseSettings()
		settings.useExternal = True
		settings.type = "mysql"
		settings.host = _env("SPOOLMANAGER_TEST_MYSQL_HOST", "localhost")
		settings.port = int(_env("SPOOLMANAGER_TEST_MYSQL_PORT", "3306"))
		settings.name = _env("SPOOLMANAGER_TEST_MYSQL_NAME", "spoolmanagerdb")
		settings.user = _env("SPOOLMANAGER_TEST_MYSQL_USER", "Olli")
		settings.password = _env("SPOOLMANAGER_TEST_MYSQL_PASSWORD", "illO")
		return settings

	def _exerciseCrud(self, settings):
		manager = self._newDatabaseManager()
		manager.initDatabase(settings, self._clientOutput)
		self.assertIsNone(manager.testDatabaseConnection(), "Database connection failed")

		spool = SpoolModel()
		spool.displayName = "TEST-SPOOL-%s" % os.getpid()
		spool.material = "ABS"
		spool.vendor = "TestVendor"
		spool.totalWeight = 1000.0
		databaseId = manager.saveSpool(spool)
		self.assertIsNotNone(databaseId, "Spool not saved")

		loaded = manager.loadSpool(databaseId)
		self.assertIsNotNone(loaded, "Spool not loaded")
		self.assertEqual("TEST-SPOOL-%s" % os.getpid(), loaded.displayName)
		self.assertEqual("ABS", loaded.material)

		count = manager.countSpoolsByQuery()
		self.assertGreaterEqual(count, 1, "Expected at least one spool")

		deletedId = manager.deleteSpool(databaseId)
		self.assertEqual(databaseId, deletedId, "Spool not deleted")

		manager.closeDatabase()

	def test_sqlite_connect(self):
		manager = self._newDatabaseManager()
		manager.initDatabase(self._buildSqliteSettings(), self._clientOutput)
		self.assertIsNone(manager.testDatabaseConnection(), "SQLite connection failed")
		manager.closeDatabase()

	def test_sqlite_crud(self):
		self._exerciseCrud(self._buildSqliteSettings())

	@unittest.skipUnless(_env("SPOOLMANAGER_TEST_POSTGRES"), "Set SPOOLMANAGER_TEST_POSTGRES=1 to run PostgreSQL tests")
	def test_postgres_connect(self):
		manager = self._newDatabaseManager()
		manager.initDatabase(self._buildPostgresSettings(), self._clientOutput)
		self.assertIsNone(manager.testDatabaseConnection(), "PostgreSQL connection failed")
		manager.closeDatabase()

	@unittest.skipUnless(_env("SPOOLMANAGER_TEST_POSTGRES"), "Set SPOOLMANAGER_TEST_POSTGRES=1 to run PostgreSQL tests")
	def test_postgres_crud(self):
		self._exerciseCrud(self._buildPostgresSettings())

	@unittest.skipUnless(_env("SPOOLMANAGER_TEST_MYSQL"), "Set SPOOLMANAGER_TEST_MYSQL=1 to run MySQL tests")
	def test_mysql_connect(self):
		manager = self._newDatabaseManager()
		manager.initDatabase(self._buildMysqlSettings(), self._clientOutput)
		self.assertIsNone(manager.testDatabaseConnection(), "MySQL connection failed")
		manager.closeDatabase()

	@unittest.skipUnless(_env("SPOOLMANAGER_TEST_MYSQL"), "Set SPOOLMANAGER_TEST_MYSQL=1 to run MySQL tests")
	def test_mysql_crud(self):
		self._exerciseCrud(self._buildMysqlSettings())


if __name__ == '__main__':
	unittest.main()
