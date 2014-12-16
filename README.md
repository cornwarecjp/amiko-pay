Amiko-pay
=========

Fast, scalable and decentralized payment network for Bitcoin, inspired by the Ripple.

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

https://bitcointalk.org/index.php?topic=94674.0

https://bitcointalk.org/index.php?topic=157437.0

https://github.com/cornwarecjp/amiko-pay

How to use
==========

Before using Amiko-pay, please check whether any local laws restrict the use of
this software. Ideally, there should be no such laws, but if they do exist,
you may still be able to use Amiko-pay legally by constraining the behavior of
the software, for instance through its settings. The makers of Amiko-pay do not
encourage breaking the law; if you decide to break the law, you do this at
your own responsibility.

Please read the file "COPYING" for licensing information.

Compilation and installation instructions can be found in the file "INSTALL".

See doc/manual.md for further usage information.

