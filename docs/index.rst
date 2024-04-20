.. aiocvv documentation master file, created by
   sphinx-quickstart on Fri Mar 15 19:35:54 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to aiocvv's documentation!
==================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:
   
   api/index

This is an API wrapper for Classeviva written in Python using asyncio.

It handles caching automatically, since the API has huge rate limits, and it's
designed to be both as easy to use as possible and as manageable as possible.


Installation
------------
.. code-block:: bash

   pip install -U aiocvv

Quickstart
----------
.. code-block:: python

   import asyncio
   import aiocvv

   async def main():
      # NOTE: WIthout awaiting, you'll have to run "await client.login()", otherwise you won't be able to use it
      client = await aiocvv.Client("username", "password")
      print(f"Hello, {client.me.name}!")
      print(f"Your school is {client.me.school.name} at {client.me.school.city}.")

   asyncio.run(main())


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
