/*
    amiko.cpp
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
#include "file.h"
#include "bitcoinaddress.h"
#include "key.h"

#include "amiko.h"


CAmiko::CAmiko(const CAmikoSettings &settings) :
	m_Settings(settings),
	m_ListenerThread(this, m_Settings.m_Value.m_portNumber),
	m_MakerThread(this),
	m_FinRoutingThread(this)
{
	CMutexLocker lock(m_Settings);

	//TODO: put some lock on the links folder to prevent data mess-up when
	//accidentally multiple amikopay processes are started

	//Construct finlinks based on directory contents
	std::vector<CString> linkFiles = CFile::getDirectoryContents(
		m_Settings.m_Value.m_linksDir);

	for(size_t i=0; i < linkFiles.size(); i++)
	{
		const CString &file = linkFiles[i];
		if(file.length() > 0 && file[0] != '.')
			m_FinLinks.push_back(
				new CFinLink(m_Settings.m_Value.m_linksDir + file));
	}
}


CAmiko::~CAmiko()
{
	stop();

	{
		CMutexLocker lock(m_PendingComLinks);
		for(std::list<CComLink *>::iterator i=m_PendingComLinks.m_Value.begin();
			i != m_PendingComLinks.m_Value.end(); i++)
		{
			(*i)->setReceiver(NULL);
			(*i)->stop();
			delete (*i);
		}
		m_PendingComLinks.m_Value.clear();
	}

	{
		CMutexLocker lock(m_OperationalComLinks);
		for(std::list<CComLink *>::iterator i=m_OperationalComLinks.m_Value.begin();
			i != m_OperationalComLinks.m_Value.end(); i++)
		{
			(*i)->setReceiver(NULL);
			(*i)->stop();
			delete (*i);
		}
		m_OperationalComLinks.m_Value.clear();
	}

	for(size_t i=0; i < m_FinLinks.size(); i++)
		delete m_FinLinks[i];
	m_FinLinks.clear();
}


void CAmiko::start()
{
	m_ListenerThread.start();
	m_MakerThread.start();
	m_FinRoutingThread.start();
}


void CAmiko::stop()
{
	m_ListenerThread.stop();
	m_MakerThread.stop();
	m_FinRoutingThread.stop();
}


CString CAmiko::makeNewLink(const CString &remoteURI)
{
	CMutexLocker lock(m_Settings);

	CKey localKey;
	localKey.makeNewKey();
	CString localURI = m_Settings.m_Value.getLocalURL(localKey).c_str();
	CString filename = m_Settings.m_Value.m_linksDir +
		getBitcoinAddress(localKey);
	m_FinLinks.push_back(new CFinLink(filename, localKey, remoteURI));

	return localURI;
}


std::vector<CLinkConfig> CAmiko::getLinkConfigs() const
{
	return std::vector<CLinkConfig>(); //TODO
}


void CAmiko::addPendingComLink(CComLink *link)
{
	CMutexLocker lock(m_PendingComLinks);	
	m_PendingComLinks.m_Value.push_back(link);
}


void CAmiko::processPendingComLinks()
{
	CMutexLocker lock1(m_PendingComLinks);
	CMutexLocker lock2(m_OperationalComLinks);

	for(std::list<CComLink *>::iterator i = m_PendingComLinks.m_Value.begin();
		i != m_PendingComLinks.m_Value.end(); i++)
	{
		if((*i)->getState() == CComLink::eClosed)
		{
			//Delete closed links (apparently initialization failed for these)
			CComLink *link = *i;
			link->stop();
			delete link;

			std::list<CComLink *>::iterator j = i; i++;
			m_PendingComLinks.m_Value.erase(j);
		}
		else if((*i)->getState() == CComLink::eOperational)
		{
			addOperationalComLink(*i);

			std::list<CComLink *>::iterator j = i; i++;
			m_PendingComLinks.m_Value.erase(j);
		}

		//This can happen if the above code erased an item
		if(i == m_PendingComLinks.m_Value.end()) break;
	}
}


void CAmiko::addOperationalComLink(CComLink *link)
{
	//Find the FinLink for this link
	CBinBuffer localPubKey = link->getLocalKey().getPublicKey();
	CFinLink *finlink = NULL;
	for(size_t i=0; i < m_FinLinks.size(); i++)
		if(m_FinLinks[i]->getLocalKey().getPublicKey() == localPubKey)
		{
			finlink = m_FinLinks[i];
			break;
		}

	if(finlink == NULL)
	{
		//No corresponding finlink found
		//This is an application bug: link should never have become operational
		//Anyway, just delete the link and throw an exception:
		log("Bug: no finlink found for new comlink; deleted the comlink\n");
		delete link;
		return;
	}

	//If there is any conflicting comlink, keep the first one and delete the new one:
	if(finlink->getReceiver() != NULL)
	{
		log("Detected double link; closing the latest link.\n");
		delete link;
		return;
	}

	//Set receiver in both directions
	link->setReceiver(finlink);
	finlink->setReceiver(link);

	//Move to operational list
	m_OperationalComLinks.m_Value.push_back(link);
}


void CAmiko::removeClosedComLinks()
{
	CMutexLocker lock(m_OperationalComLinks);

	for(std::list<CComLink *>::iterator i = m_OperationalComLinks.m_Value.begin();
		i != m_OperationalComLinks.m_Value.end(); i++)
	{
		if((*i)->getState() == CComLink::eClosed)
			removeComLink(i);
		if(i == m_OperationalComLinks.m_Value.end()) break;
	}
}


void CAmiko::removeComLink(std::list<CComLink *>::iterator &iter)
{
	CComLink *link = *iter;
	link->stop();

	//De-register (as) receiver:
	link->setReceiver(NULL);
	for(size_t i=0; i < m_FinLinks.size(); i++)
		if(m_FinLinks[i]->getReceiver() == link)
			m_FinLinks[i]->setReceiver(NULL);

	delete link;

	std::list<CComLink *>::iterator j = iter; iter++;
	m_OperationalComLinks.m_Value.erase(j);
}


void CAmiko::makeMissingComLinks()
{
	log("Start making missing com links\n");

	std::list<CLinkConfig> missingLinks;
	{
		std::vector<CLinkConfig> missingLinksVector = getLinkConfigs();
		missingLinks.assign(
			missingLinksVector.begin(), missingLinksVector.end());
	}

	{
		CMutexLocker lock(m_OperationalComLinks);
		for(std::list<CComLink *>::iterator i = m_OperationalComLinks.m_Value.begin();
			i != m_OperationalComLinks.m_Value.end(); i++)
		{
			CBinBuffer localPubKey = (*i)->getLocalKey().getPublicKey();
			for(std::list<CLinkConfig>::iterator j = missingLinks.begin();
				j != missingLinks.end(); j++)
			{
				if(j->m_localKey.getPublicKey() == localPubKey)
				{
					std::list<CLinkConfig>::iterator k = j;
					j++;
					missingLinks.erase(k);
					if(j == missingLinks.end()) break;
				}
			}
		}
	}

	log(CString::format("There are %d missing com links\n", 256, missingLinks.size()));

	for(std::list<CLinkConfig>::iterator i = missingLinks.begin();
		i != missingLinks.end(); i++)
			if(i->m_remoteURI != "")
			{
				CURI uri(i->m_remoteURI);

				CComLink *link = new CComLink(uri, getSettings(), getLinkConfigs());
				//TODO: if in the below code an exception occurs, delete the above object
				link->start();
				addPendingComLink(link);
			}

	log("End making missing com links\n");
}


