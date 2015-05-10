#    messages.py
#    Copyright (C) 2014-2015 by CJP
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

import struct

from ..utils.utils import inheritDocString



#Message type IDs
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
ID_WITHDRAW    = 13



def serializeBinList(binList):
	"""
	Serializes a list of binary strings.

	Arguments:
	binList: list of str; the to-be-serialized data.

	Return value:
	str; the serialized data.
	"""
	return "".join([
		#length: 4-byte unsigned int in network byte order:
		struct.pack("!I", len(s)) + s

		for s in binList
		])


def deserializeBinList(data):
	"""
	Deserializes a list of binary strings.

	Arguments:
	data: str; the to-be-deserialized data.

	Return value:
	list of str; the deserialized data.

	Exceptions:
	Exception: the serialized data did not conform to the expected format.
	"""
	ret = []
	while len(data) > 0:
		#length: 4-byte unsigned int in network byte order:
		length = struct.unpack("!I", data[:4])[0]
		if length+4 > len(data):
			raise Exception("Binlist deserialization error")
		ret.append(data[4:4+length])
		data = data[4+length:]

	return ret



class Message:
	"""
	Message base class.

	This class should only be used as base class for other message classes.
	"""

	def __init__(self, typeID):
		"""
		Constructor.

		Arguments:
		typeID: int; the type ID of the message (one of the ID_* constants)
		"""
		self.__typeID = typeID


	def serialize(self):
		"""
		Serializes the message.

		Return value:
		str; the serialized message data, containing the type ID and the attributes.
		"""

		# 4-byte unsigned int in network byte order:
		ID = struct.pack("!I", self.__typeID)
		return ID + self.serializeAttributes()


	def serializeAttributes(self):
		"""
		Serializes the attributes.
		This method should be overridden by Message-derived classes.
		Code that uses Message-derived object should call the serialize method
		instead of calling serializeAttributes directly.

		Return value:
		str; the serialized message attribute data.
		"""
		return ""


	def deserializeAttributes(self, s):
		"""
		De-serializes the attributes.
		This method should be overridden by Message-derived classes.
		Code that uses Message-derived object should call the deserialize
		function instead of calling deserializeAttributes directly.

		Arguments:
		s: str; the serialized message attribute data.

		Exceptions:
		Exception: the serialized data did not conform to the expected format.
		"""
		pass


	def __str__(self):
		"""
		Conversion to a human-readable string.
		Note that the returned string might not contain all attribute information.

		Return value:
		str; a human-readable description of the message.
		"""
		return "Type: %d" % self.__typeID



def deserialize(s):
	"""
	De-serializes a serialized message.

	Arguments:
	s: str; the serialized message data, containing the type ID and the attributes.

	Return value:
	Message-derived; the message object containing de-serialized attributes.

	Exceptions:
	Exception: the serialized data did not conform to the expected format.
	"""

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
		ID_DEPOSIT: Deposit,
		ID_WITHDRAW: Withdraw
		}[ID]
	except KeyError:
		raise Exception("Deserialize failed: unknown type ID")

	obj = clss()

	# Remaining bytes contain attribute data
	obj.deserializeAttributes(s[4:])

	return obj




class String(Message):
	"""
	Generic string-based message class.
	Typically used as base class for other message classes.

	Attributes:
	value: str; the string data
	"""

	def __init__(self, value="", typeID=ID_STRING):
		"""
		Constructor.

		Arguments:
		value: str; the string data
		typeID: int; the type ID of the message (one of the ID_* constants)
		"""

		Message.__init__(self, typeID)
		self.value = value


	@inheritDocString(Message)
	def serializeAttributes(self):
		return self.value


	@inheritDocString(Message)
	def deserializeAttributes(self, s):
		self.value = s


	@inheritDocString(Message)
	def __str__(self):
		return repr(self.value)



