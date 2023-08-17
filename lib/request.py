__author__ = "VK OPS CREW <ncc(at)vk.com>"


class Request:
    def __init__(self, key, script, arguments, client):
        self.signed_with = key
        self.script = script
        self.arguments = arguments
        self.client = client
        self.queue = None
        self.index = None
        self.access = None
