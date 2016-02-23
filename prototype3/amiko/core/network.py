#    network.py
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

import asyncore
import socket

from ..utils import serializable
import messages
import log
import randomsource



class ConnectFailed(Exception):
	pass


class Connection(asyncore.dispatcher_with_send):
	def __init__(self, sock, network):
		asyncore.dispatcher_with_send.__init__(self, sock, map=network.channelMap)
		self.readBuffer = ''
		self.network = network
		self.localID = None
		self.dice = None
		self.isClosed = False


	def handle_read(self):
		data = self.recv(8192)
		if data:
			self.readBuffer += data

			#TODO restrict the size of the buffer, to prevent memory issues

			while True:
				newlinePos = self.readBuffer.find('\n')
				if newlinePos < 0:
					break #no more messages in the buffer
				msgData = self.readBuffer[:newlinePos]
				self.readBuffer = self.readBuffer[newlinePos+1:]
				self.processReceivedMessageData(msgData)


	def processReceivedMessageData(self, msgData):
		log.log("Received data: %s\n" % msgData)

		try:
			container = serializable.deserialize(msgData)
			if 'received' in container.keys():
				#Process received confirmation:
				index = container['received']
				self.network.callback.handleMessage(
					messages.Confirmation(localID=self.localID, index=index)
					)
			elif 'message' in container.keys():
				index = container['index']
				msg = container['message']

				if msg.__class__ == messages.ConnectLink:
					if not (self.localID is None):
						raise Exception("Received ConnectLink message while already connected")
					self.localID = msg.ID
					self.dice = msg.dice
					self.network.checkForDuplicateConnections(self.localID)
				elif msg.__class__ == messages.Pay:
					if not (self.localID is None):
						raise Exception("Received Pay message while already connected")
					if self.network.interfaceExists(msg.ID):
						log.log("Received Pay message for payment that already has a connection; closing the new one.")
						self.network.closeConnection(self)
					self.localID = msg.ID
				else:
					#Send confirmation on non-connect messages:
					confirmation = {'received': index}
					self.send(serializable.serialize(confirmation) + '\n')

				#Always set/overwrite the ID attribute with our own localID
				msg.ID = self.localID

				#TODO: filter for acceptable message types etc. before
				#sending them to a general-purpose message handler
				self.network.callback.handleMessage(msg)
			else:
				log.log("Received message with invalid format")
		except Exception as e:
			log.logException()
			#TODO: send error back to remote host?


	def sendMessage(self, index, msg):
		log.log("Sending message %s" % str(msg.__class__))
		container = {'index': index, 'message': msg}
		self.send(serializable.serialize(container) + '\n')


	def handle_close(self):
		self.isClosed = True



class Listener(asyncore.dispatcher):
	def __init__(self, host, port, network):
		asyncore.dispatcher.__init__(self, map=network.channelMap)
		self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
		self.set_reuse_addr()
		self.bind((host, port))
		self.listen(5)

		self.network = network


	def handle_accept(self):
		try:
			sock, addr = self.accept()
			log.log('Incoming connection from %s' % repr(addr))
			self.network.makeConnectionFromSocket(sock)
		except:
			log.logException()



class Network:
	def __init__(self, host, port, callback):
		self.channelMap = {}
		self.listener = None
		self.host = host
		self.port = port
		self.callback = callback
		self.connections = []


	def openListener(self):
		if self.listener is None:
			self.listener = Listener(self.host, self.port, self)


	def processNetworkEvents(self, timeout):
		asyncore.loop(timeout=timeout, count=1, map=self.channelMap)


	def sendOutboundMessage(self, index, msg):
		self.getInterface(msg.localID).sendMessage(index, msg.message)


	def interfaceExists(self, localID):
		return not (self.getInterface(localID) is None)


	def getInterface(self, localID):
		for i in range(len(self.connections)):
			if self.connections[i].localID == localID:
				if self.connections[i].isClosed:
					log.log('Connection %s was closed remotely' % localID)
					del self.connections[i] #old reference -> remove it
					return None
				return self.connections[i]

		return None


	def makeConnection(self, address, localID, connectMessage):
		log.log('Making connection %s' % localID)

		if self.interfaceExists(localID):
			log.log('Connection %s already exists -> don\'t create it' % localID)
			return

		try:
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			sock.connect(address)
		except Exception as e:
			log.log("Connect failed: " + str(e))
			raise ConnectFailed("Connect failed: " + str(e))

		connection = self.makeConnectionFromSocket(sock)
		connection.localID = localID
		connection.dice = randomsource.getNonSecureRandom(numBytes=4)

		connectMessage.dice = connection.dice
		connection.sendMessage(None, connectMessage)

		return connection


	def makeConnectionFromSocket(self, sock):
		connection = Connection(sock, self)
		self.connections.append(connection)
		return connection


	def checkForDuplicateConnections(self, localID):
		connections = [c for c in self.connections if c.localID == localID]
		if len(connections) < 2:
			return

		keepConnection = connections[0]
		for c in connections:
			if c.dice > keepConnection.dice: #'alphabetical': big endian
				keepConnection = c

		for c in connections:
			if c != keepConnection:
				i = self.connections.index(c)
				log.log('Closing duplicate connection for %s' % localID)
				self.connections[i].close()
				del self.connections[i]


	def closeInterface(self, localID):
		for i in range(len(self.connections)):
			if self.connections[i].localID == localID:
				log.log('Closing connection %s' % localID)
				self.connections[i].close()
				del self.connections[i]
				break


	def closeConnection(self, connection):
		connection.close()
		self.connections.remove(connection)


	def closeAll(self):
		log.log('Closing all network connections')
		for c in self.connections:
			c.close()
		self.connections = []
		if self.listener is not None:
			self.listener.close()
		self.listener = None

