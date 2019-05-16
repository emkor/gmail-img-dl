import json
from datetime import datetime
from os import path
from typing import List

import piexif

from gmail_img_dl.model import Attachment, Email

EXIF_DATE_FORMAT = '%Y:%m:%d %H:%M:%S'


class ImageStore:
    def __init__(self, dir_path: str) -> None:
        self.dir_path = dir_path

    def save_attach(self, mail: Email, attachments: List[Attachment]) -> None:
        prefix = self._gen_prefix(mail)
        self._store_image_attach(attachments, prefix, mail)

    def save_meta(self, mail: Email) -> None:
        prefix = self._gen_prefix(mail)
        self._store_email_meta(prefix, mail)

    def _store_image_attach(self, attachments: List[Attachment], prefix, mail):
        for attachment in attachments:
            attach_file_name = path.join(self.dir_path, "{}_{}".format(prefix, attachment.file_name))
            if not path.exists(attach_file_name):
                with open(attach_file_name, "wb") as att_file:
                    att_file.write(attachment.data)
            write_time_taken_exif_if_needed(attach_file_name, mail.date_sent)

    def _store_email_meta(self, prefix: str, mail: Email):
        email_meta_file_name = path.join(self.dir_path, "{}.json".format(prefix))
        if not path.exists(email_meta_file_name):
            with open(email_meta_file_name, "w") as email_file:
                json.dump(mail.to_serializable(), email_file)

    def _gen_prefix(self, mail):
        prefix = "{}_{}_{}_{}".format(mail.date_sent.date().isoformat(),
                                      mail.date_sent.time().isoformat().replace(":", "-"),
                                      mail.sender_name,
                                      mail.message_id)
        return prefix


def write_time_taken_exif_if_needed(image_file_path: str, time_taken: datetime) -> None:
    image_exif = piexif.load(image_file_path)
    orig_time_taken = image_exif.get('Exif', {}).get(piexif.ExifIFD.DateTimeOriginal, None) \
                      or image_exif.get('Exif', {}).get(piexif.ExifIFD.DateTimeDigitized, None)
    if orig_time_taken is None:
        time_taken_str = time_taken.strftime(EXIF_DATE_FORMAT)
        image_exif['Exif'][piexif.ExifIFD.DateTimeOriginal] = time_taken_str
        image_exif['Exif'][piexif.ExifIFD.DateTimeDigitized] = time_taken_str
        piexif.insert(piexif.dump(image_exif), image_file_path)
