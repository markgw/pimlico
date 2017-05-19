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

import smtplib
from email.mime.text import MIMEText
from smtplib import SMTPHeloError, SMTPAuthenticationError, SMTPException


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
        data = send_text_email(subject, local_config, content=content)
    except Exception, e:
        log.error("Could not send email: %s" % e)
        return {"success": False}
    else:
        log.info("Send email to %s" % ", ".join(data["recipients"]))
        data["success"] = True
        return data


def send_text_email(subject, local_config, content=None, sender=None, recipients=None, host=None,
                    username=None, password=None):
    # Encode unicode content as utf-8
    if content is None:
        content = ""
    body = unicode(content).encode("utf-8")

    # Create a plain message
    msg = MIMEText(body)

    # Allow a single recipient to be given
    if recipients is None:
        # No explicit recipient given: expect to find a list in the local config
        if "email_recipients" not in local_config:
            raise EmailError("no recipient(s) specified for email and none found in the local config. You should "
                             "set 'email_recipients' field in your local config file")
        recipients = local_config["email_recipients"].split(",")

    if isinstance(recipients, basestring):
        recipients = [recipients]

    if sender is None:
        # No explicit sender: expect one in the local config
        if "email_sender" not in local_config:
            raise EmailError("no sender specified for email and none found in the local config. You should "
                             "set 'email_sender' field in your local config file")
        sender = local_config["email_sender"]

    if host is None:
        # Allow host to be overridden by kwarg, then check for one in the local config
        # Otherwise, fall back to default of localhost
        host = local_config.get("email_host", "localhost")

    if username is None:
        # Allow a username to be supplied as a kwarg, or via local config
        # Otherwise, we assume no authentication is needed
        username = local_config.get("email_username", None)
    if password is None:
        # Same with the password
        password = local_config.get("email_password", None)
    if username is not None and password is None:
        raise EmailError("username was supplied for SMTP, but no password. Set using 'email_password' field in local "
                         "config file")

    # Set the important headers
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ", ".join(recipients)

    # Send the email, via the SMTP server
    s = smtplib.SMTP(host)
    if username is not None:
        # Login details have been supplied, so authenticate with SMTP server
        try:
            s.login(username, password)
        except SMTPHeloError, e:
            raise EmailError("invalid HELO response from SMTP server: %s" % e)
        except SMTPAuthenticationError, e:
            raise EmailError("could not authenticate with SMTP server (host '%s' using username '%s'): %s" % (
                host, username, e
            ))
        except SMTPException, e:
            raise EmailError("could not find a suitable SMTP authentication method: %s" % e)

    # Send the message
    email_content = msg.as_string()
    s.sendmail(sender, recipients, email_content)
    s.quit()

    # Return the sending details we used
    return {
        "subject": subject,
        "recipients": recipients,
        "sender": sender,
        "username": username,
        "content": email_content,
    }


class EmailError(Exception):
    pass
