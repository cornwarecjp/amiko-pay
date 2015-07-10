#    outbox.py
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

import time

import serializable


class OutBoxMessage(serializable.Serializable):
	serializableAttributes = {'message': None, 'index': 0, 'lastAttemptTimestamp': 0.0}
serializable.registerClass(OutBoxMessage)



class OutBox(serializable.Serializable):
	serializableAttributes = {'messages':[], 'lastIndex':{}}


	def addMessage(self, msg):
		try:
			#The value wrap-around is artificially shortened to 16 bits.
			#The reason is to make wrap-around more common, so we're more likely
			#to find related bugs in an early stage of development.
			index = (self.lastIndex[msg.localID] + 1) & 0xffff
		except KeyError:
			index = 0
		#TODO: protect against overflow (more than 64k messages in the queue for a single interface)
		self.lastIndex[msg.localID] = index
		self.messages.append(OutBoxMessage(message=msg, index=index, lastAttemptTimestamp=0.0))


	def transmit(self, networkDispatcher):
		t = time.time()
		for msg in self.messages:
			if t - msg.lastAttemptTimestamp > 10.0: #Re-send every 10 seconds
				transmitted = networkDispatcher.sendOutboundMessage(msg.index, msg.message)
				if transmitted:
					msg.lastAttemptTimestamp = t


	def processConfirmation(self, confirmation):
		for i in range(len(self.messages)):
			msg = self.messages[i]
			if msg.index == confirmation.index and msg.message.localID == confirmation.localID:
				del self.messages[i]
				return


serializable.registerClass(OutBox)

