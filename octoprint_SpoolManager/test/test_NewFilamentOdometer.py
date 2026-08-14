# coding=utf-8
# SPDX-FileCopyrightText: Copyright (c) OllisGit
# SPDX-FileCopyrightText: Copyright (c) 2026 Patryk Kurzeja
# SPDX-License-Identifier: AGPL-3.0-only

import unittest

from octoprint_SpoolManager.newodometer import NewFilamentOdometer


class TestNewFilamentOdometer(unittest.TestCase):

	def _make(self):
		self.events = []
		return NewFilamentOdometer(lambda v: self.events.append(list(v)))

	# ---------------------------------------------------------------- state
	def test_initial_state(self):
		od = NewFilamentOdometer()
		self.assertEqual(od.getCurrentTool(), 0)
		self.assertEqual(od.getExtrusionAmount(), [0.0])
		self.assertEqual(od.currentE, [0.0])
		self.assertEqual(od.totalExtrusion, [0.0])
		self.assertFalse(od.relativeE)
		self.assertFalse(od.relativeMode)
		self.assertFalse(od.duplicationMode)
		self.assertEqual(od.max_extruders, 10)
		self.assertFalse(od.g90_extruder)

	def test_reset_restores_state_and_fires_event(self):
		od = self._make()
		od.processGCodeLine("G1 X0 Y0 E5.0")
		self.assertEqual(od.getExtrusionAmount(), [5.0])
		n_events = len(self.events)
		od.reset()
		self.assertEqual(od.getExtrusionAmount(), [0.0])
		self.assertEqual(od.currentE, [0.0])
		self.assertEqual(od.totalExtrusion, [0.0])
		self.assertEqual(od.currentExtruder, 0)
		self.assertEqual(len(self.events), n_events + 1)

	def test_get_extrusion_amount_returns_max_extrusion_reference(self):
		od = NewFilamentOdometer()
		self.assertIs(od.getExtrusionAmount(), od.maxExtrusion)

	# ---------------------------------------------------------------- G0-G3
	def test_absolute_extrusion_accumulates_delta(self):
		od = NewFilamentOdometer()
		od.processGCodeLine("G1 X0 Y0 E1.0")
		self.assertEqual(od.getExtrusionAmount(), [1.0])
		od.processGCodeLine("G1 X0 Y0 E2.5")  # absolute -> delta 1.5
		self.assertEqual(od.getExtrusionAmount(), [2.5])

	def test_move_without_extrusion_is_ignored(self):
		od = NewFilamentOdometer()
		od.processGCodeLine("G1 X10 Y10")
		self.assertEqual(od.getExtrusionAmount(), [0.0])

	# ---------------------------------------------------------------- G90/G91
	def test_relative_mode_accumulates_full_E(self):
		od = NewFilamentOdometer()
		od.processGCodeLine("G91")
		od.processGCodeLine("G1 E1.0")
		od.processGCodeLine("G1 E2.0")
		self.assertEqual(od.getExtrusionAmount(), [3.0])

	def test_g90_restores_absolute(self):
		od = NewFilamentOdometer()
		od.processGCodeLine("G91")
		od.processGCodeLine("G90")
		self.assertFalse(od.relativeMode)

	def test_g90_extruder_flag_controls_relativeE(self):
		od = NewFilamentOdometer()
		od.set_g90_extruder(True)
		od.processGCodeLine("G91")
		self.assertTrue(od.relativeE)
		od.processGCodeLine("G90")
		self.assertFalse(od.relativeE)

	def test_without_g90_extruder_flag_g91_leaves_relativeE(self):
		od = NewFilamentOdometer()  # g90_extruder = False (default)
		self.assertFalse(od.relativeE)
		od.processGCodeLine("G91")
		self.assertFalse(od.relativeE)

	# ---------------------------------------------------------------- M82/M83
	def test_m82_m83_toggle_relative_e(self):
		od = NewFilamentOdometer()
		od.processGCodeLine("M83")
		self.assertTrue(od.relativeE)
		od.processGCodeLine("M82")
		self.assertFalse(od.relativeE)

	# ---------------------------------------------------------------- G92
	def test_g92_e_zero_then_extrude(self):
		od = NewFilamentOdometer()
		od.processGCodeLine("G1 E2.0")
		self.assertEqual(od.currentE, [2.0])
		od.processGCodeLine("G92 E0")
		self.assertEqual(od.currentE, [0.0])
		od.processGCodeLine("G1 E3.0")
		self.assertEqual(od.currentE, [3.0])
		self.assertEqual(od.getExtrusionAmount(), [5.0])

	def test_g92_no_params_resets_current_e(self):
		od = NewFilamentOdometer()
		od.processGCodeLine("G1 E2.0")
		od.processGCodeLine("G92")
		self.assertEqual(od.currentE, [0.0])

	# ---------------------------------------------------------------- T
	def test_tool_switch_extends_arrays(self):
		od = NewFilamentOdometer()
		od.processGCodeLine("T1")
		self.assertEqual(od.getCurrentTool(), 1)
		self.assertEqual(len(od.getExtrusionAmount()), 2)
		od.processGCodeLine("G1 E2.0")
		self.assertEqual(od.getExtrusionAmount(), [0.0, 2.0])

	# ---------------------------------------------------------------- M605
	def test_duplication_mode(self):
		od = NewFilamentOdometer()
		od.processGCodeLine("T1")
		od.processGCodeLine("T0")
		od.processGCodeLine("M605 S2")
		self.assertTrue(od.duplicationMode)
		od.processGCodeLine("G1 E1.0")
		self.assertEqual(od.getExtrusionAmount(), [1.0, 1.0])
		od.processGCodeLine("M605 S0")
		self.assertFalse(od.duplicationMode)
		od.processGCodeLine("G1 E2.0")
		self.assertEqual(od.getExtrusionAmount(), [2.0, 1.0])

	# ---------------------------------------------------------------- comments
	def test_comment_stripping(self):
		od = NewFilamentOdometer()
		od.processGCodeLine("G1 E1.0 ; some comment")
		self.assertEqual(od.getExtrusionAmount(), [1.0])

	def test_empty_and_comment_only_lines_are_noops(self):
		od = NewFilamentOdometer()
		od.processGCodeLine("")
		od.processGCodeLine("; just a comment")
		self.assertEqual(od.getExtrusionAmount(), [0.0])

	# ---------------------------------------------------------------- misc
	def test_reset_extruded_length_keeps_mode(self):
		od = NewFilamentOdometer()
		od.processGCodeLine("G91")
		od.processGCodeLine("G1 E3.0")
		self.assertEqual(od.getExtrusionAmount(), [3.0])
		od.reset_extruded_length()
		self.assertEqual(od.getExtrusionAmount(), [0.0])
		self.assertTrue(od.relativeMode)

	def test_event_fires_on_extrusion(self):
		od = self._make()
		n_events = len(self.events)
		od.processGCodeLine("G1 E1.0")
		self.assertEqual(len(self.events), n_events + 1)


if __name__ == '__main__':
	unittest.main()
