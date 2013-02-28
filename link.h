/*
    link.h
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

#ifndef LINK_H
#define LINK_H

#include <map>

#include "exception.h"
#include "cstring.h"
#include "uriparser.h"

/*
Base class and factory infrastructure for link objects
*/

class CLink
{
public:
	SIMPLEEXCEPTIONCLASS(CConstructionFailed)

	/*
	uri:
	Reference to a properly formed CURI object (NOT CHECKED)
	Reference lifetime: at least until the end of this function

	Return value:
	Pointer to a newly constructed link object
	Pointer ownership is passed to the caller

	Exceptions:
	CConstructionFailed
	*/
	static CLink *make(const CURI &uri);

	/*
	uri:
	Reference to a properly formed CString object (NOT CHECKED)
	Reference lifetime: at least until the end of this function

	Return value:
	Pointer to a newly constructed link object
	Pointer ownership is passed to the caller

	Exceptions:
	CConstructionFailed
	*/
	static inline CLink *make(const CString &uri)
		{return make(CURI(uri));}


protected:


	/*
	Handler function for a link URI scheme.

	uri:
	Reference to a properly formed CURI object (NOT CHECKED)
	Reference lifetime: at least until the end of this function

	Return value:
	Pointer to a newly constructed link object
	Pointer ownership is passed to the caller

	Exceptions:
	any CException-derived class
	*/
	typedef CLink *(*t_schemeHandler)(const CURI &uri);

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


