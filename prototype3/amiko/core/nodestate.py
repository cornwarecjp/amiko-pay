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
import log

import serializable



class ObjectNotFound(Exception):
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
		messages.HaveNoRoute    : self.msg_haveNoRoute,
		messages.CancelRoute    : self.msg_cancelRoute,
		messages.HavePayerRoute : self.msg_havePayerRoute,
		messages.HavePayeeRoute : self.msg_havePayeeRoute,
		messages.Lock           : self.msg_lock,
		messages.Commit         : self.msg_commit,
		messages.SettleCommit   : self.msg_settleCommit,

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
			amount=msg.amount, receipt=msg.receipt, token=token,
			meetingPoints=msg.meetingPoints)

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
		log.log('Processing MakeRoute message')

		sourceLink = self.__getObject(msg.ID)
		ret = sourceLink.makeRouteIncoming(msg)

		transactionSide, payerID, payeeID = \
		{
		True: (transaction.side_payer, msg.ID, None),
		False: (transaction.side_payee, None, msg.ID)
		}[msg.isPayerSide]

		if msg.transactionID in self.transactions.keys():
			#Match with existing transaction
			log.log('  Found an existing open transaction with the same transactionID')
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

				log.log('  Transactions match -> sending HaveRoute messages back')

				#TODO: possibly cancelRoute message in case of shortcut
				return ret + \
				[
				messages.HavePayerRoute(ID=tx.payerID, transactionID=msg.transactionID),
				messages.HavePayeeRoute(ID=tx.payeeID, transactionID=msg.transactionID)
				]

			log.log('  Transactions don\'t match (same direction: probably a route loop)')

			#TODO: same direction -> haveNoRoute message
			return ret

		#Create new transaction
		remainingLinks = self.links.keys()
		try:
			remainingLinks.remove(msg.ID) #Skip source link
		except ValueError:
			pass #it's OK if the source link wasn't present already
		self.transactions[msg.transactionID] = transaction.Transaction(
			side=transactionSide,
			payeeID=payeeID,
			payerID=payerID,
			remainingLinkIDs=remainingLinks, 
			meetingPointID=msg.meetingPointID,
			amount=msg.amount,
			startTime=msg.startTime,
			endTime=msg.endTime
			)

		#Match with our meeting points
		if msg.meetingPointID in self.meetingPoints.keys():
			log.log('  Matched with local meeting point')
			#Do nothing, just wait for the other side to arrive.
			#TODO: route time-out
			return ret

		nextRoute = self.transactions[msg.transactionID].tryNextRoute(msg.transactionID)
		if nextRoute is None:
			log.log('  No route found')
			#Delete the tx we just created:
			del self.transactions[msg.transactionID]
			#Send back haveNoRoute:
			ret += sourceLink.haveNoRouteOutgoing(
				msg.transactionID, msg.ID, msg.isPayerSide)
			return ret

		log.log('  Forwarding MakeRoute to the first route')

		ret += self.__getObject(nextRoute).makeRouteOutgoing(nextRoute, msg)

		#TODO: route time-out
		return ret


	def msg_haveNoRoute(self, msg):
		log.log('Processing HaveNoRoute message')
		try:
			tx = self.transactions[msg.transactionID]
		except KeyError:
			log.log('  HaveNoRoute failed: transaction %s does not (or no longer) exist (ignored)' % \
				msg.transactionID.encode('hex'))
			return []

		payer = self.__getObject(tx.payerID)
		payee = self.__getObject(tx.payeeID)

		ret = []

		if tx.side == transaction.side_payer:
			ret += payee.haveNoRouteIncoming(msg, isPayerSide=True)
		elif tx.side == transaction.side_payee:
			ret += payer.haveNoRouteIncoming(msg, isPayerSide=False)
		else:
			raise Exception('  HaveNoRoute should only be received on payer or payee route')

		#Try to find another route
		nextRoute = tx.tryNextRoute(msg.transactionID)
		if nextRoute is None:
			log.log('  No remaining route found')

			if tx.side == transaction.side_payer:
				ret += payer.haveNoRouteOutgoing(msg.transactionID, tx.payerID, isPayerSide=True)
			elif tx.side == transaction.side_payee:
				ret += payee.haveNoRouteOutgoing(msg.transactionID, tx.payeeID, isPayerSide=False)
			else:
				raise Exception('  HaveNoRoute should only be received on payer or payee route')

			#Clean up cancelled transaction:
			del self.transactions[msg.transactionID]

			return ret

		log.log('  Forwarding MakeRoute to the next route')

		ret += self.__getObject(nextRoute).makeRouteOutgoing(nextRoute,
			messages.MakeRoute(
				amount         = tx.amount,
				transactionID  = msg.transactionID,
				startTime      = tx.startTime,
				endTime        = tx.endTime,
				meetingPointID = tx.meetingPointID,
				ID             = nextRoute,
				isPayerSide    = tx.side == transaction.side_payer
				))

		return ret


	def msg_cancelRoute(self, msg):
		try:
			tx = self.transactions[msg.transactionID]
		except KeyError:
			log.log('cancelRoute failed: transaction %s does not (or no longer) exist (ignored)' % \
				msg.transactionID.encode('hex'))
			return []

		payer = self.__getObject(tx.payerID)
		payee = self.__getObject(tx.payeeID)

		if msg.payerSide:
			ret = payer.cancelIncoming(msg)
			ret += payee.cancelOutgoing(msg, tx.payeeID)
		else:
			ret = payee.cancelIncoming(msg)
			ret += payer.cancelOutgoing(msg, tx.payerID)

		#Clean up cancelled transaction:
		del self.transactions[msg.transactionID]

		return ret


	def msg_havePayerRoute(self, msg):
		tx = self.transactions[msg.transactionID]
		payer = self.__getObject(tx.payerID)
		#payee = self.__getObject(tx.payeeID) #TODO: check whether this matches msg.ID

		msg.ID = tx.payerID
		return payer.handleMessage(msg)


	def msg_havePayeeRoute(self, msg):
		#Special case for payee->payer transmission of this message type:
		if msg.ID == messages.payerLocalID:
			return self.payerLink.handleMessage(msg)

		tx = self.transactions[msg.transactionID]
		#payer = self.__getObject(tx.payerID) #TODO: check whether this matches msg.ID
		payee = self.__getObject(tx.payeeID)

		msg.ID = tx.payeeID
		return payee.handleMessage(msg)


	def msg_lock(self, msg):
		tx = self.transactions[msg.transactionID]
		payer = self.__getObject(tx.payerID)
		payee = self.__getObject(tx.payeeID)

		ret = payer.lockIncoming(msg)
		ret += payee.lockOutgoing(msg, tx.payeeID)

		return ret


	def msg_commit(self, msg):
		transactionID = settings.hashAlgorithm(msg.token)
		try:
			tx = self.transactions[transactionID]
		except KeyError:
			log.log('Received a commit message for an unknown transaction. Probably we\'ve already settled, so we ignore this.')
			return []

		payer = self.__getObject(tx.payerID)
		payee = self.__getObject(tx.payeeID)

		ret = payee.commitIncoming(msg)
		ret += payer.commitOutgoing(msg, tx.payerID)
		ret += payee.settleCommitOutgoing(messages.SettleCommit(token=msg.token), tx.payeeID)

		return ret


	def msg_settleCommit(self, msg):
		transactionID = settings.hashAlgorithm(msg.token)
		tx = self.transactions[transactionID]

		ret = []

		try:
			payer = self.__getObject(tx.payerID)
			ret += payer.settleCommitIncoming(msg)
		except ObjectNotFound:
			pass #Payment is committed, so payer object may already be deleted

		try:
			payee = self.__getObject(tx.payeeID)
			ret += payee.settleCommitOutgoing(msg, tx.payeeID)
		except ObjectNotFound:
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


	def __getObject(self, objID):
		if objID == messages.payerLocalID and not (self.payerLink is None):
			return self.payerLink
		elif objID in self.payeeLinks.keys():
			return self.payeeLinks[objID]
		elif objID in self.links.keys():
			return self.links[objID]
		elif objID in self.transactions.keys():
			return self.transactions[objID]

		raise ObjectNotFound("Object ID %s not found" % repr(objID))


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

