#    iouchannel.py
#    Copyright (C) 2015-2016 by CJP
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

from ..utils import serializable
from ..utils import utils
from ..utils.crypto import Key, RIPEMD160, SHA256
from ..utils.base58 import decodeBase58Check, encodeBase58Check
from ..utils.bitcointransaction import Transaction
from ..utils.bitcoinutils import sendToStandardPubKey

from plainchannel import PlainChannel, PlainChannel_Deposit, PlainChannel_Withdraw



class IOUChannel_Address(serializable.Serializable):
	serializableAttributes = {'address': ''}
serializable.registerClass(IOUChannel_Address)



class IOUChannel_WithdrawTransaction(serializable.Serializable):
	serializableAttributes = {'transaction': ''}
serializable.registerClass(IOUChannel_WithdrawTransaction)



class IOUChannel(PlainChannel):
	"""
	Payment channel with only signed IOUs as protection.
	This implements a pure "trust-ful" Ripple-style system.
	Note that, per channel, debt (and hence trust) only goes in one direction,
	so this channel type can be used in asymmetric trust relationships
	(e.g. user trusts service provider, but not vice versa).
	"""

	serializableAttributes = utils.dictSum(PlainChannel.serializableAttributes,
		{'isIssuer': False, 'address': None, 'withdrawTxID': None})


	@staticmethod
	def makeForOwnDeposit(amount):
		return IOUChannel(
			state=PlainChannel.states.depositing,
			amountLocal=amount,
			amountRemote=0,
			isIssuer=True)


	def __init__(self, **kwargs):
		PlainChannel.__init__(self, **kwargs)


	def handleMessage(self, msg):
		"""
		Return value:
			message, function (either may be None)
		"""

		if (self.state, msg) == (self.states.depositing, None):
			return PlainChannel_Deposit(amount=self.amountLocal), None

		elif (self.state, msg.__class__) == (self.states.initial, PlainChannel_Deposit):
			self.state = self.states.ready
			self.amountRemote = msg.amount

			k = Key()
			k.makeNewKey(compressed=True)
			publicKeyHash = RIPEMD160(SHA256(k.getPublicKey()))
			self.address = encodeBase58Check(publicKeyHash, 0) #PUBKEY_ADDRESS = 0

			privateKey = encodeBase58Check(k.getPrivateKey(), 128) #PRIVKEY = 128

			def importPrivateKey(bitcoind):
				#We've just created the key and haven't shared it yet, so
				#it's impossible we've already received bitcoins on it.
				#Therefore, rescan=False is safe.
				bitcoind.importprivkey(privateKey, 'Amiko Pay IOUChannel', False)
				return None, None

			return IOUChannel_Address(address=self.address), importPrivateKey

		elif (self.state, msg.__class__) == (self.states.depositing, IOUChannel_Address):
			self.address = msg.address
			self.state = self.states.ready
			return None, None

		elif msg.__class__ == PlainChannel_Withdraw:
			if not self.isIssuer:
				raise Exception('Issuing peer should not send PlainChannel_Withdraw')

			if self.state in (self.states.withdrawing, self.states.closed):
				#Ignore if already in progress/done
				return None, None
			else:
				return self.startWithdraw()

		elif msg.__class__ == IOUChannel_WithdrawTransaction:
			if self.isIssuer:
				#TODO: store the transaction anyway? It might work to our advantage.
				raise Exception('Non-issuing peer should not send IOUChannel_WithdrawTransaction')

			#TODO: check/fix state (e.g. ongoing transactions)

			tx = Transaction.deserialize(msg.transaction)

			#TODO: check transaction contents!!!!
			#it should match with the state.

			self.state = self.states.closed
			self.withdrawTxID = tx.getTransactionID()[::-1].encode("hex")

			def sendTransaction(bitcoind):
				bitcoind.sendRawTransaction(msg.transaction)
				return None, None

			return None, sendTransaction

		raise Exception("Received unexpected channel message")


	def doClose(self):
		"""
		Return value:
			message, function (either may be None)
		"""

		if self.isIssuer:
			self.state = self.states.closed

			def makeCloseTransaction(bitcoind):
				mBTC = 100000 #Satoshi

				amount = self.amountRemote
				fee = mBTC / 100 #TODO: use configurable fee

				toHash = decodeBase58Check(self.address, 0) #PUBKEY_ADDRESS = 0

				#Make change address and store it:
				k = Key()
				k.makeNewKey(compressed=True)
				changeHash = RIPEMD160(SHA256(k.getPublicKey()))
				changePrivateKey = encodeBase58Check(k.getPrivateKey(), 128) #PRIVKEY = 128
				bitcoind.importprivkey(changePrivateKey, 'Amiko Pay IOUChannel change', False)

				tx = sendToStandardPubKey(bitcoind, amount, toHash, changeHash, fee)

				self.withdrawTxID = tx.getTransactionID()[::-1].encode("hex")

				tx = tx.serialize()

				#TODO: for security, delay sending the transaction until all
				#processing is finished. For that, create a new Bitcoin command type.
				bitcoind.sendRawTransaction(tx)

				#Tell peer about the transaction
				return IOUChannel_WithdrawTransaction(transaction=tx), None
				
			return None, makeCloseTransaction


		#else (not self.isIssuer)

		#Do NOT YET set the state to closed: we still need to get our funds
		#from the peer.

		#Ask peer to do withdrawal
 		return PlainChannel_Withdraw(), None


serializable.registerClass(IOUChannel)

