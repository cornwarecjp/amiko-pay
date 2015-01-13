(Note: this manual applies to the Python prototype version)

WARNINGS!!!
===========

Legal warning
-------------

Before using Amiko-pay, please check whether any local laws restrict the use of
this software. Ideally, there should be no such laws, but if they do exist,
you may still be able to use Amiko-pay legally by constraining the behavior of
the software, for instance through its settings. The makers of Amiko-pay do not
encourage breaking the law; if you decide to break the law, you do this at
your own responsibility.


Reliability and security warning
--------------------------------

This is unfinished and extremely experimental software; use at your own risk!
At the moment, safety mechanisms (of any kind) are virtually absent, so the use
of Amiko Pay can lead to loss of bitcoins. A list of known vulnerabilities is
maintained in doc/vulnerabilities.md.

If you still wish to continue, you should at least take the following precautions:

* Use Amiko Pay only in combination with a Bitcoin wallet containing a very small
  amount of bitcoins. You should be prepared to lose all bitcoins in your wallet
  as a result of bugs and missing features in the Amiko Pay software.
  This is also true for the bitcoins in your wallet which are not explicitly
  used through the Amiko Pay user interface!
* Only link to parties you fully trust (such as yourself) and only use Amiko Pay
  on networks you fully trust. Do not configure Amiko Pay to open a port that
  is accessible from the Internet, if you do not want to risk hackers accessing
  your system.


Settings
========

Before starting amiko-pay, please have a look at the file amikopay.conf.
Change the settings in this file to your preferred settings before starting
Amiko Pay. By default, Amiko Pay searches for amikopay.conf in the current
working directory (".").


Backups
=======

Private keys created and used by Amiko Pay are stored in your Bitcoin wallet
as Bitcoin addresses, so if you back up your Bitcoin wallet, those private keys
are in your backup.

Besides private keys, Amiko Pay stores additional information, which is needed
to be able to withdraw bitcoins from links. By default, this additional
information is stored in the file "amikopay.dat" in the current working
directory ("."); the name and location of this file is a setting.

In case of a crash during the update of the state file, you may also find a file
named <A>.new or <A>.old, where <A> is the state filename (e.g. amikopay.dat.new
or amikopay.dat.old). In that case, you may need to inspect the files to
determine which is the best file to start a recovery.

You need to backup these files to make sure you keep access to your bitcoins in
case you lose these files.


Starting Amiko Pay
==================

Note: since Amiko Pay is currently a Python application, you need to have Python
installed to be able to run Amiko Pay. Amiko Pay is developed with Python 2.7;
YMMV with other Python versions.

Prior to starting Amiko Pay, a Bitcoin process should be started, so that Amiko
Pay can connect to it through the Bitcoin RPC interface. This process should
continue to run as long as Amiko Pay is running.

Amiko Pay can be started in a terminal window. To do this, enter the
"python-prototype" directory, and enter:

	python main.py


Commands
========

When started, Amiko Pay presents a command prompt to the user. Use the "help"
command to get a list of available commands. The "exit" and "quit" commands can
be used to terminate Amiko Pay.

Command arguments are separated by whitespace. For now, arguments that include
whitespace are not supported.


Making new payment links
------------------------

Scenario: A and B want to establish a payment link.

Step 1:
A calls the "makelink" command, with a link name as argument:

	(A) > makelink linkNameAtA
	(A) amikolink://A.com/linkNameAtA

The result is an amikolink URL.

