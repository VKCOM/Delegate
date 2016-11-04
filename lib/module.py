__author__ = 'VK OPS CREW <ncc(at)vk.com>'


class Module:
    def __init__(self, server1):
        self._server = server1
        self._log = lambda *args, **kwargs: self._server.log(*args, **kwargs)

    def _continue(self, routine, arguments):
        def continuation():
            nonlocal routine, arguments
            return routine(*arguments)
        return continuation