class Pay(String):
	"""
	Pay message (sent from payer to payee on pay link)

	Attributes:
	value: str; the transaction ID (not the same as the token or hash)
	"""

	def __init__(self, value=""):
		"""
		Constructor.

		Arguments:
		value: str; the transaction ID (not the same as the token or hash)
		"""
		String.__init__(self, value, ID_PAY)



class Confirm(String):
	"""
	Confirm message (sent from payer to payee on pay link)

	Attributes:
	value: str; the ID of the meeting point
	"""

	def __init__(self, value=""):
		"""
		Constructor.

		Arguments:
		value: str; the ID of the meeting point
		"""
		String.__init__(self, value, ID_CONFIRM)



class HaveRoute(String):
	"""
	Have route message (sent from meeting point side to payer/payee side)

	Attributes:
	value: str; the transaction hash
	"""

	def __init__(self, value=""):
		"""
		Constructor.

		Arguments:
		value: str; the transaction hash
		"""
		String.__init__(self, value, ID_HAVEROUTE)



class Cancel(Message):
	"""
	Cancel message (sent from payer to payee on pay link)
	"""

	def __init__(self):
		"""
		Constructor.
		"""
		Message.__init__(self, ID_CANCEL)



class MyURLs(String):
	"""
	My URLs message (sent between peers on link)

	Attributes:
	value: str; the list of newline-separated URLs
	"""

	def __init__(self, value=[]):
		"""
		Constructor.

		Arguments:
		value: list of str; the list of URLs
		"""
		String.__init__(self, "\n".join(value), ID_MYURLS)


	def getURLs(self):
		"""
		Return value:
		list of str; the list of URLs
		"""
		return self.value.split("\n")



class Link(Message):
	"""
	Link message (sent between peers on link)

	Attributes:
	ID: str; the link ID on the receiving side of this message
	dice: int; random number, used to decide which side to keep when both sides
	      try to connect simultaneously.
	"""

	def __init__(self, ID="", dice=0):
		"""
		Constructor.

		Arguments:
		ID: str; the link ID on the receiving side of this message
		dice: int; random number, used to decide which side to keep when both
		      sides try to connect simultaneously.
		"""

		Message.__init__(self, ID_LINK)
		self.ID = ID
		self.dice = dice


	@inheritDocString(Message)
	def serializeAttributes(self):
		# 4-byte unsigned int in network byte order:
		dice = struct.pack("!I", self.dice)

		return dice + self.ID


	@inheritDocString(Message)
	def deserializeAttributes(self, s):
		# 4-byte unsigned int in network byte order:
		self.dice = struct.unpack("!I", s[:4])[0]

		self.ID = s[4:]


	@inheritDocString(Message)
	def __str__(self):
		return "dice: %d; ID: %s" % (self.dice, self.ID)



class MakeRoute(Message):
	"""
	Make route message (sent from payer/payee side to meeting point)

	Attributes:
	amount: int; the amount (in Satoshi) to be sent from payer to payee
	isPayerSide: bool; indicates whether we are on the payer side (True) or not
	             (False).
	hash: str; the transaction hash
	meetingPoint: str; the ID of the meeting point
	"""

	def __init__(self, amount=0, isPayerSide=True, hash="", meetingPoint=""):
		"""
		Constructor.

		Arguments:
		amount: int; the amount (in Satoshi) to be sent from payer to payee
		isPayerSide: bool; indicates whether we are on the payer side (True) or
		             not (False).
		hash: str; the transaction hash
		meetingPoint: str; the ID of the meeting point
		"""
		Message.__init__(self, ID_MAKEROUTE)
		self.amount = amount
		self.isPayerSide = isPayerSide
		self.hash=hash
		self.meetingPoint = meetingPoint


	@inheritDocString(Message)
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


	@inheritDocString(Message)
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


	@inheritDocString(Message)
	def __str__(self):
		return "amount: %d; payerSide: %s; hash: %s; meeting point: %s" % \
			(self.amount, str(self.isPayerSide), repr(self.hash), str(self.meetingPoint))



