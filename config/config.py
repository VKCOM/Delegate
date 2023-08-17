__author__ = "VK OPS CREW <ncc(at)vk.com>"

config = {
    "serve": "0.0.0.0",
    "port": 2390,
    "verbosity": 1,
    "salt1": b"ahThiodai0ohG1phokoo",
    "salt2": b"Aej1ohv8Naish5Siec3U",
    "path_to_users": "config/users",
    "path_to_policies": "config/policies",
    "limit": {"default": 10, "date": 2},
}

scripts = {
    "test2": {
        "cmd_line": "/bin/sleep",
        "need_arguments": True,
        "default_arguments": ["5"],
    },
    "test_args": {
        "cmd_line": "/bin/echo",
        "need_arguments": True,
        "default_arguments": ["5"],
    },
    "test": {
        "cmd_line": "/bin/date",
        "need_arguments": False,
        "lock": "date",
        "default_arguments": [],
    },
    "test_date2": {
        "cmd_line": "/bin/date",
        "need_arguments": False,
        "lock": None,
        "default_arguments": ["+%s"],
    },
}
