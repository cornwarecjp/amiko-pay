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



ID_STRING  = 1
ID_LINK    = 2
ID_PAY     = 3
ID_RECEIPT = 4



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
		ID_PAY: Pay,
		ID_RECEIPT: Receipt
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



class Receipt(Message):
	def __init__(self, amount=0, receipt="", meetingPoints=[]):
		Message.__init__(self, ID_RECEIPT)
		self.amount = amount
		self.receipt = receipt
		self.meetingPoints = meetingPoints
		#TODO: add transaction hash value


	def serializeAttributes(self):
		# 8-byte unsigned int in network byte order:
		ret = struct.pack("!Q", self.amount)

		# 4-byte unsigned int in network byte order:
		receiptLen = struct.pack("!I", len(self.receipt))
		ret += receiptLen + self.receipt

		# 4-byte unsigned int in network byte order:
		ret += struct.pack("!I", len(self.meetingPoints))

		for mp in self.meetingPoints:
			# 4-byte unsigned int in network byte order:
			mpLen = struct.pack("!I", len(mp))
			ret += mpLen + mp

		return ret


	def deserializeAttributes(self, s):
		# 8-byte unsigned int in network byte order:
		self.amount = struct.unpack("!Q", s[:8])[0]
		s = s[8:]

		# 4-byte unsigned int in network byte order:
		receiptLen = struct.unpack("!I", s[:4])[0]
		self.receipt = s[4:4+receiptLen]
		s = s[4+receiptLen:]

		# 4-byte unsigned int in network byte order:
		numMPs = struct.unpack("!I", s[:4])[0]
		s = s[4:]

		self.meetingPoints = []
		for i in range(numMPs):
			# 4-byte unsigned int in network byte order:
			mpLen = struct.unpack("!I", s[:4])[0]
			self.meetingPoints.append(s[4:4+mpLen])
			s = s[4+mpLen:]


	def __str__(self):
		return "amount: %d; receipt: \"%s\"; meeting points: %s" % \
			(self.amount, self.receipt, str(self.meetingPoints))


