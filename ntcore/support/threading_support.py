'''
    Polyfill for Condition.wait_for()
    
    Copied from Python 3.5 source code, Python license
'''

import sys

__all__ = ['Condition']

if sys.version_info[0] >= 3: # technically, 3.2... but we don't support 3.2
    from threading import Condition
else:

    from monotonic import monotonic as _time
    from threading import Condition as _ConditionBase
    
    
    class Condition(_ConditionBase):
        
        def wait_for(self, predicate, timeout=None):
            """Wait until a condition evaluates to True.
    
            predicate should be a callable which result will be interpreted as a
            boolean value.  A timeout may be provided giving the maximum time to
            wait.
    
            """
            endtime = None
            waittime = timeout
            result = predicate()
            while not result:
                if waittime is not None:
                    if endtime is None:
                        endtime = _time() + waittime
                    else:
                        waittime = endtime - _time()
                        if waittime <= 0:
                            break
                self.wait(waittime)
                result = predicate()
            return result
        
