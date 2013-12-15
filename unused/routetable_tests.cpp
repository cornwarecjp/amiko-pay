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
		m_testEntries.clear();
		m_testEntries.resize(4);

		m_testEntries[0].m_minHopCount = 5;
		m_testEntries[1].m_minHopCount = 6;
		m_testEntries[2].m_minHopCount = 6;

		m_testEntries[0].m_maxSend = 9;
		m_testEntries[0].m_maxSendHopCount = 7;
		m_testEntries[1].m_maxSend = 10;
		m_testEntries[1].m_maxSendHopCount = 8;
		m_testEntries[2].m_maxSend = 8;
		m_testEntries[2].m_maxSendHopCount = 9;

		m_testEntries[0].m_maxReceive = 0;
		m_testEntries[0].m_maxReceiveHopCount = 11;
		m_testEntries[1].m_maxReceive = 7;
		m_testEntries[1].m_maxReceiveHopCount = 12;
		m_testEntries[2].m_maxReceive = 7;
		m_testEntries[2].m_maxReceiveHopCount = 10;

		test_entryClass();
		test_tableClass();
	}

	void test_entryClass()
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
			CRouteTableEntry merged(m_testEntries);

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

	void test_tableClass()
	{
		{
			CRouteTable table;
			test("  Table default constructor results in empty table",
				table.empty() && table.m_ChangedDestinations.empty());
		}

		{
			std::vector<CRouteTable> tables;
			tables.resize(4);

			CRIPEMD160 dest1(CBinBuffer("1"));
			CRIPEMD160 dest2(CBinBuffer("2"));
			CRIPEMD160 dest3(CBinBuffer("3"));
			for(size_t i=0; i<4; i++)
				tables[i].updateRoute(dest1, m_testEntries[i]);
			tables[2].updateRoute(dest2, m_testEntries[0]);
			tables[3].updateRoute(dest3, m_testEntries[1]);

			CRouteTable merged(tables);
			test("  Table merge constructor makes merged entry",
				merged[dest1.toBinBuffer()] == CRouteTableEntry(m_testEntries));

			CRouteTableEntry e2 = merged[dest2.toBinBuffer()];
			e2.m_minHopCount--;
			e2.m_maxSendHopCount--;
			e2.m_maxReceiveHopCount--;
			test("  Table merge constructor adds single entry",
				e2 == m_testEntries[0]);

			CRouteTableEntry e3 = merged[dest3.toBinBuffer()];
			e3.m_minHopCount--;
			e3.m_maxSendHopCount--;
			e3.m_maxReceiveHopCount--;
			test("  Table merge constructor adds single entry",
				e3 == m_testEntries[1]);

			test("  Table merge constructor gives empty change list",
				merged.m_ChangedDestinations.empty());
			test("  Table merge constructor gives correct size",
				merged.size() == 3);
		}

		{
			CRouteTable table;
			CRIPEMD160 dest1(CBinBuffer("1"));
			table.updateRoute(dest1, m_testEntries[0]);

			test("  Table update adds correct entry",
				table[dest1.toBinBuffer()] == m_testEntries[0]);
			test("  Table update gives correct size",
				table.size() == 1);
			test("  Table update adds to change list",
				table.m_ChangedDestinations.count(dest1.toBinBuffer()) == 1);
			test("  Table update gives correct change list size",
				table.m_ChangedDestinations.size() == 1);
		}
	}


	std::vector<CRouteTableEntry> m_testEntries;

} routeTableTest;

