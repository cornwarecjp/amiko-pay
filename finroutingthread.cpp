/*
    finroutingthread.cpp
    Copyright (C) 2013-2014 by CJP

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

#include <limits>

#include "timer.h"
#include "log.h"
#include "exception.h"
#include "messages.h"
#include "ripemd160.h"
#include "sha256.h"

#include "finroutingthread.h"


CFinRoutingThread::CFinRoutingThread(CAmiko *amiko) :
	m_Amiko(amiko),
	m_OutgoingPayLink(NULL)
{
}

CFinRoutingThread::~CFinRoutingThread()
{
}


void CFinRoutingThread::threadFunc()
{
	//initializeRoutingTable();

	while(!m_terminate)
	{
		try
		{
			//every iteration takes 1 ms
			CTimer::sleep(1);

			processIncomingMessages();
			//processRoutingChanges();
			searchForNewPayLinks();
		}
		catch(CException &e)
		{
			log(CString::format(
				"CFinRoutingThread: Caught application exception: %s\n",
				256, e.what()));
		}
		catch(std::exception &e)
		{
			log(CString::format(
				"CFinRoutingThread: Caught standard library exception: %s\n",
				256, e.what()));
		}
	}

	{
		CMutexLocker lock(m_PayLinks);
		for(std::list<CPayLink *>::iterator i=m_PayLinks.m_Value.begin();
			i != m_PayLinks.m_Value.end(); i++)
		{
			(*i)->stop();
			delete (*i);
		}
		m_PayLinks.m_Value.clear();
	}
}


void CFinRoutingThread::doPayment(CPayLink &link)
{
	{
		CMutexLocker lock(m_OutgoingPayLink);

		if(m_OutgoingPayLink.m_Value != NULL)
			throw CPaymentFailed(
				"Payment failed: another payment is already being performed");

		m_OutgoingPayLink.m_Value = &link;
	}

	//TODO: wait until the link is finished or failed

	{
		CMutexLocker lock(m_OutgoingPayLink);
		m_OutgoingPayLink.m_Value = NULL;
	}
}


/*
void CFinRoutingThread::initializeRoutingTable()
{
	//TODO: more efficient memory usage

	std::vector<CRouteTable> tables;
	tables.resize(m_Amiko->m_FinLinks.size());

	for(size_t i=0; i < m_Amiko->m_FinLinks.size(); i++)
	{
		CMutexLocker lock(m_Amiko->m_FinLinks[i]->m_RouteTable);
		CRouteTable &linkTable = m_Amiko->m_FinLinks[i]->m_RouteTable.m_Value;
		tables[i] = linkTable;
	}

	//Routes through links:
	m_RouteTable = CRouteTable(tables);

	//Route to own meeting point:
	CAmikoSettings settings = m_Amiko->getSettings();
	CBinBuffer &ownMeetinPointPubKey = settings.m_MeetingPointPubKey;
	if(!ownMeetinPointPubKey.empty())
	{
		CRIPEMD160 address(CSHA256(ownMeetinPointPubKey).toBinBuffer());
		CRouteTableEntry entry;
		entry.m_minHopCount = 1;
		entry.m_maxSendHopCount = 1;
		entry.m_maxReceiveHopCount = 1;
		//Note: maximum amounts will be limited by the interface maxima
		//TODO: maybe make these equal to "21 million BTC"?
		entry.m_maxSend = std::numeric_limits<uint64_t>::max();
		entry.m_maxReceive = std::numeric_limits<uint64_t>::max();
		m_RouteTable.updateRoute(address, entry);
	}

	//Invalidate all entries.
	//The effect is that, on start-up, the entire routing table is re-sent to
	//all neighbors. This is extremely resource-consuming on large networks,
	//but for a prototype it's OK.
	//TODO: replace this with a production-level concept.
	for(CRouteTable::iterator i = m_RouteTable.begin(); i != m_RouteTable.end(); i++)
		m_RouteTable.m_ChangedDestinations.insert(i->first);

	sendRoutingChanges();
}
*/


void CFinRoutingThread::processIncomingMessages()
{
	for(size_t i=0; i < m_Amiko->m_FinLinks.size(); i++)
		m_Amiko->m_FinLinks[i]->processInbox();
}


