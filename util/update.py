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
            # Use forward slashes, as bash and Bazel's option parser would
            # otherwise treat backslashes as escape characters.
            workspace = workspace.replace("\\", "/")
            wrapper = os.path.join(tmp, "run_under.sh").replace("\\", "/")
            with open(wrapper, "w", newline="\n") as f:
                f.write("#!/bin/bash\n")
                f.write(f"export BUILD_WORKSPACE_DIRECTORY='{workspace}'\n")
                f.write(f"export BUILD_WORKING_DIRECTORY='{workspace}'\n")
                f.write('exec bash "$@"\n')
            # The Python runner of multirun needs a real runfiles tree, which
            # Windows disables by default.
            command += [f"--run_under=bash {wrapper}", "--enable_runfiles"]
        command.append(TARGET)
        sys.exit(subprocess.call(command, cwd=workspace))


if __name__ == "__main__":
    main()
