import os
import subprocess
from config import config

__author__ = "VK OPS CREW <ncc(at)vk.com>"
scripts = config.scripts


def launch_script(request):
    policy = request.access

    if b"ALLOW_ARGUMENTS" in policy.parameters and scripts[request.script.decode()]["need_arguments"]:
        arguments = request.arguments
    else:
        arguments = []

    if b"PROVIDE_USERNAME" in policy.parameters:
        os.environ["DELEGATE_USERNAME"] = request.signed_with.decode()

    process = subprocess.Popen(
        args=[scripts[request.script.decode()]["cmd_line"]]
        + scripts[request.script.decode()]["default_arguments"]
        + arguments,
        executable=scripts[request.script.decode()]["cmd_line"],
        stdin=open("/dev/null", "r"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd="/",
    )

    return process
