/*
    cominterface.h
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

#ifndef COMINTERFACE_H
#define COMINTERFACE_H

#include "exception.h"
#include "binbuffer.h"
#include "cthread.h"

/*
A ComInterface is an object that can take part in the message delivery system
of Amiko.
You can send messages through the interface with the sendMessage method.
If any messages are received on the interface, the ComInterface object will
send them to the "receiver" object, which is set with the setReceiver method.
*/
class CComInterface
{
public:
	SIMPLEEXCEPTIONCLASS(CMessageLost)

	/*
	Constructed object:
	ComInterface  with receiver set to NULL

	Exceptions:
	none
	*/
	CComInterface();

	virtual ~CComInterface();

	/*
	message:
	Reference to properly formed CBinBuffer object (NOT CHECKED)
	Reference lifetime: at least until the end of this function

	Exceptions:
	TODO
	*/
	virtual void sendMessage(const CBinBuffer &message)=0;

	/*
	receiver:
	either NULL, or
	Valid pointer (NOT CHECKED)
	Pointed memory contains CComInterface object (NOT CHECKED)
	Pointer ownership: remains with the caller
	Pointer lifetime: at least until setReceiver is called again with a
	different object, or until this object is deleted (whichever comes first)

	Exceptions:
	TODO
	*/
	void setReceiver(CComInterface *receiver);

	//TODO: spec
	inline CComInterface *getReceiver()
	{
		CMutexLocker lock(m_Receiver);
		return m_Receiver.m_Value;
	}

protected:
	/*
	message:
	Reference to properly formed CBinBuffer object (NOT CHECKED)
	Reference lifetime: at least until the end of this function

	Exceptions:
	CMessageLost
	TODO (same as sendMessage)
	*/
	void deliverMessage(const CBinBuffer &message);

	CCriticalSection<CComInterface *> m_Receiver;
};

#endif

