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

import settings
import link
import payeelink
import payerlink
import meetingpoint
import transaction
import persistentconnection

import messages
import serializable



class LinkNotFound(Exception):
	pass



class NodeState(serializable.Serializable):
	serializableAttributes = \
	{
	'links':{},
	'payeeLinks':{},
	'payerLink': None,
	'meetingPoints':{},
	'transactions':{},
	'connections':{},
	'timeoutMessages': []
	}


	def handleMessage(self, msg):
		return \
		{
		messages.PaymentRequest : self.msg_request,
		messages.MakePayer      : self.msg_makePayer,
		messages.MakeLink       : self.msg_makeLink,
		messages.MakeRoute      : self.msg_makeRoute,
		messages.CancelRoute    : self.msg_cancelRoute,
		messages.Lock           : self.msg_lock,
		messages.Commit         : self.msg_commit,
		messages.SettleCommit   : self.msg_settleCommit,

		messages.HavePayerRoute : self.msg_passToAnyone,
		messages.HavePayeeRoute : self.msg_passToAnyone,

		messages.Pay    : self.msg_passToPayee,
		messages.Confirm: self.msg_passToPayee,
		messages.Cancel : self.msg_passToPayee,

		messages.Timeout          : self.msg_passToPayer,
		messages.Receipt          : self.msg_passToPayer,
		messages.PayerLink_Confirm: self.msg_passToPayer,

		messages.ConnectLink: self.msg_connectLink,

		messages.OutboundMessage: self.msg_passToConnection,
		messages.Confirmation   : self.msg_passToConnection,

		messages.Link_Deposit  : self.msg_passToLink,
		messages.ChannelMessage: self.msg_passToLink,
		messages.Deposit       : self.msg_passToLink
		}[msg.__class__](msg)


	def msg_request(self, msg):
		#ID can be nonsecure random:
		#It only needs to be semi-unique, not secret.
		payeeLinkID = randomsource.getNonSecureRandom(8).encode("hex")

		#Token must be secure random
		token = randomsource.getSecureRandom(32)

		newPayeeLink = payeelink.PayeeLink(
			amount=msg.amount, receipt=msg.receipt, token=token)

		self.payeeLinks[payeeLinkID] = newPayeeLink

		self.connections[payeeLinkID] = \
			persistentconnection.PersistentConnection(host=None, port=None)

		#Returned messages:
		return [messages.ReturnValue(value=payeeLinkID)]


	def msg_makePayer(self, msg):
		if not (self.payerLink is None):
			raise Exception("There already is a payment in progress")
		self.payerLink = payerlink.PayerLink(payeeLinkID=msg.payeeLinkID)

		self.connections[messages.payerLocalID] = \
			persistentconnection.PersistentConnection(
				host=msg.host,
				port=msg.port,
				connectMessage=messages.Pay(ID=msg.payeeLinkID)
				)

		#Returned messages:
		return [
			messages.TimeoutMessage(timestamp=time.time()+5.0, message=\
				self.payerLink.getTimeoutMessage()  #Add time-out for payer
			)
			]


	def msg_makeLink(self, msg):
		if msg.localID in self.links.keys():
			raise Exception('A link with ID %s already exists' % msg.localID)

		if msg.localID in self.payeeLinks.keys():
			raise Exception('A payee link with ID %s already exists' % msg.localID)

		if msg.localID[0] == '_':
			raise Exception('Names starting with an underscore are reserved, and can not be used')

		self.links[msg.localID] = link.Link(remoteID=msg.remoteID)

		self.connections[msg.localID] = \
			persistentconnection.PersistentConnection(
				host=msg.remoteHost,
				port=msg.remotePort,
				connectMessage=messages.ConnectLink(
					ID=msg.remoteID,

					#TODO: find a way to update this whenever it changes:
					callbackHost=msg.localHost,
					callbackPort=msg.localPort,
					callbackID=msg.localID
					)
				)

		return []


	def msg_makeRoute(self, msg):
		ret = []
		#TODO: call makeIncoming on incoming link

		transactionSide, payerID, payeeID = \
		{
		True: (transaction.side_payer, msg.ID, None),
		False: (transaction.side_payee, None, msg.ID)
		}[msg.isPayerSide]

		if msg.transactionID in self.transactions.keys():
			#Match with existing transaction
			tx = self.transactions[msg.transactionID]

			#TODO: don't match if tx already has a finished route

			if transactionSide == -tx.side:
				#opposite direction -> short-cut

				#TODO: check that amount matches!!!

				tx.side = transaction.side_midpoint
				if transactionSide == transaction.side_payer:
					tx.payerID = payerID
				else: #side_payee
					tx.payeeID = payeeID

				#TODO: possibly cancelRoute message in case of shortcut
				return ret + \
				[
				messages.HavePayerRoute(ID=tx.payerID, transactionID=msg.transactionID),
				messages.HavePayeeRoute(ID=tx.payeeID, transactionID=msg.transactionID)
				]

			#TODO: same direction -> haveNoRoute message
			return ret

		#Create new transaction
		self.transactions[msg.transactionID] = transaction.Transaction(
			side=transactionSide,
			payeeID=payeeID,
			payerID=payerID,
			remainingLinkIDs=self.links.keys(), #TODO: skip source link
			meetingPointID=msg.meetingPointID,
			amount=msg.amount,
			startTime=msg.startTime,
			endTime=msg.endTime
			)

		#TODO: match with our meeting points

		nextRoute = self.transactions[msg.transactionID].tryNextRoute(msg.transactionID)
		if nextRoute is None:
			#TODO: add haveNoRoute
			return ret

		ret += self.__getLinkObject(nextRoute).makeRouteOutgoing(nextRoute, msg)

		#TODO: route time-out
		return ret


	def msg_cancelRoute(self, msg):
		try:
			tx = self.transactions[msg.transactionID]
		except KeyError:
			log.log('cancelRoute failed: transaction %s does not (or no longer) exist (ignored)' % \
				msg.transactionID.encode('hex'))
			return []

		#TODO: simplify in the future, if these always evaluate to True
		hasPayer = not (tx.payerID is None)
		hasPayee = not (tx.payeeID is None)

		if hasPayer:
			payer = self.__getLinkObject(tx.payerID)
		if hasPayee:
			payee = self.__getLinkObject(tx.payeeID)

		if msg.payerSide:
			if hasPayer:
				ret = payer.cancelIncoming(msg)
			if hasPayee:
				ret += payee.cancelOutgoing(msg)
		else:
			if hasPayee:
				ret = payee.cancelIncoming(msg)
			if hasPayer:
				ret += payer.cancelOutgoing(msg)

		#Clean up cancelled transaction:
		del self.transactions[msg.transactionID]

		return ret


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
		ret += payee.settleCommitOutgoing(messages.SettleCommit(token=msg.token))

		return ret


	def msg_settleCommit(self, msg):
		transactionID = settings.hashAlgorithm(msg.token)
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


	def msg_connectLink(self, msg):
		#Update call-back information:
		if None not in (msg.callbackHost, msg.callbackPort, msg.callbackID):
			self.connections[msg.ID].host = msg.callbackHost
			self.connections[msg.ID].port = msg.callbackPort
			self.connections[msg.ID].connectMessage.ID = msg.callbackID
			self.links[msg.ID].remoteID = msg.callbackID

		#TODO: maybe inform link about creation of the connection?
		return []


	def msg_passToAnyone(self, msg):
		return self.__getLinkObject(msg.ID).handleMessage(msg)


	def __getLinkObject(self, linkID):
		if linkID == messages.payerLocalID and not (self.payerLink is None):
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


	def msg_passToConnection(self, msg):
		return self.connections[msg.localID].handleMessage(msg)


	def msg_passToLink(self, msg):
		return self.links[msg.ID].handleMessage(msg)


serializable.registerClass(NodeState)

