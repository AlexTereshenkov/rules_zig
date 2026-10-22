#!/usr/bin/env python3
"""Update all generated files of the rule set, on any platform.

This is a thin wrapper around the `//util:update_all` multirun target.
On Windows, `bazel run` cannot execute the `.bash` script that multirun
generates, so the target is run through bash there. Bazel does not provide the
workspace variables to scripts run that way, and starts them in the runfiles
directory, so they are set explicitly.
"""

import os
import platform
import shutil
import subprocess
import sys
import tempfile

TARGET = "//util:update_all"


def main():
    if (workspace := os.getenv("BUILD_WORKSPACE_DIRECTORY")) is None:
        sys.exit("The workspace root was not found. Execute with `bazel run //util:update`.")
    if (bazel := shutil.which("bazel")) is None:
        sys.exit("Could not find the bazel executable.")

    command = [bazel, "run"]
    with tempfile.TemporaryDirectory() as tmp:
        if platform.system() == "Windows":
            # Not `bash` from PATH, it may be WSL's, which cannot see Windows paths.
            if (bash := os.getenv("BAZEL_SH")) is None:
                sys.exit("Set BAZEL_SH to the path of an MSYS2, e.g. C:/msys64/usr/bin/bash.exe.")
            # Use forward slashes, as backslashes would be treated as escapes.
            bash = bash.replace("\\", "/")
            workspace = workspace.replace("\\", "/")
            # Put it first in PATH, as scripts use `#!/usr/bin/env bash`. The
            # directory has to be in POSIX style (/c/...), as PATH is split at colons.
            bash_dir = os.path.dirname(bash)
            bash_dir = f"/{bash_dir[0].lower()}{bash_dir[2:]}"
            wrapper = os.path.join(tmp, "run_under.sh").replace("\\", "/")
            with open(wrapper, "w", newline="\n") as f:
                f.write(f"export BAZEL_SH='{bash}'\n")
                f.write(f"export PATH='{bash_dir}':\"$PATH\"\n")
                f.write(f"export BUILD_WORKSPACE_DIRECTORY='{workspace}'\n")
                f.write(f"export BUILD_WORKING_DIRECTORY='{workspace}'\n")
                f.write(f"exec '{bash}' \"$@\"\n")
            # The Python runner of multirun needs a real runfiles tree, which
            # Windows disables by default.
            command += [f'--run_under="{bash}" "{wrapper}"', "--enable_runfiles"]
        command.append(TARGET)
        sys.exit(subprocess.call(command, cwd=workspace))


if __name__ == "__main__":
    main()
