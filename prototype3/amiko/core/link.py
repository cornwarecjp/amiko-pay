#    link.py
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

import copy

import log
import settings
import messages

from ..utils import serializable


class RouteNotInChannelsException(Exception):
	pass


class Link(serializable.Serializable):
	serializableAttributes = {'remoteID': '', 'localID': '', 'channels':[]}


	def handleMessage(self, msg):
		return \
		{
		messages.Link_Deposit      : self.msg_ownDeposit,
		messages.Link_Withdraw     : self.msg_ownWithdraw,
		messages.Deposit           : self.msg_peerDeposit,
		messages.HaveRoute         : self.msg_haveRoute,
		messages.BitcoinReturnValue: self.msg_bitcoinReturnValue,
		messages.ChannelMessage    : self.continueChannelConversation
		}[msg.__class__](msg)


	def msg_ownDeposit(self, msg):
		if self.remoteID is None:
			raise Exception('Can not deposit into a link whose remote ID is unknown')

		self.channels.append(msg.channel)
		channelIndex = len(self.channels) - 1

		#Allow the channel to start a conversation with the peer,
		#related to the deposit.
		return \
			[
			messages.OutboundMessage(localID=self.localID,
				message=messages.Deposit(
					channelIndex=channelIndex,
					channelClass=str(msg.channel.__class__.__name__)
				))
			] + \
			self.startChannelConversation(channelIndex)


	def msg_peerDeposit(self, msg):
		if msg.channelIndex != len(self.channels):
			raise Exception('Received Deposit message with incorrect channel index.')

		#TODO: prevent spamming DOS attack?

		#TODO: maybe we accept some channel classes for some links, but not for others
		channel = serializable.state2Object({'_class': msg.channelClass})

		self.channels.append(channel)

		return []


	def msg_ownWithdraw(self, msg):
		if msg.channelIndex < 0:
			raise Exception('Withdraw error: negative channel index.')
		if msg.channelIndex >= len(self.channels):
			raise Exception('Withdraw error: too large channel index.')

		channelOutput = self.channels[msg.channelIndex].startWithdraw()
		return self.handleChannelOutput(msg.channelIndex, channelOutput)


	def msg_haveRoute(self, msg):
		#Forward to peer:
		msg = copy.deepcopy(msg)
		msg.ID = self.remoteID
		return [messages.OutboundMessage(localID=self.localID, message=msg)]


	def msg_bitcoinReturnValue(self, msg):
		return self.handleChannelOutput(msg.channelIndex, msg.value)


	def makeRouteOutgoing(self, msg):
		routeID = self.__makeRouteID(msg.transactionID, msg.isPayerSide)
		isOutgoing = msg.isPayerSide

		#Try the channels one by one:
		for i, c in enumerate(self.channels):

			#Reserve funds in channel.
			try:
				c.reserve(isOutgoing, routeID, msg.startTime, msg.endTime, msg.amount)
			except Exception as e:
				#TODO: make sure the state of the channel is restored?
				log.log("Reserving on channel %d failed: returned exception \"%s\"" % (i, str(e)))
				continue

			log.log("Reserving on channel %d succeeded" % i)

			msg = copy.deepcopy(msg)
			msg.ID = self.remoteID
			msg.channelIndex = i

			return \
			[
			messages.OutboundMessage(localID=self.localID, message=msg)
			]

		#None of the channels worked (or there are no channels):
		#TODO: haveNoRoute
		return []


	def makeRouteIncoming(self, msg):
		routeID = self.__makeRouteID(msg.transactionID, msg.isPayerSide)
		isOutgoing = not msg.isPayerSide

		#Reserve funds in channel
		c = self.channels[msg.channelIndex]
		c.reserve(isOutgoing, routeID, msg.startTime, msg.endTime, msg.amount)

		return []


	def haveNoRouteOutgoing(self, transactionID, isPayerSide):
		routeID = self.__makeRouteID(transactionID, isPayerSide)
		isOutgoing = not isPayerSide

		c, ci = self.__findChannelWithRoute(routeID)
		ret = self.handleChannelOutput(
			ci,
			c.unreserve(isOutgoing, routeID)
			)

		return ret + \
		[
		messages.OutboundMessage(localID=self.localID,
			message=messages.HaveNoRoute(
				transactionID=transactionID, isPayerSide=isPayerSide))
		]


	def haveNoRouteIncoming(self, msg):
		routeID = self.__makeRouteID(msg.transactionID, msg.isPayerSide)
		isOutgoing = msg.isPayerSide

		c, ci = self.__findChannelWithRoute(routeID)
		return self.handleChannelOutput(
			ci,
			c.unreserve(isOutgoing, routeID)
			)


	def cancelOutgoing(self, msg):
		routeID = self.__makeRouteID(msg.transactionID, msg.isPayerSide)
		isOutgoing = msg.isPayerSide

		c, ci = self.__findChannelWithRoute(routeID)
		ret = self.handleChannelOutput(
			ci,
			c.unreserve(isOutgoing, routeID)
			)

		msg = copy.deepcopy(msg)
		msg.ID = self.remoteID
		return ret + [messages.OutboundMessage(localID=self.localID, message=msg)]


	def cancelIncoming(self, msg):
		routeID = self.__makeRouteID(msg.transactionID, msg.isPayerSide)
		isOutgoing = not msg.isPayerSide

		c, ci = self.__findChannelWithRoute(routeID)
		return self.handleChannelOutput(
			ci,
			c.unreserve(isOutgoing, routeID)
			)


	def lockOutgoing(self, msg):
		routeID = self.__makeRouteID(msg.transactionID, msg.isPayerSide)
		c, ci = self.__findChannelWithRoute(routeID)
		c.lockOutgoing(routeID)

		#TODO: add payload
		msg = copy.deepcopy(msg)
		msg.ID = self.remoteID
		#TODO: add time-out for committing?
		return [messages.OutboundMessage(localID=self.localID, message=msg)]


	def lockIncoming(self, msg):
		#TODO: process payload
		routeID = self.__makeRouteID(msg.transactionID, msg.isPayerSide)
		c, ci = self.__findChannelWithRoute(routeID)
		c.lockIncoming(routeID)

		return []


	def requestCommitOutgoing(self, msg):
		msg = copy.deepcopy(msg)
		msg.ID = self.remoteID
		return [messages.OutboundMessage(localID=self.localID, message=msg)]


	def requestCommitIncoming(self, msg):
		#TODO: check commit hash
		return []


	def settleCommitOutgoing(self, msg):
		transactionID = settings.hashAlgorithm(msg.token)
		routeID = self.__makeRouteID(transactionID, msg.isPayerSide)
		try:
			c, ci = self.__findChannelWithRoute(routeID)
		except RouteNotInChannelsException:
			log.log('No channel found for route; assuming settleCommitOutgoing was already performed, so we skip it.')
			return []

		ret = self.handleChannelOutput(
			ci,
			c.settleCommitOutgoing(routeID, msg.token)
			)

		#TODO: add payload
		msg = copy.deepcopy(msg)
		msg.ID = self.remoteID
		return ret + [messages.OutboundMessage(localID=self.localID, message=msg)]


	def settleCommitIncoming(self, msg):
		#TODO: process payload
		transactionID = settings.hashAlgorithm(msg.token)
		routeID = self.__makeRouteID(transactionID, msg.isPayerSide)
		c, ci = self.__findChannelWithRoute(routeID)
		return self.handleChannelOutput(
			ci,
			c.settleCommitIncoming(routeID)
			)


	def startChannelConversation(self, channelIndex):
		inputMessage = messages.ChannelMessage(
			ID=self.localID,
			channelIndex=channelIndex,
			message=None #None = start of conversation
			)

		return self.continueChannelConversation(inputMessage)


	def continueChannelConversation(self, msg):
		return self.handleChannelOutput(
			msg.channelIndex,
			self.channels[msg.channelIndex].handleMessage(msg.message)
			)


	def handleChannelOutput(self, channelIndex, channelOutput):
		log.log("Channel output: " + str(channelOutput))

		channelMessages, function = channelOutput

		ret = \
		[
		messages.OutboundMessage(localID=self.localID,
			message=messages.ChannelMessage(
			channelIndex=channelIndex, message=m))
		for m in channelMessages
		]

		if not(function is None):
			ret.append(
				messages.BitcoinCommand(
					function=function,
					returnID=self.localID, returnChannelIndex=channelIndex)
				)

		return ret


	def __makeRouteID(self, transactionID, isPayerSide):
		return ('1' if isPayerSide else '0') + transactionID


	def __findChannelWithRoute(self, routeID):
		for ci, c in enumerate(self.channels):
			if c.hasRoute(routeID):
				return c, ci
		raise RouteNotInChannelsException(
			"None of the channels is processing the route")


serializable.registerClass(Link)

