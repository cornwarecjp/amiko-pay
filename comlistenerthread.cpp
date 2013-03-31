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

#include "timer.h"

#include "comlistenerthread.h"


CComListenerThread::CComListenerThread(const CAmikoSettings &settings) :

	m_Listener(settings.m_portNumber),
	m_Settings(settings)
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
					new CComLink(m_Listener, m_Settings)
					);
				m_newComLinks.m_Value.back()->start(); //start comlink thread
			}
		}
		catch(CTCPConnection::CTimeoutException &e)
		{}

		//wait 100ms when there are no new connections
		CTimer::sleep(100);
	}
}


