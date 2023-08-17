import hashlib
from config import config
from lib.module import Module
from lib.request import Request

__author__ = "VK OPS CREW <ncc(at)vk.com>"

connection_id = 0
with open("/dev/random", "rb") as f:
    salt_random = f.read(32)
cfg = config.config


class Connector(Module):
    def __init__(self, server1, socket):
        super(Connector, self).__init__(server1)
        global connection_id  # , salt_random
        self.__id = connection_id
        self.__salt_random = salt_random
        with open("/dev/urandom", "rb") as f1:
            self.__salt_random += f1.read(32)
        connection_id += 1
        self.__socket = socket
        self.__local_id = 0
        self.__hash = None
        self.__request = None
        self.__commands = {b"test": self.__cmd_test, b"hello": self.__cmd_hello}
        self.salt1 = cfg["salt1"]
        self.salt2 = cfg["salt2"]

    def __run(self, command_key, command_hash, command_run):
        self._log("__run")
        user_key = self._server.keys.get_user_key(command_key)
        if user_key is None:
            self._log("user not found: %s" % command_key.decode("ascii"))
            return self.__socket.write(b"Unauthorized\n")
        real_key = user_key
        real_hash = (
            hashlib.sha256(b":".join([real_key, self.salt2, self.__hash, b"%".join(command_run)]))
            .hexdigest()
            .encode("ascii")
        )
        self.__hash = None
        if command_hash != real_hash:
            self._log("hash mismatch: %s vs %s" % (command_hash, real_hash))
            return self.__socket.write(b"Unauthorized\n")

        self.__request = Request(command_key, command_run[0], command_run[1:], self)

        self._server.enqueue(self.__request)
        self.__commands[b"queue"] = self.__cmd_queue

    # commands
    def __cmd_test(self):
        self.__socket.write(b"test ok\n")

    def __cmd_hello(self):
        self.__hash = (
            hashlib.sha256(self.salt1 + self.__salt_random + (":%d_%d" % (self.__id, self.__local_id)).encode("ascii"))
            .hexdigest()
            .encode("ascii")
        )
        self.__local_id += 1
        self.__socket.write(b"hello " + self.__hash + b"\n")
        self.__commands[b"run"] = self.__cmd_run

    def __cmd_run(self, arguments):
        self._log("__cmd_run")
        if len(arguments) < 3 or self.__hash is None:
            return self.__socket.write(b"run failed")
        self.__run(arguments[0], arguments[1], arguments[2:])

    def __cmd_queue(self):
        if self.__request is None:
            return self.write_error(b"no active request")
        self.write_queue(self.__request.index - self.__request.queue.done)

    # responses
    def write_log(self, message):
        self.__socket.write(b"LOG: " + message + b"\n")

    def write_finish(self):
        self.__socket.write(b"FINISH\n")

    def write_start(self):
        self.__socket.write(b"started\n")

    def write_error(self, message):
        self.__socket.write(b"error: " + message + b"\n")

    def write_queue(self, index):
        self.__socket.write(("queued: %d\n" % index).encode("ascii"))

    # caller
    def __call__(self, command):
        command = command.split()
        if len(command) == 0:
            return
        try:
            routine = self.__commands[command[0]]
        except KeyError:
            self.__socket.write(b"unknown command: " + command[0] + b"\n")
            routine = lambda *x: None
        return routine(command[1:])
