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
import errno
import urlparse
import struct

import event
import amiko



class Listener:
	def __init__(self, context, port):
		self.context = context

		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		#TODO: do we want to keep this in production code?
		self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

		self.socket.bind(('localhost', port))
		self.socket.listen(10) # Maximum 10 unaccepted connections

		self.context.connect(self.socket, event.signals.readyForRead,
			self.__handleReadAvailable)
		self.context.connect(None, event.signals.quit, self.close)


	def close(self):
		print "Listener close"
		self.context.removeEventConnectionsBySender(self.socket)
		self.socket.close()


	def __handleReadAvailable(self):
		print "Read available on listener: accepting new connection"

		# Note: the new connection will register itself at the context, so
		# it will not be deleted when it goes out of scope here.
		newConnection = Connection(self.context, self)


class Connection:
	def __init__(self, amikoContext, arg):
		self.context = amikoContext
		if isinstance(arg, Listener):
			self.socket, address = arg.socket.accept()
			self.remoteURL = None
		else:
			self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.remoteURL = arg
			parsed = urlparse.urlparse(self.remoteURL)
			self.socket.connect((parsed.hostname, parsed.port))

		#self.socket.setblocking(False)

		self.__writeBuffer = ""
		self.__readBuffer = ""

		self.context.connect(self.socket, event.signals.readyForRead,
			self.__handleReadAvailable)
		self.context.connect(None, event.signals.quit, self.close)

		self.protocolVersion = None # initially unknown

		#Initiate protocol + version exchange:
		self.__sendProtocolVersion()


	def close(self):
		print "Connection close"
		self.context.removeEventConnectionsBySender(self.socket)
		self.socket.shutdown(socket.SHUT_RDWR)
		self.socket.close()


	def sendMessage(self, msg):
		# 4-byte unsigned int in network byte order:
		lenStr = struct.pack("!I", len(msg))
		self.__send(lenStr + msg)


	def __send(self, data):
		self.__writeBuffer += data
		self.context.connect(self.socket, event.signals.readyForWrite,
			self.__handleWriteAvailable)


	def __handleReadAvailable(self):
		bytes = self.socket.recv(1000000)
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

		print repr(msg)
		#TODO: message handling


	def __handleWriteAvailable(self):
		if self.__writeBuffer != "":
			print "Write available on connection"

			# Never try to send more than this amount each time:
			maxChunkSize = 4096

			bytesSent = self.socket.send(self.__writeBuffer[:maxChunkSize])
			self.__writeBuffer = self.__writeBuffer[bytesSent:]
			print "Sent bytes: ", bytesSent

			# If necessary, connect again:
			if self.__writeBuffer != "":
				self.context.connect(self.socket, event.signals.readyForWrite,
					self.__handleWriteAvailable)


	def __sendProtocolVersion(self):
		self.__send("AMIKOPAY/%d/%d\n" % \
			(amiko.minProtocolVersion, amiko.maxProtocolVersion))


	def __tryReadProtocolVersion(self):
		#TODO: exception-based code

		magic = "AMIKOPAY/"
		if len(self.__readBuffer) < len(magic):
			return
		if self.__readBuffer[:len(magic)] != magic:
			print "Received invalid magic bytes"
			self.close()
		if len(self.__readBuffer) > 128 and '\n' not in self.__readBuffer:
			print "Did not receive version negotiation terminator"
			self.close()
		pos = self.__readBuffer.index('\n')
		versions = self.__readBuffer[len(magic):pos]
		self.__readBuffer = self.__readBuffer[pos+1:]

		if '/' not in versions:
			print "No min/max separator in version string"
			self.close()
		pos = versions.index('/')
		minv = int(versions[:pos])
		maxv = int(versions[pos+1:])

		if minv > amiko.maxProtocolVersion or maxv < amiko.minProtocolVersion:
			print "No matching protocol version"
			self.close()

		# Use highest version supported by both sides:
		self.protocolVersion = min(maxv, amiko.maxProtocolVersion)

		print "Using protocol version", self.protocolVersion

