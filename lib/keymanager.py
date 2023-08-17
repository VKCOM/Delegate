__author__ = "VK OPS CREW <ncc(at)vk.com>"


class KeyManager:
    def __init__(self, logger):
        self.log = logger
        self.__users__ = dict()
        self.__groups__ = dict()

    def add_user(self, name, secret):
        if name in self.__users__:
            self.log("Already has user %s" % name, "W")
            return False
        else:
            self.log("Added new user %s" % name, "L", 2)
            self.__users__[name] = {"key": secret}
            return True

    def del_user(self, name):
        if name in self.__users__:
            if "groups" in self.__users__[name]:
                for i in self.__users__[name]["groups"]:
                    self.__groups__[i].remove(name)
            self.__users__.__delitem__(name)
            self.log("Removed key for %s" % name)
        else:
            self.log("Can't remove non-existing user %s" % name, "E")

    def get_user_key(self, name):
        if name in self.__users__:
            self.log("Requested key for %s" % name, "L", 3)
            return self.__users__[name]["key"]
        else:
            self.log("Requested key for non-existing %s" % name, "E")
            return None

    def get_user_groups(self, name):
        if name in self.__users__:
            self.log("Requested groups for %s" % name, "L", 3)
            if "groups" in self.__users__[name]:
                return self.__users__[name]["groups"]
            else:
                return None

    def get_users(self):
        return [str(x) for x in self.__users__.keys()]

    def add_group(self, name):
        if name in self.__groups__:
            self.log("Already has a group %s" % name, "E")
            return False
        else:
            self.__groups__[name] = list()
            return True

    def add_group_member(self, username, groupname):
        if username in self.__users__:
            if groupname in self.__groups__:
                self.__groups__[groupname].append(username)
                if "groups" not in self.__users__[username]:
                    self.__users__[username]["groups"] = list()
                self.__users__[username]["groups"].append(groupname)
                self.log("Added %s to %s" % (username, groupname), "L", 2)
                return True
            else:
                self.log("Has no group %s" % groupname, "E")
                return False
        else:
            self.log("Has no user %s" % username, "E")
            return False

    def remove_group_member(self, username, groupname):
        if username in self.__users__:
            if groupname in self.__groups__:
                if username in self.__groups__[groupname]:
                    self.log("Removing %s from %s" % (username, groupname), "N", 2)
                    self.__users__[username]["groups"].remove(groupname)
                    self.__groups__[groupname].remove(username)
                    return True
                else:
                    self.log("Can't remove non-member %s from %s" % (username, groupname), "E")
            else:
                self.log("Can't remove from non-existing group %s" % groupname, "E")
        else:
            self.log("Can't remove non-existing user %s" % username, "E")
        return False

    def get_group_members(self, groupname):
        if groupname in self.__groups__:
            self.log("Requested group members for %s" % groupname, "N", 3)
            return self.__groups__[groupname]
        else:
            self.log("Requested group members for non-existing %s" % groupname, "E")
            return None

    def has_group(self, groupname):
        return groupname in self.__groups__

    def has_user(self, username):
        return username in self.__users__
