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

import messages

import serializable



class Link(serializable.Serializable):
	serializableAttributes = {'remoteID': '', 'channels':[]}


	def handleMessage(self, msg):
		return \
		{
		messages.Link_Deposit  : self.msg_ownDeposit,
		messages.Deposit       : self.msg_peerDeposit,
		messages.ChannelMessage: self.continueChannelConversation,
		messages.Link_MakeRoute: self.msg_ownMakeRoute
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


	def msg_ownMakeRoute(self, msg):
		print "msg_ownMakeRoute: NYI"
		return []


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

