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



ID_STRING      = 1
ID_LINK        = 2
ID_PAY         = 3
ID_RECEIPT     = 4
ID_CONFIRM     = 5
ID_MAKEROUTE   = 6
ID_HAVEROUTE   = 7
ID_LOCK        = 8
ID_CANCEL      = 9
ID_COMMIT      = 10
ID_MYURLS      = 11
ID_DEPOSIT     = 12


class Message:
	def __init__(self, typeID):
		self.__typeID = typeID


	def serialize(self):
		# 4-byte unsigned int in network byte order:
		ID = struct.pack("!I", self.__typeID)
		return ID + self.serializeAttributes()


	def serializeAttributes(self):
		return ""


	def deserializeAttributes(self, s):
		pass


	def __str__(self):
		return "Type: %d" % self.__typeID



def deserialize(s):
	# 4-byte unsigned int in network byte order:
	ID = struct.unpack("!I", s[:4])[0]

	try:
		clss = \
		{
		ID_STRING: String,
		ID_LINK: Link,
		ID_PAY: Pay,
		ID_RECEIPT: Receipt,
		ID_CONFIRM: Confirm,
		ID_MAKEROUTE: MakeRoute,
		ID_HAVEROUTE: HaveRoute,
		ID_LOCK: Lock,
		ID_CANCEL: Cancel,
		ID_COMMIT: Commit,
		ID_MYURLS: MyURLs,
		ID_DEPOSIT: Deposit
		}[ID]
	except KeyError:
		raise Exception("Deserialize failed: unknown type ID")

	obj = clss()

	# Remaining bytes contain attribute data
	obj.deserializeAttributes(s[4:])

	return obj




class String(Message):
	def __init__(self, value="", typeID=ID_STRING):
		Message.__init__(self, typeID)
		self.value = value

	def serializeAttributes(self):
		return self.value


	def deserializeAttributes(self, s):
		self.value = s


	def __str__(self):
		return repr(self.value)



class Link(String):
	def __init__(self, value=""):
		String.__init__(self, value, ID_LINK)



class Pay(String):
	def __init__(self, value=""):
		String.__init__(self, value, ID_PAY)



class Confirm(String):
	def __init__(self, value=""):
		String.__init__(self, value, ID_CONFIRM)



class HaveRoute(String):
	def __init__(self, value=""):
		String.__init__(self, value, ID_HAVEROUTE)



class Lock(String):
	def __init__(self, value=""):
		String.__init__(self, value, ID_LOCK)



class Cancel(Message):
	def __init__(self):
		Message.__init__(self, ID_CANCEL)



class Commit(String):
	def __init__(self, value=""):
		String.__init__(self, value, ID_COMMIT)



class MyURLs(String):
	def __init__(self, value=[]):
		String.__init__(self, "\n".join(value), ID_MYURLS)

	def getURLs(self):
		return self.value.split("\n")



class MakeRoute(Message):
	def __init__(self, amount=0, isPayerSide=True, hash="", meetingPoint=""):
		Message.__init__(self, ID_MAKEROUTE)
		self.amount = amount
		self.isPayerSide = isPayerSide
		self.hash=hash
		self.meetingPoint = meetingPoint


	def serializeAttributes(self):
		# 8-byte unsigned int in network byte order:
		ret = struct.pack("!Q", self.amount)

		# 4-byte unsigned int in network byte order:
		hashLen = struct.pack("!I", len(self.hash))
		ret += hashLen + self.hash

		# 1-byte bool:
		ret += struct.pack("!?", self.isPayerSide)

		ret += self.meetingPoint

		return ret


	def deserializeAttributes(self, s):
		# 8-byte unsigned int in network byte order:
		self.amount = struct.unpack("!Q", s[:8])[0]
		s = s[8:]

		# 4-byte unsigned int in network byte order:
		hashLen = struct.unpack("!I", s[:4])[0]
		self.hash = s[4:4+hashLen]
		s = s[4+hashLen:]

		# 1-byte bool:
		self.isPayerSide = struct.unpack("!?", s[0])[0]
		s = s[1:]

		self.meetingPoint = s


	def __str__(self):
		return "amount: %d; payerSide: %s; hash: %s; meeting point: %s" % \
			(self.amount, str(self.isPayerSide), repr(self.hash), str(self.meetingPoint))



class Receipt(Message):
	def __init__(self, amount=0, receipt="", hash="", meetingPoints=[]):
		Message.__init__(self, ID_RECEIPT)
		self.amount = amount
		self.receipt = receipt
		self.hash=hash
		self.meetingPoints = meetingPoints


	def serializeAttributes(self):
		# 8-byte unsigned int in network byte order:
		ret = struct.pack("!Q", self.amount)

		# 4-byte unsigned int in network byte order:
		receiptLen = struct.pack("!I", len(self.receipt))
		ret += receiptLen + self.receipt

		# 4-byte unsigned int in network byte order:
		hashLen = struct.pack("!I", len(self.hash))
		ret += hashLen + self.hash

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
		hashLen = struct.unpack("!I", s[:4])[0]
		self.hash = s[4:4+hashLen]
		s = s[4+hashLen:]

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
		return "amount: %d; receipt: \"%s\"; hash: %s; meeting points: %s" % \
			(self.amount, self.receipt, repr(self.hash), str(self.meetingPoints))



class Deposit(Message):
	def __init__(self, ID=0, type="", stage=0, payload=""):
		Message.__init__(self, ID_DEPOSIT)
		self.ID = ID
		self.type = type
		self.stage = stage
		self.payload = payload #serialized link-type dependent data


	def serializeAttributes(self):
		# 4-byte unsigned int in network byte order:
		ret = struct.pack("!I", self.ID)

		# 4-byte unsigned int in network byte order:
		typeLen = struct.pack("!I", len(self.type))
		ret += typeLen + self.type

		# 1-byte unsigned int:
		ret += struct.pack("!B", self.stage)

		ret += self.payload

		return ret


	def deserializeAttributes(self, s):
		# 4-byte unsigned int in network byte order:
		self.ID = struct.unpack("!I", s[:4])[0]
		s = s[4:]

		# 4-byte unsigned int in network byte order:
		typeLen = struct.unpack("!I", s[:4])[0]
		self.type = s[4:4+typeLen]
		s = s[4+typeLen:]

		# 1-byte unsigned int:
		self.stage = struct.unpack("!B", s[0])[0]
		s = s[1:]

		self.payload = s


	def __str__(self):
		return "ID: %d; type: %s; stage: %d" % \
			(self.ID, self.type, self.stage)



if __name__ == "__main__":
	for clss in [
		String,
		Link,
		Pay,
		Receipt,
		Confirm,
		MakeRoute,
		HaveRoute,
		Lock,
		Cancel,
		Commit,
		MyURLs,
		Deposit
		]:

			a = clss()
			s1 = a.serialize()
			b = deserialize(s1)
			s2 = b.serialize()
			print str(a)
			print str(b)
			print s1 == s2

