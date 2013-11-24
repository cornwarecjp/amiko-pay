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
	m_localHostname(""),
	m_portNumber(AMIKO_DEFAULT_PORT),
	m_MeetingPointPubKey()
{
}


void CAmikoSettings::loadFrom(const CSettingsSource &src)
{
	m_localHostname = src.getValue("receiveConnections", "hostname",
		m_localHostname);
	m_portNumber = src.getValue("receiveConnections", "portNumber",
		m_portNumber);

	CString meetingPointPubKeyStr = src.getValue("meetingPoint", "publicKey",
		m_MeetingPointPubKey.hexDump());
	if(meetingPointPubKeyStr.empty())
	{
		log("Read from configuration file: no meeting point configured\n");
	}
	else
	{
		m_MeetingPointPubKey = CBinBuffer::fromHex(meetingPointPubKeyStr);

		log(CString::format(
			"Read from configuration file: configured meeting point %s\n",
			256,
			getBitcoinAddress(m_MeetingPointPubKey).c_str()
			));
	}

	m_links.clear();
	unsigned int i = 0;
	while(true)
	{
		CString section = CString::format("links/%d", 64, i);
		CString remoteURI       = src.getValue(section, "remoteURI", "");
		CString remotePublicKey = src.getValue(section, "remotePublicKey", "");
		CString localPrivateKey = src.getValue(section, "localPrivateKey", "");
		if(remoteURI == "" && remotePublicKey == "" && localPrivateKey == "")
			break; //apparently, section does not exist

		CLink link;
		link.m_remoteURI = remoteURI;
		link.m_localKey.setPrivateKey(CBinBuffer::fromHex(localPrivateKey));
		link.m_remoteKey.setPublicKey(CBinBuffer::fromHex(remotePublicKey));

		if(link.m_remoteURI.getPath() != getBitcoinAddress(link.m_remoteKey))
			throw CConfigError(
				"Remote URI does not correspond with remote public key");

		m_links.push_back(link);

		log(CString::format(
			"Read from configuration file: link %d connecting local %s to remote %s\n",
			1024, i,
			getBitcoinAddress(link.m_localKey).c_str(),
			link.m_remoteURI.getURI().c_str()
			));

		i++;
	}
}


