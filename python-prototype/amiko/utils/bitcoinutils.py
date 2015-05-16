#    bitcoinutils.py
#    Copyright (C) 2014-2015 by CJP
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

import base58
import struct

from bitcointransaction import Transaction, TxIn, TxOut, Script, OP

from crypto import Key, SHA256



def getInputsForAmount(bitcoind, amount):
	"""
	Returns information about unspent outputs, which are available to be used
	as inputs for a new transaction, and have a total amount that is at least
	the requested amount.

	Arguments:
	bitcoind: Bitcoind; the bitcoin daemon from which to retrieve this information
	amount: int; the minimum total amount (in Satoshi)

	Return value:
	tuple (total, inputs)
	total: int; the actual total amount (in Satoshi); total >= amount
	inputs: list of tuple (txid, vout, scriptPubKey, privateKey); the input information
	txid: str; input transaction ID. Note that the byte order is the reverse as
	      shown in Bitcoin.
	vout: int; input transaction index
	scriptPubKey: str; input transaction scriptPubKey (serialized)
	privateKey: str; corresponding private key

	Exceptions:
	Exception: insufficient funds
	"""

	unspent = bitcoind.listUnspent()

	#Filter: only use "normal" outputs, not multisig etc.
	unspent = [u for u in unspent if "address" in u]

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
	"""
	Make a transaction to send funds from ourself to a standard Bitcoin
	scriptPubKey ("send to Bitcoin address"). The transaction is returned, and
	is NOT published on the Bitcoin network by this function.

	Arguments:
	bitcoind: Bitcoind; the bitcoin daemon from which to retrieve this information
	amount: int; the amount to be sent, not including the fee (in Satoshi)
	toHash: str; the SHA256- and RIPEMD160-hashed public key of the receiver
	        (equivalent to the bitcoin address)
	changeHash: str; the SHA256- and RIPEMD160-hashed public key to which any
	            change should be sent (equivalent to the bitcoin address)
	fee: int; the transaction fee (in Satoshi)

	Return value:
	Transaction; the transaction that sends funds as specified.

	Exceptions:
	Exception: insufficient funds
	"""

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

	return tx


def sendToDataPubKey(bitcoind, data, changeHash, fee):
	"""
	Make a transaction to publish data on the block chain with an OP_RETURN
	output. No funds are sent to the OP_RETURN output: everything goes to fee
	and to the change address. The transaction is returned, and
	is NOT published on the Bitcoin network by this function.

	Arguments:
	bitcoind: Bitcoind; the bitcoin daemon from which to retrieve this information
	data: str; the data to be included in the scriptPubKey (max. 40 bytes)
	changeHash: str; the SHA256- and RIPEMD160-hashed public key to which any
	            change should be sent (equivalent to the bitcoin address)
	fee: int; the transaction fee (in Satoshi)

	Return value:
	Transaction; the transaction that sends funds as specified.

	Exceptions:
	Exception: insufficient funds
	"""

	totalIn, inputs = getInputsForAmount(bitcoind, fee)
	change = totalIn - fee

	print "%d -> %d, %d" % (totalIn, change, fee)

	tx = Transaction(
		tx_in = [
			TxIn(x[0], x[1])
			for x in inputs
			],
		tx_out = [
			TxOut(0, Script.dataPubKey(data)),
			TxOut(change, Script.standardPubKey(changeHash))
			]
		)

	for i in range(len(inputs)):
		scriptPubKey = Script.deserialize(inputs[i][2])
		key = Key()
		key.setPrivateKey(inputs[i][3])
		tx.signInput(i, scriptPubKey, [None, key.getPublicKey()], [key])

	return tx


