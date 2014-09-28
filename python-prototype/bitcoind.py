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
	def __init__(self, settings):
		log.log("Making connection to Bitcoin daemon...")
		self.access = AuthServiceProxy(settings.bitcoinRPCURL)
		log.log("...done")
		

	def getBalance(self):
		return self.DecimaltoAmount(self.access.getbalance())


	def getBlockCount(self):
		return self.access.getblockcount()


	def getTransactionHashesByBlockHeight(self, height):
		bhash = self.access.getblockhash(height)
		block = self.access.getblock(bhash)
		return block["tx"]


	def getTransaction(self, thash):
		return self.access.getrawtransaction(thash, 1)


	def listUnspent(self):
		ret = self.access.listunspent()
		for vout in ret:
			vout["txid"] = binascii.unhexlify(vout["txid"])[::-1] #reversed; TODO: is this the right place?
			vout["scriptPubKey"] = binascii.unhexlify(vout["scriptPubKey"])
			vout["amount"] = self.DecimaltoAmount(vout["amount"])
		return ret


	def getPrivateKey(self, address):
		return self.access.dumpprivkey(address)


	def DecimaltoAmount(self, value):
		return int(value*100000000)




