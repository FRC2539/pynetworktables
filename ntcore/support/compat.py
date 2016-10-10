
import sys

if sys.version_info[0] == 2:
    range = xrange
else:
    range = range

try:
    from queue import Queue, Empty
except ImportError:
    from Queue import Queue, Empty
