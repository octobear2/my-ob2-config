# Common configuration variables and functions for all autograder scripts
from os.path import dirname, join, realpath

CS162_STUDENT_VM_DOCKER_IMAGE = "cs162:latest"

RESOURCES_DIR = join(dirname(realpath(__file__)), "resources")
