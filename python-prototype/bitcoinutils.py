#    bitcoinutils.py
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

import base58


from bitcointransaction import Transaction, TxIn, TxOut, Script

from crypto import Key, SHA256



def getInputsForAmount(bitcoind, amount):
	"""
	Return value:
	total, [(txid, vout, scriptPubKey, privateKey), ...]

	total: the total amount of all the inputs (>= amount)
	txid: input transaction hash
	vout: input transaction index
	scriptPubKey: input transaction scriptPubKey (serialized)
	privateKey: corresponding private key
	"""

	unspent = bitcoind.listUnspent()

	#TODO: think about the best policy here.
	#Possible objectives:
	# - minimizing taint between addresses (privacy protection)
	# - minimizing coin fragmentation (transaction size, related to fee costs)
	# - choosing old coins (related to fee costs)
	#For now, an attempt is made to minimize coin fragmentation.

	unspent.sort(cmp=lambda a,b: cmp(a["amount"], b["amount"]))

	used = None
	total = 0
	for u in unspent:
		if u["amount"] >= amount:
			used = [u]
			total = u["amount"]
			break
	if used is None:
		used = []
		while total < amount:
			try:
				u = unspent.pop()
			except IndexError:
				raise Exception("Insufficient funds")
			used.append(u)
			total += u["amount"]

	for u in used:
		address = u["address"]
		u["privateKey"] = base58.decodeBase58Check(
			bitcoind.getPrivateKey(address), 128)

	return total, [
		(u["txid"], u["vout"], u["scriptPubKey"], u["privateKey"])
		for u in used]


def sendToStandardPubKey(bitcoind, amount, toHash, changeHash, fee):
	totalIn, inputs = getInputsForAmount(bitcoind, amount+fee)
	change = totalIn - fee - amount

	print "%d -> %d, %d, %d" % (totalIn, amount, change, fee)

	tx = Transaction(
		tx_in = [
			TxIn(x[0], x[1])
			for x in inputs
			],
		tx_out = [
			TxOut(amount, Script.standardPubKey(toHash)),
			TxOut(change, Script.standardPubKey(changeHash))
			]
		)

	for i in range(len(inputs)):
		scriptPubKey = Script.deserialize(inputs[i][2])
		key = Key()
		key.setPrivateKey(inputs[i][3])
		tx.signInput(i, scriptPubKey, [None, key.getPublicKey()], [key])


	tx = tx.serialize()

	bitcoind.sendRawTransaction(tx)

	return SHA256(SHA256(tx)) #Note: in Bitcoin, the tx hash is shown reversed!

