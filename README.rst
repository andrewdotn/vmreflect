=======================================================================
``vmreflect``: A TCP Proxy Reflector for Windows Virtual Machine Guests
=======================================================================

You’re developing a dynamic website on your MacBook, using Django or
Ruby on Rails or something. The development website is being served as
HTTP at ``localhost:8000``. You need to test it in Internet Explorer.
But you don’t want to open up the firewall on your MacBook.

.. figure:: doc/images/firewall.png
   :alt: Mac firewall settings dialog with “Block all incoming connections” checked

``vmreflect`` sets up a tunnel so that ``localhost:8000`` in a Windows
virtual machine running under VMware Fusion forwards to ``localhost:8000``
on your Mac, without doing anything to your firewall, and without opening
any new listening ports on your Mac. It does this by automatically
installing and configuring `TCP Proxy Reflector
<http://blog.magiksys.net/software/tcp-proxy-reflector>`__ by Alain
Spineux. ``vmreflect`` starts a forwarding process on your Mac, connects it
to a listening port on the VM, and tunnels traffic between the two.

Using ``vmreflect``
===================

1. Turn off the firewall on the Windows VM. If it’s a
   website-testing-only VM that you always keep behind VMware’s NAT,
   this shouldn’t be a problem.

2. Make sure there’s a password set in the Windows VM. The VMware API
   doesn’t allow a program to modify anything inside a virtual machine
   unless the program first authenticates with a valid username and
   password. ``vmreflect`` uses default values of ``Administrator`` and
   ``test``.

3. Run ``vmreflect NAME-OF-VM``.

----

| Andrew Neitsch
| March 2013
