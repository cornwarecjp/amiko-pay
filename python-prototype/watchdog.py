#    watchdog.py
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


import log



class Watchdog:
	"""
	Checks whether certain transactions are observed by Bitcoin, and calls the
	appropriate callback function if a transaction is observed.
	"""

	def __init__(self, bitcoind):
		self.bitcoind = bitcoind
		self.lastCheckedBlock = self.bitcoind.getBlockCount()
		self.onSpentCallbacks = {}

		self.toBeCheckedTransactionHashes = set([])

		#Test:
		def callback():
			print "Callback"
		#This is spent by ee475443f1fbfff84ffba43ba092a70d291df233bd1428f3d09f7bd1a6054a1f
		#in block 200000:
		tx = "6e046b9c7683b5887bbde42ec358542ffe9c250306edb2d0cf386394aa96ee10"
		self.addToWatchList(tx, 199990, callback)


	def addToWatchList(self, tx, firstBlock, callback):
		"""
		If, during check(), a transaction is detected which spends an output of
		tx, callback will be called.
		"""

		self.lastCheckedBlock = min(self.lastCheckedBlock, firstBlock)
		self.onSpentCallbacks[tx] = callback


	def check(self):
		if self.bitcoind.getBlockCount() > self.lastCheckedBlock:
			self.checkNextBlock()

		self.checkMemoryPool()

		self.checkTransactionHashes()


	def checkNextBlock(self):
		block = self.lastCheckedBlock + 1
		log.log("Watchdog: checking block %d..." % block)

		for thash in self.bitcoind.getTransactionHashesByBlockHeight(block):
			self.toBeCheckedTransactionHashes.add(thash)

		log.log("Watchdog: ...done checking block")
		self.lastCheckedBlock = block


	def checkMemoryPool(self):
		#print "checkMemoryPool" #TODO
		pass


	def checkTransactionHashes(self):
		for thash in self.toBeCheckedTransactionHashes:
			#print "Checking transaction %s..." % thash
			t = self.bitcoind.getTransaction(thash)
			for txin in t["vin"]:

				if "coinbase" in txin:
					continue #ignore coinbase transactions

				txid = txin["txid"]
				if txid in self.onSpentCallbacks:
					log.log("Watchdog: found a transaction spend!")
					print "Watchdog: found a transaction spend!"
					self.onSpentCallbacks[txid]()
					del self.onSpentCallbacks[txid]
			#print "...Done checking transaction"

		self.toBeCheckedTransactionHashes = set([])

