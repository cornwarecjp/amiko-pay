#    link.py
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

import copy

import messages

import serializable



class Link(serializable.Serializable):
	serializableAttributes = {'remoteID': '', 'channels':[], 'transactions':{}}


	def handleMessage(self, msg):
		return \
		{
		messages.Link_Deposit  : self.msg_ownDeposit,
		messages.Deposit       : self.msg_peerDeposit,
		messages.HavePayerRoute: self.msg_havePayerRoute,
		messages.ChannelMessage: self.continueChannelConversation
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
			messages.OutboundMessage(localID=msg.ID,
				message=messages.Deposit(
					ID=self.remoteID,
					channelIndex=channelIndex,
					channelClass=str(msg.channel.__class__.__name__)
				))
			] + \
			self.startChannelConversation(msg.ID, channelIndex)


	def msg_peerDeposit(self, msg):
		if msg.channelIndex != len(self.channels):
			raise Exception('Received Deposit message with incorrect channel index.')

		#TODO: prevent spamming DOS attack?

		#TODO: maybe we accept some channel classes for some links, but not for others
		channel = serializable.state2Object({'_class': msg.channelClass})

		self.channels.append(channel)

		return []


	def makeRouteOutgoing(self, localID, msg):
		#Try the channels one by one:
		for c in self.channels:

			#TODO: reserve funds in channel.
			#TODO: attach channel index to message
			#For now, assume that the channel is OK.

			self.transactions[msg.transactionID] = \
			{
			'outgoing': True
			}

			msgOutbound = copy.deepcopy(msg)
			msgOutbound.ID = self.remoteID

			return \
			[
			messages.OutboundMessage(localID=localID, message=msgOutbound)
			]

		#None of the channels worked (or there are no channels):
		#TODO: haveNoRoute
		return []


	def makeRouteIncoming(self, msg):
		#TODO: reserve funds in channel

		self.transactions[msg.transactionID] = \
			{
			'outgoing': False
			}

		return []


	def lockOutgoing(self, msg, localID):
		#TODO: lock in channel and add payload
		#TODO: add time-out for committing?
		msg = copy.deepcopy(msg)
		msg.ID = self.remoteID
		return [messages.OutboundMessage(localID=localID, message=msg)]


	def lockIncoming(self, msg):
		#TODO: check, lock in channel and process payload
		return []


	def commitOutgoing(self, msg, localID):
		#TODO: commit in channel and add payload
		msg = copy.deepcopy(msg)
		msg.ID = self.remoteID
		return [messages.OutboundMessage(localID=localID, message=msg)]


	def commitIncoming(self, msg):
		#TODO: check, commit in channel and process payload
		return []


	def msg_havePayerRoute(self, msg):
		txInfo = self.transactions[msg.transactionID]
		if txInfo['outgoing']:
			#came from peer -> pass to internal processing
			msg = copy.deepcopy(msg)
			msg.ID = msg.transactionID
		else:
			#came from internal processing -> pass to peer
			localID = msg.ID
			msg = copy.deepcopy(msg)
			msg.ID = self.remoteID
			msg = messages.OutboundMessage(localID=localID, message=msg)

		return [msg]


	def startChannelConversation(self, localID, channelIndex):
		inputMessage = messages.ChannelMessage(
			ID=localID,
			channelIndex=channelIndex,
			message=None #None = start of conversation
			)

		return self.continueChannelConversation(inputMessage)


	def continueChannelConversation(self, msg):
		outputMessage = self.channels[msg.channelIndex].handleMessage(msg.message)

		if outputMessage is None: #None = end of conversation
			return []

		return \
			[
			messages.OutboundMessage(localID=msg.ID, message=messages.ChannelMessage(
				ID=self.remoteID,
				channelIndex=msg.channelIndex,
				message=outputMessage
				))
			]


	def cancelOutgoing(self, msg):
		print "Link.cancelOutgoing: NYI"
		return []


serializable.registerClass(Link)

