#    messages.py
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

import struct



ID_STRING = 1
ID_LINK   = 2
ID_PAY    = 3


class Message:
	def __init__(self, typeID):
		self.__typeID = typeID

	def serialize(self):
		# 4-byte unsigned int in network byte order:
		ID = struct.pack("!I", self.__typeID)
		return ID + self.serializeAttributes()



def deserialize(s):
	# 4-byte unsigned int in network byte order:
	ID = struct.unpack("!I", s[:4])[0]

	try:
		clss = \
		{
		ID_STRING: String,
		ID_LINK: Link,
		ID_PAY: Pay
		}[ID]
	except KeyError:
		raise Exception("Deserialize failed: unknown type ID")

	obj = clss()

	# Remaining bytes contain attribute data
	obj.deserializeAttributes(s[4:])

	return obj




class String(Message):
	def __init__(self, val=""):
		Message.__init__(self, ID_STRING)
		self.value = val

	def serializeAttributes(self):
		return self.value


	def deserializeAttributes(self, s):
		self.value = s


	def __str__(self):
		return self.value


class Link(Message):
	def __init__(self, yourID=""):
		Message.__init__(self, ID_LINK)
		self.yourID = yourID


	def serializeAttributes(self):
		return self.yourID


	def deserializeAttributes(self, s):
		self.yourID = s


	def __str__(self):
		return "yourID: " + self.yourID



class Pay(Message):
	def __init__(self, ID=""):
		Message.__init__(self, ID_PAY)
		self.ID = ID


	def serializeAttributes(self):
		return self.ID


	def deserializeAttributes(self, s):
		self.ID = s


	def __str__(self):
		return "ID: " + self.ID

