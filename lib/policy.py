from config import config

__author__ = "VK OPS CREW <ncc(at)vk.com>"


class Policy:
    def __init__(self, user=None, group=None, parameters=None, script=None):
        self.user = user
        self.group = group
        self.parameters = parameters
        self.script = script


class PolicyManager:
    def __init__(self, key_manager, logger):
        self.policies = []
        self.users = {}
        self.groups = {}
        self.cmds = {}
        self.key_manager = key_manager
        self.log = logger

    def add_policy(self, policy):
        ok_user = False
        ok_group = False
        if policy.user is not None:
            if self.key_manager.get_user_key(policy.user) is None:
                self.log("Can not find key for user %s" % str(policy.user), "E")
                return False
            else:
                ok_user = True
        if policy.group is not None:
            if not self.key_manager.has_group(policy.group):
                self.log("Can not find key for group %s" % str(policy.group), "E")
                return False
            else:
                ok_group = True
        if ok_user and ok_group:
            self.log("Ambiguous rule. Use either user or group.", "E")
            return False
        if policy.script is None:
            self.log("You should specify script to launch", "E")
            return False
        if policy.script.decode() not in config.scripts:
            self.log("Can not find script %s" % policy.script, "E")
            return False
        if policy.user in self.users:
            self.users[policy.user].append(policy)
        else:
            self.users[policy.user] = [policy]
        if policy.group in self.groups:
            self.groups[policy.group].append(policy)
        else:
            self.groups[policy.group] = [policy]
        if policy.script in self.cmds:
            self.cmds[policy.script].append(policy)
        else:
            self.cmds[policy.script] = [policy]
        self.policies.append(policy)
        return True

    def dump_policies(self):
        for policy in self.policies:
            result_string = ""
            if policy.user is not None:
                result_string += "-u %s " % policy.user.decode()
            if policy.group is not None:
                result_string += "-g %s " % policy.group.decode()
            for param in policy.parameters:
                result_string += "-p %s " % param.decode()
            result_string += policy.script.decode() + "\n"
            print(result_string)

    def check_request(self, request):
        user_to_check = request.signed_with
        cmd_to_check = request.script
        self.log("Checking permissions for user %s to execute %s" % (user_to_check, cmd_to_check), "N", 2)
        if cmd_to_check not in self.cmds:
            self.log("Can't check permissions for non-existing scripts %s" % cmd_to_check, "E")
            return False
        for policy in self.cmds[cmd_to_check]:
            if user_to_check == policy.user:
                return policy
            elif policy.group is not None:
                groups = self.key_manager.get_user_groups(user_to_check)
                if groups is not None:
                    if policy.group in groups:
                        return policy
        self.log("No actual policy rule found", "E", 2)
        return False
