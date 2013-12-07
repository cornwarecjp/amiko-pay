/*
    file_tests.cpp
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

#include <set>

#include "file.h"
#include "test.h"

/*
TODO: document and expand
*/
class CFileTest : public CTest
{
	virtual const char *getName()
		{return "file";}

	virtual void run()
	{
		//Note: this depends on the directory where the test is run
		//The assumption is that this is the root source tree
		std::vector<CString> contents = CFile::getDirectoryContents(".");

		//std::set has a convenient find method
		std::set<CString> contents_set(contents.begin(), contents.end());

		test("  . is in directory contents",
			contents_set.find(".") != contents_set.end());
		test("  COPYING is in directory contents",
			contents_set.find("COPYING") != contents_set.end());
		test("  test is in directory contents",
			contents_set.find("test") != contents_set.end());
	}


} fileTest;

