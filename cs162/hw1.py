from os.path import join
from ob2.dockergrader.helpers import (
    copy,
    copytree,
    download_repository,
    ensure_files_exist,
    ensure_no_binaries,
    extract_repository,
    get_working_directory,
    safe_get_results,
)
from ob2.dockergrader.job import JobFailedError
from ob2.dockergrader.rpc import DockerClient, TimeoutError
from ob2.util.hooks import register_job

from cs162.common import RESOURCES_DIR

# This is the docker image we'll use to run our autograder
docker_image = "cs162:latest"


@register_job("hw1")
def build(source, commit):
    # We're using 2 Python context managers here:
    #   - get_working_directory() of them creates a temporary directory on the host
    #   - DockerClient().start() creates a new Docker container for this autograder job
    #     We mount our temporary directory to "/host" inside the Docker container, so we can
    #     communicate with it.
    with get_working_directory() as wd, \
            DockerClient().start(docker_image, volumes={wd: "/host"}) as container:

        # These helper functions download and extract code from GitHub.
        # try:
        #     download_repository(source, commit, join(wd, "hw1.tar.gz"))
        #     extract_repository(container, join("/host", "hw1.tar.gz"), "/home/vagrant/ag",
        #                        user="vagrant")
        # except TimeoutError:
        #     raise JobFailedError("I was downloading and extracting your code from GitHub, but I "
        #                          "took too long to finish and timed out. Try again?")

        # For testing purposes, we can use solution code instead of GitHub code to test our
        # autograder. You're free to leave in commented code in order to support this.
        container.bash("mkdir -p /home/vagrant/ag/hw1", user="vagrant")
        copytree(join(RESOURCES_DIR, "hw-exec", "solutions"), join(wd, "solutions"))
        container.bash("cp -R /host/solutions/. /home/vagrant/ag/hw1/", user="vagrant")

        # These functions will raise JobFailedError if they find problems with the student code
        ensure_no_binaries(container, "/home/vagrant/ag")
        ensure_files_exist(container, "/home/vagrant/ag", ["./hw1/Makefile", "./hw1/main.c",
                                                           "./hw1/map.c", "./hw1/wc.c"])

        # Our autograder consists of 2 Python scripts. You are free to use whatever language you
        # want in your autograders, as long as you make sure your Docker container can run them.
        copy(join(RESOURCES_DIR, "hw-exec", "check.py"), join(wd, "check.py"))
        copy(join(RESOURCES_DIR, "common.py"), join(wd, "common.py"))

        # We run our autograder, which produces 2 outputs: a build log and a score.
        try:
            container.bash("""cd /host
                              python2.7 check.py /home/vagrant/ag/hw1 &>build_log 162>score
                           """, user="vagrant", timeout=60)
        except TimeoutError:
            raise JobFailedError("I was grading your code, but the autograder took too long to " +
                                 "finish and timed out. Try again?")

        # This function will safely retrieve the build log and the score value, without throwing
        # unexpected exceptions.
        return safe_get_results(join(wd, "build_log"), join(wd, "score"))
