#!/usr/bin/env python

# You can write autograding scripts in any language, but we choose to write them in Python.
# Beware that ob2 will NOT be available inside your Docker container (unless you install it), so
# stick to standard library functions here.

import os
import sys

from common import *


if __name__ == "__main__":
    working_directory = sys.argv[1]
    os.chdir(working_directory)

    score = 1.0
    print BLUE + "Hello world!" + RESET

    # Our convention is that STDOUT becomes the build log and fd number 162 connects to the "score"
    # file. So, this is our idiom for writing the score:
    with os.fdopen(162, "w") as score_file:
        score_file.write(str(score))
