/*
    comlistenerthread.cpp
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

#include "comlistenerthread.h"


CComListenerThread::CComListenerThread(CAmiko *amiko, const CString &service) :
	m_Amiko(amiko),
	m_Listener(service)
{
}


CComListenerThread::~CComListenerThread()
{
	stop(); //stop listener thread

	//Clean up m_newComLinks list
	CMutexLocker lock(m_newComLinks);
	while(!m_newComLinks.m_Value.empty())
	{
		m_newComLinks.m_Value.back()->stop(); //stop link thread
		delete m_newComLinks.m_Value.back();
		m_newComLinks.m_Value.pop_back();
	}
}


void CComListenerThread::threadFunc()
{
	while(!m_terminate)
	{
		try
		{
			CMutexLocker lock(m_newComLinks);

			// Limit number of pending links
			while(m_newComLinks.m_Value.size() < 100)
			{
				m_newComLinks.m_Value.push_back(
					new CComLink(m_Listener, m_Amiko->getSettings())
					);
				m_newComLinks.m_Value.back()->start(); //start comlink thread
			}
		}
		catch(CTCPConnection::CTimeoutException &e)
		{}
		catch(CException &e)
		{
			log(CString::format(
				"CComListenerThread::threadFunc(): Caught application exception: %s\n",
				256, e.what()));
			//TODO: maybe app cleanup?
			//e.g. with atexit, on_exit
			exit(3);
		}
		catch(std::exception &e)
		{
			log(CString::format(
				"CComListenerThread::threadFunc(): Caught standard library exception: %s\n",
				256, e.what()));
			//TODO: maybe app cleanup?
			//e.g. with atexit, on_exit
			exit(3);
		}

		//wait 100ms when there are no new connections
		CTimer::sleep(100);
	}
}


CComLink *CComListenerThread::getNewComLink()
{
	CMutexLocker lock(m_newComLinks);
	CComLink *ret = NULL;

	for(std::list<CComLink *>::iterator i = m_newComLinks.m_Value.begin();
		i != m_newComLinks.m_Value.end(); i++)
	{
		if((*i)->getState() == CComLink::eClosed)
		{
			//Erase closed links (apparently initialization failed for these)
			CComLink *link = *i;
			link->stop();
			delete link;

			std::list<CComLink *>::iterator j = i; i++;
			m_newComLinks.m_Value.erase(j);
		}

		else if(ret == NULL && (*i)->getState() == CComLink::eOperational)
		{
			//Take first operational link as return value
			ret = *i;

			std::list<CComLink *>::iterator j = i; i++;
			m_newComLinks.m_Value.erase(j);
		}

		//This can happen if the above code erased an item
		if(i == m_newComLinks.m_Value.end()) break;
	}

	return ret;
}


