#    tcd.py
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

import struct



class TCD:
	"""
	A Transaction Conditions Document structure, for Lightning emulation

	Attributes:
	startTime: int; start of the time range when the transaction token must
	           be published (UNIX time)
	endTime: int; end of the time range when the transaction token must
	         be published (UNIX time)
	tokenHash: str; the SHA256- and RIPEMD160-hashed commit token
	commitAddress: str; the SHA256- and RIPEMD160-hashed public key of the
		           destination in case of commit
	rollbackAddress: str; the SHA256- and RIPEMD160-hashed public key of the
		             destination in case of rollback
	"""

	@staticmethod
	def deserialize(data):
		"""
		De-serializes a Transaction Conditions Document.
		This is a static method: it can be called without having an instance,
		as an alternative to calling the constructor directly.

		Arguments:
		data: str; the serialized Transaction Conditions Document.

		Return value:
		TCD; the de-serialized Transaction Conditions Document

		Exceptions:
		Exception: deserialization failed
		"""
		pass #TODO


	def __init__(self, startTime, endTime, tokenHash, commitAddress, rollbackAddress):
		"""
		Constructor.

		Arguments:
		startTime: int; start of the time range when the transaction token must
		           be published (UNIX time)
		endTime: int; end of the time range when the transaction token must
		         be published (UNIX time)
		tokenHash: str; the SHA256- and RIPEMD160-hashed commit token
		commitAddress: str; the SHA256- and RIPEMD160-hashed public key of the
			           destination in case of commit
		rollbackAddress: str; the SHA256- and RIPEMD160-hashed public key of the
			             destination in case of rollback
		"""
		self.startTime = startTime
		self.endTime = endTime
		self.tokenHash = tokenHash
		self.commitAddress = commitAddress
		self.rollbackAddress = rollbackAddress


	def serialize(self):
		"""
		Serializes the Transaction Conditions Document.

		Return value:
		str; the serialized Transaction Conditions Document
		"""
		pass #TODO



def serializeList(TCDlist):
		"""
		Serializes a list of Transaction Conditions Documents.

		Arguments:
		TCDlist: list of TCD; the to-be serialized list

		Return value:
		str; the serialized list
		"""
		pass #TODO


def deserializeList(data):
		"""
		De-serializes a list of Transaction Conditions Documents.

		Arguments:
		data: str; the serialized list

		Return value:
		list of TCD; the de-serialized list

		Exceptions:
		Exception: deserialization failed
		"""
		pass #TODO

