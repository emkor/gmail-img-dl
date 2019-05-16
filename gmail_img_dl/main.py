import argparse
import logging
import os
from datetime import datetime, timedelta
from os import path
from typing import Optional

from dateutil.parser import parse

from gmail_img_dl.gmail import login, GmailClient, GMAIL_MAILBOX
from gmail_img_dl.store import ImageStore
from gmail_img_dl.utils import setup_logger


def _start(user: str, password: str, since: datetime, till: datetime, out_dir: str, remove: bool):
    start_time = datetime.utcnow()
    imap_session = login(username=user, password=password)
    gmail = GmailClient(imap_session)
    store = ImageStore(dir_path=out_dir)
    email_ids = gmail.select_email_ids(mailbox=GMAIL_MAILBOX, since=since, before=till, for_delete=remove)
    logging.info("Retrieving {} email messages from {}".format(len(email_ids), user))
    for i, email_id in enumerate(email_ids):
        try:
            msg = "Fetching email {} / {}...".format(i + 1, len(email_ids))
            if i % 50 == 0:
                logging.info(msg)
            else:
                logging.debug(msg)
            email, attach = gmail.fetch(email_id)
            store.save(email, attach)
            if remove:
                gmail.trash(email_id)
        except Exception as e:
            logging.warning("Failed retrieving email with ID #{}: {}".format(email_id, e))
    took_sec = (datetime.utcnow() - start_time).total_seconds()
    logging.info("Stored {} emails under {} in {:.3f}s ({:.3f}s/email)!".format(len(email_ids), out_dir,
                                                                                took_sec, took_sec / len(email_ids)))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download image attachments from GMail")
    parser.add_argument("--since", type=str, default=None,
                        help="Lower bound for filtering emails; format: YYYY-MM-DD, i.e. 2019-02-21; default: UTC yesterday")
    parser.add_argument("--till", type=str, default=None,
                        help="Upper bound for filtering emails; format: YYYY-MM-DD, i.e. 2019-02-22; default: UTC today")
    parser.add_argument("--dir", type=str, default=".", help="Directory where data will be stored; default: .")
    parser.add_argument("--rm", action='store_true', help="If set, downloaded emails will be deleted")
    parser.add_argument("--log", type=str, default=None, help="Log events to file instead of stdout")
    return parser.parse_args()


def main(user: Optional[str], password: Optional[str], since: datetime, till: datetime, out_dir: str,
         remove: bool, log: Optional[str]) -> None:
    if not user:
        raise ValueError("Env var GMAIL_USER is not set!")
    if not password:
        raise ValueError("Env var GMAIL_PASSWORD is not set!")
    if since > till:
        raise ValueError("Since: {} is after till {}!".format(since.isoformat(), till.isoformat()))
    out_dir = path.abspath(out_dir)
    if not path.isdir(out_dir):
        raise ValueError("Given directory {} doest not exist or is not a directory!".format(out_dir))
    setup_logger(log_file=log)
    _start(user, password, since, till, out_dir, remove)


def cli_main() -> None:
    args = parse_args()
    till_dt = parse(args.till).date() if args.till is not None else datetime.now().date()
    since_dt = parse(args.since).date() if args.since is not None else till_dt - timedelta(days=1)
    main(user=os.getenv("GMAIL_USER"), password=os.getenv("GMAIL_PASSWORD"),
         since=since_dt, till=till_dt, out_dir=args.dir, remove=args.rm, log=args.log)


if __name__ == "__main__":
    cli_main()
