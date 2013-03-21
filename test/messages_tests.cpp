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
	CKey m_source, m_destination;


	virtual const char *getName()
		{return "messages";	}


	virtual void run()
	{
		m_source.makeNewKey();
		m_destination.makeNewKey();

		testHelloMessage();
		testAckMessage();
		testNackMessage();
		testFinStateMessage();
	}


	void testHelloMessage()
	{
		//Construct the message
		CHelloMessage startMessage;
		startMessage.m_publicKey = m_source.getPublicKey();
		setBaseMembervalues(startMessage);

		//Serialize the message
		CBinBuffer serializedMessage = startMessage.serialize();

		//Reconstruct message from serialized data
		CMessage *endMessage = CMessage::constructMessage(serializedMessage);

		test("  CHelloMessage serialization conserves CMessage members",
			baseMembersAreEqual(&startMessage, endMessage));
		test("  CHelloMessage serialization conserves public key",
			((CHelloMessage *)endMessage)->m_publicKey == startMessage.m_publicKey);

		//Delete constructed message
		delete endMessage;
	}


	void testAckMessage()
	{
		//Construct the message
		CAckMessage startMessage;

		//Serialize the message
		CBinBuffer serializedMessage = startMessage.serialize();

		//Reconstruct message from serialized data
		CMessage *endMessage = CMessage::constructMessage(serializedMessage);

		test("  CAckMessage serialization conserves CMessage members",
			baseMembersAreEqual(&startMessage, endMessage));

		//Delete constructed message
		delete endMessage;
	}


	void testNackMessage()
	{
		//Construct the message
		CNackMessage startMessage;
		startMessage.m_rejectedBySource = CSHA256(CBinBuffer("give me all your money"));
		startMessage.m_reasonCode = CNackMessage::eWrongBalance;
		startMessage.m_reason = "I want to keep it for myself";
		setBaseMembervalues(startMessage);

		//Serialize the message
		CBinBuffer serializedMessage = startMessage.serialize();

		//Reconstruct message from serialized data
		CMessage *endMessage = CMessage::constructMessage(serializedMessage);

		test("  CNackMessage serialization conserves CMessage members",
			baseMembersAreEqual(&startMessage, endMessage));
		CNackMessage *endMessage2 = (CNackMessage *)endMessage;
		test("  CNackMessage serialization conserves rejected hash",
			endMessage2->m_rejectedBySource == startMessage.m_rejectedBySource);
		test("  CNackMessage serialization conserves reason code",
			endMessage2->m_reasonCode == startMessage.m_reasonCode);
		test("  CNackMessage serialization conserves reason text",
			endMessage2->m_reason == startMessage.m_reason);

		//Delete constructed message
		delete endMessage;
	}


	void testFinStateMessage()
	{
		//Construct the message
		CFinStateMessage startMessage;
		startMessage.m_myBalance   = -12.4 * 100000000;
		startMessage.m_yourBalance = 100.4 * 100000000;
		startMessage.m_pendingTransactions.push_back(CSHA256(CBinBuffer("transaction 1")));
		startMessage.m_pendingTransactions.push_back(CSHA256(CBinBuffer("transaction 2")));
		startMessage.m_pendingTransactions.push_back(CSHA256(CBinBuffer("transaction 3")));
		startMessage.m_myPendingDeposits.push_back(CSHA256(CBinBuffer("deposit 1")));
		startMessage.m_myPendingDeposits.push_back(CSHA256(CBinBuffer("deposit 2")));
		startMessage.m_yourPendingDeposits.push_back(CSHA256(CBinBuffer("deposit 3")));
		setBaseMembervalues(startMessage);

		//Serialize the message
		CBinBuffer serializedMessage = startMessage.serialize();

		//Reconstruct message from serialized data
		CMessage *endMessage = CMessage::constructMessage(serializedMessage);

		test("  CFinStateMessage serialization conserves CMessage members",
			baseMembersAreEqual(&startMessage, endMessage));
		CFinStateMessage *endMessage2 = (CFinStateMessage *)endMessage;
		test("  CFinStateMessage serialization conserves my balance",
			endMessage2->m_myBalance == startMessage.m_myBalance);
		test("  CFinStateMessage serialization conserves your balance",
			endMessage2->m_yourBalance == startMessage.m_yourBalance);
		test("  CFinStateMessage serialization conserves pending transactions",
			hashVectorsAreEqual(endMessage2->m_pendingTransactions, startMessage.m_pendingTransactions));
		test("  CFinStateMessage serialization conserves my pending deposits",
			hashVectorsAreEqual(endMessage2->m_myPendingDeposits, startMessage.m_myPendingDeposits));
		test("  CFinStateMessage serialization conserves your pending deposits",
			hashVectorsAreEqual(endMessage2->m_yourPendingDeposits, startMessage.m_yourPendingDeposits));

		//Delete constructed message
		delete endMessage;
	}


	void setBaseMembervalues(CMessage &msg)
	{
		msg.m_source      = CSHA256(m_source.getPublicKey());
		msg.m_destination = CSHA256(m_destination.getPublicKey());
		msg.m_lastSentBySource     = CSHA256(CBinBuffer("Hello"));
		msg.m_lastAcceptedBySource = CSHA256(CBinBuffer("Goodbye"));
		msg.m_timestamp = 42;
		msg.sign(m_source);
	}


	bool baseMembersAreEqual(const CMessage *msg1, const CMessage *msg2) const
	{
		if(msg1->getTypeID() != msg2->getTypeID()) return false;
		if(msg1->m_source != msg2->m_source) return false;
		if(msg1->m_destination != msg2->m_destination) return false;
		if(msg1->m_signature != msg2->m_signature) return false;
		if(msg1->m_lastSentBySource != msg2->m_lastSentBySource) return false;
		if(msg1->m_lastAcceptedBySource != msg2->m_lastAcceptedBySource) return false;
		if(msg1->m_timestamp != msg2->m_timestamp) return false;
		return true;
	}


	bool hashVectorsAreEqual(const std::vector<CSHA256> &v1, const std::vector<CSHA256> &v2) const
	{
		if(v1.size() != v2.size()) return false;
		for(size_t i=0; i < v1.size(); i++)
			if(v1[i] != v2[i])
				return false;
		return true;
	}

} messagesTest;


