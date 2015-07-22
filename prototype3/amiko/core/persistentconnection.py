#    persistentconnection.py
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

import serializable



class PersistentConnectionMessage(serializable.Serializable):
	serializableAttributes = {'message': None, 'index': 0}
serializable.registerClass(PersistentConnectionMessage)



class PersistentConnection(serializable.Serializable):
	serializableAttributes = \
	{
		'host'             : None,
		'port'             : None,
		'connectMessage'   : None,
		'messages'         : [],
		'lastIndex'        : -1,
		'notYetTransmitted': 0,
		'closing'          : False
	}


	def addMessage(self, msg):
		if len(self.messages) >= 32768:
			raise Exception("Outbox is full; message %s lost for interface %s" % \
				(str(msg.message.__class__), msg.localID))

		#The value wrap-around is artificially shortened to 16 bits.
		#The reason is to make wrap-around more common, so we're more likely
		#to find related bugs in an early stage of development.
		self.lastIndex = (self.lastIndex + 1) & 0xffff

		self.messages.append(PersistentConnectionMessage(
			message=msg, index=self.lastIndex))
		self.notYetTransmitted += 1


	def transmit(self, networkDispatcher):
		if len(self.messages) == 0:
			return

		if not networkDispatcher.interfaceExists(self.messages[0].message.localID):
			#We are connected.

			#If we are closing, just forget about sending the remaining messages:
			if self.closing:
				self.messages = []

			#We are not connected (anymore):
			#Assume all not-yet-confirmed messages were lost
			self.notYetTransmitted = len(self.messages)

			return

		#Prevents a problem in the following lines:
		#self.messages[-0:] would incorrectly select all messages for retransmission
		if self.notYetTransmitted == 0:
			return

		#We are connected -> send all not-yet-transmitted messages
		for msg in self.messages[-self.notYetTransmitted:]:
			networkDispatcher.sendOutboundMessage(msg.index, msg.message)
		self.notYetTransmitted = 0


	def processConfirmation(self, confirmation):
		#A confirmation confirms all earlier messages as well.
		confirmationIndex = confirmation.index
		for i in range(len(self.messages)):
			if self.messages[i].index == confirmationIndex:
				self.messages = self.messages[i+1:]
				return


serializable.registerClass(PersistentConnection)

