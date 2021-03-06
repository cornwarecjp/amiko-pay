Amiko-pay
=========

Fast, scalable and decentralized payment network for Bitcoin.

The basic idea of Amiko-pay is that it forms a network of micro-transaction links:

https://en.bitcoin.it/wiki/Contracts#Example_7:_Rapidly-adjusted_.28micro.29payments_to_a_pre-determined_party

Payments between parties are then routed over this network, and performed by
atomically adjusting all micro-transaction links on the route.

The result is that transactions become secure without having to register them in
the Bitcoin block chain. This has the following advantages:
* Transactions become near-instantaneous (you no longer have to wait for block chain confirmations)
* The block chain can remain smaller, so the system as a whole (Bitcoin+Amiko) becomes more scalable
* Block chain transaction fees can be avoided, so transactions can become cheaper.

Links:

Website:
http://cornwarecjp.github.io/amiko-pay

Source code:
https://github.com/cornwarecjp/amiko-pay

Forum threads:
https://bitcointalk.org/index.php?topic=94674.0
https://bitcointalk.org/index.php?topic=157437.0


How to use
==========

Please read the file "COPYING" for licensing information.

Installation instructions can be found in the file "INSTALL".

See doc/manual.md for further usage information.

