# coding=utf-8
# SPDX-FileCopyrightText: Copyright (c) 2026 Patryk Kurzeja
# SPDX-License-Identifier: AGPL-3.0-only
# Test-only stub of octoprint.plugin mixins.

class SimpleApiPlugin(object):
	pass

class SettingsPlugin(object):
	pass

class AssetPlugin(object):
	pass

class TemplatePlugin(object):
	pass

class StartupPlugin(object):
	pass

class EventHandlerPlugin(object):
	pass

class BlueprintPlugin(object):
	@staticmethod
	def route(rule, **options):
		def decorator(func):
			return func
		return decorator
