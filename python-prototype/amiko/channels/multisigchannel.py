#    multisigchannel.py
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

import binascii
import copy

from ..core import channel, messages

from ..utils import bitcointransaction, crypto, base58
from ..utils.bitcoinutils import sendToMultiSigPubKey
from ..utils.bitcoinutils import makeSpendMultiSigTransaction, signMultiSigTransaction
from ..utils.bitcoinutils import verifyMultiSigSignature, applyMultiSigSignatures

from multisigtransaction import MultiSigTransaction
from tcd import TCD


"""
We use a variation of the following. The variation basically consists of having
outputs that depend on having the transaction token, of which the hash is in a
scriptPubKey.

https://en.bitcoin.it/wiki/Contracts#Example_7:_Rapidly-adjusted_.28micro.29payments_to_a_pre-determined_party

This protocol relies upon a different behavior of nLockTime to the original
design. Starting around 2013 time-locked transactions were made non standard
and no longer enter the memory pool, thus cannot be broadcast before the
timelock expires. When the behaviour of nLockTime is restored to the original
design from Satoshi, a variant of this protocol is required which is discussed
below.

We define the client to be the party sending value, and the server to be the
party receiving it. This is written from the clients perspective.

1	Create a public key (K1). Request a public key from the server (K2).
2	Create and sign but do not broadcast a transaction (T1) that sets up a
	payment of (for example) 10 BTC to an output requiring both the server's
	private key and one of your own to be used. A good way to do this is use
	OP_CHECKMULTISIG. The value to be used is chosen as an efficiency tradeoff.
3	Create a refund transaction (T2) that is connected to the output of T1 which
	sends all the money back to yourself. It has a time lock set for some time
	in the future, for instance a few hours. Don't sign it, and provide the
	unsigned transaction to the server. By convention, the output script is
	"2 K1 K2 2 CHECKMULTISIG"
4	The server signs T2 using its private key associated with K2 and returns the
	signature to the client. Note that it has not seen T1 at this point, just
	the hash (which is in the unsigned T2).
5	The client verifies the servers signature is correct and aborts if not.
6	The client signs T1 and passes the signature to the server, which now
	broadcasts the transaction (either party can do this if they both have
	connectivity). This locks in the money.
7	The client then creates a new transaction, T3, which connects to T1 like the
	refund transaction does and has two outputs. One goes to K1 and the other
	goes to K2. It starts out with all value allocated to the first output (K1),
	ie, it does the same thing as the refund transaction but is not time locked.
	The client signs T3 and provides the transaction and signature to the
	server.
8	The server verifies the output to itself is of the expected size and
	verifies the client's provided signature is correct.
9	When the client wishes to pay the server, it adjusts its copy of T3 to
	allocate more value to the server's output and less to its own. It then
	re-signs the new T3 and sends the signature to the server. It does not have
	to send the whole transaction, just the signature and the amount to
	increment by is sufficient. The server adjusts its copy of T3 to match the
	new amounts, verifies the signature and continues.

This continues until the session ends, or the 1-day period is getting close to
expiry. The AP then signs and broadcasts the last transaction it saw, allocating
the final amount to itself. The refund transaction is needed to handle the case
where the server disappears or halts at any point, leaving the allocated value
in limbo. If this happens then once the time lock has expired the client can
broadcast the refund transaction and get back all the money.

[..]

When nLockTime'd transactions are able to enter the memory pool (once more) and
transaction replacement has been re-enabled, a variant on the protocol must be
used. In this case, no refund transaction is used. Instead each T3 has a
sequence number one higher than the previous and all T3's have a time lock set
to the same period as above. Each time a payment is made the sequence number is
incremented, ensuring that the last version will take precedence. If the channel
protocol is not closed cleanly, this means the value transfer won't commit until
the time lock expires. To avoid this both parties can cooperate by signing a T3
that has a sequence number of 0xFFFFFFFF resulting in immediate confirmation
regardless of the value of nLockTime.

The lock time and sequence numbers avoid an attack in which the AP provides
connectivity, and then the user double-spends the output back to themselves
using the first version of TX2, thus preventing the cafe from claiming the bill.
If the user does try this, the TX won't be included right away, giving the
access point a window of time in which it can observe the TX broadcast, and then
broadcast the last version it saw, overriding the user's attempted double-spend.

The latter protocol that relies on transaction replacement is more flexible
because it allows the value allocated to go down as well as up during the
lifetime of the channel as long as the client receives signatures from the
server, but for many use cases this functionality is not required. Replacement
also allows for more complex configurations of channels that involve more than
two parties. Elaboration on such use cases is a left as an exercise for the
reader. 
"""

