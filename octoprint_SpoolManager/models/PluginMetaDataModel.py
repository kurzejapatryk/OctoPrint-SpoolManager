# coding=utf-8
# SPDX-FileCopyrightText: Copyright (c) OllisGit
# SPDX-FileCopyrightText: Copyright (c) 2026 Patryk Kurzeja
# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import absolute_import

from octoprint_SpoolManager.models.BaseModel import BaseModel
from peewee import CharField, Model, DecimalField, FloatField, DateField, DateTimeField, TextField, ForeignKeyField


class PluginMetaDataModel(BaseModel):

	KEY_PLUGIN_VERSION = "pluginVersion"
	KEY_DATABASE_SCHEME_VERSION = "databaseSchemeVersion"

	key = CharField(null=False)
	value = CharField(null=False)
