# SPDX-FileCopyrightText: Copyright (c) OllisGit
# SPDX-FileCopyrightText: Copyright (c) 2026 Patryk Kurzeja
# SPDX-License-Identifier: AGPL-3.0-only
from logging import StreamHandler

# Used for SQL-Logging
class WrappedLoggingHandler(StreamHandler):

	def __init__(self, wrappedLogger):
		StreamHandler.__init__(self)
		self.wrappedLogger = wrappedLogger

	def emit(self, record):
		msg = self.format(record)
		self.wrappedLogger.debug(msg)  # this is it!!!!
	# self.wrappedLogger.handle(record)
