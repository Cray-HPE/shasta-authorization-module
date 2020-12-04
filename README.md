--
This is an ansible module that simplifies interacting with JSON based 
Shasta microservices with authorization tokens. It relies on running APIs
to type check variables passed in via the request itself.

More complete documentation and examples for how to use this are included
in the 'authorized.py' module itself.

This module requires one of the following conditions to be true in order
for automatic authorization to function:
- Kubectl on the target node, such that 'oauth-client-secret' can be obtained.
- Users passing in 'oauth-client-secret' explicitly.
