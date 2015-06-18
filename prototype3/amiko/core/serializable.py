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
	registeredClasses[c.__name__] = c


def state2Object(s):
	#Default: return s
	ret = s

	#For these iterables, process the items recursively:
	if type(ret) == dict:
		ret = {k: state2Object(v) for k,v in ret.iteritems()}
	elif type(ret) == list:
		ret = [state2Object(x) for x in ret]

	#Classes are indicated by the _class item:
	if type(ret) == dict and "_class" in s.keys():
		c = registeredClasses[s["_class"]]
		ret = c(**ret)

	return ret


def object2State(obj):
	#Default: return obj
	ret = obj

	#Classes are indicated by the _class item:
	if isinstance(ret, Serializable):
		className = ret.__class__.__name__
		c = registeredClasses[className]
		attributes = c.serializableAttributes
		ret = {name: getattr(obj, name) for name in attributes.keys()}
		ret["_class"] = className

	#For these iterables, process the items recursively:
	if type(ret) == dict:
		ret = {k: object2State(v) for k,v in ret.iteritems()}
	elif type(ret) == list:
		ret = [object2State(x) for x in ret]

	return ret


def encodeStrings(obj):
	#For these iterables, process the items recursively:
	if type(obj) == dict:
		return {k: encodeStrings(v) for k,v in obj.iteritems()}
	if type(obj) == list:
		return [encodeStrings(x) for x in obj]

	if type(obj) == str:
		#Do the rewriting:
		nonReadableChars = [c for c in obj if ord(c) < 32 or ord(c) >= 128]
		isHumanReadable = len(nonReadableChars) == 0
		if isHumanReadable:
			if len(obj) > 0 and obj[0] == '!':
				obj = '!' + obj
		else:
			obj = '!x' + obj.encode('hex')

	#all other types:
	return obj


def decodeStrings(obj):
	#For these iterables, process the items recursively:
	if type(obj) == dict:
		return {k: decodeStrings(v) for k,v in obj.iteritems()}
	if type(obj) == list:
		return [decodeStrings(x) for x in obj]

	if type(obj) in (unicode, str):
		#Do the rewriting:
		obj = str(obj)
		if len(obj) >= 2 and obj[0] == '!':
			if obj[1] == 'x':
				return obj[2:].decode('hex')
			elif obj[1] == '!':
				return obj[1:]
			else:
				raise Exception('Formatting error')

	#all other types:
	return obj


def deserialize(s):
	s = json.loads(s)
	s = decodeStrings(s)
	return state2Object(s)



class Serializable:
	def __init__(self, **kwargs):
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


	def serialize(self):
		s = self.getState()
		s = encodeStrings(s)
		return json.dumps(s)

