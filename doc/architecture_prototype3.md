Introduction
============

Prototype 3 is the third major design iteration of Amiko Pay.

The first prototype had a massive multi-threading architecture, where every
transaction was handled by a separate thread. The problem with this design was
that there was a lot of data that is shared between different transactions,
so a lot of synchronization needed to take place. Besides, threads couldn't
follow a simple "dialogue" design pattern, since a transaction always involves
communicating with two external parties.

The second prototype had an event-based architecture: an entire node ran in a
single thread, processing incoming events (such as arriving network data) one
by one. This was a major improvement in terms of code size and simplicity,
but several problems were solved repeatedly in ad-hoc ways on different places
in the code. This was especially the case for dialogues, and state management
(e.g. loading and storing the state of an object).

The architecture of prototype 3 is based on the following observations:

* The event-based architecture works well. Let's keep it.
* We need to be able to store and restore the relevant part of the state of
  a node to/from disk, to be able to survive crashes. Also, in case of an error
  during the processing of a message (e.g. because the message is part of a
  hacking attempt), we must revert to the previous state, before the message
  was arrived, to ensure that messages don't leave a node in an inconsistent,
  ill-defined state. So, we need a simple way to collect/restore the state
  of many types of objects (links, channels, transactions etc.), and to
  keep old version(s) of the state of a node in memory.
* The state of a node needs to be easily serializable, for storage on disk.
  For diagnostics, it must be possible to print a (summarized) human-readable
  state on screen. Preferrably, storage on disk is also human readable,
  especially during the experimental phase of the software, when the ability
  to tweak is more important than raw performance.
* We need to be able to deal with the (sudden) disconnection of a link.
  Preferrably, the high-level code shouldn't need to know about this, except
  when considering routing directions. During an already started transaction,
  a non-connected link should act the same as a connected, but non-responsive
  link. Messages sent to a disconnected connection should be stored for future
  transmission.
* Messages need to be serializable, both for transmission and for storage as
  part of a node state. For simplicity and ease of diagnosing, the same
  human-readable serialization can be used for all purposes. Note that this
  does hurt performance: some cryptographic elements in the protocol are
  inherently binary, and need to be hex-encoded (50% efficiency) to be part
  of a human readable serialization format.
* We need to be able to deal with time-out events. Objects must be able to
  program the event dispatcher to generate such events.
* There are several cross-references in a node: links reference transactions,
  transactions reference links, both reference a routing context, and the
  routing context references back to links. Such a data structure is hard to
  serialize: preferrably, the data structure of a node state should be a tree,
  which can easily be flattened to serialized data. Cross-references should be
  implemented with IDs (transaction IDs, link IDs etc.).
* There is a lot of internal messaging between different elements in a node:
  when an event is received by one part, it can have effects on several
  other parts, and internal messaging can even go back to the original part.
  However, there are no infinite loops, and each initiating event can be fully
  processed in a limited number of steps.


State machine design
====================

Because of the focus on state data, prototype 3 is inspired by the concept of a
state machine. The number of states of an Amiko node is so high that it would be
undoable to fully write down all states and all state transitions, but the core
idea is maintained that there is a function that receives an input state and
some input data (typically data describing an event that happened), and returns
an output state and some output data. Instead of returning an output state and
some output data, the function may also generate an exception; in that case,
typical behavior would be to log the exception and restore the original state.

One problem of state machines is they are difficult to modularize. The state of
a composed object can be thought of as the concatenation of the states of all
its modules. When the composed object receives an event, it can delegate event
processing to one or more of its modules who are interested in the event. If
they are the only ones that need to update their state, that would be the entire
story. However, all the cross-messaging between objects in Amiko Pay means that
objects might need to alter their state, even when they were not interested in
the original event. Therefore, the composed object needs to make sure all
inter-module messaging is finished, before it can combine all module states into
the new composed state.

Serialization and objects
=========================

The Python json library makes serialization easy, especially when the state
data is composed of only basic Python data types like strings, integers,
booleans, dictionaries and lists. The json library supports escaping of
non-ASCII data, which might be used for easy handling of binary data. As an
alternative, a filter function might be designed that changes some
known-to-be-binary elements in the state to a hexadecimal encoding. Another
type of filtering function might select those parts of a state that are
interesting to display in a user interface.

As a consequence of using json, state data and message data must consist of
only basic Python data types. However, the use of custom classes would be
extremely useful, for instance to identify different types of messages.
To get the best of both worlds, a common base class will be used for all
serializable objects, to assist (de)serialization of custom classes with an
absolute minimum of per-class boilerplate code.


Messages
========

A message contains

* the message type
* of course, the message contents
* the message destination. This is the combination of the ID of the destination
  and a description of the type of the destination. The type description is
  necessary to prevent collisions between the ID namespaces of different types.

Incoming events (e.g. network data) are messages, but internal messaging is also
done with messages. In some cases, messages need to be stored as part of the
node state:

* messages to be sent over a network connection that is currently down
* messages to be sent back to ourselves in the future as time-out events.


Node state structure
====================

This is a (likely incomplete) summary of the state structure and the type of
objects in the state of an Amiko node:

	node
	|
	\- links (ID = local link ID)
	|  |
	|  \- channels (ID = channel index)
	|     |
	|     \- channel-specific data, including IDs of transactions
	|
	\- payee links (ID = payment ID; shared name space with links)
	|  |
	|  \- transaction ID
	|
	\- meeting points (ID = meeting point ID)
	|  |
	|  \- IDs of non-matched transactions
	|
	\- transactions (ID = hash of commit token)
	   |
	   \- meeting point ID
	   |
	   \- link IDs (including remaining links for unfinished routing)

The not-yet-transmitted messages (network messages to be sent to a currently
closed network connection, and time-out messages to be sent in the future)
are not included in this diagram: they *should* be stored to disk, to be
restored after shutdown / crash, but they are handled by the event dispatcher.
Storing them here would imply external code changing the state object;
this is avoided by storing them outside the node state.

