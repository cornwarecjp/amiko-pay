#    settings.py
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

import hashlib



#Design settings (changing these creates an incompatibility):

def hashAlgorithm(data):
	return hashlib.sha256(data).digest()

defaultPort = 4321



#User-changeable settings (can be loaded from conf file):
class Settings:
	def __init__(self, filename=None):
		#Default values
		self.listenHost = 'localhost'
		self.listenPort = defaultPort
		self.advertizedHost = self.listenHost
		self.advertizedPort = self.listenPort

		if filename != None:
			self.load(filename)


	def load(self, filename):
		pass #TODO


	def getAdvertizedNetworkLocation(self):
		if self.advertizedPort == defaultPort:
			return self.advertizedHost
		return "%s:%s" % (self.advertizedHost, self.advertizedPort)


