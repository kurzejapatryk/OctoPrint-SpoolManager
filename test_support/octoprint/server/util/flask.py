# coding=utf-8
# SPDX-FileCopyrightText: Copyright (c) 2026 Patryk Kurzeja
# SPDX-License-Identifier: AGPL-3.0-only
# Test-only stub of octoprint.server.util.flask decorators.

def no_firstrun_access(func):
	return func

def restricted_access(func):
	return func
