/*
    amikosettings.h
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

#ifndef AMIKOSETTINGS_H
#define AMIKOSETTINGS_H

#include <vector>

#include "binbuffer.h"
#include "key.h"
#include "bitcoinaddress.h"
#include "settingssource.h"
#include "exception.h"

//TODO: choose friendly default ports
#define AMIKO_DEFAULT_LINK_PORT "12345"
#define AMIKO_DEFAULT_PAYMENT_PORT "12346"

//TODO: find a better place for this class
class CLinkConfig
{
public:
	CKey m_localKey;  //Local key (public and private key)
	CString m_remoteURI; //Remote URI (empty when unknown)
	bool m_completed; //true: link is completed (remote public key is known)
	CKey m_remoteKey; //Remote key (public key, must be empty or correspond with m_remoteURI)
};


class CAmikoSettings
{
public:
	SIMPLEEXCEPTIONCLASS(CConfigError)

	/*
	Constructed object:
	Contains default settings

	Exceptions:
	none
	*/
	CAmikoSettings();

	/*
	src:
	Reference to properly formed CSettingsSource object (NOT CHECKED)
	Reference lifetime: at least until the end of this function

	All original link settings are removed.
	Settings present in the file are loaded.
	Settings not present in the file are unchanged.

	Exceptions:
	CString::CFormatException
	CURI::CParseFailure
	CURI::CNotFound
	CKey::CConstructError
	CKey::CKeyError
	CBinBuffer::CWriteError
	CConfigError
	*/
	void loadFrom(const CSettingsSource &src);

	CString m_paymentPortNumber;

	CString m_linkHostname;
	CString m_linkPortNumber;

	//public key, or empty if there is no meeting point
	CBinBuffer m_MeetingPointPubKey;

	CString m_linksDir;

	/*
	localKey:
	Reference to properly formed CKey object (NOT CHECKED)
	Reference lifetime: at least until the end of this function
	Contains a public key (CHECKED)

	Return value:
	CString object

	Exceptions:
	CKey::CKeyError
	*/
	inline CString getLocalLinkURL(const CKey &localKey)
	{
		return CString("amikolink://") +
			m_linkHostname + ":" + m_linkPortNumber + "/" +
			getBitcoinAddress(localKey);
	}
};

#endif

