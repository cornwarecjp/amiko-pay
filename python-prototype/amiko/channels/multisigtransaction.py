#    multisigtransaction.py
#    Copyright (C) 2015 by CJP
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

import struct
import binascii

from ..utils import bitcointransaction

from ..utils.bitcoinutils import sendToMultiSigPubKey
from ..utils.bitcoinutils import makeSpendMultiSigTransaction, signMultiSigTransaction
from ..utils.bitcoinutils import verifyMultiSigSignature, applyMultiSigSignatures

from ..utils.crypto import SHA256, RIPEMD160

import tcd



class MultiSigTransaction:
	"""
	A multi-signature transaction with Transaction Conditions Documents,
	for Lightning HTLC emulation.

	Attributes:
	transaction: Transaction; the "withdraw" transaction that spends the
	             multi-signature output of the deposit transaction.
	TCDlist: list of TCD; The Transaction Conditions Documents that apply to this
	         transaction.
	"""

	@staticmethod
	def makeNew(ownKey, depositTxID, amount, fee, lockTime):
		"""
		Make a new MultiSigTransaction, for the initial deposit.
		All funds are returned to the address of ownKey, and there are no active
		micro-transactions (hence no locked funds and no TCDs).
		This is a static method: it can be called without having an instance,
		as an alternative to calling the constructor directly.

		Arguments:
		ownKey: Key; our own key. Should contain a public key.
		depositTxID: str; The transaction ID of the deposit transaction.
		             Note that the byte order is the reverse as shown in Bitcoin.
		amount: int; the amount to be sent, including the fee (in Satoshi).
		        This must be equal to the amount in the input.
		fee: int; the transaction fee (in Satoshi).
		lockTime: int; The lock time.

		Return value:
		MultiSigTransaction; the created transaction structure.
		"""

		returnKeyHash = RIPEMD160(SHA256(ownKey.getPublicKey()))
		transaction = makeSpendMultiSigTransaction(
			depositTxID, 0, amount, returnKeyHash, fee)
		transaction.lockTime = lockTime
		return MultiSigTransaction(transaction, [])


	@staticmethod
	def makeFromState(state):
		"""
		Make a MultiSigTransaction, based on the given state object.
		This is a static method: it can be called without having an instance,
		as an alternative to calling the constructor directly.

		Arguments:
		state: A data structure, consisting of only standard Python types like
		       dict, list, str, bool, int.

		Return value:
		MultiSigTransaction; the created transaction structure.

		Exceptions:
		Exception: loading from the state object failed
		"""

		transaction = bitcointransaction.Transaction.deserialize(
			binascii.unhexlify(state["tx"])
			)
		TCDlist = tcd.deserializeList(
			binascii.unhexlify(state["TCDs"])
			)
		return MultiSigTransaction(transaction, TCDlist)


	@staticmethod
	def deserialize(data):
		"""
		De-serializes a MultiSigTransaction.
		This is a static method: it can be called without having an instance,
		as an alternative to calling the constructor directly.

		Arguments:
		data: str; the serialized MultiSigTransaction.

		Return value:
		MultiSigTransaction; the created transaction structure.

		Exceptions:
		Exception: deserialization failed
		"""

		length = struct.unpack('!I', data[:4])[0] #uint32_t
		TCDlist = tcd.deserializeList(data[4:4+length])
		transaction = bitcointransaction.Transaction.deserialize(data[4+length:])
		return MultiSigTransaction(transaction, TCDlist)


	def __init__(self, transaction, TCDlist):
		"""
		Constructor.

		Arguments:
		transaction: Transaction; the "withdraw" transaction that spends the
			         multi-signature output of the deposit transaction.
		TCDlist: list of TCD; The Transaction Conditions Documents that apply to
		         this transaction.
		"""

		self.transaction = transaction
		self.TCDlist = TCDlist


	def serialize(self):
		"""
		Serializes the MultiSigTransaction.

		Return value:
		str; the serialized MultiSigTransaction.
		"""

		serializedList = tcd.serializeList(self.TCDlist)
		return struct.pack('!I', len(serializedList)) + \
			serializedList + self.transaction.serialize()


	def getState(self, forDisplay=False):
		"""
		Return a data structure that contains state information of the
		MultiSigTransaction.

		Arguments:
		forDisplay: bool; indicates whether the returned state is for user
		            interface display purposes (True) or for state saving
		            purposes (False). For user interface display purposes, a
		            summary may be returned instead of the complete state.

		Return value:
		A data structure, consisting of only standard Python types like dict,
		list, str, bool, int.
		"""

		ret = {}
		if forDisplay:
			ret["ID"] = self.transaction.getTransactionID()[::-1].encode("hex")
		else:
			ret["tx"] = self.transaction.serialize().encode("hex")
			ret["TCDs"] = tcd.serializeList(self.TCDlist).encode("hex")
		return ret


	def setOutputs(self, ownPubKey, peerPubKey, escrowPubKey,
		ownAmount, peerAmount):
		"""
		Re-write the outputs of the transaction, based on the TCDlist attribute
		and the given arguments.

		Arguments:
		ownPubKey: str; our own public key.
		peerPubKey: str; the public key of the peer.
		escrowPubKey: str; the public key of the escrow service.
		ownAmount: int; the non-locked funds available to ourselves (in Satoshi).
		peerAmount: int; the non-locked funds available to the peer (in Satoshi).
		"""

		ownKeyHash = RIPEMD160(SHA256(ownPubKey))
		peerKeyHash = RIPEMD160(SHA256(peerPubKey))

		lockedAmount = sum([doc.amount for doc in self.TCDlist])

		self.transaction.tx_out = []

		if len(self.TCDlist) > 0:
			pass #TODO: add OP_RETURN output

		if ownAmount > 0:
			self.transaction.tx_out.append(bitcointransaction.TxOut(
				ownAmount,
				bitcointransaction.Script.standardPubKey(ownKeyHash))
				)

		if peerAmount > 0:
			self.transaction.tx_out.append(bitcointransaction.TxOut(
				peerAmount,
				bitcointransaction.Script.standardPubKey(peerKeyHash))
				)

		if lockedAmount > 0:
			self.transaction.tx_out.append(bitcointransaction.TxOut(
				lockedAmount,
				bitcointransaction.Script.multiSigPubKey(
					[ownPubKey, peerPubKey, escrowPubKey]))
					)