"""
Named stages of a multi-signature channel.
The channel forms a state machine that transitions between those states.
Possible state transitions:
(construction)                -> OwnDeposit_Initial
OwnDeposit_Initial            -> OwnDeposit_SendingPublicKey
OwnDeposit_SendingPublicKey   -> OwnDeposit_SendingT2
OwnDeposit_SendingT2          -> WaitingForT1

(construction)                -> PeerDeposit_Initial
PeerDeposit_Initial           -> PeerDeposit_SendingPublicKey
PeerDeposit_SendingPublicKey  -> PeerDeposit_SendingSignature
PeerDeposit_SendingSignature  -> WaitingForT1

WaitingForT1                  -> Ready

Ready                         -> Stopping
Stopping                      -> Stopped
Stopped                       -> OwnWithdraw_SendingT2
OwnWithdraw_SendingT2         -> Closed

Stopped                       -> PeerWithdraw_SendingSignature
PeerWithdraw_SendingSignature -> Closed



Purposes of T1, T2_peerSigned, T2_latest during different stages:

OwnDeposit_Initial:
OwnDeposit_SendingPublicKey:
PeerDeposit_Initial:
PeerDeposit_SendingPublicKey:
T1 = None
T2_latest = None
T2_peerSigned = None

OwnDeposit_SendingT2:
T1 = deposit transaction
T2_latest = initial withdraw transaction
T2_peerSigned = None

PeerDeposit_SendingSignature:
T1 = None
T2_latest = initial withdraw transaction
T2_peerSigned = T2_latest

WaitingForT1:
Ready:
Stopping:
Stopped:
T1 = deposit transaction
T2_latest = last withdraw transaction (may be equal to T2_peerSig)
T2_peerSigned = last withdraw transaction which has peer signature (peerSignature applies), or None if not needed

OwnWithdraw_SendingT2:
PeerWithdraw_SendingSignature:
T1 = deposit transaction
T2_latest = final withdraw transaction
T2_peerSigned = last withdraw transaction which has peer signature (peerSignature applies)

Closed:
T1 = deposit transaction
T2_latest = final withdraw transaction
T2_peerSigned = T2_latest
"""
stages = \
[
	"OwnDeposit_Initial",
	"OwnDeposit_SendingPublicKey",
	"OwnDeposit_SendingT2",
	"PeerDeposit_Initial",
	"PeerDeposit_SendingPublicKey",
	"PeerDeposit_SendingSignature",
	"WaitingForT1",
	"Ready",
	"Stopping",
	"Stopped",
	"OwnWithdraw_SendingT2",
	"PeerWithdraw_SendingSignature",
	"Closed"
]
stages = {x: i for i, x in enumerate(stages)} #name   -> integer
stageNames = {v:k for k,v in stages.items()}  #iteger -> name

