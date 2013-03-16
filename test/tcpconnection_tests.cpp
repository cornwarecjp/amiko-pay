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

private:
	CTCPListener m_Listener;

	virtual const char *getName()
		{return "tcpconnection";}

	virtual void run()
	{
		CTCPConnection *c1 = new CTCPConnection("localhost", "4321");
		CTCPConnection *c2 = new CTCPConnection(m_Listener);

		c1->send(CBinBuffer("blabla"));

		CBinBuffer result; result.resize(6);
		c2->receive(result, 1); //1 ms timeout
		test("  CTCPConnection transfers data", result.toString() == "blabla");

		//Delete in the correct order, to allow release of the port number
		delete c1;
		//sleep(1);
		delete c2;
	}

} tcpconnectionTest;

