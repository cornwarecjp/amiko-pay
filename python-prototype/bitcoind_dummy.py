#    bitcoind_dummy.py
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

import binascii

import log



class Bitcoind_Dummy:
	"""
	Simulated connection to a Bitcoin daemon process.
	"""

	def __init__(self, settings):
		pass


	def isConnected(self):
		return True
		

	def getBalance(self):
		return 0


	def getBlockCount(self):
		return 0


	def getNewAddress(self):
		raise Exception("Not yet implemented")


	def getPrivateKey(self, address):
		raise Exception("Not yet implemented")


	def getTransactionHashesByBlockHeight(self, height):
		raise Exception("Not yet implemented")


	def getTransaction(self, thash):
		raise Exception("Not yet implemented")


	def listUnspent(self):
		raise Exception("Not yet implemented")


	def sendRawTransaction(self, txData):
		raise Exception("Not yet implemented")


