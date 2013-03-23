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

#include "log.h"

#include "comlink.h"

CComLink::CComLink() : m_State(ePending)
{
}


CComLink::~CComLink()
{
}


void CComLink::sendMessage(const CBinBuffer &message)
{
	{
		CMutexLocker lock(m_SendQueue);
		m_SendQueue.m_Value.push(message);
	}
	m_HasNewSendData.post();
}


void CComLink::threadFunc()
{
	if(getState() != ePending)
	{
		log("CComLink::threadFunc(): initial state was not 'pending'; stopping thread\n");
		CMutexLocker lock(m_State);
		m_State.m_Value = eClosed;
		return;
	}

	//Catch all exceptions and handle them
	try
	{
		initialize();

		{
			CMutexLocker lock(m_State);
			m_State.m_Value = eOperational;
		}

		while(!m_terminate)
		{
			//Receive data:
			try
			{
				while(true)
					deliverReceivedMessage(receiveMessageDirect());
			}
			catch(CNoDataAvailable &e)
			{
				/*
				Ignore this exception:
				It is normal that this occurs, in fact it is our way to get out of
				the while loop in the try block
				*/
			}

			//Wait a while, unless there is data to be sent:
			m_HasNewSendData.waitWithTimeout(10); //10 ms

			//Send data:
			{
				CMutexLocker lock(m_SendQueue);
				while(!m_SendQueue.m_Value.empty())
				{
					sendMessageDirect(m_SendQueue.m_Value.front());
					m_SendQueue.m_Value.pop();
				}
			}
		}
	}
	catch(CException &e)
	{
		log(CString::format(
			"CComLink::threadFunc(): Caught application exception: %s\n",
			256, e.what()));
	}
	catch(std::exception &e)
	{
		log(CString::format(
			"CComLink::threadFunc(): Caught standard library exception: %s\n",
			256, e.what()));
	}

	{
		CMutexLocker lock(m_State);
		m_State.m_Value = eClosed;
	}
}


const CKey &CComLink::getRemoteAddress() const
{
	return m_RemoteAddress;
}


const CKey &CComLink::getLocalAddress() const
{
	return m_LocalAddress;
}


