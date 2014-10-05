#    bitcoind.py
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

from bitcoinrpc.authproxy import AuthServiceProxy

import log



class Bitcoind:
	"""
	Connection to a Bitcoin daemon process.
	"""

	def __init__(self, settings):
		"""
		Arguments:
		settings: a settings object; must contain the attribute bitcoinRPCURL.

		Connects to a Bitcoin daemon process, indicated by settings.bitcoinRPCURL.
		If settings.bitcoinRPCURL is empty, this object will not be connected.
		"""

		if settings.bitcoinRPCURL != "":
			log.log("Making connection to Bitcoin daemon...")
			self.access = AuthServiceProxy(settings.bitcoinRPCURL)
			log.log("...done")
		else:
			log.log("Bitcoin-RPC URL is not set: not connecting")
			self.access = None


	def isConnected(self):
		"""
		Return value:
		bool

		Returns whether this object is connected.
		"""

		return self.access != None
		

	def getBalance(self):
		"""
		Return value:
		int, in Satoshi

		Returns the balance.
		"""

		return self.DecimaltoAmount(self.access.getbalance())


	def getBlockCount(self):
		"""
		Return value:
		int

		Returns the block count.
		"""

		return self.access.getblockcount()


	def getPrivateKey(self, address):
		"""
		Arguments:
		address: str, Base58Check-encoded address
		Return value:
		str, Base58Check-encoded private key

		Returns the private key corresponding to the given address.
		"""

		return self.access.dumpprivkey(address)


	def getTransactionHashesByBlockHeight(self, height):
		"""
		Arguments:
		height: int
		Return value:
		list of str, hexadecimal, Bitcoin hash byte order

		Returns the transaction hashes in the block (in the main chain) at the
		given height.
		"""

		bhash = self.access.getblockhash(height)
		block = self.access.getblock(bhash)
		return block["tx"]


	def getTransaction(self, thash):
		"""
		Arguments:
		thash: str, hexadecimal, Bitcoin hash byte order

		Return value:
		dict, containing:
			vin: list of dict, each element containing:
				coinbase [only for coinbase transactions]
				txid [only for non-coinbase transactions]:
					str, hexadecimal, Bitcoin hash byte order
					hash of input transaction

		Returns information about the transaction indicated by the given hash.
		"""

		return self.access.getrawtransaction(thash, 1)


	def listUnspent(self):
		"""
		Return value:
		list of dict, each element containing:
			address: 
				str, Base58Check-encoded address
			amount:
				int, in Satoshi
			scriptPubKey:
				str, binary
			txid:
				str, binary, OpenSSL byte order
			vout:
				int

		Returns information about the available unspent transaction outputs.
		"""

		ret = self.access.listunspent()
		for vout in ret:
			vout["txid"] = binascii.unhexlify(vout["txid"])[::-1] #reversed; TODO: is this the right place?
			vout["scriptPubKey"] = binascii.unhexlify(vout["scriptPubKey"])
			vout["amount"] = self.DecimaltoAmount(vout["amount"])
		return ret


	def sendRawTransaction(self, txData):
		"""
		Arguments:
		txData: str, binary

		Send the given serialized transaction over the Bitcoin network.
		"""

		self.access.sendrawtransaction(txData.encode("hex"))


	def DecimaltoAmount(self, value):
		return int(value*100000000)