class Receipt(Message):
	"""
	Receipt message (sent from payee to payer on pay link)

	Attributes:
	amount: int; the amount (in Satoshi) to be sent from payer to payee
	receipt: str; receipt data
	hash: str; the transaction hash
	meetingPoints: list of str; the IDs of accepted meeting points
	"""

	def __init__(self, amount=0, receipt="", hash="", meetingPoints=[]):
		"""
		Constructor.

		Arguments:
		amount: int; the amount (in Satoshi) to be sent from payer to payee
		receipt: str; receipt data
		hash: str; the transaction hash
		meetingPoints: list of str; the IDs of accepted meeting points
		"""

		Message.__init__(self, ID_RECEIPT)
		self.amount = amount
		self.receipt = receipt
		self.hash=hash
		self.meetingPoints = meetingPoints


	@inheritDocString(Message)
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


	@inheritDocString(Message)
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


	@inheritDocString(Message)
	def __str__(self):
		return "amount: %d; receipt: \"%s\"; hash: %s; meeting points: %s" % \
			(self.amount, self.receipt, repr(self.hash), str(self.meetingPoints))



class ChannelMessage(Message):
	"""
	Base class for messages that involve a microtransaction channel.

	Attributes:
	channelID: int; the ID of the channel
	stage: int; the stage (only used for interactions that have multiple stages)
	payload: str; meaning depends on channel type, message type and stage
	"""

	def __init__(self, typeID, channelID=0, stage=0, payload=""):
		"""
		Constructor.

		Arguments:
		typeID: int; the type ID of the message (one of the ID_* constants)
		channelID: int; the ID of the channel
		stage: int; the stage (only used for interactions that have multiple stages)
		payload: str; meaning depends on channel type, message type and stage
		"""

		Message.__init__(self, typeID)
		self.channelID = channelID
		self.stage = stage
		self.payload = payload #serialized link-type dependent data


	@inheritDocString(Message)
	def serializeAttributes(self):
		# 4-byte unsigned int in network byte order:
		ret = struct.pack("!I", self.channelID)

		# 1-byte unsigned int:
		ret += struct.pack("!B", self.stage)

		ret += self.payload

		return ret


	@inheritDocString(Message)
	def deserializeAttributes(self, s):
		# 4-byte unsigned int in network byte order:
		self.channelID = struct.unpack("!I", s[:4])[0]
		s = s[4:]

		# 1-byte unsigned int:
		self.stage = struct.unpack("!B", s[0])[0]
		s = s[1:]

		self.payload = s


	@inheritDocString(Message)
	def __str__(self):
		return "channelID: %d; stage: %d" % (self.channelID, self.stage)



class Deposit(ChannelMessage):
	"""
	Deposit message (sent between peers on link)

	Attributes:
	channelID: int; the ID of the channel
	stage: int; the stage (only used for interactions that have multiple stages)
	payload: str; meaning depends on channel type and stage
	type: str; the type of channel to be created by the deposit
	isInitial: bool; indicates whether this is the first message in the deposit
	           sequence (True) or not (False)
	"""

	def __init__(self, channelID=0, type="", isInitial=False, stage=0, payload=""):
		"""
		Constructor.

		Arguments:
		channelID: int; the ID of the channel
		type: str; the type of channel to be created by the deposit
		isInitial: bool; indicates whether this is the first message in the deposit
			       sequence (True) or not (False)
		stage: int; the stage (only used for interactions that have multiple stages)
		payload: str; meaning depends on channel type and stage
		"""
		ChannelMessage.__init__(self, ID_DEPOSIT, channelID, stage, payload)
		self.type = type
		self.isInitial = isInitial


	@inheritDocString(Message)
	def serializeAttributes(self):
		# 4-byte unsigned int in network byte order:
		typeLen = struct.pack("!I", len(self.type))
		ret = typeLen + self.type

		# 1-byte unsigned int:
		ret += struct.pack("!B", int(self.isInitial))

		ret += ChannelMessage.serializeAttributes(self)
		return ret


	@inheritDocString(Message)
	def deserializeAttributes(self, s):
		# 4-byte unsigned int in network byte order:
		typeLen = struct.unpack("!I", s[:4])[0]
		self.type = s[4:4+typeLen]
		s = s[4+typeLen:]

		# 1-byte unsigned int:
		self.isInitial = bool(struct.unpack("!B", s[0])[0])
		s = s[1:]

		ChannelMessage.deserializeAttributes(self, s)


	@inheritDocString(Message)
	def __str__(self):
		return "channelID: %d; type: %s; isInitial: %s; stage: %d" % \
			(self.channelID, self.type, str(self.isInitial), self.stage)



