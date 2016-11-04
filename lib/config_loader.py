from lib.policy import Policy
from config import config

__author__ = 'VK OPS CREW <ncc(at)vk.com>'
cfg = config.config


class ConfigLoader:
    def __init__(self, log, users_file, policies_file, policy_manager, key_manager):
        self.log = log
        self.users_file = users_file
        self.policies_file = policies_file
        self.policy_manager = policy_manager
        self.key_manager = key_manager

    def read(self):
        try:
            users_fd = open(self.users_file, "r")
            policies_fd = open(self.policies_file, "r")
        except IOError as e:
            self.log(e, "E")
            return False
        for line in users_fd.readlines():
            if line.strip().encode() == b"":
                continue    # empty line
            l = line.strip().encode().split(b"#")[0].strip().split(b":")
            # TODO: move this check somewhere else
            if len(l) > 2:
                self.log("More than one ':' while parsing users file?", "E")
                return False
            if b"group" in l[0][0:5]:
                self.key_manager.add_group(l[0].split(b" ")[1])
                for u in l[1].strip().split(b" "):
                    self.key_manager.add_group_member(u, l[0].split(b" ")[1])
            else:
                self.key_manager.add_user(l[0].strip(), l[1].strip())
        users_fd.close()

        cnt = 0
        for line in policies_fd.readlines():
            if line.strip().encode() == b"":
                continue    # empty line
            cnt += 1
            tokens = line.strip().encode().split(b"#")[0].split(b" ")
            policy = Policy()
            policy.parameters = []
            prev_token = None
            for token in tokens:
                if prev_token == b'-u':
                    policy.user = token
                elif prev_token == b'-g':
                    policy.group = token
                elif prev_token == b'-p':
                    policy.parameters.append(token)
                prev_token = token
            policy.script = tokens[-1]
            if not self.policy_manager.add_policy(policy):
                self.log("    File %s line %d" % (cfg["path_to_policies"], cnt), "E")
                return False
        policies_fd.close()
        return True
