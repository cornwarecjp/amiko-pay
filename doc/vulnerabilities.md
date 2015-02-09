Introduction
============
Due to the fact that Amiko Pay is experimental and unfinished software,
a lot of analysis on its security has not yet been performed. Even the most
basic types of testing, such as an automated set of unit tests with full code
coverage, are still missing. Because of this, you should expect Amiko Pay to
contain several unknown vulnerabilities, which may lead to worse consequences
than the ones listed below (e.g. they might lead to arbitrary code execution
with the privileges of the Amiko Pay process).

Therefore, the list below is far from exhaustive. At the present state of
development, the list below is mainly composed of issues related to
not-yet-implemented security features and to design issues.


Loss of Bitcoins
=================

No lock time
------------
"Refund" transactions are not yet protected by a lock time, so they are always
"final". As a result, an attacker can steal bitcoins from a direct neighbor by
first performing an Amiko payment through their shared link, and then publishing
an earlier version of the refund transaction on the Bitcoin network. The
neighbor can then try to cancel the theft by publishing the most recent version
of the refund transaction, but, assuming equal connectivity in the Bitcoin
network, even then the theft has at least 50% probability of success.


No transaction checks
---------------------
A lot of checks on transactions exchanged by neighbors are not yet implemented.
As a result, an attacker can steal bitcoins from a direct neighbor, for instance
by performing an Amiko payment through their shared link, where the updated
refund transaction is incorrect. It may even be a transaction which will be
accepted by Bitcoin, but assigns too many bitcoins to the attacker.


No protection during transaction
--------------------------------
Between lock and commit/rollback, the bitcoins which are locked in a link
because of an Amiko transaction are protected with a 2-of-2 multisignature
script, requiring consensus between both sides of the link about whether
commit/rollback has occurred. An attacker who is one of the sides of such a link
can hold those bitcoins hostage by refusing to reach consensus with his
neighbor.


Transaction malleability
------------------------
The validity of the "T2" transaction of a microtransaction channel depends on
the transaction ID of the "T1" transaction. Between the moment of publishing T1
and the inclusion of T1 into the block chain, it is possible for attackers to
change the transaction ID of T1, due to Bitcoin transaction malleability. As a
result, the direct neighbor in a link can hold the deposited bitcoins hostage
by refusing to re-sign a modified T2 transaction which contains the new
transaction ID.


No payment channel token check
------------------------------
A payer does not yet check the validity of the token received by the payee on
commit. As a result, an attacking payee can trick the payer into releasing the
payment amount to the payer's first neighbor in the transaction route. If the
token is used as proof of payment, the payer does not have a valid proof, so the
payee can claim the transaction has failed, and refuse to transfer corresponding
goods/services.


Loss of privacy
===============

No encrypted communication
--------------------------
Communication takes place over non-encrypted TCP connections. As a result, an
attacker who has access to network traffic can see which transactions
(transaction tokens and amounts) take place between a user and his neighbors.
This is also true for the payment link between payer and payee. An attacker who
has access to network traffic of all links in a transaction route can see which
nodes send which transactions (including amounts) to which nodes. The receipt is
also visible, since it's sent over the non-encrypted payment link between payer
and payee.


No link authentication
----------------------
When an incoming link connection arrives, the neighbor is not authenticated.
As a result, an attacker who knows the URL of a link of a node can connect to
that node, pretending to be the other side of the link. The node then
incorrectly believes to be connected, and does not attempt to connect to its
real neigbor. The attacker can then perform a Denial of Service on all
operations that involve the link; also, all operations that are attempted by the
node may reveal information to the attacker, leading to a loss of privacy.

If an attacker knows the URLs of both sides of the link, the attacker can
connect to both sides of the link, and position himself as a man-in-the-middle.
This is even possible by an attacker who has no lower-level methods of
re-routing traffic, such as influencing IP routing or changing DNS responses.


Denial of Service
=================

Missing timeouts
----------------
A lot of communication time-outs are missing. As a result, an attacker can stall
a transaction forever, by never responding to a message, while a response is
required by the protocol.


Missing resume handling
-----------------------
After a disconnect/reconnect of a link, and after shutdown/restart of a node,
communication of unfinished transactions is not resumed properly. As a result,
ongoing transactions can hang forever, potentially as a result of a deliberate
action of an attacker.


Meeting point ID spoofing
-------------------------
There is no method for guaranteeing meeting point ID uniqueness; when two nodes
use the same meeting point ID on the same network, transactions which route
towards that ID can fail to find a route. As a result, an attacker can make
transaction routing on the Amiko network unreliable.

