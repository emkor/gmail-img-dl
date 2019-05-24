import imaplib
import email
import logging
from email.message import EmailMessage
from imaplib import IMAP4_SSL
from datetime import date
from typing import List, Tuple, Optional

import pytz
from dateutil.parser import parse

from gmail_img_dl.model import Attachment, Email

IMAP_OK = "OK"
ACCEPTED_MIME_TYPES = ["image/jpeg"]
GMAIL_HOST = "imap.gmail.com"
GMAIL_MAILBOX = "INBOX"
GMAIL_ALL_MAILBOX = "[Gmail]/Wszystkie"


class ImapSession:
    def __init__(self, username: str, password: str) -> None:
        self.password = password
        self.username = username
        self._session = None  # type: Optional[imaplib.IMAP4_SSL]

    def open(self) -> imaplib.IMAP4_SSL:
        self._session = imaplib.IMAP4_SSL(GMAIL_HOST)  # type: ignore
        typ, account_details = self._session.login(self.username, self.password)  # type: ignore
        if typ == IMAP_OK:
            return self._session
        else:
            raise ValueError("Could not login as {}: {}".format(self.username, typ))

    def close(self) -> None:
        if self._session is not None:
            self._session.close()

    def __enter__(self) -> imaplib.IMAP4_SSL:
        return self.open()

    def __exit__(self, *args) -> None:
        return self.close()


class GmailClient:
    def __init__(self, imap_session: IMAP4_SSL) -> None:
        self.imap_session = imap_session

    def select_email_ids(self, mailbox: str, since: date, before: date, for_delete: bool) -> List[str]:
        typ, message_count_bin = self.imap_session.select(mailbox, readonly=not for_delete)
        if typ == IMAP_OK:
            criteria = _build_list_email_criteria(since=since, before=before)
            typ, data = self.imap_session.search(None, criteria)
            if typ == IMAP_OK:
                return data[0].split()
            else:
                raise ValueError("Could not login!")
        else:
            raise ValueError("Could not select mailbox {}: {}".format(mailbox, typ))

    def fetch(self, email_id: str) -> Tuple[Email, List[Attachment]]:
        typ, message_parts = self.imap_session.fetch(email_id, "(RFC822)")
        if typ == IMAP_OK:
            email_body_text = message_parts[0][1].decode("utf-8")
            email_body = email.message_from_string(email_body_text, _class=EmailMessage)  # type: ignore
            attach = get_mail_attachments(email_body)
            return _build_email_msg(email_body), attach
        else:
            raise ValueError("Could not read message with id {}: {}".format(email_id, typ))

    def trash(self, email_id: str) -> None:
        self.imap_session.store(email_id, '+X-GM-LABELS', '\\Trash')
        self.imap_session.store(email_id, '+FLAGS', '\\Deleted')


def get_mail_attachments(mail: EmailMessage) -> List[Attachment]:
    attachments = []
    for attach in mail.iter_attachments():
        mime_type = attach.get_content_type()
        if mime_type.lower() in ACCEPTED_MIME_TYPES:
            a = Attachment(mime_type, attach.get_filename(), attach.get_payload(decode=True))  # type: ignore
            attachments.append(a)
        else:
            logging.warning("Ignoring attachment {} having MIME: {}".format(attach.get_filename(), mime_type))
    return attachments


def _build_email_msg(raw_email: EmailMessage) -> Email:
    parsed_utc_date = parse(str(raw_email.get("Date"))).astimezone(pytz.utc)
    sender_name_raw, _, sender_mail_raw = str(raw_email.get("From")).partition("<")
    sender_mail = sender_mail_raw.replace(">", "")
    sender_name = sender_name_raw.replace('"', '')
    recipient = str(raw_email.get("To")).replace("<", "").replace(">", "")
    subject = str(raw_email.get("Subject"))
    raw_message_id, _, _ = str(raw_email.get("Message-ID")).partition("@")
    message_id = raw_message_id.replace("<", "")
    return Email(message_id, parsed_utc_date, sender_name, sender_mail, recipient, subject)


def _build_list_email_criteria(since: date, before: date) -> str:
    return '(SINCE "{}" BEFORE "{}")'.format(since.strftime("%d-%b-%Y"), before.strftime("%d-%b-%Y"))
