/*
    comlink.cpp
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

#include "comlink.h"


void CComLink::sendMessage(const CMessage &message)
{
	m_SendQueue.lock();
	m_SendQueue.m_Value.push(message.serialize());
	m_SendQueue.unlock();
	m_HasNewSendData.post();
}


void CComLink::threadFunc()
{
	//TODO: catch all exceptions and handle them

	initialize();

	while(!m_terminate)
	{
		//TODO: receive data

		m_HasNewSendData.waitWithTimeout(10); //10 ms
		m_SendQueue.lock();
		while(!m_SendQueue.m_Value.empty())
		{
			sendMessageDirect(m_SendQueue.m_Value.front());
			m_SendQueue.m_Value.pop();
		}
		m_SendQueue.unlock();
	}
}


std::map<CString, CComLink::t_schemeHandler> CComLink::m_schemeHandlers;

void CComLink::registerSchemeHandler(const CString &scheme, CComLink::t_schemeHandler handler)
{
	m_schemeHandlers[scheme] = handler;
}

CComLink *CComLink::make(const CURI &uri)
{
	CString scheme = uri.getScheme();
	if(scheme == "")
		throw CConstructionFailed("Empty scheme");

	std::map<CString, t_schemeHandler>::const_iterator iterator =
		m_schemeHandlers.find(scheme);

	if(iterator == m_schemeHandlers.end())
		throw CConstructionFailed("unknown scheme");

	const t_schemeHandler handler = iterator->second;
	try
	{
		return handler(uri);
	}
	catch(CException &e)
	{
		throw CConstructionFailed(e.what());
	}
}

