# coding=utf-8
# SPDX-FileCopyrightText: Copyright (c) OllisGit
# SPDX-FileCopyrightText: Copyright (c) 2026 Patryk Kurzeja
# SPDX-License-Identifier: AGPL-3.0-only

import flask
import logging
import shutil
import tempfile
import unittest
from urllib.parse import urlencode

from octoprint_SpoolManager import SpoolmanagerPlugin
from octoprint_SpoolManager.DatabaseManager import DatabaseManager
from octoprint_SpoolManager.models.SpoolModel import SpoolModel


class _FakeSettings(object):
	"""Minimal stand-in for the OctoPrint settings object."""

	def __init__(self, **values):
		self._store = values

	@staticmethod
	def _extract_key(key):
		# OctoPrint settings paths are passed as a list, e.g. ["key"].
		return key[0] if isinstance(key, (list, tuple)) else key

	def get(self, key, default=None):
		return self._store.get(self._extract_key(key), default)

	def get_boolean(self, key, default=None):
		return self._store.get(self._extract_key(key), default)


class _FakePrinterProfileManager(object):
	def __init__(self, tool_count=1):
		self._tool_count = tool_count

	def get_current_or_default(self):
		return {"extruder": {"count": self._tool_count}}


class _FakePrinter(object):
	def __init__(self, printing=False):
		self._printing = printing

	def is_printing(self):
		return self._printing


