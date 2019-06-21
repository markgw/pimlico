# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html
"""Email sending utilities

Configure email sending functionality by adding the following fields to your Pimlico local config file:

`email_sender`
   From-address for all sent emails

`email_recipients`
   To-addresses, separated by commas. All notification emails will be sent to all recipients

`email_host`
   (optional) Hostname of your SMTP server. Defaults to `localhost`

`email_username`
   (optional) Username to authenticate with your SMTP server. If not given, it is assumed that no authentication
   is required

`email_password`
   (optional) Password to authenticate with your SMTP server. Must be supplied if `username` is given

"""

from __future__ import absolute_import

from builtins import str
from past.builtins import basestring
from builtins import object

import smtplib
from email.mime.text import MIMEText
from smtplib import SMTPHeloError, SMTPAuthenticationError, SMTPException


class EmailConfig(object):
    def __init__(self, sender=None, recipients=None, host=None, username=None, password=None):
        self.password = password
        self.username = username
        self.host = host

        if isinstance(recipients, basestring):
            recipients = [recipients]
        self.recipients = recipients
        self.sender = sender

        if username is not None and password is None:
            raise EmailError("username was supplied for SMTP, but no password")

    @classmethod
    def from_local_config(cls, local_config):
        # Expect to find a list of recipients in the local config
        if "email_recipients" not in local_config:
            raise EmailError("no recipient(s) specified in the local config. You should "
                             "set 'email_recipients' field in your local config file")
        recipients = local_config["email_recipients"].split(",")

        if "email_sender" not in local_config:
            raise EmailError("no sender specified in the local config. You should "
                             "set 'email_sender' field in your local config file")
        sender = local_config["email_sender"]

        # Fall back to default of localhost
        host = local_config.get("email_host", "localhost")

        # Allow a username to be supplied
        # Otherwise, we assume no authentication is needed
        username = local_config.get("email_username", None)
        # Same with the password
        password = local_config.get("email_password", None)

        return EmailConfig(sender=sender, recipients=recipients, host=host, username=username, password=password)


def send_pimlico_email(subject, content, local_config, log):
    """
    Primary method for sending emails from Pimlico. Tries to send an email with the given content, using
    the email details found in the local config. If something goes wrong, an error is logged on the given
    log.

    :param subject: email subject
    :param content: email text (may be unicode)
    :param local_config: local config dictionary
    :param log: logger to log errors to (and info if the sending works)
    """
    try:
        # Read email config from the local config
        config = EmailConfig.from_local_config(local_config)
        data = send_text_email(config, subject, content=content)
    except Exception as e:
        log.error("Could not send email: %s" % e)
        return {"success": False}
    else:
        log.info("Send email to %s" % ", ".join(data["recipients"]))
        data["success"] = True
        return data


def send_text_email(email_config, subject, content=None):
    # Encode unicode content as utf-8
    if content is None:
        content = ""
    body = str(content).encode("utf-8")

    # Create a plain message
    msg = MIMEText(body)

    # Allow a single recipient to be given
    if email_config.recipients is None:
        raise EmailError("email recipient(s) must be specified")

    if email_config.sender is None:
        raise EmailError("email sender must be specified")

    # Set the important headers
    msg['Subject'] = subject
    msg['From'] = email_config.sender
    msg['To'] = ", ".join(email_config.recipients)

    # Send the email, via the SMTP server
    s = smtplib.SMTP(email_config.host)
    if email_config.username is not None:
        # Login details have been supplied, so authenticate with SMTP server
        try:
            s.login(email_config.username, email_config.password)
        except SMTPHeloError as e:
            raise EmailError("invalid HELO response from SMTP server: %s" % e)
        except SMTPAuthenticationError as e:
            raise EmailError("could not authenticate with SMTP server (host '%s' using username '%s'): %s" % (
                email_config.host, email_config.username, e
            ))
        except SMTPException as e:
            raise EmailError("could not find a suitable SMTP authentication method: %s" % e)

    # Send the message
    email_content = msg.as_string()
    s.sendmail(email_config.sender, email_config.recipients, email_content)
    s.quit()

    # Return the sending details we used
    return {
        "subject": subject,
        "recipients": email_config.recipients,
        "sender": email_config.sender,
        "username": email_config.username,
        "content": email_content,
    }


class EmailError(Exception):
    pass
