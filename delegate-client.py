#!/usr/bin/env python3
import argparse
import hashlib
import socket
import time
import sys
import os
from os.path import expanduser

__author__ = "VK OPS CREW <ncc(at)vk.com>"
salt2 = b"Aej1ohv8Naish5Siec3U"

parser = argparse.ArgumentParser()
parser.add_argument("target", help="host and port of delegate server you want to connect", metavar="host:port")
parser.add_argument("script", help="name of the script you want to launch")
parser.add_argument("-i", help="override default path to passfile", metavar="path/to/passfile")
parser.add_argument("params", help="parameters to script if applicable", metavar="params", nargs="*")
args = parser.parse_args()

path_to_passfile = expanduser(args.i or "~/.delegate/passfile")

if not os.path.isfile(path_to_passfile):
    print("Can't find passfile: %s" % path_to_passfile)
    sys.exit(1)

key_id, key_value = open(path_to_passfile).readline().strip().encode().split(b":")

target = args.target
host, port = target.split(":", 1)
port = int(port)

server_buffer = b""
server = socket.create_connection((host, port))


def query(data=None):
    global server, server_buffer
    if data is not None:
        r = 0
        data += b"\n"
        while r < len(data):
            r += server.send(data[r:])
    if b"\n" not in server_buffer:
        while True:
            data = server.recv(2048)
            if not len(data):
                raise Exception("server has gone away")
            server_buffer += data
            if b"\n" in data:
                break
    result1, server_buffer = server_buffer.split(b"\n", 1)
    return result1


try:
    hello = query(b"hello")
    result, key = hello.split()
    assert result == b"hello"

    command = [args.script.encode()]
    if args.params:
        for i in args.params:
            command.append(i.encode())

    command_hash = (
        hashlib.sha256(key_value + b":" + salt2 + b":" + key + b":" + b"%".join(command)).hexdigest().encode("ascii")
    )
    started = query(b"run " + key_id + b" " + command_hash + b" " + b" ".join(command))
    queued = None
    while started.startswith(b"queued:"):
        new_queued = int(started.split()[1])
        if queued != new_queued:
            queued = new_queued
            print("\rqueue size: %d" % queued, end="")
        started = query(b"queue")
        time.sleep(0.1)
    if started != b"started":
        print("\rrun fail: %s" % started.decode("iso8859-1"), file=sys.stderr)
        sys.exit(1)

    print("\r[request send]")
    while True:
        log = query()
        if log == b"FINISH":
            break
        if log.startswith(b"queued:"):
            continue
        if log.startswith(b"LOG: "):
            log = log[5:]
            if log.startswith(b"stdout: "):
                log = log[8:]
                print(log.decode("utf-8"))
                continue
            elif log.startswith(b"stderr: "):
                log = log[8:]
                print(log.decode("utf-8"), file=sys.stderr)
                continue
        print("UNKNOWN: " + log.decode("utf-8"))
except Exception as e:
    print(e)
    sys.exit(1)
