# coding=utf-8
# SPDX-FileCopyrightText: Copyright (c) OllisGit
# SPDX-FileCopyrightText: Copyright (c) 2026 Patryk Kurzeja
# SPDX-License-Identifier: AGPL-3.0-only

import logging
import shutil
import tempfile
import unittest

from octoprint_SpoolManager.DatabaseManager import DatabaseManager
from octoprint_SpoolManager.models.SpoolModel import SpoolModel


class TestLoadAllSpoolsByQuery(unittest.TestCase):

	def setUp(self):
		self._tempDir = tempfile.mkdtemp(prefix="spm-lsq-")
		settings = DatabaseManager.DatabaseSettings()
		settings.useExternal = False
		settings.baseFolder = self._tempDir
		self._logger = logging.getLogger("test")
		self._manager = DatabaseManager(self._logger, sqlLoggingEnabled=False)
		self._manager.initDatabase(settings, self._clientOutput)
		self._seed()

	def tearDown(self):
		self._manager.closeDatabase()
		shutil.rmtree(self._tempDir, ignore_errors=True)

	def _clientOutput(self, msgType, title, message):
		self._logger.debug("[%s] %s: %s" % (msgType, title, message))

	def _seed(self):
		def make(name, material, vendor, ccode, cname, total, used, active, template=False):
			spool = SpoolModel()
			spool.displayName = name
			spool.material = material
			spool.vendor = vendor
			spool.color = ccode
			spool.colorName = cname
			spool.isActive = active
			spool.isTemplate = template
			spool.totalWeight = total
			spool.usedWeight = used
			self._manager.saveSpool(spool)

		make("Alpha",  "PLA",  "V1", "#ff0000", "red",    1000.0, 100.0, True)
		make("Beta",   "ABS",  "V2", "#00ff00", "green",   500.0, 500.0, True)
		make("Gamma",  "PETG", "V1", "#0000ff", "blue",   2000.0,   0.0, False, True)
		make("delta",  "PLA",  "V3", "#ff0000", "red",     800.0, 400.0, True)
		make("Epsilon","PLA",  "V2", "#ffff00", "yellow",  700.0,  None, True)
		make("Zeta",   "TPU",  "V3", "#00ffff", "cyan",    300.0, 150.0, True)

	def _query(self, **overrides):
		query = {
			"sortColumn": "displayName",
			"sortOrder": "asc",
			"filterName": "all",
			"from": 0,
			"to": 100,
			"materialFilter": "all",
			"vendorFilter": "all",
			"colorFilter": "all",
		}
		query.update(overrides)
		return query

	def _load(self, query):
		result = self._manager.loadAllSpoolsByQuery(query)
		return list(result)

	def _names(self, query):
		return [m.displayName for m in self._load(query)]

	def test_no_query_returns_all(self):
		models = self._load(self._query())
		self.assertEqual(len(models), 6)
		self.assertTrue(all(isinstance(m, SpoolModel) for m in models))

	def test_pagination(self):
		self.assertEqual(self._names(self._query(**{"from": 0, "to": 3})),
						["Alpha", "Beta", "delta"])
		self.assertEqual(self._names(self._query(**{"from": 3, "to": 3})),
						["Epsilon", "Gamma", "Zeta"])

	def test_selected_page_size_all_ignores_paging(self):
		self.assertEqual(len(self._load(self._query(**{"from": 0, "to": 2}, selectedPageSize="all"))), 6)

	def test_sort_displayname_case_insensitive(self):
		self.assertEqual(self._names(self._query(sortColumn="displayName", sortOrder="asc")),
						["Alpha", "Beta", "delta", "Epsilon", "Gamma", "Zeta"])

	def test_sort_displayname_desc(self):
		self.assertEqual(self._names(self._query(sortColumn="displayName", sortOrder="desc")),
						["Zeta", "Gamma", "Epsilon", "delta", "Beta", "Alpha"])

	def test_sort_remaining_asc(self):
		# note: saveSpool treats a missing usedWeight as 0.0, so remaining is never NULL
		# here (700 for Epsilon), hence NULL-ordering does not come into play
		self.assertEqual(self._names(self._query(sortColumn="remaining", sortOrder="asc")),
						["Beta", "Zeta", "delta", "Epsilon", "Alpha", "Gamma"])

	def test_material_filter(self):
		names = self._names(self._query(materialFilter="PLA,TPU"))
		self.assertEqual(len(names), 4)
		self.assertTrue(all(m in ("Alpha", "delta", "Epsilon", "Zeta") for m in names))

	def test_vendor_filter(self):
		self.assertEqual(self._names(self._query(vendorFilter="V1")), ["Alpha", "Gamma"])

	def test_color_filter(self):
		self.assertEqual(self._names(self._query(colorFilter="#ff0000;red")), ["Alpha", "delta"])

	def test_hide_empty_spools(self):
		models = self._load(self._query(filterName="hideEmptySpools"))
		names = [m.displayName for m in models]
		self.assertEqual(len(models), 5)
		self.assertNotIn("Beta", names)  # remaining == 0

	def test_hide_inactive_spools(self):
		models = self._load(self._query(filterName="hideInactiveSpools"))
		names = [m.displayName for m in models]
		self.assertEqual(len(models), 5)
		self.assertNotIn("Gamma", names)  # isActive == False

	def test_hide_empty_and_inactive_spools(self):
		names = self._names(self._query(filterName="hideEmptySpools,hideInactiveSpools"))
		self.assertEqual(len(names), 4)
		self.assertNotIn("Beta", names)
		self.assertNotIn("Gamma", names)

	def test_only_templates(self):
		self.assertEqual(self._names(self._query(filterName="onlyTemplates")), ["Gamma"])


if __name__ == '__main__':
	unittest.main()
