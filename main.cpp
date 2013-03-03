/*
    main.cpp
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

#include <cstdio>

#include <unistd.h>

#include <openssl/ssl.h>
#include <openssl/err.h>

#include "exception.h"
#include "log.h"

#include "amikocomlink.h"
#include "tcplistener.h"

#include "key.h"
#include "sha256.h"

void client()
{
	CAmikoComLink link(CURI("amikolink://localhost"));

	sleep(2);
}


void server()
{
	CTCPListener listener(AMIKO_DEFAULT_PORT);
	CAmikoComLink link(listener);

	sleep(3);
}

void testKeys()
{
	while(1)
	{
		CKey privKey;
		privKey.makeNewKey();
		CKey pubKey;
		pubKey.setPublicKey(privKey.getPublicKey());

		CBinBuffer data("blablabla");
		CBinBuffer goodSig = privKey.sign(data);

		CKey otherKey;
		otherKey.makeNewKey();
		CBinBuffer badSig1 = otherKey.sign(data);

		CBinBuffer badSig2 = privKey.sign(CBinBuffer("bad data"));

		if(pubKey.verify(data, goodSig))
			{printf("test 1: ok\n");}
		else
			{printf("test 1: not ok\n"); break;}

		if(!pubKey.verify(data, badSig1))
			{printf("test 2: ok\n");}
		else
			{printf("test 2: not ok\n"); break;}

		if(!pubKey.verify(data, badSig2))
			{printf("test 3: ok\n");}
		else
			{printf("test 3: not ok\n"); break;}
	}
}

int main(int argc, char **argv)
{
	try
	{
		SSL_load_error_strings();
		SSL_library_init();

		/*
		TODO:
		Multi-threaded applications must provide two callback functions to
		OpenSSL by calling CRYPTO_set_locking_callback() and
		CRYPTO_set_id_callback(), for all versions of OpenSSL up to and
		including 0.9.8[abc...].
		As of version 1.0.0, CRYPTO_set_id_callback() and associated APIs are
		deprecated by CRYPTO_THREADID_set_callback() and friends.
		This is described in the threads(3) manpage. 
		*/

		CAmikoComLink::registerForScheme("amikolink");

		if(argc < 2) throw CException("Missing commandline argument");

		CString command(argv[1]);

		if(command == "client") client();
		if(command == "server") server();
		if(command == "testKeys") testKeys();

		/*
		printf("%p\n", CLink::make("amikolink://localhost"));
		*/

		ERR_free_strings();

		log("Successful exit\n");
		return 0;
	}
	catch(CException &e)
	{
		log(CString::format("Caught application exception: %s\n", 256, e.what()));
		return 1;
	}
	catch(std::exception &e)
	{
		log(CString::format("Caught standard library exception: %s\n", 256, e.what()));
		return 2;
	}
}

