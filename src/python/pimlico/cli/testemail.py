# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

from __future__ import print_function

from pimlico.cli.subcommands import PimlicoCLISubcommand
from pimlico.utils.email import send_pimlico_email


class EmailCmd(PimlicoCLISubcommand):
    command_name = "email"
    command_help = "Test email settings and try sending an email using them"

    def run_command(self, pipeline, opts):
        content = """\
This email is a test sent from Pimlico pipeline '%s'.

If you issued the email test command, your email settings are now working and
you can use Pimlico's email notification features.

If you were not expecting this email, someone has perhaps typed your email
address into their settings by accident. Please ignore it. The sender no
doubt apologizes for their mistake.
""" % pipeline.name
        # Send a dummy email to see if email sending works
        data = send_pimlico_email("Test email from Pimlico", content, pipeline.local_config, pipeline.log)
        if data["success"]:
            print("Email sending worked: check your email (%s) to see if the test message has arrived" % \
                  ", ".join(data["recipients"]))
        else:
            print("Email sending failed")
