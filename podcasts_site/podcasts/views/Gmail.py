import os.path
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from django.conf import settings

from podcasts.views.setup_logger import Loggers


class Gmail:

    def __init__(self, from_email=None, password=None, smtp='smtp.gmail.com', port=587, max_number_of_retries=5):
        """
        initialized the gmail object for a gmail account

        Keyword Argument
        from_email -- the email address to log into
        password -- the password for the email to log into
        smtp -- the server that hosts the smptlib server for gmail
        port -- the port for the smptlib server for gmail
        max_number_of_retries -- the maximum number of times to try opening and closing the connection to the smptlib
         server as well as sending the email
        """
        self.logger = Loggers.get_logger("youtube_dlp")
        self.connection_successful = False
        number_of_retries = 0
        if from_email is None:
            from_email = settings.GMAIL_USERNAME
        if password is None:
            password = settings.GMAIL_PASSWORD
        self.from_email = from_email
        self.max_number_of_retries = max_number_of_retries
        while not self.connection_successful and number_of_retries < max_number_of_retries:
            try:
                self.server = smtplib.SMTP(f'{smtp}:{port}')
                self.logger.info(f"[Gmail __init__()] setup smptlib server connection to {smtp}:{port}")
                self.server.connect(f'{smtp}:{port}')
                self.logger.info("[Gmail __init__()] smptlib server connected")
                self.server.ehlo()
                self.logger.info("[Gmail __init__()] smptlib server ehlo() successful")
                self.server.starttls()
                self.logger.info("[Gmail __init__()] smptlib server ttls started")
                self.logger.info(f"[Gmail __init__()] Logging into account {from_email}")
                self.server.login(from_email, password)
                self.logger.info(f"[Gmail __init__()] login to email {from_email} successful")
                self.connection_successful = True
                self.error_message = None
            except Exception as e:
                number_of_retries += 1
                self.logger.error(f"[Gmail __init__()] experienced following error when initializing.\n{e}")
                self.error_message = f"{e}"

    def send_email(self, subject, body, to_email, to_name, from_name="podcasts site", attachments=None):
        """
        send email to the specified email address

        Keyword Argument
        subject -- the subject for the email to send
        body - -the body of the email to send
        to_email -- the email address to send the email to
        to_name -- the name of the person to send the email to
        from_name -- the name to assign to the from name field
        attachment -- the logs to attach to the email if applicable

        Return
        Bool -- true or false to indicate if email was sent successfully
        error_message -- None if success, otherwise, returns the error experienced
        """
        if self.connection_successful:
            number_of_retries = 0
            while number_of_retries < self.max_number_of_retries:
                try:
                    msg = MIMEMultipart()
                    msg['From'] = from_name + " <" + self.from_email + ">"
                    msg['To'] = to_name + " <" + to_email + ">"
                    msg['Subject'] = subject
                    if body:
                        msg.attach(MIMEText(body))

                    if attachments is not None:
                        for attachment in attachments:
                            if os.path.exists(attachment):
                                try:
                                    self.logger.info("trying to attach {}".format(attachment))
                                    package = open(attachment, 'rb')
                                    payload = MIMEBase('application', 'octet-stream')
                                    payload.set_payload(package.read())
                                    encoders.encode_base64(payload)
                                    payload.add_header('Content-Disposition', "attachment; filename={}".format(attachment))
                                    msg.attach(payload)
                                    self.logger.info("{} has been attached".format(attachment))
                                except Exception as e:
                                    self.logger.info(f"{attachment} could not be attached. Error: {e}")
                    self.logger.info(f"[Gmail send_email()] sending email to {to_email}")
                    self.server.send_message(from_addr=self.from_email, to_addrs=to_email, msg=msg)
                    return True, None
                except Exception as e:
                    self.logger.info(f"[Gmail send_email()] unable to send email to {to_email} due to error.\n{e}")
                    number_of_retries += 1
                    self.error_message = f"{e}"
        return False, self.error_message

    def close_connection(self):
        """
        Closes connection to smptlib server

        Return
        Bool -- true or false to indicate if email was sent successfully
        error_message -- None if success, otherwise, returns the error experienced
        """
        if self.connection_successful:
            number_of_retries = 0
            while number_of_retries < self.max_number_of_retries:
                try:
                    self.logger.info("[Gmail close_connection()] closing connection to smtplib server")
                    self.server.close()
                    self.logger.info("[Gmail close_connection()] connection to smtplib server closed")
                    return True, None
                except Exception as e:
                    self.logger.error(
                        "[Gmail close_connection()] experienced following error when attempting "
                        f"to close connection to smtplib server.\n{e}"
                    )
                    number_of_retries += 1
                    self.error_message = f"{e}"
        return False, self.error_message