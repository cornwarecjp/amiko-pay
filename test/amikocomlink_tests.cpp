/*
    key_tests.cpp
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

#include "amikocomlink.h"
#include "tcplistener.h"
#include "cthread.h"

#include "test.h"

/*
TODO: document and expand
*/

class CAmikoComLinkTestServer : public CThread
{
	void threadFunc()
	{
		CTCPListener listener(AMIKO_DEFAULT_PORT);
		CAmikoComLink *c2 = new CAmikoComLink(listener);

		//100 ms
		usleep(100000);

		delete c2;
	}
} amikoComLinkTestServer;


class CAmikoComLinkTest : public CTest
{
	virtual const char *getName()
		{return "amikocomlink";}

	virtual void run()
	{
		amikoComLinkTestServer.start();

		//50 ms
		usleep(50000);

		CAmikoComLink *c1 = new CAmikoComLink(CURI("amikolink://localhost"));
		delete c1;

		amikoComLinkTestServer.stop();
	}
} amikoComLinkTest;

