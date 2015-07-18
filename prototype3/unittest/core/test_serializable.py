#!/usr/bin/env python
#    test_serializable.py
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

import unittest
import json

import testenvironment

from amiko.core import serializable


class C(serializable.Serializable):
	serializableAttributes = {'x':1, 'y':2}



class Test(unittest.TestCase):
	def setUp(self):
		serializable.registeredClasses = {}
		serializable.registerClass(C)


	def test_registerClassNameCollision(self):
		"Test registerClass name collision"

		self.assertRaises(Exception, serializable.registerClass, C)


	def test_registerAddress(self):
		"Test registerAddress"

		self.assertEqual(serializable.registeredClasses, {'C': C})


	def test_object2State(self):
		"Test object2State"

		obj = C(x={'a':C(), 'b':3}, y=[C(), 4])
		self.assertEqual(serializable.object2State(obj),
			{'_class':'C',
				'x': {'a':{'_class':'C', 'x':1, 'y':2}, 'b':3},
				'y': [{'_class':'C', 'x':1, 'y':2}, 4]
			}
			)


	def test_state2Object(self):
		"Test state2Object"

		obj = serializable.state2Object(
			{'_class':'C',
				'x': {'a':{'_class':'C'}, 'b':3},
				'y': [{'_class':'C', 'x':5, 'y':6}, 4]
			}
			)

		self.assertEqual(obj.__class__, C)
		self.assertEqual(len(obj.x), 2)
		self.assertEqual(len(obj.y), 2)
		self.assertEqual(type(obj.x), dict)
		self.assertEqual(type(obj.y), list)
		self.assertEqual(obj.x['a'].__class__, C)
		self.assertEqual(obj.x['a'].x, 1)
		self.assertEqual(obj.x['a'].y, 2)
		self.assertEqual(obj.x['b'], 3)
		self.assertEqual(obj.y[0].__class__, C)
		self.assertEqual(obj.y[0].x, 5)
		self.assertEqual(obj.y[0].y, 6)
		self.assertEqual(obj.y[1], 4)


	def test_deserialize(self):
		"Test deserialize"

		obj = serializable.deserialize(
			'{"x": {"a": "!xff00", "b": "foo"}, "y": ["!!bar", 4], "_class": "C"}'
			)
		self.assertEqual(obj.__class__, C)
		self.assertEqual(len(obj.x), 2)
		self.assertEqual(len(obj.y), 2)
		self.assertEqual(type(obj.x), dict)
		self.assertEqual(type(obj.y), list)
		self.assertEqual(obj.x['a'], '\xff\x00')
		self.assertEqual(obj.x['b'], 'foo')
		self.assertEqual(obj.y[0], '!bar')
		self.assertEqual(obj.y[1], 4)

		self.assertRaises(Exception, serializable.deserialize, '"!foo"')


	def test_getState(self):
		"Test getState"

		obj = C(x={'a':C(), 'b':3}, y=[C(), 4])
		self.assertEqual(obj.getState(),
			{'_class':'C',
				'x': {'a':{'_class':'C', 'x':1, 'y':2}, 'b':3},
				'y': [{'_class':'C', 'x':1, 'y':2}, 4]
			}
			)


	def test_serialize(self):
		"Test serialize"

		obj = C(x={'a':"\xff\x00", 'b':"foo", "\x01": "\x02"}, y=["!bar", 4])
		self.assertEqual(serializable.serialize(obj),
			'{'
			'"y": ["!!bar", 4], '
			'"x": {"a": "!xff00", "b": "foo", "!x01": "!x02"}, '
			'"_class": "C"}'
			)



if __name__ == "__main__":
	unittest.main(verbosity=2)

