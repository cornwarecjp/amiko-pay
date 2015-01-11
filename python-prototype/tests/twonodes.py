#!/usr/bin/env python
#    twonodes.py
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

import sys
import time
import pprint

sys.path.append("..")

import amiko
import event



node1 = amiko.Amiko(conffile="twonodes_1.conf")
node1.start()
node2 = amiko.Amiko(conffile="twonodes_2.conf")
node2.start()

#Allow links to connect
time.sleep(3)

print "Node 1:"
pprint.pprint(node1.list())

print "Node 2:"
pprint.pprint(node2.list())

URL = node2.request(123, "receipt")
print "Payment URL:", URL

payer = node1.pay(URL)
node1.confirmPayment(payer, True)
print "Payment is ", payer.state

#Allow paylink to disconnect
time.sleep(0.5)

print "Node 1:"
pprint.pprint(node1.list())

print "Node 2:"
pprint.pprint(node2.list())

node1.stop()
node2.stop()