class MultiSigChannel(channel.Channel):
	"""
	Payment channel with Bitcoin multi-signature transaction protection.
	"""

	def __init__(self, bitcoind, state):
		channel.Channel.__init__(self, state)
		self.bitcoind = bitcoind

		self.stage = stages[state["stage"]] #name -> integer

		self.ownAddress = str(state["ownAddress"])
		ownPrivateKey = base58.decodeBase58Check(
			self.bitcoind.getPrivateKey(self.ownAddress), 128
			)
		self.ownKey = crypto.Key()
		self.ownKey.setPrivateKey(ownPrivateKey)

		self.peerKey = None
		if "peerPublicKey" in state:
			self.peerKey = crypto.Key()
			self.peerKey.setPublicKey(
				binascii.unhexlify(state["peerPublicKey"])
				)

		self.escrowKey = None
		if "escrowPublicKey" in state:
			self.escrowKey = crypto.Key()
			self.escrowKey.setPublicKey(
				binascii.unhexlify(state["escrowPublicKey"])
				)

		self.hasFirstPublicKey = bool(state["hasFirstPublicKey"])

		self.T1 = None
		self.T2_peerSigned = None
		self.T2_latest = None
		self.peerSignature = None
		if "T1" in state:
			self.T1 = bitcointransaction.Transaction.deserialize(
				binascii.unhexlify(state["T1"])
				)
		if "T2_peerSigned" in state:
			self.T2_peerSigned = MultiSigTransaction.makeFromState(
				state["T2_peerSigned"])
		if "T2_latest" in state:
			self.T2_latest = MultiSigTransaction.makeFromState(
				state["T2_latest"])
		if "peerSignature" in state:
			self.peerSignature = binascii.unhexlify(state["peerSignature"])


	def getType(self):
		return "multisig"


	def getState(self, forDisplay=False):
		ret = channel.Channel.getState(self, forDisplay)
		ret["stage"] = stageNames[self.stage]
		ret["ownAddress"] = self.ownAddress
		if forDisplay:
			pubKey = self.ownKey.getPublicKey()
			ret["ownPublicKey"] = pubKey.encode("hex")
		if self.peerKey != None:
			pubKey = self.peerKey.getPublicKey()
			ret["peerPublicKey"] = pubKey.encode("hex")
			if forDisplay:
				ret["peerAddress"] = base58.encodeBase58Check(
					crypto.RIPEMD160(crypto.SHA256(pubKey)),
					0)
		if self.escrowKey != None:
			pubKey = self.escrowKey.getPublicKey()
			ret["escrowPublicKey"] = pubKey.encode("hex")

		ret["hasFirstPublicKey"] = int(self.hasFirstPublicKey)

		if self.T1 != None:
			if forDisplay:
				ret["T1"] = self.T1.getTransactionID()[::-1].encode("hex")
			else:
				ret["T1"] = self.T1.serialize().encode("hex")
		if self.T2_peerSigned != None:
			ret["T2_peerSigned"] = self.T2_peerSigned.getState(forDisplay)
		if self.T2_latest != None:
			ret["T2_latest"] = self.T2_latest.getState(forDisplay)
		if self.peerSignature != None:
			ret["peerSignature"] = self.peerSignature.encode("hex")
		return ret


	def makeT1AndT2(self):
		fee = 10000 #0.1 mBTC (TODO: make configurable)

		if self.amountLocal <= 2*fee: #both deposit and withdraw fees
			raise Exception("The deposited amount needs to be more than the transaction fees")

		ownPubKey = self.ownKey.getPublicKey()
		peerPubKey = self.peerKey.getPublicKey()
		returnKeyHash = crypto.RIPEMD160(crypto.SHA256(ownPubKey))

		#We send an extra fee here, so that T2's initial return becomes
		# exactly self.amountLocal
		assert self.hasFirstPublicKey
		self.T1 = sendToMultiSigPubKey(self.bitcoind, self.amountLocal + fee,
			ownPubKey,
			peerPubKey,
			returnKeyHash,
			fee)

		T1_ID = self.T1.getTransactionID() #opposite endianness as in Bitcoind

		#TODO: set lock time!!!
		lockTime = 0
		#The amount argument is the amount in the INPUT of T2, so it's again
		#with an added fee, to make the OUTPUT equal to self.amountLocal.
		self.T2_latest = MultiSigTransaction.makeNew(
			self.ownKey, T1_ID, self.amountLocal + fee, fee, lockTime)


	def checkT1(self):
		if self.stage != stages["WaitingForT1"]:
			return

		#TODO: check whether T1 has some confirmations
		#TODO: add a watchdog entry for spending of T1
		self.stage = stages["Ready"]


	def checkStopped(self):
		if self.stage == stages["Stopping"] and \
			len(self.transactionsIncomingReserved) == 0 and \
			len(self.transactionsOutgoingReserved) == 0 and \
			len(self.transactionsIncomingLocked) == 0 and \
			len(self.transactionsOutgoingLocked) == 0:
				self.stage = stages["Stopped"]


	def makeWithdrawT2(self):
		self.T2_latest.transaction.lockTime = 0


	def getPublicKeyPair(self):
		if self.hasFirstPublicKey:
			return self.ownKey.getPublicKey(), self.peerKey.getPublicKey()
		return self.peerKey.getPublicKey(), self.ownKey.getPublicKey()


	def makeDepositMessage(self, message):
		if self.stage == stages["OwnDeposit_Initial"] and \
			message == None:

			#Initial message:
			self.stage = stages["OwnDeposit_SendingPublicKey"]
			return messages.Deposit(
				self.ID, self.getType(), isInitial=True, stage=self.stage,
				payload=[self.ownKey.getPublicKey()])

		elif self.stage == stages["PeerDeposit_Initial"] and \
			message.stage == stages["OwnDeposit_SendingPublicKey"]:

			#Received deposit message with public key from peer
			self.peerKey = crypto.Key()
			self.peerKey.setPublicKey(message.payload[0])
			self.stage = stages["PeerDeposit_SendingPublicKey"]
			return messages.Deposit(
				self.ID, self.getType(), stage=self.stage,
				payload=[self.ownKey.getPublicKey()])

		elif self.stage == stages["OwnDeposit_SendingPublicKey"] and \
			message.stage == stages["PeerDeposit_SendingPublicKey"]:

			#Received reply on own deposit message
			self.peerKey = crypto.Key()
			self.peerKey.setPublicKey(message.payload[0])
			self.makeT1AndT2()
			self.stage = stages["OwnDeposit_SendingT2"]
			return messages.Deposit(
				self.ID, self.getType(), stage=self.stage,
				payload=[self.T2_latest.serialize()])

		elif self.stage == stages["PeerDeposit_SendingPublicKey"] and \
			message.stage == stages["OwnDeposit_SendingT2"]:

			#Received T2
			self.T2_latest = MultiSigTransaction.deserialize(message.payload[0])
			#TODO: maybe re-serialize to check consistency
			self.amountRemote = sum(tx.amount for tx in self.T2_latest.transaction.tx_out)
			assert not self.hasFirstPublicKey
			signature = signMultiSigTransaction(
				self.T2_latest.transaction, 0,
				[self.peerKey.getPublicKey(), self.ownKey.getPublicKey()],
				self.ownKey)
			self.stage = stages["PeerDeposit_SendingSignature"]
			return messages.Deposit(
				self.ID, self.getType(), stage=self.stage, payload=[signature])

		elif self.stage == stages["OwnDeposit_SendingT2"] and \
			message.stage == stages["PeerDeposit_SendingSignature"]:

			signature = message.payload[0]
			assert self.hasFirstPublicKey
			if not verifyMultiSigSignature(
				self.T2_latest.transaction, 0,
				[self.ownKey.getPublicKey(), self.peerKey.getPublicKey()],
				self.peerKey, signature):
					raise Exception("Signature failure!") #TODO: what to do now?
			self.peerSignature = signature
			self.T2_peerSigned = copy.deepcopy(self.T2_latest)
			T1_serialized = self.T1.serialize()
			self.stage = stages["WaitingForT1"]

			#Publish T1 in Bitcoind
			self.bitcoind.sendRawTransaction(T1_serialized)

			return messages.Deposit(
				self.ID, self.getType(), stage=self.stage, payload=[T1_serialized])

		elif self.stage == stages["PeerDeposit_SendingSignature"] and \
			message.stage == stages["WaitingForT1"]:

			T1_serialized = message.payload[0]
			self.T1 = bitcointransaction.Transaction.deserialize(T1_serialized)
			#TODO: maybe re-serialize to check consistency
			#TODO: check T1 (and that it matches T2)

			self.stage = stages["WaitingForT1"]

			#Publish T1 in Bitcoind
			self.bitcoind.sendRawTransaction(T1_serialized)

			print "DONE"

		else:
			raise Exception("Received illegal deposit message")

		return None


	def makeWithdrawMessage(self, message):
		self.checkT1()

		#TODO: make some code to enter the "stopping" state prior to withdrawing,
		#and then wait until there are no more ongoing transactions.
		#This is not necessary for low-volume tests in controlled environments,
		#but as soon as people start transferring other peoples' transactions,
		#you want to be able to stop other peoples' transactions from
		#interfering with your withdrawal.
		if self.stage == stages["Ready"]:
			self.stage = stages["Stopping"]

		self.checkStopped()

		if message == None:
			if self.stage != stages["Stopped"]:
				raise Exception("Can not withdraw: channel must be Stopped, but is " + \
					stageNames[self.stage])

			self.makeWithdrawT2()
			self.stage = stages["OwnWithdraw_SendingT2"]
			return messages.Withdraw(
				self.ID, stage=self.stage, payload=[self.T2_latest.serialize()])

		elif self.stage == stages["Stopped"] and \
			message.stage == stages["OwnWithdraw_SendingT2"]:

			#Received T2
			self.T2_latest = MultiSigTransaction.deserialize(message.payload[0])
			#TODO: maybe re-serialize to check consistency
			#TODO: lots of checks on T2 (IMPORTANT!)
			pubKey1, pubKey2 = self.getPublicKeyPair()
			signature = signMultiSigTransaction(
				self.T2_latest.transaction, 0, [pubKey1, pubKey2], self.ownKey)
			self.stage = stages["PeerWithdraw_SendingSignature"]
			return messages.Withdraw(
				self.ID, stage=self.stage, payload=[signature])

		elif self.stage == stages["OwnWithdraw_SendingT2"] and \
			message.stage == stages["PeerWithdraw_SendingSignature"]:

			peerSignature = message.payload[0]
			pubKey1, pubKey2 = self.getPublicKeyPair()
			if not verifyMultiSigSignature(
				self.T2_latest.transaction, 0,
				[pubKey1, pubKey2], self.peerKey, peerSignature):
					raise Exception("Signature failure!") #TODO: what to do now?

			ownSignature = signMultiSigTransaction(
				self.T2_latest.transaction, 0, [pubKey1, pubKey2], self.ownKey)

			if self.hasFirstPublicKey:
				applyMultiSigSignatures(self.T2_latest.transaction, ownSignature, peerSignature)
			else:
				applyMultiSigSignatures(self.T2_latest.transaction, peerSignature, ownSignature)

			self.peerSignature = peerSignature
			self.T2_peerSigned = copy.deepcopy(self.T2_latest)
			self.stage = stages["Closed"]

			#Publish T2 in Bitcoind
			T2_serialized = self.T2_latest.transaction.serialize()
			self.bitcoind.sendRawTransaction(T2_serialized)

			return messages.Withdraw(
				self.ID, stage=self.stage, payload=[T2_serialized])

		elif self.stage == stages["PeerWithdraw_SendingSignature"] and \
			message.stage == stages["Closed"]:

			T2 = bitcointransaction.Transaction.deserialize(message.payload[0])
			#TODO: maybe re-serialize to check consistency
			#TODO: lots of checks on T2 (IMPORTANT!)

			#TODO:
			#self.T2_latest = T2
			#self.peerSignature = TODO
			#self.T2_peerSigned = copy.deepcopy(T2)
			self.stage = stages["Closed"]

			#Publish T2 in Bitcoind
			T2_serialized = message.payload[0]
			self.bitcoind.sendRawTransaction(T2_serialized)

			print "DONE"

		else:
			raise Exception("Received illegal withdraw message")

		return None


	def reserve(self, isPayerSide, hash, amount):
		self.checkT1()

		if self.stage != stages["Ready"]:
			raise channel.CheckFail(
				"Can not reserve: channel must be Ready, but is " + \
				stageNames[self.stage])

		channel.Channel.reserve(self, isPayerSide, hash, amount)


	def makeTransactionT2(self):
		amountLocal = \
			self.amountLocal + \
			sum(self.transactionsOutgoingReserved.values())
		amountRemote = \
			self.amountRemote + \
			sum(self.transactionsIncomingReserved.values())

		ownPubKey = self.ownKey.getPublicKey()
		peerPubKey = self.peerKey.getPublicKey()
		escrowPubKey = ownPubKey #TODO!!!

		self.T2_latest.setOutputs(ownPubKey, peerPubKey, escrowPubKey,
			amountLocal, amountRemote)

		#TODO: check that the sum of T2's outputs equals T1's output minus fee


	def makeTransactionPayload(self):
		pubKey1, pubKey2 = self.getPublicKeyPair()
		#TODO: add escrow key
		ownSignature = signMultiSigTransaction(
			self.T2_latest.transaction, 0, [pubKey1, pubKey2], self.ownKey)

		return [ownSignature, self.T2_latest.serialize()]


	def processTransactionPayload(self, payload):
		peerSignature = payload[0]
		T2 = MultiSigTransaction.deserialize(payload[1])

		#TODO: add escrow key
		pubKey1, pubKey2 = self.getPublicKeyPair()
		if not verifyMultiSigSignature(
			T2.transaction, 0, [pubKey1, pubKey2], self.peerKey, peerSignature):
				raise Exception("Signature failure!") #TODO: what to do now?

		#TODO: lots of checks on T2 (IMPORTANT!)

		self.peerSignature = peerSignature
		self.T2_latest = T2
		self.T2_peerSigned = copy.deepcopy(T2)


	def lockOutgoing(self, hash):
		message = channel.Channel.lockOutgoing(self, hash)

		ownKeyHash = crypto.RIPEMD160(crypto.SHA256(self.ownKey.getPublicKey()))
		peerKeyHash = crypto.RIPEMD160(crypto.SHA256(self.peerKey.getPublicKey()))
		self.T2_latest.addTCD(TCD(
			startTime=0, endTime=0, #TODO!!!
			amount=self.transactionsOutgoingLocked[hash], tokenHash=hash,
			commitAddress=peerKeyHash, rollbackAddress=ownKeyHash
			))
		self.makeTransactionT2()

		message.payload = self.makeTransactionPayload()
		return message


	def lockIncoming(self, message):
		self.processTransactionPayload(message.payload)
		channel.Channel.lockIncoming(self, message)


	def commitOutgoing(self, hash, token):
		message = channel.Channel.commitOutgoing(self, hash, token)

		self.T2_latest.removeTCD(hash)
		self.makeTransactionT2()

		message.payload = self.makeTransactionPayload()
		return message


	def commitIncoming(self, hash, message):
		self.processTransactionPayload(message.payload)
		channel.Channel.commitIncoming(self, hash, message)



