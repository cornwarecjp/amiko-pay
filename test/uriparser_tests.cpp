/*
    uriparser_tests.cpp
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

#include "uriparser.h"
#include "test.h"

void getPort(void *arg)
{
	((CURI *)arg)->getPort();
}

/*
TODO: document and expand
*/
class CUriParserTest : public CTest
{
	virtual const char *getName()
		{return "uri";}

	virtual void run()
	{
		CURI url1("scheme://host.domain:1234/foo/bar");
		test("  Scheme is found", url1.getScheme() == "scheme");
		test("  Host is found", url1.getHost() == "host.domain");
		test("  Port is found", url1.getPort() == "1234");
		test("  Present port does not equal default value",
			url1.getPort("42") == "1234");

		CURI url2("scheme://host.domain/foo/bar");
		test("  Request missing port gives exception",
			throws<CURI::CNotFound>(getPort, &url2)
			);
		test("  Missing port is given default value",
			url2.getPort("1234") == "1234");
	}
} uriParserTest;

