/*
    uriparser.h
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

#ifndef URI_H
#define URI_H

#include "Uri.h"

#include "exception.h"
#include "cstring.h"

/*
This class attempts to implement RFC3986 (https://tools.ietf.org/html/rfc3986)
for as far as needed in this application.

TODO: define how this deals with non-ASCII characters.
For now, non-ASCII characters are officially not supported!
*/
class CURI
{
public:
	SIMPLEEXCEPTIONCLASS(CParseFailure)
	SIMPLEEXCEPTIONCLASS(CNotFound)

	/*
	uri:
	Reference to a correctly formed CString object (NOT CHECKED)
	Reference lifetime: at least until the end of this function
	ASCII encoded (TODO: support unicode) (NOT CHECKED)

	Constructed object:
	URI object corresponding to contents of uri

	Exceptions:
	CParseFailure
	*/
	CURI(const CString &uri);

	//TODO: copy constructor, assignment operator

	~CURI();

	/*
	Return value:
	Reference to a correctly formed CString object
	Reference lifetime: equal to lifetime of this object
	ASCII encoded (TODO: support unicode)

	Exceptions:
	none
	*/
	inline const CString &getURI() const
		{return m_URIText;}

	/*
	Return value:
	ASCII encoded (TODO: support unicode)

	Exceptions:
	CNotFound
	*/
	inline CString getScheme() const
		{return getText(m_URI.scheme);}
	inline CString getHost() const
		{return getText(m_URI.hostText);}
	inline CString getPort() const
		{return getText(m_URI.portText);}

	/*
	dflt:
	Reference to a correctly formed CString object (NOT CHECKED)
	Reference lifetime: at least until the end of this function
	ASCII encoded (TODO: support unicode) (NOT CHECKED)

	Return value:
	ASCII encoded (TODO: support unicode)

	Exceptions:
	none
	*/
	inline CString getScheme(const CString &dflt) const
		{return getText(m_URI.scheme, dflt);}
	inline CString getHost(const CString &dflt) const
		{return getText(m_URI.hostText, dflt);}
	inline CString getPort(const CString &dflt) const
		{return getText(m_URI.portText, dflt);}

private:
	/*
	Note: m_URI contains pointers to the data in m_URIText
	*/
	UriUriA m_URI;
	CString m_URIText;

	/*
	Return value:
	ASCII encoded (TODO: support unicode)

	Exceptions:
	CNotFound
	*/
	CString getText(const UriTextRangeA &range) const;

	/*
	dflt:
	Reference to a correctly formed CString object (NOT CHECKED)
	Reference lifetime: at least until the end of this function
	ASCII encoded (TODO: support unicode) (NOT CHECKED)

	Return value:
	ASCII encoded (TODO: support unicode)

	Exceptions:
	none
	*/
	CString getText(const UriTextRangeA &range, const CString &dflt) const;
};

#endif


