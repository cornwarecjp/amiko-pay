/*
    cstring_tests.cpp
    Copyright (C) 2013 by CJP

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

#include <cstdio>

#include "cstring.h"
#include "test.h"

/*
TODO: document and expand
*/
class CStringTest : public CTest
{
	virtual const char *getName() const
		{return "cstring";}

	virtual void run()
	{
		{
			std::string data[] = {"a", "b", "c", "NULL"};
			testSplit("a b c", data);
		}

		{
			std::string data[] = {"a", "b", "c", "NULL"};
			testSplit("  a   b   c  ", data);
		}

		{
			std::string data[] = {"a b", "c", "NULL"};
			testSplit("#a b# #c#", data);
		}

		{
			std::string data[] = {"a b", "c", "NULL"};
			testSplit("#a b##c#", data);
		}

		{
			std::string data[] = {"a b", "c", "NULL"};
			testSplit("  #a b# #c#  ", data);
		}
	}

	void testSplit(const CString &str, std::string *data)
	{
		std::vector<CString> items = str.split(' ', true, '#');

		bool ok = true;
		size_t i = 0;
		while(true)
		{
			if(data[i] == "NULL") break;

			if(items[i] != CString(data[i]))
			{
				ok = false;
				break;
			}

			i++;
		}
		ok = ok && i == items.size();

		test("  Split", ok);
	}

} stringTest;

