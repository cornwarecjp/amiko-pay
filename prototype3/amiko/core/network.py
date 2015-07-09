#    network.py
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

import asyncore
import socket

import serializable
import log


class Connect(serializable.Serializable):
	"""
	This is a base class for messages that indicate a connection ID
	(Link and Pay).
	"""
	serializableAttributes = {'ID':''}



class OutboundMessage(serializable.Serializable):
	serializableAttributes = {'localID':'', 'message': None}
serializable.registerClass(OutboundMessage)



class Connection(asyncore.dispatcher_with_send):
	def __init__(self, sock, callback):
		asyncore.dispatcher_with_send.__init__(self, sock)
		self.readBuffer = ''
		self.callback = callback
		self.localID = None


	def handle_read(self):
		data = self.recv(8192)
		if data:
			self.readBuffer += data

			#TODO restrict the size of the buffer, to prevent memory issues

			newlinePos = self.readBuffer.find('\n')
			if newlinePos >= 0:
				msgData = self.readBuffer[:newlinePos]
				self.readBuffer = self.readBuffer[newlinePos+1:]

				try:
					msg = serializable.deserialize(msgData)
					#print "Got message: ", str(msg.__class__)

					if isinstance(msg, Connect):
						if not (self.localID is None):
							raise Exception("Received connect message while already connected")
						self.localID = msg.ID

					self.callback.handleMessage(msg)
				except Exception as e:
					log.logException()
					#TODO: send error back to remote host?


	def sendMessage(self, msg):
		self.send(serializable.serialize(msg) + '\n')



class EventDispatcher(asyncore.dispatcher):
	def __init__(self, host, port, callback):
		asyncore.dispatcher.__init__(self)
		self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
		self.set_reuse_addr()
		self.bind((host, port))
		self.listen(5)

		self.callback = callback
		self.connections = []


	def handle_accept(self):
		pair = self.accept()
		if pair is not None:
			sock, addr = pair
			print 'Incoming connection from %s' % repr(addr)
			self.connections.append(Connection(sock, self.callback))


	def sendOutboundMessage(self, msg):
		localID = msg.localID
		interfaces = [c for c in self.connections if c.localID == localID]
		if len(interfaces) == 0:
			return False
		interfaces[0].sendMessage(msg.message)
		return True


	def makeConnection(self, address, callback):
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.connect(address)
		connection = Connection(sock, callback)
		self.connections.append(connection)
		return connection


