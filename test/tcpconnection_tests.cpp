/*
    tcpconnection_tests.cpp
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

#include <unistd.h>

#include "tcpconnection.h"
#include "tcplistener.h"
#include "test.h"

/*
TODO: document and expand
*/
class CTCPConnectionTest : public CTest
{
public:
	CTCPConnectionTest() : m_Listener("4321") {}

	~CTCPConnectionTest()
	{
		//Some time before deleting the listener, to make sure all open
		//connections are cleaned up, so the port can be released
		sleep(1);
	}


private:
	CTCPListener m_Listener;

	virtual const char *getName()
		{return "tcpconnection";}

	virtual void run()
	{
		{
			CTCPConnection c1("localhost", "4321");
			CTCPConnection c2(m_Listener);

			c1.send(CBinBuffer("blabla"));

			//Some time to allow the message to arrive
			sleep(1);

			CBinBuffer result; result.resize(6);
			c2.receive(result);
			test("  CTCPConnection transfers data", result.toString() == "blabla");
		}

	}
} tcpconnectionTest;