void CFinRoutingThread::searchForNewPayLinks()
{
	//Receiver-side payments
	{
		CMutexLocker lock(m_PayLinks);
		for(std::list<CPayLink *>::iterator
				i = m_PayLinks.m_Value.begin();
				i != m_PayLinks.m_Value.end(); i++)
			if((*i)->getState() == CPayLink::eOperational)
			{
				bool found = false;
				for(std::list<CActiveTransaction>::iterator
						j = m_activeTransactions.begin();
						j != m_activeTransactions.end(); j++)
					if(j->m_inboundInterface ==
						(*i)->m_transaction.m_commitHash.toBinBuffer()
						&&
						j->m_receiverSide == (*i)->isReceiverSide())
					{
						found = true;
						break;
					}

				if(!found)
					addAndProcessPayLink(*(*i));
			}
	}

	//Sender-side payment
	{
		CMutexLocker lock(m_OutgoingPayLink);
		CPayLink *paylink = m_OutgoingPayLink.m_Value;

		if(paylink != NULL)
		{
			bool found = false;
			for(std::list<CActiveTransaction>::iterator
					j = m_activeTransactions.begin();
					j != m_activeTransactions.end(); j++)
				if(j->m_inboundInterface ==
					paylink->m_transaction.m_commitHash.toBinBuffer()
					&&
					j->m_receiverSide == paylink->isReceiverSide())
				{
					found = true;
					break;
				}

			if(!found)
				addAndProcessPayLink(*paylink);
		}
	}
}


void CFinRoutingThread::addAndProcessPayLink(const CPayLink &link)
{
	log(CString::format("Adding operational link with hash %s\n", 256,
		link.m_transaction.m_commitHash.toBinBuffer().hexDump().c_str()));

	{
		CActiveTransaction t;
		t.m_inboundInterface = link.m_transaction.m_commitHash.toBinBuffer();
		//TODO: set up outbound interfaces
		t.m_amount = link.m_transaction.m_amount;
		t.m_receiverSide = link.isReceiverSide();
		t.m_commitHash = link.m_transaction.m_commitHash;
		t.m_meetingPoint = link.m_transaction.m_meetingPoint;

		m_activeTransactions.push_back(t);
	}

	CActiveTransaction &t = m_activeTransactions.back();
	matchWithOwnMeetingPoint(t);
}


void CFinRoutingThread::matchWithOwnMeetingPoint(CActiveTransaction &t)
{
	CRIPEMD160 meetingpoint(
			CSHA256(m_Amiko->getSettings().m_MeetingPointPubKey).toBinBuffer()
			);

	if(t.m_meetingPoint == meetingpoint)
	{
		log("Transaction arrives at local meeting point\n");

		t.m_remainingOutboundInterfaces.clear();
		t.m_currentOutboundInterface.clear();

		//TODO: match with other-side active transaction, if it exists
	}
}


/*
void CFinRoutingThread::processRoutingChanges()
{
	//All destinations changed by all peers
	std::set<CBinBuffer> changedDestinations;

	for(size_t i=0; i < m_Amiko->m_FinLinks.size(); i++)
	{
		CMutexLocker lock(m_Amiko->m_FinLinks[i]->m_RouteTable);
		CRouteTable &linkTable = m_Amiko->m_FinLinks[i]->m_RouteTable.m_Value;
		changedDestinations.insert(
			linkTable.m_ChangedDestinations.begin(),
			linkTable.m_ChangedDestinations.end());
		linkTable.m_ChangedDestinations.clear();
	}

	//Note: since the FinLink's route tables are unlocked, it is possible they
	//will be changed here by another thread. This is not a problem: the updated
	//data is better anyway, and it will also be processed automatically in the
	//next iteration.

	//Find the best routes for all changed destinations
	for(std::set<CBinBuffer>::iterator dest=changedDestinations.begin();
		dest != changedDestinations.end(); dest++)
	{
		std::vector<CRouteTableEntry> routes;

		for(size_t i=0; i < m_Amiko->m_FinLinks.size(); i++)
		{
			CMutexLocker lock(m_Amiko->m_FinLinks[i]->m_RouteTable);
			CRouteTable &linkTable = m_Amiko->m_FinLinks[i]->m_RouteTable.m_Value;

			CRouteTable::const_iterator iter = linkTable.find(*dest);
			if(iter != linkTable.end())
				routes.push_back(iter->second);
		}

		CRouteTableEntry mergedRouteInfo(routes);

		m_RouteTable.updateRoute(*dest, mergedRouteInfo);
	}

	sendRoutingChanges();
}


void CFinRoutingThread::sendRoutingChanges()
{
	//We're finished if nothing has changed
	if(m_RouteTable.m_ChangedDestinations.empty()) return;

	//Make an update message for our peers:
	CRouteInfoMessage msg;
	for(
		std::set<CBinBuffer>::iterator i = m_RouteTable.m_ChangedDestinations.begin();
		i != m_RouteTable.m_ChangedDestinations.end();
		i++)
	{
		msg.m_entries.push_back(std::pair<CRIPEMD160, CRouteTableEntry>(
			CRIPEMD160::fromBinBuffer(*i),
			m_RouteTable[*i]
			));
	}

	//Send the update to all peers:
	for(size_t i=0; i < m_Amiko->m_FinLinks.size(); i++)
		if(m_Amiko->m_FinLinks[i]->isCompleted())
			m_Amiko->m_FinLinks[i]->sendOutboundMessage(msg);

	//Clear the list of changed destinations,
	//since we've sent the update to all peers
	m_RouteTable.m_ChangedDestinations.clear();
}
*/

