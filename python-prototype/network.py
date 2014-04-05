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



class Listener(event.Handler):
	def __init__(self, context, port):
		event.Handler.__init__(self, context)

		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		#TODO: do we want to keep this in production code?
		self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

		self.socket.bind(('localhost', port))
		self.socket.listen(10) # Maximum 10 unaccepted connections

		self.connect(self.socket, event.signals.readyForRead,
			self.__handleReadAvailable)
		self.connect(None, event.signals.quit, self.close)


	def close(self):
		print "Listener close"
		self.disconnectAll()
		self.context.removeConnectionsBySender(self.socket)
		self.socket.close()


	def __handleReadAvailable(self):
		print "Read available on listener: accepting new connection"

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
		print "Connection close"

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
		self.__writeBuffer += data
		self.connect(self.socket, event.signals.readyForWrite,
			self.__handleWriteAvailable)


	def __handleReadAvailable(self):
		try:
			bytes = self.socket.recv(4096)

			if len(bytes) == 0:
				print "Detected socket close by other side; closing this side too"
				self.close()

			self.__readBuffer += bytes
			if self.protocolVersion == None:
				self.__tryReadProtocolVersion()
			if self.protocolVersion == None:
				return

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
		except Exception as e:
			print "Exception while handling received data from socket: "
			traceback.print_exc()
			self.close()


	def __handleWriteAvailable(self):
		if self.__writeBuffer != "":
			# Never try to send more than this amount each time:
			maxChunkSize = 4096

			bytesSent = self.socket.send(self.__writeBuffer[:maxChunkSize])
			self.__writeBuffer = self.__writeBuffer[bytesSent:]
			#print "Sent bytes: ", bytesSent

			# If necessary, connect again:
			if self.__writeBuffer != "":
				self.connect(self.socket, event.signals.readyForWrite,
					self.__handleWriteAvailable)


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

		print "Using protocol version", self.protocolVersion


	def __handleMessage(self, message):

		if isinstance(message, messages.Link):
			self.context.sendSignal(None, event.signals.link,
				self, message)
			return

		if isinstance(message, messages.Pay):
			self.context.sendSignal(None, event.signals.pay,
				self, message)
			return

		#TODO: other message handling
		print "Received unknown message type: ", str(message)