Note that A can now see the link information with the "list" command.
The link is not yet connected:

	(A) > list
	(A) {'links': [{'channels': [],
	(A)             'isConnected': False,
	(A)             'localID': 'linkNameAtA',
	(A)             'localURL': 'amikolink://A.com/linkNameAtA',
	(A)             'name': 'linkNameAtA',
	(A)             'openTransactions': [],
	(A)             'remoteID': '',
	(A)             'remoteURL': ''}],
	(A)  ...


Step 2:
A gives the amikolink URL to B. This can, for instance, be done through a
web interface.

Step 3:
B calls the "makelink" command with a name and the amikolink URL as argument:

	(B) > makelink linkNameAtB amikolink://A.com/linkNameAtA

Note that B can now see the link information with the "list" command:

	(B) > list
	(B) {'links': [{'channels': [],
	(B)             'isConnected': True,
	(B)             'localID': 'linkNameAtB',
	(B)             'localURL': 'amikolink://B.net/linkNameAtB',
	(B)             'name': 'linkNameAtB',
	(B)             'openTransactions': [],
	(B)             'remoteID': 'linkNameAtA',
	(B)             'remoteURL': 'amikolink://A.com/linkNameAtA'}],
	(B)  ...

The process of B will now repeatedly try to connect to the process of A, using
the given URL. Once a successful connection is established, the process of B
will pass its own amikolink URL to A, so that, in the future, A can call back B
to re-establish the connection. Once connected, the link will stay connected,
until either an error occurs on the link or one of the two sides terminates.
If a non-connected link exists, Amiko Pay will repeatedly try to re-connect that
link.


Depositing into a link
----------------------

Scenario: A wishes to deposit bitcoins into the link with B

A calls the "deposit" command, with the amount and the link name as arguments:

	(A) > deposit linkNameAtA 100000
	(A) Are you sure (y/n)? y
	(A) > DONE

Note that the amount is given in Satoshi, not in Bitcoin!

The deposit adds a payment channel to the link. Once the deposit is successful,
it results in a Bitcoin transaction which locks the specified amount of A's
bitcoins into the payment channel. The payment channel should not be used for
further activities until this deposit transaction has received a few
confirmations in the Bitcoin block chain.


Performing an Amiko payment
---------------------------

Scenario: B wishes to receive a payment from A. Note that, in this scenario,
A and B do not need to share a direct link: it is sufficient that a
link-to-link route can be found between A and B that has sufficient liquidity
to perform the payment.

Step 1:
B calls the "request" command, with as arguments

* the amount to be received
* (optionally) a receipt

The result is an amikopay URL:

	(B) > request 20000 SomeReceiptText
	(B) amikopay://B.net/9c8c48c9000a5c11

Step 2:
B gives the amikopay URL to A. This can be done, for instance, through a web
interface, a QR code or NFC.

Step 3:
A calls the "pay" command with the amikopay URL as argument. Optionally, A can
also specify the name of the link over which the payment should be performed.
Now, Amiko Pay shows the receipt and the amount to A, and asks A to confirm the
payment. If A confirms the payment, the payment is performed:

	(A) > pay amikopay://localhost/9c8c48c9000a5c11 linkNameAtA
	(A) Receipt:  'SomeReceiptText'
	(A) Amount:  20000
	(A) Do you want to pay (y/n)? y
	(A) Payment is  committed

If the payment is successful, balances on the payment channel(s) between A and B
are adjusted in such a way that the bitcoins are subtracted from A's balance and
added to B's balance.


Withdrawing from a link
----------------------

Scenario: A wishes to withdraw bitcoins from the link with B

A calls the "withdraw" command, with the link name and the channel ID as arguments.
The channel ID can be found with the "list" command:

	(A) > list
	(A) {'links': [{'channels': [{'ID': 0,
	(A)                           ...
	(A)                           'amountLocal': 80000,
	(A)                           'amountRemote': 20000,
	(A)                           ...
	(A)                           'type': 'multisig'}],
	(A)             'isConnected': True,
	(A)             'localID': 'linkNameAtA',
	(A)             'localURL': 'amikolink://localhost/linkNameAtA',
	(A)             'name': 'linkNameAtA',
	(A)             'openTransactions': [],
	(A)             'remoteID': 'linkNameAtB',
	(A)             'remoteURL': 'amikolink://localhost/linkNameAtB'},
	(A)             ...
	(A) > withdraw linkNameAtA 0
	(A) Are you sure (y/n)? y
	(A) > DONE

Once the withdrawal is successful, it results in a Bitcoin transaction which
releases the locked bitcoins from the payment channel. Each side of the link
receives its own balance in bitcoins. From this point on, the payment channel
can no longer be used for Amiko payments.

Diagnostics
-----------

Amiko Pay writes diagnostics information to a file "debug.log" in the current
directory (".").

