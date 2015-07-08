#    payeelink.py
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


from ..utils import utils

import settings

import serializable



class Pay(serializable.Serializable):
	serializableAttributes = {'ID':''}
serializable.registerClass(Pay)



class PayeeLink(serializable.Serializable):
	states = utils.Enum([
		"initial", "confirmed", "hasRoutes", "sentCommit", "cancelled", "committed"
		])

	serializableAttributes = \
	{
		'state': states.initial,
		'amount': 0,
		'receipt': None,
		'token': None
	}

	def __init__(self, **kwargs):
		serializable.Serializable.__init__(self, **kwargs)

		#This will fail if token is not set (is None).
		#So, token must always be set for successful construction.
		self.transactionID = settings.hashAlgorithm(self.token)


	def handleMessage(self, msg):
		print "payee:handleMessage called"
		return []


serializable.registerClass(PayeeLink)

