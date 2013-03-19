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
#include "cthread.h"

#include "amikocomlink.h"
#include "commanager.h"

void app()
{
	CComManager comManager;

	comManager.start();

	sleep(20);

	comManager.stop();
}

int main(int argc, char **argv)
{
	try
	{
		SSL_load_error_strings();
		SSL_library_init();
		COpenSSLMutexes openSSLMutexes;

		CAmikoComLink::registerForScheme("amikolink");

		app();

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

