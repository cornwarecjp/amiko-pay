/*
    main.cpp
    Copyright (C) 2013-2014 by CJP

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

#include <cstdio>

#include <openssl/ssl.h>
#include <openssl/err.h>

#include "exception.h"
#include "log.h"
#include "cthread.h"

#include "conffile.h"
#include "commandlineparams.h"
#include "amiko.h"
#include "timer.h"
#include "key.h"
#include "version.h"
#include "paylink.h"

CString getInput(CString question="")
{
	printf("%s", question.c_str());
	CString ret;
	while(true)
	{
		char c = getchar();
		if(c == '\n') break;
		ret += c;
	}
	return ret;
}


CString getMultilineInput(CString question="")
{
	CString ret;
	bool isOdd = false;
	while(true)
	{
		CString line = getInput(question);
		ret += line;

		for(size_t i=0; i < line.length(); i++)
			if(line[i] == '\"')
				isOdd = !isOdd;
		if(!isOdd) break;

		ret += "\n";
		question = "... ";
	}
	return ret;
}

#define uBTC 100
#define mBTC 100000
#define  BTC 100000000
uint64_t readBitcoinAmount(const CString &str, uint64_t unit)
{
	uint64_t beforeDecimal=0, afterDecimal=0, afterDecimalDivisor=1;

	size_t dotpos = str.find('.');
	if(dotpos == str.npos) //not found
	{
		beforeDecimal = str.parseAsDecimalInteger();
	}
	else //found
	{
		beforeDecimal = CString(str.substr(0, dotpos)).parseAsDecimalInteger();
		CString after = str.substr(dotpos+1);
		afterDecimal  = after.parseAsDecimalInteger();
		size_t pos = 0;
		while(pos < after.length() && after[pos] >= '0' && after[pos] <= '9')
		{
			afterDecimalDivisor *= 10;
			pos++;
		}
	}

	//TODO: check whether this will give an integer overflow
	//Note: insignificant digits will always be ROUNDED DOWN!!!
	return unit*beforeDecimal + (unit*afterDecimal)/afterDecimalDivisor;
}


CString writeBitcoinAmount(uint64_t amount, uint64_t unit)
{
	uint64_t beforeDecimal = amount / unit;
	uint64_t afterDecimal  = amount % unit;
	return CString::format("%ld.%08ld", 64,
		long(beforeDecimal), long(afterDecimal));
}


void doCommand(CAmiko &amiko, const std::vector<CString> &splitInput)
{
#define CHECKNUMARGS(n) \
	if(splitInput.size() < ((n)+1)) \
	{ \
		printf("Error: command requires %ld arguments; %ld given\n", \
			long(n), long(splitInput.size())-1); \
		return; \
	}

	if(splitInput[0] == "request")
	{
		CHECKNUMARGS(1)

		//TODO: make unit configurable
		uint64_t amount = readBitcoinAmount(splitInput[1], BTC);

		CString receipt = "";
		if(splitInput.size() >= 3)
			receipt = splitInput[2];

		CString ID = amiko.addPaymentRequest(receipt, amount);
		printf("%s\n", ID.c_str());
	}
	else if(splitInput[0] == "pay")
	{
		CHECKNUMARGS(1)
		CString paymentURL = splitInput[1];
		CPayLink link = CURI(paymentURL);
		link.initialHandshake();

		printf("<RECEIPT>\n%s\n</RECEIPT>\n", link.m_transaction.m_receipt.c_str());

		//TODO: make unit configurable
		CString writtenAmount = writeBitcoinAmount(link.m_transaction.m_amount, BTC);
		printf("Amount: %s BTC\n",
			writtenAmount.c_str());

		CString answer = getInput(
			CString::format("Do you want to pay %s BTC (y/n)? ", 1024,
			writtenAmount.c_str())
				);
		link.sendPayerAgrees(answer == "y" || answer == "Y");

		link.start();
		amiko.doPayment(link);
	}
	else if(splitInput[0] == "newlink")
	{
		CString remoteURI;
		if(splitInput.size() >= 2)
			remoteURI = splitInput[1];

		CString localURI = amiko.makeNewLink(remoteURI);
		printf("%s\n", localURI.c_str());
	}
	else if(splitInput[0] == "setremoteuri")
	{
		CHECKNUMARGS(2)
		amiko.setRemoteURI(splitInput[1], splitInput[2]);
	}
	else if(splitInput[0] == "listlinks")
	{
		std::vector<CAmiko::CLinkStatus> list = amiko.listLinks();
		for(size_t i=0; i < list.size(); i++)
		{
			CAmiko::CLinkStatus &status = list[i];

			printf("link %ld:\n", long(i+1));
			printf("  local address: %s\n",
				getBitcoinAddress(status.m_localKey).c_str());
			printf("  local URI: \"%s\"\n",
				status.m_localURI.c_str());
			printf("  remote URI: \"%s\"\n",
				status.m_remoteURI.c_str());
			printf("  completed: %s\n",
				status.m_completed ? "true" : "false");
			printf("  connected: %s\n",
				status.m_connected ? "true" : "false");
		}
	}
	else if(splitInput[0] == "newkey")
	{
		CKey key;
		key.makeNewKey();

		printf("localPrivateKey = %s\n", key.getPrivateKey().hexDump().c_str());
		printf("remoteURI = %s\n", amiko.getSettings().getLocalLinkURL(key).c_str());
		printf("remotePublicKey = %s\n", key.getPublicKey().hexDump().c_str());
	}
	else if(splitInput[0] == "help")
	{
		printf(
			"exit:\n"
			"quit:\n"
			"  Terminate application.\n"
			"help:\n"
			"  Display this message.\n"
			"request amount [receipt]:\n"
			"  Request payment of amount BTC, with optional receipt.\n"
			"  Returns the payment URL.\n"
			"pay paymentURL:\n"
			"  Perform the payment indicated by paymentURL.\n"
			"newlink [remoteURI]:\n"
			"  Create a new link, and optionally provide it with the link\n"
			"  URI of the remote party.\n"
			"  Returns the local URI, which can be given to the remote user.\n"
			"setremoteuri localAddress remoteURI:\n"
			"  Sets the remote URI of the link with the given local address.\n"
			"listlinks\n"
			"  List all links and their status\n"
			"newkey:\n"
			"  Make a new key pair and display its properties.\n"
			);
	}
	else
	{
		printf("Unrecognized command \"%s\"\n", splitInput[0].c_str());
	}
}


void app(const std::vector<CString> &arguments)
{
	CCommandlineParams commandline(arguments);

	CString conffilename = commandline.getValue(
		"files", "conffile", "amikopay.conf");

	CAmikoSettings settings;
	settings.loadFrom(CConfFile(conffilename));
	settings.loadFrom(commandline); //overrides settings from conffile
	CAmiko amiko(settings);
	amiko.start();

	//Wait some time to allow initialization to finish
	CTimer::sleep(1000);

	printf(
		"\n"
		"\n"
		"Amiko Pay " AMIKO_VERSION " Copyright (C) 2013 - " AMIKO_LASTCOPYRIGHTYEAR "\n"
		"\n"
		"Amiko Pay is free software: you can redistribute it and/or modify\n"
		"it under the terms of the GNU General Public License as published by\n"
		"the Free Software Foundation, either version 3 of the License, or\n"
		"(at your option) any later version.\n"
		"\n"
		"Amiko Pay is distributed in the hope that it will be useful,\n"
		"but WITHOUT ANY WARRANTY; without even the implied warranty of\n"
		"MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the\n"
		"GNU General Public License for more details.\n"
		"\n"
		"You should have received a copy of the GNU General Public License\n"
		"along with Amiko Pay. If not, see <http://www.gnu.org/licenses/>.\n"
		"\n"
		"Enter \"help\" for a list of commands.\n"
		);


	while(true)
	{
		CString input = getMultilineInput("> ");

		std::vector<CString> splitInput = input.split(' ', true, '\"');
		if(splitInput.size() == 0) continue;

		if(splitInput[0] == "quit" || splitInput[0] == "exit")
		{
			break;
		}
		else
		{
			try
			{
				doCommand(amiko, splitInput);
			}
			catch(CException &e)
			{
				printf(
					"Exception in command %s:\n"
					"%s\n", splitInput[0].c_str(), e.what()
					);

				/*
				We assume here that the exception does not mean that the
				application is left behind in an unsafe situation.
				So, we just continue with the commandline loop.
				*/
			}
		}
	}

	amiko.stop();
}


int main(int argc, char **argv)
{
	log("\n\nStart version " AMIKO_VERSION "\n");
	try
	{
		SSL_load_error_strings();
		SSL_library_init();
		COpenSSLMutexes openSSLMutexes;

		std::vector<CString> arguments;
		if(argc > 1)
			for(int i=1; i<argc; i++)
				arguments.push_back(CString(argv[i]));

		app(arguments);

		ERR_free_strings();

		log("Successful exit\n");
		return 0;
	}
	catch(CException &e)
	{
		CString msg = CString::format("Caught application exception: %s\n", 256, e.what());
		log(msg);
		printf("%s", msg.c_str());
		return 1;
	}
	catch(std::exception &e)
	{
		CString msg = CString::format("Caught standard library exception: %s\n", 256, e.what());
		log(msg);
		printf("%s", msg.c_str());
		return 2;
	}
}

