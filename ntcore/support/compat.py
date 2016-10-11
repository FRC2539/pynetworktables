
import sys

try:
    from configparser import RawConfigParser
except ImportError:
    from ConfigParser import RawConfigParser

try:
    from queue import Queue, Empty
except ImportError:
    from Queue import Queue, Empty

if sys.version_info[0] == 2:
    range = xrange
else:
    range = range