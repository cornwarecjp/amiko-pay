/*
    routetable_tests.cpp
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

#include "routetable.h"
#include "test.h"

/*
TODO: document and expand
*/
class CRouteTableTest : public CTest
{
	virtual const char *getName()
		{return "routetable";}

	virtual void run()
	{
		{
			CRouteTableEntry entry;

			test("  Entry default constructor sets minHopCount correctly",
				entry.m_minHopCount == 0xffff);
			test("  Entry default constructor sets maxSendHopCount correctly",
				entry.m_maxSendHopCount == 0xffff);
			test("  Entry default constructor sets maxReceiveHopCount correctly",
				entry.m_maxReceiveHopCount == 0xffff);
			test("  Entry default constructor sets maxSend correctly",
				entry.m_maxSend == 0);
			test("  Entry default constructor sets maxReceive correctly",
				entry.m_maxReceive == 0);
		}

		{
			std::vector<CRouteTableEntry> entries;
			entries.resize(4);

			entries[0].m_minHopCount = 5;
			entries[1].m_minHopCount = 6;
			entries[2].m_minHopCount = 6;

			entries[0].m_maxSend = 9;
			entries[0].m_maxSendHopCount = 7;
			entries[1].m_maxSend = 10;
			entries[1].m_maxSendHopCount = 8;
			entries[2].m_maxSend = 8;
			entries[2].m_maxSendHopCount = 9;

			entries[0].m_maxReceive = 0;
			entries[0].m_maxReceiveHopCount = 11;
			entries[1].m_maxReceive = 7;
			entries[1].m_maxReceiveHopCount = 12;
			entries[2].m_maxReceive = 7;
			entries[2].m_maxReceiveHopCount = 10;

			CRouteTableEntry merged(entries);

			test("  Entry merge constructor sets minHopCount correctly",
				merged.m_minHopCount == 6);
			test("  Entry merge constructor sets maxSendHopCount correctly",
				merged.m_maxSendHopCount == 9);
			test("  Entry merge constructor sets maxReceiveHopCount correctly",
				merged.m_maxReceiveHopCount == 11);
			test("  Entry merge constructor sets maxSend correctly",
				merged.m_maxSend == 10);
			test("  Entry merge constructor sets maxReceive correctly",
				merged.m_maxReceive == 7);
		}

		{
			CRouteTableEntry e1, e2;
			e2 = e1;
			test("  Equality test returns true on equal entries",
				(e1 == e2) && !(e1 != e2));

#define TESTINEQ(name, member) e2 = e1; e2.member = 42; test("  Equality test returns false when " name " is different", (e1 != e2) && !(e1 == e2));
			TESTINEQ("minHopCount", m_minHopCount);
			TESTINEQ("maxSendHopCount", m_maxSendHopCount);
			TESTINEQ("maxReceiveHopCount", m_maxReceiveHopCount);
			TESTINEQ("maxSend", m_maxSend);
			TESTINEQ("maxReceive", m_maxReceive);
		}
	}
} routeTableTest;

