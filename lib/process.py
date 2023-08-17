import os
import errno
import fcntl
import select
import signal
from lib.module import Module

__author__ = "VK OPS CREW <ncc(at)vk.com>"


class Pool(Module):
    def __init__(self, server):
        super(Pool, self).__init__(server)
        assert self._server.pool is None
        self._server.pool = self
        self.__pids = {}
        signal.signal(signal.SIGCHLD, self.__sigchld)

    def __sigchld(self, signo):
        assert signo == signal.SIGCHLD
        # self._log('SIGCHLD')
        self._server.set_sigchld(self._continue(self.__check_all, ()))
        # self._server.action_postpone(self._continue(self.__check_all, ()))

    def __check_all(self):
        for x in self.__pids.values():
            yield self._continue(x.check, ())
        return
        while True:
            try:
                pid, pid_exit, pid_usage = os.wait3(os.WNOHANG)
            except OSError as why:
                if why.errno == errno.ECHILD:
                    break
                else:
                    raise why
            # except ChildProcessError:
            #     break
            if not pid:
                break
            self._log("process %d exited: %d" % (pid, pid_exit))
            self._log("postpone check process: %s" % pid, 2)
            yield self._continue(self.__pids[pid].check, ())

    def register(self, pid, process):
        assert pid not in self.__pids
        self.__pids[pid] = process

    def unregister(self, pid):
        assert pid in self.__pids
        del self.__pids[pid]


class Process(Module):
    def __init__(self, server, popen, request):
        super(Process, self).__init__(server)
        self.__request = request
        self.__process = popen
        self.__data = b""
        self.__pid = popen.pid
        self.__stdout = popen.stdout
        self.__stderr = popen.stderr
        self.__finished = False
        self._server.pool.register(self.__pid, self)

        fl = fcntl.fcntl(self.__stdout, fcntl.F_GETFL)
        fcntl.fcntl(self.__stdout, fcntl.F_SETFL, fl | os.O_NONBLOCK)
        fl = fcntl.fcntl(self.__stderr, fcntl.F_GETFL)
        fcntl.fcntl(self.__stderr, fcntl.F_SETFL, fl | os.O_NONBLOCK)
        self._server.epoll.register(self.__stdout, lambda events: self.__handle(b"stdout", self.__stdout, events))
        self._server.epoll.register(self.__stderr, lambda events: self.__handle(b"stderr", self.__stderr, events))

    def __handle(self, type_of, handle, events):
        assert events
        if events & select.EPOLLIN:
            events &= ~select.EPOLLIN
            self.__communicate(handle, type_of)
        if events & select.EPOLLHUP:
            events &= ~select.EPOLLHUP
            yield self._continue(self.__request.queue.run_next, ())
        if events:
            self._log("unhandled poll events: 0x%04x\n" % events, "D", 3)
        assert not events

    def __communicate(self, handle=None, type_of=None):
        if self.__finished:
            return
        if handle is None:
            for x, y in [(self.__stdout, b"stdout"), (self.__stderr, b"stderr")]:
                self.__communicate(x, y)
            return
        while True:
            from io import BlockingIOError

            try:
                data = handle.read()
                # print(type(data))
                if type(data) != bytes:
                    data = bytes(data, "ascii")
                # print(type(data))
                if data is None or not data:
                    break
            except BlockingIOError:
                break
            except EOFError:
                break
            self._log("received from process: %s" % ("".join("%c" % x for x in data)), verbosity=3)
            data = data.split(b"\n")
            for chunk in data[:-1]:
                self.__request.client.write_log(type_of + b": " + self.__data + chunk)
                self.__request.data = b""
            self.__data = data[-1]

    def check(self):
        self._log("check process: %s" % self.__pid, verbosity=2)
        finished = self.__process.poll()
        if finished is None:
            return
        self._log("subprocess poll: %s" % str(finished), "D", 3)
        self._server.wake()
        self.__communicate()
        if self.__data:
            self.__request.client.write_log(self.__data + b"%[noeoln]")
        self.__request.client.write_finish()
        self._server.epoll.unregister(self.__stdout)
        self._server.epoll.unregister(self.__stderr)
        self.__stdout.close()
        self.__stderr.close()
        self.__finished = True
        self._server.pool.unregister(self.__pid)
        # no yield from in python3.2
        for x in self.__request.queue.terminated():
            yield x
