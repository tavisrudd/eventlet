try:
    # shoot for epoll module first
    from epoll import poll as epoll
except ImportError, e:
    # if we can't import that, hope we're on 2.6
    from select import epoll

import time
from eventlet.hubs.hub import BaseHub
from eventlet.hubs import poll
from eventlet.hubs.poll import READ, WRITE

# NOTE: we rely on the fact that the epoll flag constants
# are identical in value to the poll constants

class Hub(poll.Hub):
    WAIT_MULTIPLIER = 1.0  # epoll.poll's timeout is measured in seconds
    def __init__(self, clock=time.time):
        BaseHub.__init__(self, clock)
        self.poll = epoll()
        try:
            # modify is required by select.epoll
            self.modify = self.poll.modify
        except AttributeError:
            self.modify = self.poll.register

    def add(self, evtype, fileno, cb):
        oldlisteners = bool(self.listeners[READ].get(fileno) or
                            self.listeners[WRITE].get(fileno))
        listener = BaseHub.add(self,evtype, fileno, cb)
        if not oldlisteners:
            # Means we've added a new listener
            self.register(fileno, new=True)
        else:
            self.register(fileno, new=False)
        return listener
