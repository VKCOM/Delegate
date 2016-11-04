import select
from lib.module import Module

__author__ = 'VK OPS CREW <ncc(at)vk.com>'


class Epoll(Module):
    def __init__(self, server1):
        super().__init__(server1)
        self.__epoll = select.epoll()
        self.__callback = {}
        self.__timeout = 0
        self.__default_timeout = 0.5
        self._server.epoll = self
        self._server.action_add(self._continue(self.poll, ()))
        self._server.action_sleep_add(self._continue(self.sleep, ()))

    def sleep(self):
        self.__timeout = self.__default_timeout

    def register(self, handler, callback):
        fileno = handler.fileno()
        assert fileno not in self.__callback
        self.__callback[fileno] = callback
        self.__epoll.register(handler,
                              select.EPOLLIN | select.EPOLLOUT | select.EPOLLERR | select.EPOLLHUP | select.EPOLLET)

    def unregister(self, handler):
        fileno = handler.fileno()
        self.__epoll.unregister(handler)
        del self.__callback[fileno]

    def poll(self):
        self._log("poll from epoll#%d" % self.__epoll.fileno(), verbosity=5)
        try:
            for fileno, events in self.__epoll.poll(timeout=self.__timeout):
                self.__timeout = 0
                self._server.wake()
                self._log("event from epoll#%d for #%d:%d" % (self.__epoll.fileno(), fileno, events), verbosity=4)

                yield self._continue(self.__callback[fileno], (events,))
        except IOError:
            # TODO: check if EINTR, exit if not
            pass
