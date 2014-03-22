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
import urlparse

import amiko



class Listener:
	def __init__(self, amikoContext, port):
		self.context = amikoContext

		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.bind(('localhost', port))
		self.socket.listen(10) # Maximum 10 unaccepted connections

		self.context.connect(self.socket, amiko.signals.readyForRead,
			self.handleReadAvailable)
		self.context.connect(None, amiko.signals.quit, self.close)


	def close(self):
		print "Listener close"
		self.context.removeEventConnectionsBySender(self.socket)
		self.socket.close()


	def handleReadAvailable(self):
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

		self.context.connect(self.socket, amiko.signals.readyForRead,
			self.handleReadAvailable)
		self.context.connect(None, amiko.signals.quit, self.close)


	def close(self):
		print "Connection close"
		self.context.removeEventConnectionsBySender(self.socket)
		self.socket.shutdown(socket.SHUT_RDWR)
		self.socket.close()


	def handleReadAvailable(self):
		print "Read available on connection: printing data"
		print self.receive()


	def receive(self):
		return self.socket.recv(64)


	def send(self, data):
		self.socket.send(data)


