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



registeredClasses = {}

def registerClass(c, attributes):
	"""
	c: class
	attributes: dict of name:defaultValue pairs
	"""
	registeredClasses[c.__name__] = (c, attributes)


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
		c, attributes = registeredClasses[s["_class"]]
		attributes = {name: ret[name] for name in attributes.keys()}
		ret = c(**attributes)

	return ret


def object2State(obj):
	#Default: return obj
	ret = obj

	#Classes are indicated by the _class item:
	if isinstance(ret, Serializable):
		className = ret.__class__.__name__
		c, attributes = registeredClasses[className]
		ret = {name: getattr(obj, name) for name in attributes.keys()}
		ret["_class"] = className

	#For these iterables, process the items recursively:
	if type(ret) == dict:
		ret = {k: object2State(v) for k,v in ret.iteritems()}
	elif type(ret) == list:
		ret = [object2State(x) for x in ret]

	return ret



class Serializable:
	def __init__(self, **kwargs):
		c, attributes = registeredClasses[self.__class__.__name__]
		for name in attributes.keys():
			setattr(self, name, copy.deepcopy(
					kwargs[name]
				if name in kwargs else
					attributes[name] #default value
				))



if __name__ == "__main__":

	class A(Serializable):
		def __init__(self, **kwargs):
			Serializable.__init__(self, **kwargs)


	class B(Serializable):
		def __init__(self, **kwargs):
			Serializable.__init__(self, **kwargs)


	registerClass(A, {'x':None, 'y':None})
	registerClass(B, {'a':None, 'b':None})

	a1 = A(x=1, y={'key1': B(a=True, b=None), 'key2': [3,1,4,1]})
	state = object2State(a1)
	print state
	a2 = state2Object(state)
	state = object2State(a2)
	print state

