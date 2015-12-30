#    serializable.py
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

import copy
import json



registeredClasses = {}

def registerClass(c):
	"""
	c: class
	"""
	if c.__name__ in registeredClasses.keys():
		raise Exception("Multiple serializable classes with the same name: " + c.__name__)
	registeredClasses[c.__name__] = c


def applyRecursively(selectFunction, transformFunction, obj):
	#For these iterables, process the items recursively:
	if type(obj) == dict:
		obj = \
		{
		applyRecursively(selectFunction, transformFunction, k):
			applyRecursively(selectFunction, transformFunction, v)
		for k,v in obj.iteritems()
		}
	if type(obj) == list:
		obj = \
		[
		applyRecursively(selectFunction, transformFunction, x)
		for x in obj
		]

	#Apply the transformation for selected objects:
	if selectFunction(obj):
		return transformFunction(obj)

	return obj


def state2Object(s, context=None):
	def transformFunction(attribs):
		c = registeredClasses[attribs["_class"]]
		return c(context, **attribs)

	return applyRecursively(
		lambda obj: type(obj) == dict and "_class" in obj.keys(),
		transformFunction,
		s)


def object2State(s):
	def transformFunction(obj):
		className = obj.__class__.__name__
		c = registeredClasses[className]
		attributes = c.serializableAttributes
		obj = \
		{
			name: object2State(getattr(obj, name))
			for name in attributes.keys()
		}
		obj["_class"] = className
		return obj

	return applyRecursively(
		lambda obj: isinstance(obj, Serializable),
		transformFunction,
		s)


def encodeStrings(s):
	def transformFunction(obj):
		nonReadableChars = [c for c in obj if ord(c) < 32 or ord(c) >= 128]
		isHumanReadable = len(nonReadableChars) == 0
		if isHumanReadable:
			if len(obj) > 0 and obj[0] == '!':
				obj = '!' + obj
		else:
			obj = '!x' + obj.encode('hex')
		return obj

	return applyRecursively(
		lambda obj: type(obj) == str,
		transformFunction,
		s)


def decodeStrings(s):
	def transformFunction(obj):
		obj = str(obj)
		if len(obj) >= 2 and obj[0] == '!':
			if obj[1] == 'x':
				return obj[2:].decode('hex')
			elif obj[1] == '!':
				return obj[1:]
			else:
				raise Exception('Formatting error')
		return obj

	return applyRecursively(
		lambda obj: type(obj) in (unicode, str),
		transformFunction,
		s)


def deserializeState(s):
	return decodeStrings(json.loads(s))


def deserialize(s, context=None):
	return state2Object(deserializeState(s), context)


def serializeState(s):
	return json.dumps(encodeStrings(s))


def serialize(obj):
	return serializeState(object2State(obj))



class Serializable:
	def __init__(self, context=None, **kwargs):
		c = registeredClasses[self.__class__.__name__]
		attributes = c.serializableAttributes
		for name in attributes.keys():
			setattr(self, name, copy.deepcopy(
					kwargs[name]
				if name in kwargs else
					attributes[name] #default value
				))


	def getState(self):
		return object2State(self)

