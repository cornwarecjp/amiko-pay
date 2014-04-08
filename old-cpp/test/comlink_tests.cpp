/*
    comlink_tests.cpp
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
#include <vector>

#include "comlink.h"
#include "amikosettings.h"
#include "tcplistener.h"
#include "cthread.h"
#include "messages.h"
#include "timer.h"
#include "bitcoinaddress.h"
#include "uriparser.h"

#include "test.h"

/*
TODO: document and expand
*/

class CTestReceiver : public CComInterface
{
public:
	void sendMessage(const CBinBuffer &message)
	{
		CMutexLocker lock(m_receivedMessages);
		m_receivedMessages.m_Value.push_back(message);
	}

	void clear()
	{
		CMutexLocker lock(m_receivedMessages);
		m_receivedMessages.m_Value.clear();
	}

	std::vector<CBinBuffer> getMessages()
	{
		CMutexLocker lock(m_receivedMessages);
		return m_receivedMessages.m_Value;
	}

	CCriticalSection< std::vector<CBinBuffer> > m_receivedMessages;

} testReceiver;


class CComLinkTest : public CTest
{
	virtual const char *getName() const
		{return "comlink";}

	virtual void run()
	{
		CAmikoSettings settings1, settings2;
		settings1.m_hostname = "localhost";
		settings2.m_hostname = "localhost";
		settings1.m_linkPortNumber = AMIKO_DEFAULT_LINK_PORT;
		settings2.m_linkPortNumber = AMIKO_DEFAULT_LINK_PORT;

		CLinkConfig link1;
		std::vector<CLinkConfig> linkConfig2;
		linkConfig2.resize(1);
		CLinkConfig &link2 = linkConfig2[0];

		link1.m_localKey.makeNewKey();
		link2.m_localKey.makeNewKey();
		link1.m_remoteKey.setPublicKey(link2.m_localKey.getPublicKey());
		link2.m_remoteKey.setPublicKey(link1.m_localKey.getPublicKey());
		link1.m_remoteURI = settings2.getLocalLinkURL(link2.m_localKey);
		link1.m_completed = true;
		link2.m_completed = true;

		//Start listening at TCP port
		CTCPListener listener(settings2.m_linkPortNumber);

		//Connect to TCP port
		CComLink *c1 = new CComLink(link1, settings1);
		c1->setReceiver(&testReceiver);
		c1->start();

		//Accept connection on TCP port and loopback messages
		CComLink *c2 = new CComLink(listener, settings2, linkConfig2);
		c2->setReceiver(c2); //loop-back
		c2->start();

		//wait until initialization is finished:
		while(
			c1->getState() == CComLink::ePending ||
			c2->getState() == CComLink::ePending)
				CTimer::sleep(10); //10 ms

		testReceiver.clear();
		c1->sendMessage(CBinBuffer("test"));
		CTimer::sleep(100); //100 ms
		std::vector<CBinBuffer> msgs = testReceiver.getMessages();
		test("  Message transmission preserves contents",
			msgs.size() == 1 &&
			msgs[0].toString() == "test");

		c1->setReceiver(NULL);
		c1->stop();
		delete c1;

		c2->setReceiver(NULL);
		c2->stop();
		delete c2;
	}
} comLinkTest;


