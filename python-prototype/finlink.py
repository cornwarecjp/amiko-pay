#    finlink.py
#    Copyright (C) 2014 by CJP
#
#    This file is part of Amiko Pay.
#
#    Amiko Pay is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Amiko Pay is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Amiko Pay. If not, see <http://www.gnu.org/licenses/>.

import time



class FinLink:
	def __init__(self, amikoContext, localID, remoteID):
		self.context = amikoContext

		self.localURL = "amikolink://localhost:4321/" + localID
		self.remoteURL = "amikolink://localhost:4321/" + remoteID #TODO

		self.context.setTimer(time.time() + 1.0, self.handleTimeout)


	def handleTimeout(self):
		print "Timeout event; local URL is " + self.localURL

		# Register again:
		self.context.setTimer(time.time() + 1.0, self.handleTimeout)


