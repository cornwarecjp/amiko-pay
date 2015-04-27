#    dummy_interfaces.py
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

from amiko.utils import base58



class Tracer:
	def __init__(self):
		self.trace = []


	def __getattr__(self, name):
		def generic_method(*args, **kwargs):
			#print self, (name, args, kwargs)
			self.trace.append((name, args, kwargs))

		return generic_method


	def __eq__(self, x):
		#Exception: this doesn't get through __getattr__
		return id(x) == id(self)


	def __ne__(self, x):
		#Exception: this doesn't get through __getattr__
		return id(x) != id(self)



class DummyLink(Tracer):
	def __init__(self, ID):
		Tracer.__init__(self)
		self.localID = ID


	def __str__(self):
		return "DummyLink:" + self.localID


	def __repr__(self):
		return self.__str__()



class DummyMeetingPoint(Tracer):
	def __init__(self, ID):
		Tracer.__init__(self)
		self.ID = ID

	def __str__(self):
		return "DummyMeetingPoint:" + self.ID



class DummyRoutingContext:
	def __init__(self):
		self.links = [DummyLink("link1"), DummyLink("link2"), DummyLink("link3")]
		self.meetingPoints = []



class DummyTransaction(Tracer):
	def __init__(self, amount, hash, meetingPoint, isPayerSide):
		Tracer.__init__(self)
		self.amount = amount
		self.hash = hash
		self.meetingPoint = meetingPoint
		self.__isPayerSide = isPayerSide


	def isPayerSide(self):
		#Exception: this doesn't get through __getattr__
		#But we DO want it traced:
		self.trace.append(('isPayerSide', [], {}))
		return self.__isPayerSide


	def __str__(self):
		return "DummyTransaction:" + self.hash


	def __repr__(self):
		return self.__str__()



class DummyBitcoind(Tracer):
	def listUnspent(self):
		#Exception: this doesn't get through __getattr__
		#But we DO want it traced:
		self.trace.append(('listUnspent', [], {}))
		return \
		[
			{
				"amount": 10, "address": "foo",
				"txid": "foo_tx", "vout": 3,
				"scriptPubKey": "foo_pub"
			},
			{
				"amount": 20, "address": "bar",
				"txid": "bar_tx", "vout": 2,
				"scriptPubKey": "bar_pub"
			},
			{
				"amount": 50, "address": "foobar",
				"txid": "foobar_tx", "vout": 1,
				"scriptPubKey": "foobar_pub"
			},
			{"amount": 100}
		]


	def getPrivateKey(self, address):
		return base58.encodeBase58Check(address, 128)

