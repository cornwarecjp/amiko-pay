/*
    finroutingthread.cpp
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

#include "timer.h"
#include "log.h"
#include "exception.h"
#include "messages.h"

#include "finroutingthread.h"


CFinRoutingThread::CFinRoutingThread(CAmiko *amiko) :
	m_Amiko(amiko)
{
	//Initialize routing table:
	//TODO
}

CFinRoutingThread::~CFinRoutingThread()
{
}


void CFinRoutingThread::threadFunc()
{
	initializeRoutingTable();

	while(!m_terminate)
	{
		try
		{
			//every iteration takes 1 ms
			CTimer::sleep(1);

			processIncomingMessages();
			processRoutingChanges();
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
}


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

	m_RouteTable = CRouteTable(tables);
}


void CFinRoutingThread::processIncomingMessages()
{
	for(size_t i=0; i < m_Amiko->m_FinLinks.size(); i++)
		m_Amiko->m_FinLinks[i]->processInbox();
}


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
	{
		m_Amiko->m_FinLinks[i]->sendOutboundMessage(msg);
	}

	//Clear the list of changed destinations,
	//since we've sent the update to all peers
	m_RouteTable.m_ChangedDestinations.clear();
}


