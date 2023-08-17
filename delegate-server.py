#!/usr/bin/env python3
import sys
from config import config

__author__ = "VK OPS CREW <ncc(at)vk.com>"

config = config.config
if not isinstance(config, dict):
    print("Can't open config")
    sys.exit(1)

salt1 = config["salt1"]
salt2 = config["salt2"]

if __name__ == "__main__":
    from lib.logger import Logger
    from lib.keymanager import KeyManager
    from lib.policy import PolicyManager
    from lib.config_loader import ConfigLoader
    from lib.auth import Connector
    from lib.epoll import Epoll
    from lib.request_queue import RequestQueue
    from lib.server import Server
    from lib.sockets import ServerSocket
    from lib.process import Pool

    logger = Logger(outfile=config.get("log-file", None), verbosity=config["verbosity"])
    keys = KeyManager(logger)
    policy = PolicyManager(keys, logger)
    loader = ConfigLoader(logger, config["path_to_users"], config["path_to_policies"], policy, keys)
    res = loader.read()
    if not res:
        logger("Failed to read config. Exiting", "E")
    else:
        with Server(logger, keys, policy, config=config, queuer=RequestQueue) as server:
            epoll = Epoll(server)
            process_pool = Pool(server)
            server_socket = ServerSocket(server, Connector)
            logger("Server started")
            server.run()
