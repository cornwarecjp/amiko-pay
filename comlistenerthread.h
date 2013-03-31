/*
    comlistenerthread.h
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

#ifndef COMLISTENERTHREAD_H
#define COMLISTENERTHREAD_H

#include <list>

#include "tcplistener.h"
#include "comlink.h"

#include "cthread.h"

class CComListenerThread : public CThread
{
public:
	/*
	Constructed object:
	non-running thread, listening for incoming TCP connection requests on port
	number indicated by service

	Exceptions:
	CTCPListener::CConnectException
	*/
	CComListenerThread(const CAmikoSettings &settings);

	~CComListenerThread();

	/*
	Return value:
	NULL, or:
	Valid pointer
	Pointed memory contains CComLink object
	Pointer ownership: passed to caller
	*/
	CComLink *getNewComLink();

	void threadFunc();


private:
	CTCPListener m_Listener;
	CAmikoSettings m_Settings;

	CCriticalSection< std::list<CComLink *> > m_newComLinks;
};

#endif

