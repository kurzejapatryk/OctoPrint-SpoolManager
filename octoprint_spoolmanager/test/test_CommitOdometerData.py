# coding=utf-8
# SPDX-FileCopyrightText: Copyright (c) OllisGit
# SPDX-FileCopyrightText: Copyright (c) 2026 Patryk Kurzeja
# SPDX-License-Identifier: AGPL-3.0-only

import logging
import unittest

from octoprint_spoolmanager import SpoolManagerPlugin
from octoprint_spoolmanager.models.SpoolModel import SpoolModel


class _FakeOdometer(object):
	def __init__(self, extrusions):
		self.extrusions = list(extrusions)
		self.reset_called = False

	def getExtrusionAmount(self):
		return self.extrusions

	def reset_extruded_length(self):
		self.reset_called = True


class _FakeDatabaseManager(object):
	def __init__(self):
		self.saved = []

	def saveSpool(self, spool):
		self.saved.append(spool)


class TestCommitOdometerData(unittest.TestCase):

	def setUp(self):
		self.plugin = SpoolManagerPlugin()
		self.plugin._logger = logging.getLogger("test")
		self.events = []
		self.client_messages = []

	def _make_spool(self, **overrides):
		spool = SpoolModel()
		spool.displayName = "Spool A"
		spool.material = "PLA"
		spool.colorName = "red"
		spool.databaseId = 1
		spool.totalWeight = 1000.0
		spool.diameter = 1.75
		spool.density = 1.24
		spool.usedLength = None
		spool.usedWeight = None
		for key, value in overrides.items():
			setattr(spool, key, value)
		return spool

	def _configure(self, selected, extrusions):
		self.plugin.loadSelectedSpools = lambda: selected
		dm = _FakeDatabaseManager()
		self.plugin._databaseManager = dm
		od = _FakeOdometer(extrusions)
		self.plugin.myFilamentOdometer = od
		self.plugin._sendPayload2EventBus = lambda key, payload: self.events.append((key, payload))
		self.plugin._sendDataToClient = lambda data: self.client_messages.append(data)
		return dm, od

	def test_updates_used_length_and_weight(self):
		spool = self._make_spool()
		self._configure([spool], [10.0])
		self.plugin.commitOdometerData()

		self.assertEqual(spool.usedLength, 10.0)
		expected = self.plugin._calculateWeight(10.0, 1.75, 1.24)
		self.assertAlmostEqual(spool.usedWeight, expected)
		self.assertIsNotNone(spool.lastUse)
		self.assertEqual(len(self.plugin._databaseManager.saved), 1)

	def test_accumulates_previous_used_length(self):
		spool = self._make_spool(usedLength=5.0, usedWeight=2.0)
		self._configure([spool], [10.0])
		self.plugin.commitOdometerData()
		self.assertEqual(spool.usedLength, 15.0)

	def test_missing_diameter_or_density_skips_weight(self):
		spool = self._make_spool(diameter=None, density=None)
		self._configure([spool], [10.0])
		self.plugin.commitOdometerData()
		self.assertEqual(spool.usedLength, 10.0)
		self.assertIsNone(spool.usedWeight)
		self.assertEqual(len(self.plugin._databaseManager.saved), 1)  # length still saved

	def test_none_spool_slot_is_skipped(self):
		spool = self._make_spool()
		self._configure([spool, None], [10.0, 20.0])
		self.plugin.commitOdometerData()
		self.assertEqual(len(self.plugin._databaseManager.saved), 1)
		self.assertEqual(spool.usedLength, 10.0)

	def test_missing_extrusion_for_tool_is_skipped(self):
		spool0 = self._make_spool()
		spool1 = self._make_spool(databaseId=2, displayName="Spool B")
		self._configure([spool0, spool1], [10.0])  # odometer only has tool 0
		self.plugin.commitOdometerData()
		self.assertEqual(len(self.plugin._databaseManager.saved), 1)

	def test_event_bus_payload(self):
		spool = self._make_spool()
		self._configure([spool], [10.0])
		self.plugin.commitOdometerData()
		self.assertEqual(len(self.events), 1)
		key, payload = self.events[0]
		self.assertEqual(key, "spool_weight_updated_after_print")
		self.assertEqual(payload["toolId"], 0)
		self.assertEqual(payload["databaseId"], 1)
		self.assertEqual(payload["spoolName"], "Spool A")
		self.assertEqual(payload["material"], "PLA")
		self.assertEqual(payload["colorName"], "red")

	def test_sends_reload_to_client_when_spool_updated(self):
		spool = self._make_spool()
		self._configure([spool], [10.0])
		self.plugin.commitOdometerData()
		self.assertTrue(
			any("reloadTable and sidebarSpools" == m.get("action") for m in self.client_messages))

	def test_odometer_reset_extruded_length_called(self):
		spool = self._make_spool()
		_, od = self._configure([spool], [10.0])
		self.plugin.commitOdometerData()
		self.assertTrue(od.reset_called)


if __name__ == '__main__':
	unittest.main()
