from copy import copy
from datetime import datetime
from typing import Dict

from gmail_img_dl.utils import utc_datetime_to_iso_format, utc_iso_format_to_datetime


class Model(object):
    def to_serializable(self) -> Dict:
        return copy(self.__dict__)

    def from_serializable(self, json_dict):
        return self.__class__(**json_dict)


class Attachment(Model):
    def __init__(self, mime: str, file_name: str, data: bytes) -> None:
        self.mime = mime
        self.file_name = file_name
        self.data = data


class Email(Model):
    def __init__(self, message_id: str, date_sent: datetime,
                 sender_name: str, sender_mail: str, recipient_mail: str, subject: str):
        self.message_id = message_id
        self.date_sent = date_sent
        self.sender_name = sender_name
        self.sender_mail = sender_mail
        self.recipient_mail = recipient_mail
        self.subject = subject

    def to_serializable(self):
        serialized = copy(self.__dict__)
        serialized.update({"date_sent": utc_datetime_to_iso_format(self.date_sent)})
        return serialized

    def from_serializable(self, json_dict):
        json_dict.update({"date_sent": utc_iso_format_to_datetime(json_dict["date_sent"])})
        return self.__class__(**json_dict)
