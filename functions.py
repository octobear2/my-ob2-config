from importlib import import_module
from os.path import abspath, dirname
import sys

import ob2.config as config
from ob2.database.virtual import GenericReadOnlyVTModule
from ob2.util.hooks import register_filter, register_partial

# Insert the current directory into sys.path
#
# In order to avoid naming conflicts, we created a new "cs162" module that contains all of our
# custom code. This module has many self-referencing imports, so we need all of Python's module
# infrastructure in order to support it.
current_directory = dirname(abspath(__file__))
sys.path.insert(0, current_directory)

# .. and then make sure all the submodules get initialized.
for assignment in config.assignments:
    if not assignment.manual_grading:
        import_module("cs162.%s" % assignment.name)

# Then, get rid of it, so we don't pollute sys.path any more
sys.path.remove(current_directory)


# This partial is displayed on the log in page. It would be a good idea to put some HTML here that
# explains what this autograder does.
@register_partial("onboarding-log-in")
def cs162_onboarding_login_page():
    return """
        <p>
            This is the log in page for the autograding system for CS162. Students can use this
            system to view autograder results for homework and projects.  As outlined in hw0, you
            will need an account with the online code-sharing website, GitHub. You can create a
            <strong>free</strong> GitHub account if you don&rsquo;t have an account already.
        </p>
        """


# This partial is displayed on the last step of onboarding, after the student has registered their
# student ID and uploaded a photo (optional). It is a useful place to put some course policies, if
# you want.
@register_partial("onboarding-welcome")
def cs162_onboarding_welcome():
    return """
        <p>
            You can access this autograder at <strong>cs162.eecs.berkeley.edu/autograder</strong>.
            All of your homework, project, and exam grades will be made available to you through
            the autograder&rsquo;s web interface. For coding assignments, you can use the autograder
            to track your progress and request new versions of your code to be graded.
        </p>
        <p>
            There are some things you should know about the CS162 Autograder.
        </p>
        <ul>
            <li>
                Homeworks and Projects will be graded automatically when you push your code to
                GitHub. When you push code to GitHub, you will receive an email report and you can
                see your autograder results through this web interface.
            </li>
            <li>
                Late homeworks and projects will NOT be graded automatically when you push to
                GitHub. This policy is designed to prevent you from accidentally using slip days by
                accidentally pushing code after the deadline. If you want to use slip days,
                <strong>you must log in to this web interface and request a new build
                manually.</strong>
            </li>
            <li>
                Your score on an assignment will be the highest score you achieve on that assignment
                on any build. If you push code to GitHub that lowers your autograder score, it will
                be ignored. Additionally, late builds will NOT use slip days unless they actually
                increase your score.
            </li>
        </ul>
        """


# Here's an example of adding your own SQLite Virtual Table Module (vtmodule) to the database.
# We've written the GenericReadOnlyVTModule class to help you create read-only virtual tables,
# which are useful for data analysis.
#
# See ob2/database/virtual.py for more information.
ta_to_group_matching = {
    "Andrew": [28, 61, 24, 22, 74, 15, 60, 21, 49, 46, 41, 13, 19],
    "Aleks": [63, 44, 70, 59, 18, 5, 54, 30, 35, 27, 29, 32, 51, 12],
    "William": [3, 2, 73, 47, 39, 16, 56, 68, 4],
    "Roger": [45, 42, 7, 72, 11, 55, 65, 62, 66, 67, 77, 10, 57, 53],
    "Alec": [36, 69, 33, 78, 1, 80, 43, 23, 9, 75, 38, 34, 20, 71],
    "Jackson": [26, 40, 6, 79, 14, 48, 31, 8, 37, 64, 52, 25, 76, 58, 50, 17],
}
ta_values = [(ta, "group%d" % group) for ta in ta_to_group_matching for group in ta_to_group_matching[ta]]
ta_vtmodule = GenericReadOnlyVTModule("ta", ["ta", "group"], [str, str], ta_values)


# Now, we add our newly-created virtual table module to the list of all virtual table modules.
@register_filter("database-vtmodules")
def cs162_database_vtmodules(vtmodules):
    return vtmodules + [ta_vtmodule]


# You should DEFINITELY have a function like this, or simialar to this. This function determines
# which autograder jobs to run when we receive a GitHub "push" event. This code is what we use in
# CS162, but you may need to adapt it to suit your own course policies.
@register_filter("pushhooks-jobs-to-run")
def cs162_get_jobs_to_run(jobs, repo_name, ref, modified_files):
    """
    Returns a list of autograder jobs to start, based on the contents of a GitHub pushhook.

    repo_name      -- The name of the repo that caused the pushhook
    ref            -- The name of the ref that was pushed (e.g. "refs/heads/master")
    modified_files -- A list of files that were changed in the push, relative to repo root

    """

    # We only build code that lives on the master branch. (NOTE: if multiple branches are pushed at
    # the same time, then we get a push event for EACH branch, so no need to worry about that case)
    if ref != "refs/heads/master":
        return []

    # We have repos in our GitHub organization for staff use. These should not trigger any
    # autograder jobs. By default, repos of the form [a-z]{2,3} or group\d+ are recognized as
    # student repos. You can change this behavior by using the "get-repo-type" filter hook
    # (see ob2/util/config_data.py for more details)
    repo_type = get_repo_type(repo_name)
    if repo_type is None:
        return []

    is_group_repo = repo_type == "group"
    for assignment in config.assignments:
        if assignment[MANUAL_GRADING]:
            continue
        if now_compare(assignment[START_AUTO_BUILDING], assignment[END_AUTO_BUILDING]) != 0:
            continue
        if assignment[IS_GROUP] != is_group_repo:
            continue
        # Only build hw1 if diff contains modifications to hw1/ (for example)
        # If it's a group project, ignore this rule.
        if not (filter(lambda p: p.startswith(assignment[NAME] + "/"), modified_files) or
                assignment[IS_GROUP]):
            continue
        jobs.append(assignment[NAME])
    return jobs


# This function lets you tell ob2 how to connect to your SMTP server. Our cs162.eecs server has a
# mail exchanger listening on 0.0.0.0:25, so we'll just use that one.
@register_filter("connect-to-smtp")
def cs162_connect_to_smtp(smtp_obj):
    """
    Given an instance of smtplib.SMTP, connect and/or authenticate with the desired mail exchanger
    used to send mail. Returns smtp_obj (or a compatible object).

    """

    smtp_obj.connect("127.0.0.1")
    return smtp_obj
