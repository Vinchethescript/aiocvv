from . import client
from . import errors
from . import utils
from .errors import *
from .enums import *
from .dataclasses import *
from .me import Me
from .client import ClassevivaClient
from .client import ClassevivaClient as Client  # pylint: disable=reimported

__version__ = "0.0.1"
__author__ = "Vinche.zsh"
__email__ = "vinchethescript@gmail.com"
__license__ = "GPL-3.0"
__description__ = "An asynchronous client for Classeviva written in Python."
__url__ = "https://github.com/Vinchethescript/aiocvv"
