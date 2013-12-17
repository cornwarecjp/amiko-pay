/*
    amiko_tests.cpp
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
#include <vector>

#include "amikosettings.h"
#include "file.h"
#include "timer.h"
#include "bitcoinaddress.h"

#include "amiko.h"

#include "test.h"

/*
TODO: document and expand
*/


void clearDirectory(const CString &dir)
{
	std::vector<CString> files = CFile::getDirectoryContents(dir);
	for(size_t i=0; i < files.size(); i++)
		if(files[i].length() > 0 && files[i][0] != '.')
			CFile::remove(dir + files[i]);
}


class CAmikoTest : public CTest
{
	virtual const char *getName() const
		{return "amiko";}

	virtual void run()
	{
		CAmikoSettings settings1, settings2;
		settings1.m_localHostname = "localhost";
		settings1.m_portNumber = "12345";
		settings1.m_linksDir = "./testlinks/amiko1/"; //final slash is necessary
		settings2.m_localHostname = "localhost";
		settings2.m_portNumber = "12346";
		settings2.m_linksDir = "./testlinks/amiko2/"; //final slash is necessary

		CFile::makeDirectory(settings1.m_linksDir);
		CFile::makeDirectory(settings2.m_linksDir);
		clearDirectory(settings1.m_linksDir);
		clearDirectory(settings2.m_linksDir);

		CAmiko amiko1(settings1), amiko2(settings2);

		amiko1.start();
		amiko2.start();

		CString URI1 = amiko1.makeNewLink();
		CString localAddress1;
		{
			std::vector<CAmiko::CLinkStatus> status = amiko1.listLinks();
			test("  the created link exists (and is the only link)",
				status.size() == 1);
			test("  the created link has the expected local URI",
				status[0].m_localURI == URI1);
			test("  the created link has an empty remote URI",
				status[0].m_remoteURI == "");
			test("  the created link is not completed",
				status[0].m_completed == false);
			test("  the created link is not connected",
				status[0].m_connected == false);
			localAddress1 = getBitcoinAddress(status[0].m_localKey);
		}

		CString URI2 = amiko2.makeNewLink();
		{
			std::vector<CAmiko::CLinkStatus> status = amiko2.listLinks();
			test("  the created link exists (and is the only link)",
				status.size() == 1);
			test("  the created link has the expected local URI",
				status[0].m_localURI == URI2);
			test("  the created link has an empty remote URI",
				status[0].m_remoteURI == "");
			test("  the created link is not completed",
				status[0].m_completed == false);
			test("  the created link is not connected",
				status[0].m_connected == false);
		}

		amiko1.setRemoteURI(localAddress1, URI2);

		//Allow the two sides to connect
		//TODO: reduce this time once we can set it with a setting
		CTimer::sleep(11000);

		{
			std::vector<CAmiko::CLinkStatus> status = amiko1.listLinks();
			test("  the created link exists (and is the only link)",
				status.size() == 1);
			test("  the created link has the expected remote URI",
				status[0].m_remoteURI == URI2);
			test("  the created link is completed",
				status[0].m_completed == true);
			test("  the created link is connected",
				status[0].m_connected == true);
		}

		{
			std::vector<CAmiko::CLinkStatus> status = amiko2.listLinks();
			test("  the created link exists (and is the only link)",
				status.size() == 1);
			test("  the created link has the expected remote URI",
				status[0].m_remoteURI == URI1);
			test("  the created link is completed",
				status[0].m_completed == true);
			test("  the created link is connected",
				status[0].m_connected == true);
		}

		amiko1.stop();

		//Allow the two sides to disconnect
		CTimer::sleep(100);

		{
			std::vector<CAmiko::CLinkStatus> status = amiko2.listLinks();
			test("  the created link exists (and is the only link)",
				status.size() == 1);
			test("  the created link has the expected remote URI",
				status[0].m_remoteURI == URI1);
			test("  the created link is completed",
				status[0].m_completed == true);
			test("  the created link is not connected",
				status[0].m_connected == false);
		}

		amiko2.stop();
	}
} amikoTest;


