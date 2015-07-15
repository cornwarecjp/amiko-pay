#    nodestate.py
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

import randomsource

import time

import network
import settings
import link
import payeelink
import payerlink
import meetingpoint
import transaction

import serializable



class LinkNotFound(Exception):
	pass



class PaymentRequest(serializable.Serializable):
	serializableAttributes = {'amount':0, 'receipt':''}
serializable.registerClass(PaymentRequest)


class MakePayer(serializable.Serializable):
	serializableAttributes = {'payeeLinkID': ''}
serializable.registerClass(MakePayer)


class ReturnValue(serializable.Serializable):
	serializableAttributes = {'value':''}
serializable.registerClass(ReturnValue)


class MakeRoute(serializable.Serializable):
	serializableAttributes = \
	{
		'amount': 0,
		'transactionID': '',
		'startTime': None,
		'endTime': None,
		'meetingPointID': '',
		'payerID':None,
		'payeeID':None
	}
serializable.registerClass(MakeRoute)


class HavePayerRoute(serializable.Serializable):
	serializableAttributes = {'ID': '', 'transactionID': ''}
serializable.registerClass(HavePayerRoute)


class HavePayeeRoute(serializable.Serializable):
	serializableAttributes = {'ID': '', 'transactionID': ''}
serializable.registerClass(HavePayeeRoute)


class Lock(serializable.Serializable):
	serializableAttributes = {'transactionID': ''} #TODO: add payload
serializable.registerClass(Lock)


class Commit(serializable.Serializable):
	serializableAttributes = {'token': ''}
serializable.registerClass(Commit)


class SettleCommit(serializable.Serializable):
	serializableAttributes = {'transactionID': ''} #TODO: add payload
serializable.registerClass(SettleCommit)


class TimeoutMessage(serializable.Serializable):
	serializableAttributes = {'timestamp': 0.0, 'message': None}
serializable.registerClass(TimeoutMessage)



class NodeState(serializable.Serializable):
	serializableAttributes = \
	{
	'links':{},
	'payeeLinks':{},
	'payerLink': None,
	'meetingPoints':{},
	'transactions':{}
	}


	def handleMessage(self, msg):
		return \
		{
		PaymentRequest : self.msg_request,
		MakePayer      : self.msg_makePayer,
		MakeRoute      : self.msg_makeRoute,
		Lock           : self.msg_lock,
		Commit         : self.msg_commit,
		SettleCommit   : self.msg_settleCommit,

		HavePayerRoute : self.msg_passToAnyone,
		HavePayeeRoute : self.msg_passToAnyone,

		payeelink.Pay    : self.msg_passToPayee,
		payeelink.Confirm: self.msg_passToPayee,
		payeelink.Cancel : self.msg_passToPayee,

		payerlink.Timeout          : self.msg_passToPayer,
		payerlink.Receipt          : self.msg_passToPayer,
		payerlink.PayerLink_Confirm: self.msg_passToPayer

		}[msg.__class__](msg)


	def msg_request(self, msg):
		#ID can be nonsecure random:
		#It only needs to be semi-unique, not secret.
		requestID = randomsource.getNonSecureRandom(8).encode("hex")

		#Token must be secure random
		token = randomsource.getSecureRandom(32)

		newPayeeLink = payeelink.PayeeLink(
			amount=msg.amount, receipt=msg.receipt, token=token)

		self.payeeLinks[requestID] = newPayeeLink

		#Returned messages:
		return [ReturnValue(value=requestID)]


	def msg_makePayer(self, msg):
		if not (self.payerLink is None):
			raise Exception("There already is a payment in progress")
		self.payerLink = payerlink.PayerLink(payeeLinkID=msg.payeeLinkID)

		#Returned messages:
		return [
			TimeoutMessage(timestamp=time.time()+5.0, message=\
				self.payerLink.getTimeoutMessage()  #Add time-out for payer
			)
			]


	def msg_makeRoute(self, msg):
		transactionSide = \
		{
		(False, True): transaction.side_payer,
		(True, False): transaction.side_payee
		}[(msg.payerID is None, msg.payeeID is None)]

		if msg.transactionID in self.transactions.keys():
			#Match with existing transaction
			tx = self.transactions[msg.transactionID]

			#TODO: don't match if tx already has a finished route

			if transactionSide == -tx.side:
				#opposite direction -> short-cut

				#TODO: check that amount matches!!!

				tx.side = transaction.side_midpoint
				if transactionSide == transaction.side_payer:
					tx.payerID = msg.payerID
				else: #side_payee
					tx.payeeID = msg.payeeID

				#TODO: haveRoute messages, and possibly cancelRoute in case of shortcut
				return \
				[
				HavePayerRoute(ID=tx.payerID, transactionID=msg.transactionID),
				HavePayeeRoute(ID=tx.payeeID, transactionID=msg.transactionID)
				]

			#TODO: same direction -> haveNoRoute message
			return []

		#Create new transaction
		self.transactions[msg.transactionID] = transaction.Transaction(
			side=transactionSide,
			payeeID=msg.payeeID,
			payerID=msg.payerID,
			remainingLinkIDs=self.links.keys(),
			meetingPointID=msg.meetingPointID,
			amount=msg.amount,
			startTime=msg.startTime,
			endTime=msg.endTime
			)

		return []


	def msg_lock(self, msg):
		tx = self.transactions[msg.transactionID]
		payer = self.__getLinkObject(tx.payerID)
		payee = self.__getLinkObject(tx.payeeID)

		ret = payer.lockIncoming(msg)
		ret += payee.lockOutgoing(msg, tx.payeeID)

		return ret


	def msg_commit(self, msg):
		transactionID = settings.hashAlgorithm(msg.token)
		tx = self.transactions[transactionID]
		payer = self.__getLinkObject(tx.payerID)
		payee = self.__getLinkObject(tx.payeeID)

		ret = payee.commitIncoming(msg)
		ret += payer.commitOutgoing(msg)
		ret += payee.settleCommitOutgoing(SettleCommit(transactionID=transactionID))

		return ret


	def msg_settleCommit(self, msg):
		transactionID = msg.transactionID
		tx = self.transactions[transactionID]

		ret = []

		try:
			payer = self.__getLinkObject(tx.payerID)
			ret += payer.settleCommitIncoming(msg)
		except LinkNotFound:
			pass #Payment is committed, so payer object may already be deleted

		try:
			payee = self.__getLinkObject(tx.payeeID)
			ret += payee.settleCommitOutgoing(msg)
		except LinkNotFound:
			pass #Payment is committed, so payee object may already be deleted

		#Clean up no-longer-needed transaction:
		del self.transactions[transactionID]

		return ret


	def msg_passToAnyone(self, msg):
		return self.__getLinkObject(msg.ID).handleMessage(msg)


	def __getLinkObject(self, linkID):
		if linkID == network.payerLocalID and not (self.payerLink is None):
			return self.payerLink
		elif linkID in self.payeeLinks.keys():
			return self.payeeLinks[linkID]
		elif linkID in self.links.keys():
			return self.links[linkID]

		raise LinkNotFound("Link ID %s not found" % repr(linkID))


	def msg_passToPayee(self, msg):
		payee = self.payeeLinks[msg.ID]
		return payee.handleMessage(msg)


	def msg_passToPayer(self, msg):
		if self.payerLink is None:
			raise Exception("Received message for payer, but there is no payer")
		return self.payerLink.handleMessage(msg)


serializable.registerClass(NodeState)