def constructFromDeposit(bitcoind, channelID, amount, escrowKey):
	ownAddress = bitcoind.getNewAddress()
	state = \
	{
		"ID": channelID,
		"stage": "OwnDeposit_Initial",
		"amountLocal" : amount,
		"amountRemote": 0,
		"transactionsIncomingLocked"  : {},
		"transactionsIncomingReserved": {},
		"transactionsOutgoingLocked"  : {},
		"transactionsOutgoingReserved": {},

		"ownAddress": ownAddress,
		"escrowPublicKey": escrowKey.encode("hex"),
		"hasFirstPublicKey": 1
	}
	return MultiSigChannel(bitcoind, state)



def constructFromDepositMessage(bitcoind, message):

	#TODO: check for available funds, so we don't end up with a mess
	#if halfway the process it turns out we can not do the deposit because of
	#insufficient funds.

	ownAddress = bitcoind.getNewAddress()
	state = \
	{
		"ID": message.channelID,
		"stage": "PeerDeposit_Initial",
		"amountLocal" : 0,
		"amountRemote": 0, #To be increased later
		"transactionsIncomingLocked"  : {},
		"transactionsIncomingReserved": {},
		"transactionsOutgoingLocked"  : {},
		"transactionsOutgoingReserved": {},

		"ownAddress": ownAddress,
		"hasFirstPublicKey": 0
	}
	return MultiSigChannel(bitcoind, state)

