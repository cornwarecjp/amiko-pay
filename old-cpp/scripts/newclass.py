import sys
import time
import os

"""
Purpose of this script:
easily generate new source files for a new class

Usage: python scripts/newclass.py BaseName
-> class name = CBaseName
-> files = basename.h, basename.cpp
"""

baseName = sys.argv[1]

cppFilename = baseName.lower() + '.cpp'
hFilename   = baseName.lower() + '.h'

preprocessorConst = baseName.upper() + "_H"

className = "C" + baseName

year = str(time.localtime(time.time()).tm_year)


hContents = \
"""/*
    {0}
    Copyright (C) {1} by <author>

    This file is part of Amiko Pay.

    Amiko Pay is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Amiko Pay is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Amiko Pay. If not, see <http://www.gnu.org/licenses/>.
*/

#ifndef {2}
#define {2}

class {3}
{{
public:
	/*
	Constructed object:

	Exceptions:
	*/
	{3}();

	~{3}();

}};

#endif

""".format(hFilename, year, preprocessorConst, className)


cppContents = \
"""/*
    {0}
    Copyright (C) {1} by <author>

    This file is part of Amiko Pay.

    Amiko Pay is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Amiko Pay is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Amiko Pay. If not, see <http://www.gnu.org/licenses/>.
*/

#include "{2}"


{3}::{3}()
{{
}}

{3}::~{3}()
{{
}}

""".format(cppFilename, year, hFilename, className)

print "header filename: ", hFilename
print "implementation filename: ", cppFilename
print "class name: ", className
answer = raw_input("OK (y/n)? ")

if answer.lower() != 'y':
	raise Exception("terminated by user")

if os.path.exists(hFilename):
	raise Exception(hFilename + " already exists")

if os.path.exists(cppFilename):
	raise Exception(cppFilename + " already exists")

with open(hFilename, "wb") as f:
	f.write(hContents)

with open(cppFilename, "wb") as f:
	f.write(cppContents)

