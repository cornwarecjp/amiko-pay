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

#include "amikocomlink.h"
#include "tcplistener.h"
#include "cthread.h"
#include "messages.h"
#include "timer.h"

#include "test.h"

/*
TODO: document and expand
*/

void receiveMessage(void *arg);


class CAmikoComLinkTest : public CTest
{
	virtual const char *getName()
		{return "amikocomlink";}

	virtual void run()
	{
		CTCPListener listener(AMIKO_DEFAULT_PORT);

		CAmikoComLink *c1 = new CAmikoComLink(CURI("amikolink://localhost"));

		CAmikoComLink *c2 = new CAmikoComLink(listener);
		c2->setReceiver(c2); //loop-back
		c2->start();

		c1->initialize();

		{
			c1->sendMessageDirect(CBinBuffer("test"));
			CTimer::sleep(100); //100 ms
			CBinBuffer msg = c1->receiveMessageDirect();
			test("  Message transmission preserves contents",
				msg.toString() == "test");
		}

		test("  NoDataAvailable exception occurs when no message is available",
			throws<CComLink::CNoDataAvailable>(receiveMessage, c1));

		delete c1;

		c2->setReceiver(NULL);
		c2->stop();
		delete c2;
	}
} amikoComLinkTest;


void receiveMessage(void *arg)
{
	CAmikoComLink *c = (CAmikoComLink *)arg;
	CBinBuffer msg = c->receiveMessageDirect();
}

