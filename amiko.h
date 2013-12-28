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
#include <vector>
#include <map>

#include "cthread.h"
#include "amikosettings.h"
#include "comlink.h"
#include "finlink.h"
#include "paylink.h"
#include "transaction.h"
#include "amikolistenerthread.h"
#include "commakerthread.h"
#include "finroutingthread.h"

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
	CFinLink::CSaveError
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
	TODO: spec
	*/
	CString makeNewLink(const CString &remoteURI="");

	/*
	TODO: spec
	*/
	void setRemoteURI(const CString &localAddress, const CString &remoteURI);

	class CLinkStatus : public CLinkConfig
	{
	public:
		CLinkStatus(const CLinkConfig &c) : CLinkConfig(c) {}

		CString m_localURI;
		bool m_connected;
	};
	/*
	TODO: spec
	*/
	std::vector<CLinkStatus> listLinks();

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
	Exceptions:
	none
	*/
	std::vector<CLinkConfig> getLinkConfigs() const;

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
	CThread::CStartFailedError
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

	/*
	link:
	Pointer to properly formed CPayLink object (NOT CHECKED)
	Pointer ownership: passed to this object
	PayLink thread is already started

	Exceptions:
	CMutex::CError
	*/
	void addPayLink(CPayLink *link);

	/*
	Exceptions:
	CMutex::CError
	*/
	inline size_t getNumPayLinks()
	{
		CMutexLocker lock(m_PayLinks);
		return m_PayLinks.m_Value.size();
	}

	//TODO: spec
	CString addPaymentRequest(const CString &receipt, uint64_t amount);

	/*
	Exceptions:
	none
	*/
	std::map<CString, CTransaction> getIncomingPayments()
	{
		CMutexLocker lock(m_IncomingPayments);
		return m_IncomingPayments.m_Value;
	}

	//TODO: protect with mutex!!
	std::vector<CFinLink *> m_FinLinks;

	CCriticalSection< std::list<CPayLink *> > m_PayLinks;

private:

	//TODO: spec
	void addOperationalComLink(CComLink *link);

	//TODO: spec
	void removeComLink(std::list<CComLink *>::iterator &iter);

	CCriticalSection<CAmikoSettings> m_Settings;

	CAmikoListenerThread m_ListenerThread;
	CComMakerThread m_MakerThread;
	CFinRoutingThread m_FinRoutingThread;

	CCriticalSection< std::list<CComLink *> > m_PendingComLinks;
	CCriticalSection< std::list<CComLink *> > m_OperationalComLinks;

	CCriticalSection< std::map<CString, CTransaction> > m_IncomingPayments;
};

#endif