class TestSpoolManagerAPI(unittest.TestCase):

	EXPECTED_QUERY_KEYS = {"templateSpools", "catalogs", "totalItemCount", "allSpools", "selectedSpools"}

	def setUp(self):
		self._tempDir = tempfile.mkdtemp(prefix="spm-api-")
		self._logger = logging.getLogger("test")

		settings = DatabaseManager.DatabaseSettings()
		settings.useExternal = False
		settings.baseFolder = self._tempDir
		self._db = DatabaseManager(self._logger, sqlLoggingEnabled=False)
		self._db.initDatabase(settings, self._clientOutput)

		self._plugin = SpoolmanagerPlugin()
		self._plugin._logger = self._logger
		self._plugin._databaseManager = self._db
		self._plugin._settings = _FakeSettings()
		self._plugin._printer = _FakePrinter(printing=False)
		self._plugin._printer_profile_manager = _FakePrinterProfileManager(tool_count=1)

		self.events = []
		self.client_messages = []
		self._plugin._sendPayload2EventBus = lambda key, payload: self.events.append((key, payload))
		self._plugin._sendDataToClient = lambda data: self.client_messages.append(data)
		self._plugin._sendMessageToClient = lambda *a, **k: None

		# Default deterministic mocks for the methods the API delegates to.
		self._plugin.loadSelectedSpools = lambda: []
		self._plugin._readingFilamentMetaData = lambda: False
		self._plugin.checkRemainingFilament = staticmethod(
			lambda *a, **k: {"metaDataMissing": False, "attributesMissing": False, "detailedSpoolResult": []})
		self._plugin._selectSpool = lambda toolIndex, databaseId: None
		self._plugin.set_temp_offsets = lambda *a, **k: None

		self.client = self._build_app().test_client()

	def tearDown(self):
		self._db.closeDatabase()
		shutil.rmtree(self._tempDir, ignore_errors=True)

	def _clientOutput(self, msgType, title, message):
		self._logger.debug("[%s] %s: %s" % (msgType, title, message))

	def _build_app(self):
		app = flask.Flask(__name__)
		app.testing = True
		bp = flask.Blueprint("SpoolManager", __name__)
		bp.add_url_rule("/loadSpoolsByQuery", endpoint="loadSpoolsByQuery",
						view_func=self._plugin.loadAllSpoolsByQuery, methods=["GET"])
		bp.add_url_rule("/saveSpool", endpoint="saveSpool",
						view_func=self._plugin.saveSpool, methods=["PUT"])
		bp.add_url_rule("/deleteSpool/<int:databaseId>", endpoint="deleteSpool",
						view_func=self._plugin.deleteSpool, methods=["DELETE"])
		bp.add_url_rule("/selectSpool", endpoint="selectSpool",
						view_func=self._plugin.select_spool, methods=["PUT"])
		bp.add_url_rule("/allowedToPrint", endpoint="allowedToPrint",
						view_func=self._plugin.allowed_to_print, methods=["GET"])
		bp.add_url_rule("/startPrintConfirmed", endpoint="startPrintConfirmed",
						view_func=self._plugin.start_print_confirmed, methods=["GET"])
		bp.add_url_rule("/loadDatabaseMetaData", endpoint="loadDatabaseMetaData",
						view_func=self._plugin.loadDatabaseMetaData, methods=["GET"])
		bp.add_url_rule("/testDatabaseConnection", endpoint="testDatabaseConnection",
						view_func=self._plugin.testDatabaseConnection, methods=["PUT"])
		app.register_blueprint(bp, url_prefix="/plugin/SpoolManager")
		return app

	def _seed_spool(self, **overrides):
		spool = SpoolModel()
		spool.displayName = "Test Spool"
		spool.material = "PLA"
		spool.vendor = "Acme"
		spool.color = "#ff0000"
		spool.colorName = "red"
		spool.isActive = True
		spool.diameter = 1.75
		spool.density = 1.24
		spool.totalWeight = 1000.0
		spool.usedWeight = 200.0
		for key, value in overrides.items():
			setattr(spool, key, value)
		self._db.saveSpool(spool)
		return spool

	def _load_query_url(self, **overrides):
		params = {
			"sortColumn": "displayName",
			"sortOrder": "asc",
			"filterName": "all",
			"from": "0",
			"to": "100",
			"materialFilter": "all",
			"vendorFilter": "all",
			"colorFilter": "all",
			"selectedPageSize": "10",
		}
		params.update({k: str(v) for k, v in overrides.items()})
		return "/plugin/SpoolManager/loadSpoolsByQuery?" + urlencode(params)
	# ------------------------------------------------------------------ contract
	def test_load_spools_by_query_shape(self):
		self._seed_spool()
		resp = self.client.get(self._load_query_url())
		self.assertEqual(resp.status_code, 200)
		data = resp.get_json()
		self.assertEqual(set(data.keys()), self.EXPECTED_QUERY_KEYS)
		self.assertEqual(data["totalItemCount"], 1)
		self.assertEqual(len(data["allSpools"]), 1)
		self.assertEqual(data["allSpools"][0]["displayName"], "Test Spool")
		self.assertEqual(data["allSpools"][0]["material"], "PLA")
		for cat in ("vendors", "materials", "colors", "labels"):
			self.assertIn(cat, data["catalogs"])
		self.assertIsInstance(data["selectedSpools"], list)

	def test_save_spool_creates_and_fires_event(self):
		before = self._db.countSpoolsByQuery()
		resp = self.client.put("/plugin/SpoolManager/saveSpool", json={
			"displayName": "New Spool",
			"material": "PETG",
			"isActive": True,
		})
		self.assertEqual(resp.status_code, 200)
		self.assertEqual(self._db.countSpoolsByQuery(), before + 1)
		self.assertIn("spool_added", [key for key, _ in self.events])

	def test_delete_spool_fires_event(self):
		spool = self._seed_spool()
		databaseId = spool.databaseId
		resp = self.client.delete("/plugin/SpoolManager/deleteSpool/%d" % databaseId)
		self.assertEqual(resp.status_code, 200)
		self.assertEqual(self._db.loadSpool(databaseId), None)
		self.assertIn("spool_deleted", [key for key, _ in self.events])

	def test_select_spool_ok(self):
		spool = self._seed_spool()
		self._plugin._selectSpool = lambda toolIndex, databaseId: spool
		resp = self.client.put("/plugin/SpoolManager/selectSpool", json={
			"databaseId": spool.databaseId,
			"toolIndex": 0,
		})
		self.assertEqual(resp.status_code, 200)
		data = resp.get_json()
		self.assertEqual(set(data.keys()), {"selectedSpool"})
		self.assertEqual(data["selectedSpool"]["displayName"], "Test Spool")

	def test_select_spool_mid_print_409(self):
		self._plugin._printer = _FakePrinter(printing=True)
		resp = self.client.put("/plugin/SpoolManager/selectSpool", json={
			"databaseId": 1,
			"toolIndex": 0,
		})
		self.assertEqual(resp.status_code, 409)

	def test_allowed_to_print_shape(self):
		resp = self.client.get("/plugin/SpoolManager/allowedToPrint")
		self.assertEqual(resp.status_code, 200)
		data = resp.get_json()
		self.assertEqual(set(data["result"].keys()),
						{"noSpoolSelected", "filamentNotEnough", "reminderSpoolSelection"})
		self.assertIn("metaOrAttributesMissing", data)

	def test_start_print_confirmed(self):
		resp = self.client.get("/plugin/SpoolManager/startPrintConfirmed")
		self.assertEqual(resp.status_code, 200)
		self.assertEqual(resp.get_json(), {"result": "goForIt"})

	# ------------------------------------------------------------------ DB meta
	def test_load_database_meta_data(self):
		resp = self.client.get("/plugin/SpoolManager/loadDatabaseMetaData")
		self.assertEqual(resp.status_code, 200)
		data = resp.get_json()
		self.assertIn("metadata", data)
		self.assertIs(data["metadata"]["success"], True)
		self.assertEqual(data["metadata"]["localSchemeVersionFromDatabaseModel"], "7")

	def test_test_database_connection(self):
		resp = self.client.put("/plugin/SpoolManager/testDatabaseConnection", json={"useExternal": False})
		self.assertEqual(resp.status_code, 200)
		data = resp.get_json()
		self.assertIn("metadata", data)
		self.assertIs(data["metadata"]["success"], True)
		self.assertEqual(data["metadata"]["localSchemeVersionFromDatabaseModel"], "7")


if __name__ == '__main__':
	unittest.main()
