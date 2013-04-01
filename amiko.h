/*
    amiko.h
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

#ifndef AMIKO_H
#define AMIKO_H

#include <list>

#include "cthread.h"

#include "amikosettings.h"
#include "comlink.h"
#include "comlistenerthread.h"
#include "commakerthread.h"

/*
Container of application-level data
*/
class CAmiko
{
public:
	/*
	settings:
	Reference to properly formed CAmikoSettings object (NOT CHECKED)
	Reference lifetime: at least the lifetime of this object

	Constructed object:
	Empty Amiko object

	Exceptions:
	none
	*/
	CAmiko(const CAmikoSettings &settings);

	~CAmiko();

	/*
	this object:
	not running (CHECKED)

	Exceptions:
	CThread::CAlreadyRunningError
	CThread::CStartFailedError
	*/
	void start();

	/*
	Note: waits until threads stop

	Exceptions:
	CThread::CStopFailedError
	*/
	void stop();

	/*
	Return value:
	CAmikoSettings object

	Exceptions:
	CMutex::CError
	*/
	inline CAmikoSettings getSettings()
	{
		CMutexLocker lock(m_Settings);
		return m_Settings.m_Value;
	}

	/*
	link:
	Pointer to properly formed CComLink object (NOT CHECKED)
	Pointer ownership: passed to this object
	ComLink thread is already started

	Exceptions:
	CMutex::CError
	*/
	void addPendingComLink(CComLink *link);

	/*
	Exceptions:
	CMutex::CError
	CThread::CStopFailedError
	*/
	void processPendingComLinks();

	/*
	Exceptions:
	CMutex::CError
	CThread::CStopFailedError
	*/
	void removeClosedComLinks();

	/*
	Exceptions:
	CMutex::CError
	TODO
	*/
	void makeMissingComLinks();

	/*
	Exceptions:
	CMutex::CError
	*/
	inline size_t getNumPendingComLinks()
	{
		CMutexLocker lock(m_PendingComLinks);
		return m_PendingComLinks.m_Value.size();
	}

private:
	CCriticalSection<CAmikoSettings> m_Settings;

	CComListenerThread m_ListenerThread;
	CComMakerThread m_MakerThread;

	CCriticalSection< std::list<CComLink *> > m_PendingComLinks;
	CCriticalSection< std::list<CComLink *> > m_OperationalComLinks;
};

#endif

