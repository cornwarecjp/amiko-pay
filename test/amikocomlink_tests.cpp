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
				CMessage *msg = c2->receiveMessageDirect();
				c2->sendMessageDirect(*msg);
			}
			catch(CTCPConnection::CTimeoutException &e)
			{
				CTimer::sleep(50); //50 ms
			}
			catch(CTCPConnection::CReceiveException &e)
			{
				//Connection closed or other error: stop
				break;
			}
		}

		delete c2;
	}
} amikoComLinkTestServer;


void receiveMessage(void *arg);


class CAmikoComLinkTest : public CTest
{
	virtual const char *getName()
		{return "amikocomlink";}

	virtual void run()
	{
		amikoComLinkTestServer.start();

		//Wait some time to make "sure" the server is initialized
		CTimer::sleep(50); //50 ms

		CAmikoComLink *c1 = new CAmikoComLink(CURI("amikolink://localhost"));

		{
			CNackMessage nack1; nack1.m_reason = "test";
			c1->sendMessageDirect(nack1);
			CTimer::sleep(100); //100 ms
			CMessage *msg = c1->receiveMessageDirect();
			test("  Message transmission preserves type",
				msg->getTypeID() == CMessage::eNack);
			CNackMessage *nack2 = (CNackMessage *)msg;
			test("  Message transmission preserves contents",
				nack2->m_reason == nack1.m_reason);
			delete msg;
		}

		test("  Timeout exception occurs when no message is available",
			throws<CTCPConnection::CTimeoutException>(receiveMessage, c1));

		delete c1;

		amikoComLinkTestServer.stop();
	}
} amikoComLinkTest;


void receiveMessage(void *arg)
{
	CAmikoComLink *c = (CAmikoComLink *)arg;
	CMessage *msg = c->receiveMessageDirect();
	delete msg;
}

