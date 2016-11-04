import signal
import queue
from config import config as cfg

__author__ = 'VK OPS CREW <ncc(at)vk.com>'


class Server:
    def __init__(self, logger1, keys1, policy1, config, queuer):
        self.log = logger1
        self.keys = keys1
        self.policy = policy1
        self.pool = None
        self.__config = config
        self.__queue = {}
        self.__finish = False
        self.__sleep = False
        self.__actions_start = []
        self.__actions_sleep = []
        self.__actions_now = queue.Queue()
        self.__queuer = queuer
        self.__sigchld = None
        # self.__actions_cron = []

        signal.signal(signal.SIGTERM, lambda signo, frame: self.__signal(signo))
        signal.signal(signal.SIGUSR1, lambda signo, frame: self.__signal(signo))
        signal.signal(signal.SIGCHLD, lambda signo, frame: self.__signal(signo))
        signal.signal(signal.SIGUSR2, lambda signo, frame: self.__signal(signo))
        # TODO: more signals (HUP)

    def __signal(self, signo):
        if signo == signal.SIGTERM:
            # self.log("[SIGTERM]")
            self.__finish = True
        elif signo == signal.SIGUSR1:
            self.log.reopen()
            # self.log("logs rotated")
        elif signo == signal.SIGCHLD:
            self.log.reopen()
            self.wake()
            # self.log("caught SIGCHLD, ignore it")
        elif signo == signal.SIGUSR2:
            self.reload_config()
        else:
            self.log("unknown signal: %d" % signo, "E")
            self.__finish = True

    def action_add(self, action):
        self.__actions_start.append(action)

    def action_sleep_add(self, action):
        self.__actions_sleep.append(action)

    def action_postpone(self, action):
        self.__actions_now.put(action)

    def set_sigchld(self, action):
        self.__sigchld = action

    def wake(self):
        self.__sleep = False

    def reload_config(self):
        self.log("Rereading config", "L")
        from lib.config_loader import ConfigLoader
        from lib.keymanager import KeyManager
        from lib.policy import PolicyManager
        keys = KeyManager(self.log)

        policy = PolicyManager(keys, self.log)
        loader = ConfigLoader(
            self.log,
            self.__config["path_to_users"],
            self.__config["path_to_policies"],
            policy,
            keys
        )
        if loader.read():
            self.keys = keys
            self.policy = policy
            self.log("Successfully updated config", "L")
        else:
            self.log("Failed to reread config", "E")

    def run(self):
        actions = queue.Queue()
        try:
            while True:
                self.log("actions queue: %d" % actions.qsize(), "L", 4)
                if actions.empty():
                    if self.__finish:
                        break
                    if self.__sigchld is not None:
                        actions.put(self.__sigchld)
                        self.__sigchld = None
                    if not self.__actions_now.empty():
                        actions = self.__actions_now
                        self.__actions_now = queue.Queue()
                        continue
                    if self.__sleep:
                        for x in self.__actions_sleep:
                            actions.put(x)
                    self.__sleep = True
                    for x in self.__actions_start:
                        actions.put(x)
                    continue
                action = actions.get()
                result = action()
                if result is None:
                    continue
                for x in result:
                    actions.put(x)
        except KeyboardInterrupt:
            self.log("[Ctrl+C]")
        self.log("TODO: graceful exit (close all sockets etc)")

    def enqueue(self, request):
        request.access = self.policy.check_request(request)
        action = request.script.decode()
        token = cfg.scripts.get(action, {}).get('lock', '')
        if token is None:
            token = 'default'
        if token not in self.__queue:
            limit = 1
            if 'limit' in self.__config and token in self.__config['limit']:
                limit = self.__config['limit'][token]
            self.__queue[token] = self.__queuer(self, limit=limit)
        self.__queue[token].append(request)

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        signal.signal(signal.SIGUSR1, signal.SIG_DFL)
        self.log("TODO: close all sockets")
