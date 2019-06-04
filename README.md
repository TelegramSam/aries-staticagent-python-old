Agent Concept
=============

This is an exploration into a new routing and transport handling mechanism for agents. Most of the ideas are evolutions
of the functionality featured in the [Python Reference Agent][1]. This concept agent may eventually end up as the Python
Reference Agent 2.0 and will almost certainly become the backbone of the Agent Test Suite (DID Comm Protocol Test
Suite).

As this agent has developed, three main things differentiate it from the original reference agent:

1. Cleaner separation of concerns
	- Transport (both sending and receiving) of messages are handled solely by the `Conductor`.
	- Packaging is also handled by the `Conductor`.
	- The `Agent` only ever handles fully unpacked messages with [Message Trust Context][2] attached. (Currently
		only provisional context is implemented, pending a more complete solution)
2. New message handling mechanism
	- Message handlers can be registered in three different ways (detailed examples below)
		- `@agent.route('message_type')` decorator on handler methods.
		- `@module` decorator and explicit route definitions with `@route_def` decorator.
		- `@module` decorator and implicit route definitions through methods matching message type names.
3. Hooks
	- By defining hook points and registering hooks for a hook point, cleaner separation between modules and validators
		can be achieved.
	- Hook points inside of a class can be defined with `@self_hook_point` decorator on the method to wrap in hooks.
	- Hook points outside of a class can be defined with `@hook_point` decorator on the method to wrap in hooks.
	- Hooks are declared using `@hook('post_METHOD')` decorator or through `register_hook` methods on hook-able objects.

[1]: https://github.com/hyperledger/indy-agent/tree/master/python
[2]: https://github.com/hyperledger/aries-rfcs/tree/master/concepts/0029-message-trust-contexts

Stay tuned for a more in depth README
