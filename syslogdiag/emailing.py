import base64
import json
import smtplib
import urllib.parse
import urllib.request

from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart

from syscore.objects import arg_not_supplied
from sysdata.config.production_config import get_production_config

# For using Gmail, which requires OAuth2.
# The OAuth2 logic below may or may not work with other email providers.
GOOGLE_ACCOUNTS_BASE_URL = 'https://accounts.google.com'


def send_mail_file(textfile, subject):
    """
    Sends an email of a particular text file with subject line

    """

    fp = open(textfile, "rb")
    # Create a text/plain message
    msg = MIMEText(fp.read())
    fp.close()

    msg["Subject"] = subject

    _send_msg(msg)


def send_mail_msg(body, subject):
    """
    Sends an email of particular text file with subject line

    """

    # Create a text/plain message
    msg = MIMEMultipart()

    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    _send_msg(msg)


def send_mail_pdfs(preamble, filelist, subject):
    """
    Sends an email of files with preamble and subject line

    """

    # Create a text/plain message
    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg.preamble = preamble

    for file in filelist:
        fp = open(file, "rb")
        attach = MIMEApplication(fp.read(), "pdf")
        fp.close()
        attach.add_header("Content-Disposition", "attachment", filename="file.pdf")
        msg.attach(attach)

    _send_msg(msg)


def _send_msg(msg):
    """
    Send a message composed by other things

    """

    email_server, email_address, email_pwd, email_to, email_port, \
        oauth2_client_id, oauth2_client_secret, oauth2_refresh_token = get_email_details()

    me = email_address
    you = email_to
    msg["From"] = me
    msg["To"] = you

    # Send the message via our own SMTP server, but don't include the
    # envelope header.
    s = smtplib.SMTP(email_server, email_port)

    if oauth2_client_id is not arg_not_supplied:
        s.ehlo(oauth2_client_id)

    # add tls for those using yahoo or gmail.
    try:
        s.starttls()
    except:
        pass

    if oauth2_client_id is not arg_not_supplied and oauth2_client_secret is not arg_not_supplied:

        if oauth2_refresh_token is arg_not_supplied:
            oauth2_refresh_token = None

        access_token, expires_in = refresh_authorization(oauth2_client_id, oauth2_client_secret, oauth2_refresh_token)
        oauth2_auth_string = generate_oauth2_string(email_address, access_token, as_base64=True)
        s.docmd('AUTH', 'XOAUTH2 ' + oauth2_auth_string)
    else:
        s.login(email_address, email_pwd)

    s.sendmail(me, [you], msg.as_string())
    s.quit()


def get_email_details():
    # FIXME DON'T LIKE RETURNING ALL THESE VALUES - return CONFIG or subset?
    production_config = get_production_config()

    email_address = production_config.get_element_or_arg_not_supplied('email_address')
    email_server = production_config.get_element_or_arg_not_supplied('email_server')
    email_to = production_config.get_element_or_arg_not_supplied('email_to')
    email_port = production_config.get_element_or_arg_not_supplied('email_port')
    email_pwd = production_config.get_element_or_arg_not_supplied('email_pwd')
    oauth2_client_id = production_config.get_element_or_arg_not_supplied('oauth2_client_id')
    oauth2_client_secret = production_config.get_element_or_arg_not_supplied('oauth2_client_secret')
    oauth2_refresh_token = production_config.get_element_or_arg_not_supplied('oauth2_refresh_token')

    if email_address is arg_not_supplied \
        or email_server is arg_not_supplied \
        or email_to is arg_not_supplied \
        or email_port is arg_not_supplied:

        raise Exception("Email requires private config entries for: email_server, email_port, email_address, email_to")

    using_pwd = email_pwd is not arg_not_supplied
    using_oauth = (oauth2_client_id is not arg_not_supplied and oauth2_client_secret is not arg_not_supplied)

    if not using_pwd and not using_oauth:
        raise Exception("Email requires private config entries for EITHER: email_pwd "
                        "OR (oauth2_client_id AND oauth2_client_secret) ")

    return email_server, email_address, email_pwd, email_to, email_port, \
        oauth2_client_id, oauth2_client_secret, oauth2_refresh_token


def generate_oauth2_string(username, access_token, as_base64=False):
    auth_string = 'user=%s\1auth=Bearer %s\1\1' % (username, access_token)
    if as_base64:
        auth_string = base64.b64encode(auth_string.encode('ascii')).decode('ascii')
    return auth_string


def refresh_authorization(google_client_id, google_client_secret, refresh_token):
    response = call_refresh_token(google_client_id, google_client_secret, refresh_token)
    return response['access_token'], response['expires_in']


def call_refresh_token(client_id, client_secret, refresh_token):
    params = {'client_id': client_id,
              'client_secret': client_secret,
              'refresh_token': refresh_token,
              'grant_type': 'refresh_token'}
    request_url = command_to_url('o/oauth2/token')
    print(request_url)
    response = urllib.request.urlopen(request_url, urllib.parse.urlencode(params).encode('UTF-8')).read().decode('UTF-8')
    return json.loads(response)


def command_to_url(command):
    return '%s/%s' % (GOOGLE_ACCOUNTS_BASE_URL, command)

