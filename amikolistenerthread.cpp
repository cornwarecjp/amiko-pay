/*
    amikolistenerthread.cpp
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

#include <cstdlib>

#include "timer.h"
#include "log.h"
#include "comlink.h"

#include "amikolistenerthread.h"


CAmikoListenerThread::CAmikoListenerThread(CAmiko *amiko,
	const CString &paymentService, const CString &linkService) :

	m_Amiko(amiko),
	m_paymentListener(paymentService),
	m_linkListener(linkService)
{
}


CAmikoListenerThread::~CAmikoListenerThread()
{
}


void CAmikoListenerThread::threadFunc()
{
	while(!m_terminate)
	{
		try
		{
			acceptNewConnections();
			m_Amiko->removeClosedComLinks();
			m_Amiko->processPendingComLinks();
		}
		catch(CException &e)
		{
			log(CString::format(
				"CAmikoListenerThread::threadFunc(): Caught application exception: %s\n",
				256, e.what()));
			//TODO: maybe app cleanup?
			//e.g. with atexit, on_exit
			exit(3);
		}
		catch(std::exception &e)
		{
			log(CString::format(
				"CAmikoListenerThread::threadFunc(): Caught standard library exception: %s\n",
				256, e.what()));
			//TODO: maybe app cleanup?
			//e.g. with atexit, on_exit
			exit(3);
		}

		//wait 100ms when there are no new connections
		CTimer::sleep(100);
	}
}


void CAmikoListenerThread::acceptNewConnections()
{
	try
	{
		// Limit number of pending links
		while(m_Amiko->getNumPendingComLinks() < 100)
		{
			CComLink *link = new CComLink(m_linkListener, m_Amiko->getSettings(), m_Amiko->getLinkConfigs());
			//TODO: if in the below code an exception occurs, delete the above object
			link->start(); //start comlink thread
			m_Amiko->addPendingComLink(link);
		}
	}
	catch(CTCPConnection::CTimeoutException &e)
	{}
}

