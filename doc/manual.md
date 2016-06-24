(Note: this manual applies to the prototype3 version)

WARNINGS
========

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


Compatibility warning
---------------------

This version of Amiko Pay is not guaranteed to remain compatible with future
versions, and there is not guaranteed to be a clean migration path.


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
named _A_.new or _A_.old, where _A_ is the state filename (e.g. amikopay.dat.new
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
"prototype3" directory, and enter:

	python main.py


Commands
========

When started, Amiko Pay presents a command prompt to the user. Use the "help"
command to get a list of available commands. The "exit" and "quit" commands can
be used to terminate Amiko Pay.


Making new payment links
------------------------

Scenario: A and B want to establish a payment link.

Step 1:
A calls the "makelink" command, with an empty remote URL:

	(A) > makelink
	(A) Local name of the link: linkNameAtA
	(A) Remote URL of the link (can be empty):
	(A) Link URL (pass this to the peer):  amikolink://A.com/linkNameAtA

The result is an amikolink URL.

Note that A can now see the link information with the "list" command.

	(A) > list
	(A) {...
	(A) 'links': {'linkNameAtA': {'_class': 'Link',
	(A)                           'channels': [],
	(A)                           'localID': 'linkNameAtA',
	(A)                           'remoteID': None}},
	(A) ...}


Step 2:
A gives the amikolink URL to B. This can, for instance, be done through a
web interface.

Step 3:
B calls the "makelink", using the given amikolink URL as remote URL:

	(B) > makelink
	(B) Local name of the link: linkNameAtB
	(B) Remote URL of the link (can be empty): amikolink://A.com/linkNameAtA
	(B) Link URL (pass this to the peer):  amikolink://B.net/linkNameAtB

Note that B can now see the link information with the "list" command:

	(B) > list
	(B) {...
	(B) 'links': {'linkNameAtB': {'_class': 'Link',
	(B)                           'channels': [],
	(B)                           'localID': 'linkNameAtB',
	(B)                           'remoteID': 'linkNameAtA'}},
	(B) ...}

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

A calls the "deposit" command

	(A) > deposit
	(A) 1: linkNameAtA
	(A) Choose a link to deposit in (leave empty to abort): 1
	(A) Amount (Satoshi): 100000
	(A) Are you sure (y/n)? y

Note that the amount is given in Satoshi, not in Bitcoin!

The deposit adds a payment channel to the link. For now, this is a channel of
type IOUChannel:

	(A) > list
	(A) {...
	(A)  'links': {'linkNameAtA': {'_class': 'Link',
	(A)                            'channels': [{'_class': 'IOUChannel',
	(A)                                          'address': _some address_,
	(A)                                          'amountLocal': 100000,
	(A)                                          'amountRemote': 0,
	(A)                                          'isIssuer': True,
	(A)                                          'state': 'open',
	(A)                                          'transactionsIncomingLocked': {},
	(A)                                          'transactionsIncomingReserved': {},
	(A)                                          'transactionsOutgoingLocked': {},
	(A)                                          'transactionsOutgoingReserved': {},
	(A)                                          'withdrawTxID': None}],
	(A)                            'localID': 'linkNameAtA',
	(A)                            'remoteID': 'linkNameAtB'},
	(A) ...}

This type of channel, when created as such, transfers IOU's issued by A. When
closing the channel, A transfers the owed amount to B with a regular Bitcoin
transaction.


Creating a meeting point
------------------------
To allow transactions to take place, the payer and payee need to establish a
route between each other. They have to agree on a meeting point, and then they
will both route towards that meeting point.

Any node can host one or more meeting points. The payee node sends a list of
meeting points to the payer node, and the payer node selects one of these. The
list of meeting points as assembled by the payee node consists of:
* all meeting points that are hosted on the payee node
* all external meeting points, as configured in the payee node settings

The easiest way to have a meeting point for performing transactions is to host
a meeting point on the payee node. To create a meeting point on node B:

	(B) > makemeetingpoint
	(B) Name of the meeting point: MP_B

The name can be anything, as long as it is unique on the network. When multiple
meeting points have the same name, transactions using those meeting points can
fail to find a route.

You can see that a meeting point has been created:

	(B) > list
	(B) {...
	(B)  'meetingPoints': {'MP_B': {'ID': 'MP_B',
	(B)                             '_class': 'MeetingPoint',
	(B)                             'unmatchedRoutes': {}}},
	(B) ...}


Performing an Amiko payment
---------------------------

Scenario: B wishes to receive a payment from A. Note that, in this scenario,
A and B do not need to share a direct link: it is sufficient that a
link-to-link route can be found between A and B that has sufficient liquidity
to perform the payment.

Step 1:
B calls the "request" command. The result is an amikopay URL:

	(B) > request
	(B) Amount (Satoshi): 123
	(B) Receipt (can be empty): This is a receipt
	(B) 1: (any link)
	(B) 2: linkNameAtB
	(B) Choose a link to receive with (leave empty to abort): 1
	(B) Request URL (pass this to the payer):  amikopay://B.net/c21699c701c3db1e

Note that, by choosing "(any link)", Amiko Pay will automatically choose a
suitable link to receive the funds on. By choosing one of the links, you force
Amiko Pay to receive funds on that link. This is useful, for instance, for
making payments to yourself (send on one link and receive on another).

Step 2:
B gives the amikopay URL to A. This can be done, for instance, through a web
interface, a QR code or NFC.

Step 3:
A calls the "pay" command. Like on the payee side, it is possible to either let
Amiko Pay automatically select a link, or force the payment through a specific
link on the payer side. Now, Amiko Pay shows the receipt and the amount to A,
and asks A to confirm the payment. If A confirms the payment, the payment is
performed:

	(A) > pay
	(A) Request URL: amikopay://localhost/c21699c701c3db1e
	(A) 1: (any link)
	(A) 2: linkNameAtA
	(A) Choose a link to pay with (leave empty to abort): 1
	(A) Receipt:  'This is a receipt'
	(A) Amount: (Satoshi) 123
	(A) Do you want to pay (y/n)? y
	(A) Payment is  committed

If the payment is successful, balances on the payment channel(s) between A and B
are adjusted in such a way that the bitcoins are subtracted from A's balance and
added to B's balance.

Both on payer and payee side, both successful and unsuccessful transactions are
logged in a CSV file. The name of this file is a setting; by default, the name
is 'payments.log'.

Withdrawing from a link
----------------------

Scenario: A wishes to withdraw bitcoins from the link with B

A calls the "withdraw" command:

	(A) > withdraw
	(A) 1: linkNameAtA
	(A) Choose a link to withdraw from (leave empty to abort): 1
	(A) 1: 0
	(A) Channel index (leave empty to abort): 1
	(A) Are you sure (y/n)? y

Once the withdrawal is successful, it results in a Bitcoin transaction which
releases the locked bitcoins from the payment channel. Each side of the link
receives its own balance in bitcoins. From this point on, the payment channel
can no longer be used for Amiko payments.

Diagnostics
-----------

Amiko Pay writes diagnostics information to a file "debug.log" in the current
directory (".").

