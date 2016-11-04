from lib.module import Module
from lib.scripts import launch_script
from lib.process import Process

__author__ = 'VK OPS CREW <ncc(at)vk.com>'


class RequestQueue(Module):
    def __init__(self, server1, limit=1):
        super(RequestQueue, self).__init__(server1)
        self.__queue = []
        self.__active = 0
        self.__prestart = 0
        self.__done = 0
        self.__limit = limit
        self.__index = 0
        self._server.action_add(self._continue(self.run_next, ()))

    @property
    def done(self):
        return self.__done

    def append(self, request):
        self.__index += 1
        request.index = self.__index
        request.queue = self
        self.__queue.append(request)
        request.client.write_queue(request.index - self.__done)
        self._log("new request #%d, queue size: %d" % (request.index, len(self.__queue)))

    def run_next(self):
        if not self.__active + self.__prestart < self.__limit:
            return
        if len(self.__queue) == 0:
            return
        self.__prestart += 1
        self._server.wake()
        request = self.__queue[0]
        self.__queue = self.__queue[1:]  # TODO: optimize
        yield self._continue(self.__run, (request,))

    def __run(self, request):
        assert self.__active < self.__limit
        self.__prestart -= 1
        if request.access is False:
            request.client.write_error(b'access_denied')
            return
        self.__active += 1
        request.client.write_start()
        request.process = Process(self._server, launch_script(request), request)

    def terminated(self):
        self._log('Active cleared, in queue: %d' % len(self.__queue), "D", 3)
        self.__active -= 1
        self.__done += 1
        yield self._continue(self.run_next, ())

