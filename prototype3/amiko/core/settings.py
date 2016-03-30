#    settings.py
#    Copyright (C) 2014-2016 by CJP
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
#
#    Additional permission under GNU GPL version 3 section 7
#
#    If you modify this Program, or any covered work, by linking or combining it
#    with the OpenSSL library (or a modified version of that library),
#    containing parts covered by the terms of the OpenSSL License and the SSLeay
#    License, the licensors of this Program grant you additional permission to
#    convey the resulting work. Corresponding Source for a non-source form of
#    such a combination shall include the source code for the parts of the
#    OpenSSL library used as well as that of the covered work.

import ConfigParser
import binascii

from ..utils import crypto



#Design settings (changing these creates an incompatibility):

def hashAlgorithm(data):
	return crypto.RIPEMD160(crypto.SHA256(data))
	

defaultPort = 4321



#User-changeable settings (can be loaded from conf file):
class Settings:
	def __init__(self, filename=None):
		self.__config = None
		self.load(filename)


	def load(self, filename):
		if filename != None:
			self.__config = ConfigParser.RawConfigParser()
			self.__config.read(filename)

		#general
		self.name = self.__get(
			"general", "name", '')

		#bitcoin RPC
		self.bitcoinRPCURL = self.__get(
			"bitcoind", "RPCURL", "")

		#network
		self.listenHost = self.__get(
			"network", "listenHost", '')
		self.listenPort = int(self.__get(
			"network", "listenPort", defaultPort))
		self.advertizedHost = self.__get(
			"network", "advertizedHost", self.listenHost)
		self.advertizedPort = int(self.__get(
			"network", "advertizedPort", self.listenPort))

		#providers
		self.externalMeetingPoints = self.__get(
			"providers", "externalMeetingPoints", "")
		self.externalMeetingPoints = self.externalMeetingPoints.split(",")
		self.externalMeetingPoints = \
			[s.strip() for s in self.externalMeetingPoints]
		if self.externalMeetingPoints[-1] == '':
			self.externalMeetingPoints = self.externalMeetingPoints[:-1] #remove empty

		#time
		self.payeeTimeout = int(self.__get(
			"time", "payeeTimeout", "60"))
		self.hopTimeoutIncrement = int(self.__get(
			"time", "hopTimeoutIncrement", "86400"))

		#files
		self.stateFile = self.__get(
			"files", "statefile", "amikopay.dat")
		self.payLogFile = self.__get(
			"files", "paylogfile", "payments.log")

		self.__config = None


	def __get(self, section, option, default):
		try:
			return self.__config.get(section, option)
		except:
			return default


	def getAdvertizedNetworkLocation(self):
		if self.advertizedPort == defaultPort:
			return self.advertizedHost
		return "%s:%s" % (self.advertizedHost, self.advertizedPort)


