#    nodestate.py
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

from ..utils import serializable



class LinkNotFound(Exception):
	pass



class TransactionNotFound(Exception):
	pass



class NodeState(serializable.Serializable):
	'''
	Serializable class containing all state data of a single node.
	Also implements top-level message handling of the node.

	Note that, between constructing this object and using it, an attribute
	with the name 'settings' must be set to an object of type settings.Settings:
	this attribute is used in the methods of this class, but it is not
	initialized in the constructor, since it is not part of the serializable
	data.
	'''

	serializableAttributes = \
	{
	'links':{},
	'payeeLinks':{},
	'payerLink': None,
	'meetingPoints':{},
	'transactions':[],
	'connections':{},
	'timeoutMessages': []
	}


	def handleMessage(self, msg):
		return \
		{
		messages.PaymentRequest        : self.msg_request,
		messages.MakePayer             : self.msg_makePayer,
		messages.MakeLink              : self.msg_makeLink,
		messages.MakeMeetingPoint      : self.msg_makeMeetingPoint,

		messages.TimeoutMessage        : self.msg_timeoutMessage,
		messages.FilterTimeouts        : self.msg_filterTimeouts,

		messages.MakeRoute             : self.msg_makeRoute,
		messages.HaveNoRoute           : self.msg_haveNoRoute,
		messages.CancelRoute           : self.msg_cancelRoute,
		messages.NodeStateTimeout_Route: self.msg_timeout_route,
		messages.HaveRoute             : self.msg_haveRoute,
		messages.NodeStateTimeout_Lock : self.msg_timeout_lock,
		messages.Lock                  : self.msg_lock,
		messages.RequestCommit         : self.msg_requestCommit,
		messages.SettleCommit          : self.msg_settleCommit,
		messages.SettleRollback        : self.msg_settleRollback,

		messages.Pay    : self.msg_passToPayee,
		messages.Confirm: self.msg_passToPayee,
		messages.Cancel : self.msg_passToPayerPayee,

		messages.PayerTimeout     : self.msg_passToPayer,
		messages.Receipt          : self.msg_passToPayer,
		messages.PayerLink_Confirm: self.msg_passToPayer,

		messages.ConnectLink: self.msg_connectLink,

		messages.OutboundMessage: self.msg_passToConnection,
		messages.Confirmation   : self.msg_passToConnection,

		messages.Link_Deposit      : self.msg_passToLink,
		messages.Link_Withdraw     : self.msg_passToLink,
		messages.LinkTimeout_Commit: self.msg_passToLink,
		messages.ChannelMessage    : self.msg_passToLink,
		messages.Deposit           : self.msg_passToLink,
		messages.BitcoinReturnValue: self.msg_passToLink
		}[msg.__class__](msg)


	def msg_request(self, msg):
		#ID can be nonsecure random:
		#It only needs to be semi-unique, not secret.
		payeeLinkID = randomsource.getNonSecureRandom(8).encode("hex")

		#Token must be secure random
		token = randomsource.getSecureRandom(32)

		newPayeeLink = payeelink.PayeeLink(
			ID=payeeLinkID,
			amount=msg.amount, receipt=msg.receipt, token=token,
			meetingPoints=msg.meetingPoints, routingContext=msg.routingContext)

		self.payeeLinks[payeeLinkID] = newPayeeLink

		self.connections[payeeLinkID] = \
			persistentconnection.PersistentConnection(host=None, port=None)

		#Returned messages:
		return [messages.ReturnValue(value=payeeLinkID)]


	def msg_makePayer(self, msg):
		if not (self.payerLink is None):
			raise Exception("There already is a payment in progress")
		self.payerLink = payerlink.PayerLink(
			payeeLinkID=msg.payeeLinkID,
			routingContext=msg.routingContext)

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

		self.links[msg.localID] = link.Link(remoteID=msg.remoteID, localID=msg.localID)

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


	def msg_makeMeetingPoint(self, msg):
		self.meetingPoints[msg.name] = meetingpoint.MeetingPoint(ID=msg.name)

		return []


	def msg_timeoutMessage(self, msg):
		self.timeoutMessages.append(msg)
		self.timeoutMessages.sort(
			cmp = lambda a, b: int(a.timestamp - b.timestamp)
			)
		return []


	def msg_filterTimeouts(self, msg):
		self.timeoutMessages = filter(
			lambda message: msg.function(message.message),
			self.timeoutMessages
			)

		return []


	def msg_makeRoute(self, msg):
		log.log('Processing MakeRoute message')

		sourceLink = self.__getLinkObject(msg.ID)
		ret = sourceLink.makeRouteIncoming(msg)

		payerID, payeeID = \
		{
		True: (msg.ID, None),
		False: (None, msg.ID)
		}[msg.isPayerSide]

		#Possible routes we can take
		if msg.routingContext is None:
			#Order is important: try meeting points first
			possibleLinks = self.meetingPoints.keys() + self.links.keys()
		else:
			possibleLinks = [msg.routingContext]

		def tryRemove(ID):
			try:
				possibleLinks.remove(ID)
			except ValueError:
				pass #it's OK if the source link wasn't present already
			
		#Remove the source link:
		tryRemove(msg.ID)

		#Remove source link and possible routes of earlier instances of
		#this route:
		#for these, the route should be made by the earlier instance.
		#Allowing them to be selected by later instances would allow
		#infinite routing loops.
		#Note: generally, this will remove ALL routes, if earlier instances of
		#the same route exist. The only situation where this is not the case
		#is when an earlier instance was restricted in its routing choices,
		#and, theoretically, when a new route was created in-between.
		earlierTransactions = self.findMultipleTransactions(
			transactionID=msg.transactionID, isPayerSide=msg.isPayerSide)
		for earlierTx in earlierTransactions:
			earlierSourceLinkID = earlierTx.payerID if msg.isPayerSide else earlierTx.payeeID
			tryRemove(earlierSourceLinkID)

			for ID in earlierTx.initialLinkIDs:
				tryRemove(ID)

		#Increment end time on the payee side:
		#On the payer side, this will be done in haveRoute.
		if not msg.isPayerSide:
			#TODO: check sanity (and data type) of startTime, endTime
			msg.endTime += self.settings.timeoutIncrement

		#Create new transaction
		newTx = transaction.Transaction(
			state=transaction.Transaction.states.makingRoute,
			isPayerSide=msg.isPayerSide,
			payeeID=payeeID,
			payerID=payerID,

			initialLinkIDs=possibleLinks[:],
			remainingLinkIDs=possibleLinks[:],

			meetingPointID=msg.meetingPointID,
			amount=msg.amount,

			transactionID=msg.transactionID,
			startTime=msg.startTime,
			endTime=msg.endTime
			)
		self.transactions.append(newTx)

		nextRoute = newTx.tryNextRoute()
		if nextRoute is None:
			log.log('  No route found')
			#Delete the tx we just created:
			self.transactions.remove(newTx)
			#Send back haveNoRoute:
			ret += sourceLink.haveNoRouteOutgoing(
				msg.transactionID, msg.isPayerSide)
			return ret

		log.log('  Forwarding MakeRoute to the first route')

		ret += self.__getLinkObject(nextRoute).makeRouteOutgoing(msg)

		#route time-out:
		#TODO: configurable time-out value?
		ret.append(messages.TimeoutMessage(timestamp=time.time()+5.0, message=\
			messages.NodeStateTimeout_Route(
				transactionID=msg.transactionID, isPayerSide=msg.isPayerSide,
				payerID=newTx.payerID
				)))

		return ret


	def msg_haveNoRoute(self, msg):
		log.log('Processing HaveNoRoute message')
		try:
			if msg.isPayerSide:
				tx = self.findTransaction(
					transactionID=msg.transactionID, payeeID=msg.ID, isPayerSide=True)
			else:
				tx = self.findTransaction(
					transactionID=msg.transactionID, payerID=msg.ID, isPayerSide=False)
		except TransactionNotFound:
			log.log('  HaveNoRoute failed: transaction %s does not (or no longer) exist (ignored)' % \
				msg.transactionID.encode('hex'))
			return []

		payer = self.__getLinkObject(tx.payerID)
		payee = self.__getLinkObject(tx.payeeID)

		ret = []

		if tx.isPayerSide:
			ret += payee.haveNoRouteIncoming(msg)
		else:
			ret += payer.haveNoRouteIncoming(msg)

		#Clean up old route time-out:
		oldPayerID = tx.payerID #keep reference to innermost object
		ret.append(messages.FilterTimeouts(function = lambda message: not (
			isinstance(message, messages.NodeStateTimeout_Route)
			and
			message.transactionID == msg.transactionID
			and
			message.isPayerSide == msg.isPayerSide
			and
			message.payerID == oldPayerID
			)))

		#Try to find another route
		nextRoute = tx.tryNextRoute()
		if nextRoute is None:
			log.log('  No remaining route found')

			if tx.isPayerSide:
				ret += payer.haveNoRouteOutgoing(msg.transactionID, isPayerSide=True)
			else:
				ret += payee.haveNoRouteOutgoing(msg.transactionID, isPayerSide=False)

			#Clean up cancelled transaction:
			self.transactions.remove(tx)

			return ret

		log.log('  Forwarding MakeRoute to the next route')

		ret += self.__getLinkObject(nextRoute).makeRouteOutgoing(
			messages.MakeRoute(
				amount         = tx.amount,
				transactionID  = msg.transactionID,
				startTime      = tx.startTime,
				endTime        = tx.endTime,
				meetingPointID = tx.meetingPointID,
				ID             = nextRoute,
				isPayerSide    = tx.isPayerSide
				))

		#route time-out:
		#TODO: configurable time-out value?
		ret.append(messages.TimeoutMessage(timestamp=time.time()+5.0, message=\
			messages.NodeStateTimeout_Route(
				transactionID=msg.transactionID, isPayerSide=msg.isPayerSide,
				payerID=tx.payerID
				)))

		return ret


	def msg_cancelRoute(self, msg):
		try:
			if msg.isPayerSide:
				tx = self.findTransaction(
					transactionID=msg.transactionID, payerID=msg.ID, isPayerSide=True)
			else:
				tx = self.findTransaction(
					transactionID=msg.transactionID, payeeID=msg.ID, isPayerSide=False)
		except TransactionNotFound:
			log.log('cancelRoute failed: transaction %s does not (or no longer) exist (ignored)' % \
				msg.transactionID.encode('hex'))
			return []

		payer = self.__getLinkObject(tx.payerID)
		payee = self.__getLinkObject(tx.payeeID)

		if msg.isPayerSide:
			ret = payer.cancelIncoming(msg)
			ret += payee.cancelOutgoing(msg)
		else:
			ret = payee.cancelIncoming(msg)
			ret += payer.cancelOutgoing(msg)

		#Clean up cancelled transaction:
		self.transactions.remove(tx)

		#Clean up route time-out:
		ret.append(messages.FilterTimeouts(function = lambda message: not (
			isinstance(message, messages.NodeStateTimeout_Route)
			and
			message.transactionID == msg.transactionID
			and
			message.isPayerSide == msg.isPayerSide
			and
			message.payerID == tx.payerID
			)))

		return ret


	def msg_timeout_route(self, msg):
		try:
			tx = self.findTransaction(
				transactionID=msg.transactionID, payerID=msg.payerID, isPayerSide=msg.isPayerSide)
		except TransactionNotFound:
			log.log('  Route timeout: transaction %s no longer exists (ignored)' % \
				msg.transactionID.encode('hex'))
			return []

		if tx.state != transaction.Transaction.states.makingRoute:
			log.log('  Ignoring route timeout: we already have a route')
			return []

		payer = self.__getLinkObject(tx.payerID)
		payee = self.__getLinkObject(tx.payeeID)

		if msg.isPayerSide:
			ret = payer.haveNoRouteOutgoing(msg.transactionID, isPayerSide=True)
			ret += payee.cancelOutgoing(messages.CancelRoute(
				transactionID=msg.transactionID, isPayerSide=True
				))
		else:
			ret = payee.haveNoRouteOutgoing(msg.transactionID, isPayerSide=False)
			ret += payer.cancelOutgoing(messages.CancelRoute(
				transactionID=msg.transactionID, isPayerSide=False
				))

		#Clean up cancelled transaction:
		self.transactions.remove(tx)

		return ret


	def msg_haveRoute(self, msg):
		#Special case for payee->payer transmission of this message type:
		if msg.ID == messages.payerLocalID:
			return self.payerLink.haveRouteIncoming(msg)

		#TODO: check sanity (and data type) of startTime, endTime

		ret = []

		if msg.isPayerSide:
			tx = self.findTransaction(
				transactionID=msg.transactionID, payeeID=msg.ID, isPayerSide=True)
			payer = self.__getLinkObject(tx.payerID)
			payee = self.__getLinkObject(tx.payeeID)
			ret += payee.haveRouteIncoming(msg)
			msg.ID = tx.payerID
			msg.endTime += self.settings.timeoutIncrement
			ret += payer.haveRouteOutgoing(msg)
		else:
			tx = self.findTransaction(
				transactionID=msg.transactionID, payerID=msg.ID, isPayerSide=False)
			payer = self.__getLinkObject(tx.payerID)
			payee = self.__getLinkObject(tx.payeeID)
			ret += payer.haveRouteIncoming(msg)
			msg.ID = tx.payeeID
			msg.endTime -= self.settings.timeoutIncrement
			ret += payee.haveRouteOutgoing(msg)
			#TODO: compare startTime, endTime with MakeRoute values

		tx.state = transaction.Transaction.states.haveRoute

		#Lock time-out:
		#TODO: configurable time-out value?
		ret.append(messages.TimeoutMessage(timestamp=time.time()+5.0, message=\
			messages.NodeStateTimeout_Lock(
				transactionID=msg.transactionID, isPayerSide=msg.isPayerSide,
				payerID=tx.payerID
				)))

		#Clean up route time-out:
		ret.append(messages.FilterTimeouts(function = lambda message: not (
			isinstance(message, messages.NodeStateTimeout_Route)
			and
			message.transactionID == msg.transactionID
			and
			message.isPayerSide == msg.isPayerSide
			and
			message.payerID == tx.payerID
			)))

		return ret


	def msg_timeout_lock(self, msg):
		try:
			tx = self.findTransaction(
				transactionID=msg.transactionID, payerID=msg.payerID, isPayerSide=msg.isPayerSide)
		except TransactionNotFound:
			#This can happen when another node has timed out before us,
			#and sent us a HaveNoRoute / CancelRoute.
			log.log('  Lock timeout: transaction %s no longer exists (ignored)' % \
				msg.transactionID.encode('hex'))
			return []

		if tx.state != transaction.Transaction.states.haveRoute:
			log.log('  Ignoring lock timeout: transaction is already locked')
			return []

		payer = self.__getLinkObject(tx.payerID)
		payee = self.__getLinkObject(tx.payeeID)

		if msg.isPayerSide:
			ret = payer.haveNoRouteOutgoing(msg.transactionID, isPayerSide=True)
			ret += payee.cancelOutgoing(messages.CancelRoute(
				transactionID=msg.transactionID, isPayerSide=True
				))
		else:
			ret = payee.haveNoRouteOutgoing(msg.transactionID, isPayerSide=False)
			ret += payer.cancelOutgoing(messages.CancelRoute(
				transactionID=msg.transactionID, isPayerSide=False
				))

		#Clean up cancelled transaction:
		self.transactions.remove(tx)

		return ret


	def msg_lock(self, msg):
		try:
			tx = self.findTransaction(
				transactionID=msg.transactionID, payerID=msg.ID, isPayerSide=msg.isPayerSide)
		except TransactionNotFound:
			log.log('Received a lock for an unknown transaction.')
			log.log('Going to reserve and lock it, and then settle for rollback.')
			#This could be, for instance, a transaction which has already been
			#timed out on this node.
			#Let's be nice, and release the funds back to our peer.
			#(Note: releasing funds ASAP is also good for ourselves)

			payer = self.__getLinkObject(msg.ID)
			#First, reserve and lock the transaction (to get the link state right for the rollback)
			ret = payer.makeRouteIncoming(messages.MakeRoute(
				amount=msg.amount,
				transactionID=msg.transactionID,
				isPayerSide=msg.isPayerSide,
				startTime=msg.startTime,
				endTime=msg.endTime,
				channelIndex=msg.channelIndex
				))
			ret += payer.lockIncoming(msg)
			#Then, settle for rollback (this is the "being nice" part)
			ret += payer.settleRollbackOutgoing(messages.SettleRollback(
				transactionID=msg.transactionID, isPayerSide=msg.isPayerSide
				))
			return ret

		payer = self.__getLinkObject(tx.payerID)
		payee = self.__getLinkObject(tx.payeeID)

		tx.state = transaction.Transaction.states.locked

		ret = payer.lockIncoming(msg)
		ret += payee.lockOutgoing(msg)
		return ret


	def msg_requestCommit(self, msg):
		transactionID = settings.hashAlgorithm(msg.token)
		try:
			tx = self.findTransaction(
				transactionID=transactionID, payeeID=msg.ID, isPayerSide=msg.isPayerSide)
		except TransactionNotFound:
			log.log('Received a request commit message for an unknown transaction. Probably we\'ve already settled, so we ignore this.')
			return []

		payer = self.__getLinkObject(tx.payerID)
		payee = self.__getLinkObject(tx.payeeID)

		tx.state = transaction.Transaction.states.requestedCommit

		ret = payee.requestCommitIncoming(msg)
		ret += payer.requestCommitOutgoing(msg)
		ret += payee.settleCommitOutgoing(
			messages.SettleCommit(token=msg.token, isPayerSide=msg.isPayerSide))

		return ret


	def msg_settleCommit(self, msg):
		#Special case for payee->payer transmission of this message type:
		if msg.ID == messages.payerLocalID:
			#Start settling on the payer side route,
			#no matter what the payee says.
			msg.isPayerSide = True

		transactionID = settings.hashAlgorithm(msg.token)

		ret = []

		try:
			payer = self.__getLinkObject(msg.ID)
			ret += payer.settleCommitIncoming(msg)
		except LinkNotFound:
			log.log('Payer link not found (ignored)')
			#Payment is committed, so payer object may already be deleted
			#Pass: continue with payee side handling and tx removing
			pass

		try:
			tx = self.findTransaction(
				transactionID=transactionID, payerID=msg.ID, isPayerSide=msg.isPayerSide)
		except TransactionNotFound:
			log.log('Transaction not found (ignored)')
			#Payment is committed, so transaction object may already be deleted
			#Return here: don't remove non-existing tx
			return ret

		try:
			payee = self.__getLinkObject(tx.payeeID)
			ret += payee.settleCommitOutgoing(msg)
		except LinkNotFound:
			log.log('Payee link not found (ignored)')
			#Payment is committed, so payee object may already be deleted
			#Pass: continue with removing tx
			pass

		#Clean up no-longer-needed transaction:
		self.transactions.remove(tx)

		return ret


	def msg_settleRollback(self, msg):
		ret = []

		try:
			payee = self.__getLinkObject(msg.ID)
			ret += payee.settleRollbackIncoming(msg)
		except LinkNotFound:
			log.log('Payee link not found (ignored)')
			#Payment is cancelled, so payee object may already be deleted
			#Pass: continue with payer side handling and tx removing
			pass

		try:
			tx = self.findTransaction(
				transactionID=msg.transactionID, payeeID=msg.ID, isPayerSide=msg.isPayerSide)
		except TransactionNotFound:
			log.log('Transaction not found (ignored)')
			#Payment is cancelled, so transaction object may already be deleted
			#Return here: don't remove non-existing tx
			return ret

		try:
			payer = self.__getLinkObject(tx.payerID)
			ret += payer.settleRollbackOutgoing(msg)
		except LinkNotFound:
			log.log('Payer link not found (ignored)')
			#Payment is cancelled, so payer object may already be deleted
			#Pass: continue with removing tx
			pass

		#Clean up no-longer-needed transaction:
		self.transactions.remove(tx)

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


	def __getLinkObject(self, linkID):
		if linkID == messages.payerLocalID and not (self.payerLink is None):
			return self.payerLink
		elif linkID in self.payeeLinks.keys():
			return self.payeeLinks[linkID]
		elif linkID in self.links.keys():
			return self.links[linkID]
		elif linkID in self.meetingPoints.keys():
			return self.meetingPoints[linkID]

		raise LinkNotFound("Link ID %s not found" % repr(linkID))


	def msg_passToPayerPayee(self, msg):
		if msg.ID == messages.payerLocalID:
			return self.msg_passToPayer(msg)
		return self.msg_passToPayee(msg)


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


	def findMultipleTransactions(self, transactionID, isPayerSide, payerID=None, payeeID=None):
		ret = self.transactions[:]

		if transactionID is not None:
			ret = [x for x in ret if x.transactionID == transactionID]
		if isPayerSide is not None:
			ret = [x for x in ret if x.isPayerSide == isPayerSide]
		if payerID is not None:
			ret = [x for x in ret if x.payerID == payerID]
		if payeeID is not None:
			ret = [x for x in ret if x.payeeID == payeeID]

		return ret


	def findTransaction(self, transactionID, isPayerSide, payerID=None, payeeID=None):
		ret = self.findMultipleTransactions(transactionID, isPayerSide, payerID, payeeID)

		def queryText():
			ret = []
			if transactionID is not None:
				ret.append('transactionID=%s' % repr(transactionID))
			if isPayerSide is not None:
				ret.append('isPayerSide=%s' % str(isPayerSide))
			if payerID is not None:
				ret.append('payerID=%s' % payerID)
			if payeeID is not None:
				ret.append('payeeID=%s' % payeeID)
			return ', '.join(ret)

		if len(ret) == 0:
			raise TransactionNotFound(
				'No transaction found with ' + queryText())

		if len(ret) > 1:
			raise Exception(
				'Ambiguous query: multiple transactions found with ' + \
				queryText())

		return ret[0]


serializable.registerClass(NodeState)

