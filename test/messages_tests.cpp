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
	virtual const char *getName()
		{return "messages";	}

	virtual void run()
	{
		testPublicKeyMessage();
	}

	void testPublicKeyMessage()
	{
		CKey source, destination;
		source.makeNewKey();
		destination.makeNewKey();

		//Construct the message
		CPublicKeyMessage startMessage;
		startMessage.m_source = CSHA256(source.getPublicKey());
		startMessage.m_destination = CSHA256(destination.getPublicKey());
		startMessage.m_lastSentBySource     = CSHA256(CBinBuffer("Hello"));
		startMessage.m_lastAcceptedBySource = CSHA256(CBinBuffer("Goodbye"));
		startMessage.m_Timestamp = 42;
		startMessage.m_publicKey = source.getPublicKey();
		startMessage.sign(source);

		//Serialize the message
		CBinBuffer serializedMessage = startMessage.serialize();
		//printf("Message: %s\n\n", serializedMessage.hexDump().c_str());

		//Reconstruct message from serialized data
		CMessage *endMessage = CMessage::constructMessage(serializedMessage);

		test("  PublicKeyMessage serialization conserves message type",
			endMessage->getTypeID() == startMessage.getTypeID());
		test("  PublicKeyMessage serialization conserves source address",
			endMessage->m_source == startMessage.m_source);
		test("  PublicKeyMessage serialization conserves destination address",
			endMessage->m_destination == startMessage.m_destination);
		test("  PublicKeyMessage serialization conserves signature",
			endMessage->m_Signature == startMessage.m_Signature);
		test("  PublicKeyMessage serialization conserves last sent hash",
			endMessage->m_lastSentBySource == startMessage.m_lastSentBySource);
		test("  PublicKeyMessage serialization conserves last accepted hash",
			endMessage->m_lastAcceptedBySource == startMessage.m_lastAcceptedBySource);
		test("  PublicKeyMessage serialization conserves timestamp",
			endMessage->m_Timestamp == startMessage.m_Timestamp);

		test("  PublicKeyMessage serialization conserves public key",
			((CPublicKeyMessage *)endMessage)->m_publicKey == startMessage.m_publicKey);

		//Delete constructed message
		delete endMessage;
	}

} messagesTest;