class Withdraw(ChannelMessage):
	"""
	Withdraw message (sent between peers on link)

	Attributes:
	channelID: int; the ID of the channel
	stage: int; the stage (only used for interactions that have multiple stages)
	payload: str; meaning depends on channel type and stage
	"""

	def __init__(self, channelID=0, stage=0, payload=""):
		"""
		Constructor.

		Arguments:
		channelID: int; the ID of the channel
		stage: int; the stage (only used for interactions that have multiple stages)
		payload: str; meaning depends on channel type and stage
		"""
		ChannelMessage.__init__(self, ID_WITHDRAW, channelID, stage, payload)



class Lock(ChannelMessage):
	"""
	Lock message (sent from payer to payee)

	Attributes:
	channelID: int; the ID of the channel
	stage: int; the stage (unused: always zero)
	payload: str; meaning depends on channel type
	hash: str; the transaction hash
	"""

	def __init__(self, channelID=0, hash="", payload=""):
		"""
		Constructor.

		Arguments:
		channelID: int; the ID of the channel
		hash: str; the transaction hash
		payload: str; meaning depends on channel type
		"""

		ChannelMessage.__init__(self, ID_LOCK, channelID, payload=payload)
		self.hash = hash


	@inheritDocString(Message)
	def serializeAttributes(self):
		# 4-byte unsigned int in network byte order:
		hashLen = struct.pack("!I", len(self.hash))
		ret = hashLen + self.hash

		ret += ChannelMessage.serializeAttributes(self)
		return ret


	@inheritDocString(Message)
	def deserializeAttributes(self, s):
		# 4-byte unsigned int in network byte order:
		hashLen = struct.unpack("!I", s[:4])[0]
		self.hash = s[4:4+hashLen]
		s = s[4+hashLen:]

		ChannelMessage.deserializeAttributes(self, s)


	@inheritDocString(Message)
	def __str__(self):
		return "channelID: %d; hash: %s" % \
			(self.channelID, self.hash.encode("hex"))



class Commit(ChannelMessage):
	"""
	Commit message (sent from payer to payee)

	Attributes:
	channelID: int; the ID of the channel
	stage: int; the stage (unused: always zero)
	payload: str; meaning depends on channel type
	token: str; the transaction token
	"""

	def __init__(self, channelID=0, token="", payload=""):
		"""
		Constructor.

		Arguments:
		channelID: int; the ID of the channel
		token: str; the transaction token
		payload: str; meaning depends on channel type
		"""

		ChannelMessage.__init__(self, ID_COMMIT, channelID, payload=payload)
		self.token = token


	@inheritDocString(Message)
	def serializeAttributes(self):
		# 4-byte unsigned int in network byte order:
		tokenLen = struct.pack("!I", len(self.token))
		ret = tokenLen + self.token

		ret += ChannelMessage.serializeAttributes(self)
		return ret


	@inheritDocString(Message)
	def deserializeAttributes(self, s):
		# 4-byte unsigned int in network byte order:
		tokenLen = struct.unpack("!I", s[:4])[0]
		self.token = s[4:4+tokenLen]
		s = s[4+tokenLen:]

		ChannelMessage.deserializeAttributes(self, s)


	@inheritDocString(Message)
	def __str__(self):
		return "channelID: %d; token: %s" % \
			(self.channelID, self.token.encode("hex"))

