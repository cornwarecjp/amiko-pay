/*
    routetable.cpp
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

#include <limits>
#include <algorithm>

#include "routetable.h"

CRouteTableEntry::CRouteTableEntry() :
	//Initialize as worst-possible route:
	m_minHopCount(std::numeric_limits<uint16_t>::max()),
	m_maxSendHopCount(std::numeric_limits<uint16_t>::max()),
	m_maxReceiveHopCount(std::numeric_limits<uint16_t>::max()),
	m_maxSend(0),
	m_maxReceive(0)
{
}


CRouteTableEntry::CRouteTableEntry(
	const std::vector<CRouteTableEntry> &entries) :
		//Initialize as worst-possible route:
		m_minHopCount(std::numeric_limits<uint32_t>::max()),
		m_maxSendHopCount(std::numeric_limits<uint32_t>::max()),
		m_maxReceiveHopCount(std::numeric_limits<uint32_t>::max()),
		m_maxSend(0),
		m_maxReceive(0)
{
	for(size_t i=0; i < entries.size(); i++)
	{
		//The shortest route to destination:
		m_minHopCount = std::min(m_minHopCount, entries[i].m_minHopCount);

		//Max amount to send and corresponding hop count:
		if(entries[i].m_maxSend == m_maxSend)
		{
			m_maxSendHopCount = std::min(
				m_maxSendHopCount, entries[i].m_maxSendHopCount);
		}
		else if(entries[i].m_maxSend > m_maxSend)
		{
			m_maxSendHopCount = entries[i].m_maxSendHopCount;
			m_maxSend = entries[i].m_maxSend;
		}

		//Max amount to receive and corresponding hop count:
		if(entries[i].m_maxReceive == m_maxReceive)
		{
			m_maxReceiveHopCount = std::min(
				m_maxReceiveHopCount, entries[i].m_maxReceiveHopCount);
		}
		else if(entries[i].m_maxReceive > m_maxReceive)
		{
			m_maxReceiveHopCount = entries[i].m_maxReceiveHopCount;
			m_maxReceive = entries[i].m_maxReceive;
		}
	}

	//Include ourselves in the hop count:
	m_minHopCount++;
	m_maxSendHopCount++;
	m_maxReceiveHopCount++;
}


CRouteTable::CRouteTable()
{
}


CRouteTable::CRouteTable(const std::vector<CRouteTable> &tables)
{
	std::set<CBinBuffer> destinations;
	for(size_t i=0; i < tables.size(); i++)
	{
		const CRouteTable &t = tables[i];
		for(CRouteTable::const_iterator j = t.begin(); j != t.end(); j++)
			destinations.insert(j->first);
	}

	for(std::set<CBinBuffer>::iterator dest=destinations.begin();
		dest != destinations.end(); dest++)
	{
		std::vector<CRouteTableEntry> routes;

		for(size_t i=0; i < tables.size(); i++)
		{
			CRouteTable::const_iterator iter = tables[i].find(*dest);
			if(iter != tables[i].end())
				routes.push_back(iter->second);
		}

		CRouteTableEntry mergedRouteInfo(routes);

		(*this)[*dest] = mergedRouteInfo;
	}
}


void CRouteTable::updateRoute(const CRIPEMD160 &destination, const CRouteTableEntry &entry)
{
	(*this)[destination.toBinBuffer()] = entry;
	m_ChangedDestinations.insert(destination.toBinBuffer());

	//TODO: remove unimportant entries from the route table
}

