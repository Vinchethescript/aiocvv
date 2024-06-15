"""
The modules are used to make manual HTTP requests to the Classeviva APIs. These come from the official API documentation and are implemented in the wrapper exactly as they were written on there.

Modules are useful when:

* You use the :attr:`~aiocvv.client.ClassevivaClient.me` attribute in :class:`~aiocvv.client.ClassevivaClient` to get the information you need more easily, which automatically uses the right module;
* You want to make a request to an endpoint that hasn't been/is partially implemented in this wrapper;
* You want to have more control over the request or response;
* You don't want to manually write every URL, like you would do with the :meth:`~aiocvv.client.ClassevivaClient.request` method.

.. note::
    Of course, if you decide to use modules,
    you will have to parse the response yourself,
    as they only return the raw response.

.. warning::
    The modules are not made to be manually constructed, but
    to be used through the :class:`~aiocvv.client.ClassevivaClient` instance.
"""

from .teachers import TeachersModule
from .students import StudentsModule
from .parents import ParentsModule
