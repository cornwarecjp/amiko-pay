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

#include "bitcoinaddress.h"

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
		testRouteInfoMessage();
		testFinStateMessage();
	}


	void testHelloMessage()
	{
		//Construct the message
		CHelloMessage startMessage;
		startMessage.m_myPublicKey = m_source.getPublicKey();
		startMessage.m_myPreferredURL = CString("amikolink://localhost/") +
			getBitcoinAddress(m_source);
		startMessage.m_yourAddress = getBitcoinAddress(m_destination);
		setBaseMembervalues(startMessage);

		//Serialize the message
		CBinBuffer serializedMessage = startMessage.serialize();

		//Reconstruct message from serialized data
		CMessage *endMessage = CMessage::constructMessage(serializedMessage);

		test("  CHelloMessage serialization conserves CMessage members",
			baseMembersAreEqual(&startMessage, endMessage));
		CHelloMessage *endMessage2 = (CHelloMessage *)endMessage;
		test("  CHelloMessage serialization conserves public key",
			endMessage2->m_myPublicKey == startMessage.m_myPublicKey);
		test("  CHelloMessage serialization conserves preferred URL",
			endMessage2->m_myPreferredURL == startMessage.m_myPreferredURL);
		test("  CHelloMessage serialization conserves address",
			endMessage2->m_yourAddress == startMessage.m_yourAddress);

		//Delete constructed message
		delete endMessage;
	}


	void testAckMessage()
	{
		//Construct the message
		CAckMessage startMessage;
		startMessage.m_acceptedBySource = CSHA256(CBinBuffer("your money is yours"));

		//Serialize the message
		CBinBuffer serializedMessage = startMessage.serialize();

		//Reconstruct message from serialized data
		CMessage *endMessage = CMessage::constructMessage(serializedMessage);

		test("  CAckMessage serialization conserves CMessage members",
			baseMembersAreEqual(&startMessage, endMessage));
		CAckMessage *endMessage2 = (CAckMessage *)endMessage;
		test("  CAckMessage serialization conserves accepted hash",
			endMessage2->m_acceptedBySource == startMessage.m_acceptedBySource);

		//Delete constructed message
		delete endMessage;
	}


	void testNackMessage()
	{
		//Construct the message
		CNackMessage startMessage;
		startMessage.m_acceptedBySource = CSHA256(CBinBuffer("your money is yours"));
		startMessage.m_rejectedBySource = CSHA256(CBinBuffer("give me all your money"));
		startMessage.m_reasonCode = CNackMessage::eNonstandardReason;
		startMessage.m_reason = "I want to keep it for myself";
		setBaseMembervalues(startMessage);

		//Serialize the message
		CBinBuffer serializedMessage = startMessage.serialize();

		//Reconstruct message from serialized data
		CMessage *endMessage = CMessage::constructMessage(serializedMessage);

		test("  CNackMessage serialization conserves CMessage members",
			baseMembersAreEqual(&startMessage, endMessage));
		CNackMessage *endMessage2 = (CNackMessage *)endMessage;
		test("  CNackMessage serialization conserves accepted hash",
			endMessage2->m_acceptedBySource == startMessage.m_acceptedBySource);
		test("  CNackMessage serialization conserves rejected hash",
			endMessage2->m_rejectedBySource == startMessage.m_rejectedBySource);
		test("  CNackMessage serialization conserves reason code",
			endMessage2->m_reasonCode == startMessage.m_reasonCode);
		test("  CNackMessage serialization conserves reason text",
			endMessage2->m_reason == startMessage.m_reason);

		//Delete constructed message
		delete endMessage;
	}


	void testRouteInfoMessage()
	{
		//Construct the message
		CRouteTableEntry info1, info2;
		info1.m_minHopCount = 1;
		info1.m_maxSendHopCount = 3;
		info1.m_maxReceiveHopCount = 2;
		info1.m_maxSend = 2100000000000000;
		info1.m_maxReceive = 300000000;
		info2.m_minHopCount = 42;
		info2.m_maxSendHopCount = 1234;
		info2.m_maxReceiveHopCount = 4321;
		info2.m_maxSend = 4000000000;
		info2.m_maxReceive = 42000000;
		CRouteInfoMessage startMessage;
		startMessage.m_entries.push_back(
			std::pair<CRIPEMD160, CRouteTableEntry>(
				CRIPEMD160(CBinBuffer("meetingpoint 1")), info1
			));
		startMessage.m_entries.push_back(
			std::pair<CRIPEMD160, CRouteTableEntry>(
				CRIPEMD160(CBinBuffer("meetingpoint 2")), info2
			));
		setBaseMembervalues(startMessage);

		//Serialize the message
		CBinBuffer serializedMessage = startMessage.serialize();

		//Reconstruct message from serialized data
		CMessage *endMessage = CMessage::constructMessage(serializedMessage);

		test("  CRouteInfoMessage serialization conserves CMessage members",
			baseMembersAreEqual(&startMessage, endMessage));
		CRouteInfoMessage *endMessage2 = (CRouteInfoMessage *)endMessage;
		test("  CRouteInfoMessage serialization conserves number of entries",
			endMessage2->m_entries.size() == startMessage.m_entries.size());
		for(size_t i=0; i < startMessage.m_entries.size(); i++)
		{
			test("  CRouteInfoMessage serialization conserves meeting point",
				endMessage2->m_entries[i].first == startMessage.m_entries[i].first);
			test("  CRouteInfoMessage serialization conserves min hop count",
				endMessage2->m_entries[i].second.m_minHopCount ==
				startMessage.m_entries[i].second.m_minHopCount);
			test("  CRouteInfoMessage serialization conserves max send hop count",
				endMessage2->m_entries[i].second.m_maxSendHopCount ==
				startMessage.m_entries[i].second.m_maxSendHopCount);
			test("  CRouteInfoMessage serialization conserves max receive hop count",
				endMessage2->m_entries[i].second.m_maxReceiveHopCount ==
				startMessage.m_entries[i].second.m_maxReceiveHopCount);
			test("  CRouteInfoMessage serialization conserves max send",
				endMessage2->m_entries[i].second.m_maxSend ==
				startMessage.m_entries[i].second.m_maxSend);
			test("  CRouteInfoMessage serialization conserves max receive",
				endMessage2->m_entries[i].second.m_maxReceive ==
				startMessage.m_entries[i].second.m_maxReceive);
		}

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
		msg.m_source      = CRIPEMD160(CSHA256(m_source.getPublicKey()).toBinBuffer());
		msg.m_destination = CRIPEMD160(CSHA256(m_destination.getPublicKey()).toBinBuffer());
		msg.m_previousMessage = CSHA256(CBinBuffer("Hello"));
		msg.m_timestamp = 42;
		msg.sign(m_source);
	}


	bool baseMembersAreEqual(const CMessage *msg1, const CMessage *msg2) const
	{
		if(msg1->getTypeID() != msg2->getTypeID()) return false;
		if(msg1->m_source != msg2->m_source) return false;
		if(msg1->m_destination != msg2->m_destination) return false;
		if(msg1->m_signature != msg2->m_signature) return false;
		if(msg1->m_previousMessage != msg2->m_previousMessage) return false;
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


