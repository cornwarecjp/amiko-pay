#    uid.py
#    Copyright (C) 2015-2016 by CJP
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

import serializable



class Context:
	def __init__(self):
		self.reset()


	def reset(self):
		self.objects = {}
		self.nextID = 0


	def makeNewAndRegister(self, obj):
		while self.nextID in self.objects:
			self.nextID += 1
		newUID = self.nextID
		self.register(newUID, obj)
		self.nextID += 1
		return newUID


	def register(self, UID, obj):
		if UID in self.objects and obj != self.objects[UID]:
			raise Exception(
				"Attempt to register multiple objects with the same UID %d" % \
				UID)
		self.objects[UID] = obj


	def registerAllUIDs(self, obj):

		def transformFunction(x):
			if isinstance(x, Serializable):
				x.registerUID(self)

		obj.applyRecursively(transformFunction)



class Serializable(serializable.Serializable):
	"""
	Note: derived classes must have 'UID' in their serializableAttributes,
	      with default value None.
	"""

	def registerUID(self, context):
		if self.UID is None:
			self.UID = context.makeNewAndRegister(self)
		else:
			context.register(self.UID, self)

