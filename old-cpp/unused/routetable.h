/*
    routetable.h
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

#ifndef ROUTETABLE_H
#define ROUTETABLE_H

#include <stdint.h>

#include <map>
#include <set>
#include <vector>

#include "binbuffer.h"
#include "ripemd160.h"

class CRouteTableEntry
{
public:
	/*
	Constructed object:
	Route table entry with 'worst-possible' route

	Exceptions:
	none
	*/
	CRouteTableEntry();

	/*
	entries:
	Reference to properly formed object (NOT CHECKED)
	Reference lifetime: at least until the end of this function

	Constructed object:
	Merge of the given entries, and increments the hop count

	Exceptions:
	none
	*/
	CRouteTableEntry(const std::vector<CRouteTableEntry> &entries);

	/*
	e2:
	Reference to properly formed CRouteTableEntry object (NOT CHECKED)
	Reference lifetime: at least until the end of this function

	Exceptions:
	none
	*/
	bool operator==(const CRouteTableEntry &e2) const;

	/*
	e2:
	Reference to properly formed CRouteTableEntry object (NOT CHECKED)
	Reference lifetime: at least until the end of this function

	Exceptions:
	none
	*/
	inline bool operator!=(const CRouteTableEntry &e2) const
		{return !operator==(e2);}


	uint16_t m_minHopCount;        //expected hop count at zero amount
	uint16_t m_maxSendHopCount;    //expected hop count at max send amount
	uint16_t m_maxReceiveHopCount; //expected hop count at max receive amount

	uint64_t m_maxSend;     //expected maximum send capacity
	uint64_t m_maxReceive;  //expected maximum receive capacity
};


class CRouteTable : public std::map<CBinBuffer, CRouteTableEntry>
{
public:
	/*
	Constructed object:
	Empty route table

	Exceptions:
	none
	*/
	CRouteTable();

	/*
	tables:
	Reference to properly formed object (NOT CHECKED)
	Reference lifetime: at least until the end of this function

	Constructed object:
	Merge of the given tables, with incremented hop count
	m_ChangedDestinations is empty

	Exceptions:
	none
	*/
	CRouteTable(const std::vector<CRouteTable> &tables);

	/*
	destination:
	Reference to properly formed CRIPEMD160 object (NOT CHECKED)
	Reference lifetime: at least until the end of this function

	entry:
	Reference to properly formed CRouteTableEntry object (NOT CHECKED)
	Reference lifetime: at least until the end of this function

	Exceptions:
	none
	*/
	void updateRoute(const CRIPEMD160 &destination, const CRouteTableEntry &entry);


	std::set<CBinBuffer> m_ChangedDestinations;
};

#endif

