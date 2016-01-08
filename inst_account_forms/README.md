Introduction
============

You can configure this application to send instructional account forms to students when they sign
up. This is an optional feature that can be disabled completely.


Setup
=====

1. Set `inst_account_enabled` to true inside `config.yaml`.
2. Inside this directory, create files named `aa.pdf`, `ab.pdf`, etc for each of the logins that
   are assigned to users in the database.


Other notes
===========

Upon startup, the code in `ob2/database/validation.py` will ensure that each user's account form
exists in this directory.

The account form will be attached as a PDF attachment to the onboarding confirmation email.

You can use Apache PDFBox to split the master account forms PDF and the `strings` utility to
identify which login corresponds to each account form.
See [binutils/strings.html](https://sourceware.org/binutils/docs/binutils/strings.html)
