/*
    amikosettings.cpp
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

#include "amikosettings.h"

#include "log.h"
#include "bitcoinaddress.h"

CAmikoSettings::CAmikoSettings() :
	//defaults
	m_paymentPortNumber(AMIKO_DEFAULT_PAYMENT_PORT),
	m_linkHostname(""),
	m_linkPortNumber(AMIKO_DEFAULT_LINK_PORT),
	m_MeetingPointPubKey(),
	m_linksDir(".")
{
}


void CAmikoSettings::loadFrom(const CSettingsSource &src)
{
	m_paymentPortNumber = src.getValue("receivePayments", "portNumber",
		m_paymentPortNumber);

	m_linkHostname = src.getValue("receiveLinks", "hostname",
		m_linkHostname);
	m_linkPortNumber = src.getValue("receiveLinks", "portNumber",
		m_linkPortNumber);

	CString meetingPointPubKeyStr = src.getValue("meetingPoint", "publicKey",
		m_MeetingPointPubKey.hexDump());
	if(meetingPointPubKeyStr.empty())
	{
		log("No meeting point configured\n");
	}
	else
	{
		m_MeetingPointPubKey = CBinBuffer::fromHex(meetingPointPubKeyStr);

		log(CString::format(
			"Configured meeting point %s\n",
			256,
			getBitcoinAddress(m_MeetingPointPubKey).c_str()
			));
	}

	m_linksDir = src.getValue("files", "linksdir", m_linksDir);

	//Make sure the links dir ends with a path separator.
	//TODO: check whether this works on windows too
	if(m_linksDir[m_linksDir.length()-1] != '/')
		m_linksDir += '/';
}


