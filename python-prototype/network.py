#    network.py
#    Copyright (C) 2014 by CJP
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

import socket
import struct
import traceback

import event
import amiko
import messages
import log



class Listener(event.Handler):
	def __init__(self, context, host, port):
		event.Handler.__init__(self, context)

		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		log.log("Listener opened: " + str(self.socket.fileno()))

		#TODO: do we want to keep this in production code?
		self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

		self.socket.bind((host, port))
		self.socket.listen(10) # Maximum 10 unaccepted connections

		self.connect(self.socket, event.signals.readyForRead,
			self.__handleReadAvailable)
		self.connect(None, event.signals.quit, self.close)


	def close(self):
		log.log("Listener closed: " + str(self.socket.fileno()))
		self.disconnectAll()
		self.context.removeConnectionsBySender(self.socket)
		self.socket.close()


	def __handleReadAvailable(self):
		log.log("Read available on listener: accepting new connection")

		# Note: the new connection will register itself at the context, so
		# it will not be deleted when it goes out of scope here.
		newConnection = Connection(self.context, self)


class Connection(event.Handler):
	def __init__(self, context, arg):
		event.Handler.__init__(self, context)

		if isinstance(arg, Listener):
			self.socket, address = arg.socket.accept()
		else:
			self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.socket.connect(arg)

		log.log("Connection opened: " + str(self.socket.fileno()))

		#self.socket.setblocking(False)

		self.__writeBuffer = ""
		self.__readBuffer = ""
		self.__isClosed = False

		self.connect(self.socket, event.signals.readyForRead,
			self.__handleReadAvailable)
		self.connect(None, event.signals.quit, self.close)

		self.protocolVersion = None # initially unknown

		#Initiate protocol + version exchange:
		self.__sendProtocolVersion()


	def close(self):
		if self.__isClosed:
			return #don't close again

		log.log("Connection closed: " + str(self.socket.fileno()))

		try:
			self.socket.shutdown(socket.SHUT_RDWR)
		except:
			pass #the shutdown was optional anyway, so ignore errors

		self.socket.close()
		self.__isClosed = True

		self.context.sendSignal(self, event.signals.closed)

		self.disconnectAll()
		self.context.removeConnectionsBySender(self.socket)


	def isClosed(self):
		return self.__isClosed


	def sendMessage(self, msg):
		#print "Sending message: ", msg

		#serialize:
		msg = msg.serialize()

		#print "Sending serialized message: ", repr(msg)

		# 4-byte unsigned int in network byte order:
		lenStr = struct.pack("!I", len(msg))
		self.__send(lenStr + msg)


	def __send(self, data):
		if self.isClosed():
			raise Exception("Connection is closed")

		self.__writeBuffer += data
		self.connect(self.socket, event.signals.readyForWrite,
			self.__handleWriteAvailable)


	def __handleReadAvailable(self):
		try:
			bytes = self.socket.recv(4096)

			if len(bytes) == 0:
				log.log("Detected socket close by other side; closing this side too")
				self.close()

			self.__readBuffer += bytes
			if self.protocolVersion == None:
				self.__tryReadProtocolVersion()
			if self.protocolVersion == None:
				return

			#There can be multiple messages in the read buffer,
			#so repeat until there is no more complete message
			while True:

				# Message detection:
				if len(self.__readBuffer) < 4:
					return

				# 4-byte unsigned int in network byte order:
				msgLen = struct.unpack("!I", self.__readBuffer[:4])[0]
				if len(self.__readBuffer) < msgLen+4:
					return

				msg = self.__readBuffer[4:msgLen+4]
				self.__readBuffer = self.__readBuffer[msgLen+4:]

				#print "Received serialized message: ", repr(msg)

				#de-serialize
				msg = messages.deserialize(msg)

				self.__handleMessage(msg)

		except:
			log.logException()
			self.close()


	def __handleWriteAvailable(self):
		if self.__writeBuffer != "":
			# Never try to send more than this amount each time:
			maxChunkSize = 4096

			bytesSent = self.socket.send(self.__writeBuffer[:maxChunkSize])
			self.__writeBuffer = self.__writeBuffer[bytesSent:]
			#print "Sent bytes: ", bytesSent

		#Disconnect once write is finished:
		if self.__writeBuffer == "":
			self.context.removeConnectionsByHandler(self.__handleWriteAvailable)


	def __sendProtocolVersion(self):
		self.__send("AMIKOPAY/%d/%d\n" % \
			(amiko.minProtocolVersion, amiko.maxProtocolVersion))


	def __tryReadProtocolVersion(self):

		magic = "AMIKOPAY/"
		if len(self.__readBuffer) < len(magic):
			return
		if self.__readBuffer[:len(magic)] != magic:
			raise Exception("Received invalid magic bytes")

		if len(self.__readBuffer) > 128 and '\n' not in self.__readBuffer:
			raise Exception("Did not receive version negotiation terminator")
		pos = self.__readBuffer.index('\n')

		versions = self.__readBuffer[len(magic):pos]
		self.__readBuffer = self.__readBuffer[pos+1:]

		if '/' not in versions:
			raise Exception("No min/max separator in version string")
			self.close()
		pos = versions.index('/')

		minv = int(versions[:pos])
		maxv = int(versions[pos+1:])

		if minv > amiko.maxProtocolVersion or maxv < amiko.minProtocolVersion:
			raise Exception("No matching protocol version")

		# Use highest version supported by both sides:
		self.protocolVersion = min(maxv, amiko.maxProtocolVersion)

		log.log("Using protocol version " + str(self.protocolVersion))


	def __handleMessage(self, message):

		if isinstance(message, messages.Link):
			self.context.sendSignal(None, event.signals.link,
				self, message)
			return

		if isinstance(message, messages.Pay):
			self.context.sendSignal(None, event.signals.pay,
				self, message)
			return

		# All other messages: message event
		self.context.sendSignal(self, event.signals.message,
			message)
		

