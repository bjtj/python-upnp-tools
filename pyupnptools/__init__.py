from __future__ import print_function
from .ssdp import *
from .upnp_control_point import *
from .upnp_server import *
import logging

logging.basicConfig(level=logging.ERROR,
                    format='[%(asctime)s] %(name)s %(levelname).1s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