def sendToMultiSigPubKey(bitcoind, amount, toPubKey1, toPubKey2, changeHash, fee):
	"""
	Make a transaction to send funds from ourself to a 2-of-2 multi-signature
	scriptPubKey. The transaction is returned, and is NOT published on the
	Bitcoin network by this function.

	Arguments:
	bitcoind: Bitcoind; the bitcoin daemon from which to retrieve this information
	amount: int; the amount to be sent, not including the fee (in Satoshi)
	toPubKey1: str; the first public key
	toPubKey2: str; the second public key
	changeHash: str; the SHA256- and RIPEMD160-hashed public key to which any
	            change should be sent (equivalent to the bitcoin address)
	fee: int; the transaction fee (in Satoshi)

	Return value:
	Transaction; the transaction that sends funds as specified.

	Exceptions:
	Exception: insufficient funds
	"""

	totalIn, inputs = getInputsForAmount(bitcoind, amount+fee)
	change = totalIn - fee - amount

	#print "%d -> %d, %d, %d" % (totalIn, amount, change, fee)

	tx = Transaction(
		tx_in = [
			TxIn(x[0], x[1])
			for x in inputs
			],
		tx_out = [
			TxOut(amount, Script.multiSigPubKey([toPubKey1, toPubKey2])),
			TxOut(change, Script.standardPubKey(changeHash))
			]
		)

	for i in range(len(inputs)):
		scriptPubKey = Script.deserialize(inputs[i][2])
		key = Key()
		key.setPrivateKey(inputs[i][3])
		tx.signInput(i, scriptPubKey, [None, key.getPublicKey()], [key])

	return tx


def makeSpendMultiSigTransaction(outputHash, outputIndex, amount, toHash, fee):
	"""
	Make an (non-signed) transaction to send funds from a 2-of-2 multi-signature
	output to a standard Bitcoin scriptPubKey ("send to Bitcoin address").
	The transaction is returned, and is NOT published on the Bitcoin network by
	this function.

	Arguments:
	outputHash: str; the transaction ID of the previous output transaction
	            Note that the byte order is the reverse as shown in Bitcoin.
	outputIndex: int; the index of the output in the previous output transaction
	amount: int; the amount to be sent, including the fee (in Satoshi).
	        This must be equal to the amount in the input.
	toHash: str; the SHA256- and RIPEMD160-hashed public key of the receiver
	        (equivalent to the bitcoin address)
	fee: int; the transaction fee (in Satoshi)

	Return value:
	Transaction; the transaction that sends funds as specified.
	"""

	tx = Transaction(
		tx_in = [TxIn(outputHash, outputIndex)],
		tx_out = [TxOut(amount-fee, Script.standardPubKey(toHash))]
		)

	return tx


def signMultiSigTransaction(tx, inputIndex, pubKeys, key):
	"""
	Create a signature for a transaction that spends a 2-of-2 multi-signature
	output. The signature is returned, and is NOT inserted in the transaction.

	Arguments:
	tx: Transaction; the transaction
	outputIndex: int; the index of the transaction input to which a signature
	             applies
	pubKeys: sequence of str; the public keys
	         2 <= len(pubKeys) <= 16
	key: Key; the private key to be used for signing (should correspond to one
	     of the keys in pubKeys)

	Return value:
	str; the signature, including the hash type
	"""

	hashType = 1 #SIGHASH_ALL
	scriptPubKey = Script.multiSigPubKey(pubKeys)
	bodyHash = tx.getSignatureBodyHash(inputIndex, scriptPubKey, hashType)
	return key.sign(bodyHash) + struct.pack('B', hashType) #uint8_t


def verifyMultiSigSignature(tx, inputIndex, pubKeys, key, signature):
	"""
	Verify a signature for a transaction that spends a 2-of-2 multi-signature
	output.

	Arguments:
	tx: Transaction; the transaction
	inputIndex: int; the index of the transaction input to which a signature
	            applies
	pubKeys: sequence of str; the public keys
	         2 <= len(pubKeys) <= 16
	key: Key; the public key used for signing (should correspond to one of the
	     keys in pubKeys)
	signature: str; the signature, including the hash type

	Return value:
	bool; indicates whether the signature is correct (True) or not (False)

	Exceptions:
	Exception: signature verification failed
	"""

	hashType = struct.unpack('B', signature[-1])[0] #uint8_t
	if hashType != 1: #SIGHASH_ALL
		return False
	signature = signature[:-1]
	scriptPubKey = Script.multiSigPubKey(pubKeys)
	bodyHash = tx.getSignatureBodyHash(inputIndex, scriptPubKey, hashType)
	return key.verify(bodyHash, signature)


def applyMultiSigSignatures(tx, sig1, sig2):
	"""
	Apply signatures to a transaction that spends a 2-of-2 multi-signature
	output.

	Arguments:
	tx: Transaction; the transaction. Note that the transaction will be changed
	    by this function.
	sig1: str; the signature, including the hash type, corresponding with the
	      first public key
	sig2: str; the signature, including the hash type, corresponding with the
	      second public key
	"""
	tx.signInputWithSignatures(0, [OP.ZERO, None, None], [sig1, sig2])


