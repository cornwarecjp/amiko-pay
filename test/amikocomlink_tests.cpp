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
#include "messages.h"

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

		//Continue echoeing until stop() is called
		while(!m_terminate)
		{
			try
			{
				CMessage *msg = c2->receiveMessage();
				c2->sendMessage(*msg);
			}
			catch(CTCPConnection::CTimeoutException &e)
			{
				usleep(50000); //50 ms
			}
		}

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

		//Wait some time to make "sure" the server is initialized
		usleep(50000); //50 ms

		CAmikoComLink *c1 = new CAmikoComLink(CURI("amikolink://localhost"));

		{
			CNackMessage nack1; nack1.m_reason = "test";
			c1->sendMessage(nack1);
			usleep(100000); //100 ms
			CMessage *msg = c1->receiveMessage();
			test("  Message transmission preserves type",
				msg->getTypeID() == CMessage::eNack);
			CNackMessage *nack2 = (CNackMessage *)msg;
			test("  Message transmission preserves contents",
				nack2->m_reason == nack1.m_reason);
			delete msg;
		}

		delete c1;

		amikoComLinkTestServer.stop();
	}
} amikoComLinkTest;

