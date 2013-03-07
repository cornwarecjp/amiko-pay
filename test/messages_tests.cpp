/*
    messages_tests.cpp
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

#include "messages.h"

#include "test.h"

/*
TODO: document and expand
*/
class CMessagesTest : public CTest
{
	virtual void run()
	{
		printf("Messages tests:\n");
		testPublicKeyMessage();
	}

	void testPublicKeyMessage()
	{
		CKey source, destination;
		source.makeNewKey();
		destination.makeNewKey();

		//Construct the message
		CMyPublicKeyMessage startMessage;
		startMessage.m_Source = source;
		startMessage.m_Destination.setPublicKey(destination.getPublicKey());
		startMessage.m_lastSentByMe     = CSHA256(CBinBuffer("Hello"));
		startMessage.m_lastAcceptedByMe = CSHA256(CBinBuffer("Goodbye"));
		startMessage.m_Timestamp = 42;
		startMessage.m_PublicKey = source.getPublicKey();
		startMessage.sign();

		//Serialize the message
		CBinBuffer serializedMessage = startMessage.serialize();
		//printf("Message: %s\n\n", serializedMessage.hexDump().c_str());

		//Reconstruct message from serialized data
		CMessage *_endMessage = CMessage::constructMessage(serializedMessage);

		test("  PublicKeyMessage serialization conserves message type",
			_endMessage->getTypeID() == startMessage.getTypeID());
		//TODO: check whether the messages are equal

		//Delete constructed message
		delete _endMessage;
	}

} messagesTest;


