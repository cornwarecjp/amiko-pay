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

#include "binbuffer.h"
#include "ripemd160.h"

class CRouteTableEntry
{
public:
	unsigned int m_expectedHopCount;
	uint64_t m_expectedMaxSend;
	uint64_t m_expectedMaxReceive;
};


class CRouteTable : public std::map<CBinBuffer, CRouteTableEntry>
{
public:

	//TODO: spec
	void updateRoute(const CRIPEMD160 &node, const CRouteTableEntry &entry);

	std::set<CBinBuffer> m_ChangedRoutes;
};

#endif

