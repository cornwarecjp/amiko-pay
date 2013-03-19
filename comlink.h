/*
    comlink.h
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

#ifndef COMLINK_H
#define COMLINK_H

#include <map>
#include <queue>

#include "exception.h"
#include "cstring.h"
#include "uriparser.h"
#include "message.h"

#include "cthread.h"

/*
Base class and factory infrastructure for communication link objects
*/

class CComLink : public CThread
{
public:
	SIMPLEEXCEPTIONCLASS(CConstructionFailed)

	/*
	message:
	Reference to properly formed CMessage object (NOT CHECKED)
	Reference lifetime: at least until the end of this function

	Exceptions:
	TODO
	*/
	void sendMessage(const CMessage &message);

	void threadFunc();


protected:
	/*
	TODO
	*/
	virtual void initialize()=0;

	/*
	message:
	Reference to properly formed CMessage object (NOT CHECKED)
	Reference lifetime: at least until the end of this function

	Exceptions:
	TODO
	*/
	virtual void sendMessageDirect(const CMessage &message)=0;

	/*
	Return value:
	Valid pointer
	Pointer ownership: passed to the caller
	Pointed memory contains CMessage-derived object
	Pointed object is deserialized from data

	Exceptions:
	TODO
	*/
	virtual CMessage *receiveMessageDirect()=0;


private:

	CCriticalSection< std::queue<CBinBuffer> > m_SendQueue;


public:
	/*
	uri:
	Reference to a properly formed CURI object (NOT CHECKED)
	Reference lifetime: at least until the end of this function

	Return value:
	Pointer to a newly constructed communication link object
	Pointer ownership is passed to the caller

	Exceptions:
	CConstructionFailed
	*/
	static CComLink *make(const CURI &uri);

	/*
	uri:
	Reference to a properly formed CString object (NOT CHECKED)
	Reference lifetime: at least until the end of this function

	Return value:
	Pointer to a newly constructed communication link object
	Pointer ownership is passed to the caller

	Exceptions:
	CConstructionFailed
	*/
	static inline CComLink *make(const CString &uri)
		{return make(CURI(uri));}


protected:

	/*
	Handler function for a communication link URI scheme.

	uri:
	Reference to a properly formed CURI object (NOT CHECKED)
	Reference lifetime: at least until the end of this function

	Return value:
	Pointer to a newly constructed communication link object
	Pointer ownership is passed to the caller

	Exceptions:
	any CException-derived class
	*/
	typedef CComLink *(*t_schemeHandler)(const CURI &uri);

	/*
	scheme:
	Reference to a properly formed CString object (NOT CHECKED)
	Reference lifetime: at least until the end of this function

	handler:
	Function pointer to a function which conforms to the
	description of t_schemeHandler

	WARNING:
	NOT thread-safe; only meant to be called at program initialization

	Exceptions:
	none
	*/
	static void registerSchemeHandler(const CString &scheme, t_schemeHandler handler);


private:


	static std::map<CString, t_schemeHandler> m_schemeHandlers;
};

#endif


