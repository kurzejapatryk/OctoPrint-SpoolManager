# coding=utf-8
# SPDX-FileCopyrightText: Copyright (c) OllisGit
# SPDX-FileCopyrightText: Copyright (c) 2026 Patryk Kurzeja
# SPDX-License-Identifier: AGPL-3.0-only

import datetime
import unittest

from octoprint_spoolmanager.api import Transformer
from octoprint_spoolmanager.models.SpoolModel import SpoolModel


def _build_spool(**overrides):
	"""Build a SpoolModel with known, fully populated values."""
	spool = SpoolModel()
	spool.displayName = "Test Spool"
	spool.vendor = "Acme"
	spool.material = "PLA"
	spool.color = "#ff0000"
	spool.colorName = "red"
	spool.code = "X-001"
	spool.isActive = True
	spool.density = 1.24
	spool.diameter = 1.75
	spool.totalWeight = 1000.0
	spool.spoolWeight = 100.0
	spool.usedWeight = 200.0
	spool.totalLength = 1000
	spool.usedLength = 0
	spool.firstUse = datetime.datetime(2020, 3, 2, 10, 33)
	spool.lastUse = datetime.datetime(2020, 4, 5, 14, 0)
	spool.purchasedOn = datetime.date(2020, 2, 1)
	spool.created = datetime.datetime(2020, 1, 1, 0, 0)
	spool.updated = datetime.datetime(2020, 1, 2, 9, 30)
	for key, value in overrides.items():
		setattr(spool, key, value)
	return spool


class TestCalculateRemainingWeight(unittest.TestCase):

	def test_both_floats(self):
		self.assertEqual(Transformer.calculateRemainingWeight(200.0, 1000.0), 800.0)

	def test_both_ints(self):
		self.assertEqual(Transformer.calculateRemainingWeight(0, 1000), 1000)

	def test_used_none(self):
		self.assertIsNone(Transformer.calculateRemainingWeight(None, 1000.0))

	def test_total_none(self):
		self.assertIsNone(Transformer.calculateRemainingWeight(200.0, None))

	def test_non_numeric_returns_none(self):
		self.assertIsNone(Transformer.calculateRemainingWeight("200", 1000.0))

	def test_negative_remaining(self):
		self.assertEqual(Transformer.calculateRemainingWeight(1500.0, 1000.0), -500.0)


class TestPercentages(unittest.TestCase):

	def test_remaining_percentage_normal(self):
		self.assertEqual(Transformer._calculateRemainingPercentage(800.0, 1000.0), 80.0)

	def test_remaining_percentage_zero_total(self):
		self.assertIsNone(Transformer._calculateRemainingPercentage(800.0, 0))

	def test_remaining_percentage_none(self):
		self.assertIsNone(Transformer._calculateRemainingPercentage(None, 1000.0))

	def test_used_percentage_normal(self):
		self.assertEqual(Transformer._calculateUsedPercentage(200.0, 1000.0), 20.0)

	def test_used_percentage_zero_total(self):
		self.assertIsNone(Transformer._calculateUsedPercentage(200.0, 0))

	def test_used_percentage_non_numeric(self):
		self.assertIsNone(Transformer._calculateUsedPercentage("200", 1000.0))


class TestTransformSpoolModelToDict(unittest.TestCase):

	def test_returns_the_models_internal_data_dict(self):
		spool = _build_spool()
		result = Transformer.transformSpoolModelToDict(spool)
		self.assertIs(result, spool.__data__)

	def test_dates_are_formatted(self):
		result = Transformer.transformSpoolModelToDict(_build_spool())
		self.assertEqual(result["firstUse"], "02.03.2020 10:33")
		self.assertEqual(result["lastUse"], "05.04.2020 14:00")
		self.assertEqual(result["purchasedOn"], "01.02.2020")
		self.assertEqual(result["created"], "01.01.2020 00:00")
		self.assertEqual(result["updated"], "02.01.2020 09:30")

	def test_weights_are_formatted_and_calculated(self):
		result = Transformer.transformSpoolModelToDict(_build_spool())
		self.assertEqual(result["totalWeight"], "1000.0")
		self.assertEqual(result["spoolWeight"], "100.0")
		self.assertEqual(result["usedWeight"], "200.0")
		self.assertEqual(result["remainingWeight"], "800.0")
		self.assertEqual(result["remainingPercentage"], "80.0")
		self.assertEqual(result["usedPercentage"], "20.0")

	def test_lengths_are_formatted_and_calculated(self):
		result = Transformer.transformSpoolModelToDict(_build_spool())
		self.assertEqual(result["remainingLength"], "1000")
		self.assertEqual(result["remainingLengthPercentage"], "100")
		self.assertEqual(result["usedLengthPercentage"], "0")

	def test_other_fields_are_preserved(self):
		result = Transformer.transformSpoolModelToDict(_build_spool())
		self.assertEqual(result["displayName"], "Test Spool")
		self.assertEqual(result["vendor"], "Acme")
		self.assertEqual(result["material"], "PLA")
		self.assertEqual(result["color"], "#ff0000")
		self.assertEqual(result["code"], "X-001")

	def test_none_fields_yield_empty_strings(self):
		spool = _build_spool(totalWeight=None, usedWeight=None, totalLength=None, usedLength=None)
		result = Transformer.transformSpoolModelToDict(spool)
		self.assertEqual(result["totalWeight"], "")
		self.assertEqual(result["usedWeight"], "")
		self.assertEqual(result["remainingWeight"], "")
		self.assertEqual(result["remainingPercentage"], "")
		self.assertEqual(result["usedPercentage"], "")
		self.assertEqual(result["remainingLength"], "")
		self.assertEqual(result["remainingLengthPercentage"], "")
		self.assertEqual(result["usedLengthPercentage"], "")

	def test_transform_mutates_the_models_internal_data(self):
		# Documented contract: the transform writes transformed values back into the
		# model's internal data dict (spoolAsDict is ``spoolModel.__data__``).
		spool = _build_spool()
		Transformer.transformSpoolModelToDict(spool)
		self.assertIsInstance(spool.__data__["totalWeight"], str)
		self.assertEqual(spool.__data__["totalWeight"], "1000.0")
		self.assertEqual(spool.__data__["remainingWeight"], "800.0")


class TestTransformAllSpoolModelsToDict(unittest.TestCase):

	def test_none_returns_empty_list(self):
		self.assertEqual(Transformer.transformAllSpoolModelsToDict(None), [])

	def test_empty_list_returns_empty_list(self):
		self.assertEqual(Transformer.transformAllSpoolModelsToDict([]), [])

	def test_multiple_models(self):
		spools = [_build_spool(), _build_spool(displayName="Second Spool")]
		result = Transformer.transformAllSpoolModelsToDict(spools)
		self.assertEqual(len(result), 2)
		self.assertEqual(result[0]["displayName"], "Test Spool")
		self.assertEqual(result[1]["displayName"], "Second Spool")


class TestRemainingPercentageContract(unittest.TestCase):

	def test_remaining_percentage_is_based_on_remaining_not_used(self):
		# Regression guard: Transformer.transformSpoolModelToDict (line 60) computes
		# remainingPercentage via _calculateUsedPercentage(remainingWeight, totalWeight).
		# For total=1000, used=200 -> remaining=800, so remaining% must be 80, not 20.
		result = Transformer.transformSpoolModelToDict(_build_spool())
		self.assertEqual(result["remainingPercentage"], "80.0")
		self.assertNotEqual(result["remainingPercentage"], "20.0")


if __name__ == '__main__':
	unittest.main()
