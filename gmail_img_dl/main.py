import argparse
import logging
import os
from datetime import datetime, timedelta
from os import path
from typing import Optional

from dateutil.parser import parse

from gmail_img_dl.gmail import GmailClient, GMAIL_MAILBOX, ImapSession
from gmail_img_dl.store import ImageStore
from gmail_img_dl.utils import setup_logger


def _start(user: str, password: str, since: datetime, till: datetime, out_dir: str, remove: bool, dl_meta: bool):
    start_time = datetime.utcnow()
    with ImapSession(username=user, password=password) as session:
        gmail = GmailClient(session)
        store = ImageStore(dir_path=out_dir)
        email_ids = gmail.select_email_ids(mailbox=GMAIL_MAILBOX, since=since, before=till, for_delete=remove)
        logging.info("Retrieving {} email messages from {} from period {}-{}".format(len(email_ids), user,
                                                                                     since.isoformat(),
                                                                                     till.isoformat()))
        for i, email_id in enumerate(email_ids):
            msg = "Fetching email {} / {}...".format(i + 1, len(email_ids))
            if i % 10 == 0:
                logging.info(msg)
            else:
                logging.debug(msg)
            email, attach = gmail.fetch(email_id)
            store.save_attach(email, attach)
            if dl_meta:
                store.save_meta(email)
            if remove:
                gmail.trash(email_id)
    took_sec = (datetime.utcnow() - start_time).total_seconds()
    logging.info(
        "Stored {} emails from period {}-{} under {} in {:.3f}s ({:.3f}s/email)!".format(len(email_ids),
                                                                                         since.isoformat(),
                                                                                         till.isoformat(), out_dir,
                                                                                         took_sec,
                                                                                         took_sec / len(email_ids)))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download image attachments from GMail")
    parser.add_argument("dir", type=str, help="Directory where data will be stored")
    parser.add_argument("--box", type=str, default=GMAIL_MAILBOX,
                        help="Mailbox to download emails from; default to {}".format(GMAIL_MAILBOX))
    parser.add_argument("--till", type=str, default=None,
                        help="Upper bound for selecting emails; format: YYYY-MM-DD, i.e. 2019-02-22; default: UTC today")
    parser.add_argument("--since", type=str, default=None,
                        help="Lower bound for selecting emails; format: YYYY-MM-DD, i.e. 2019-02-21; default: till - 1 day")
    parser.add_argument("--meta", action='store_true',
                        help="If set, will download email metadata and store as JSON file, too")
    parser.add_argument("--rm", action='store_true', help="If set, downloaded emails will be deleted")
    parser.add_argument("--log", type=str, default=None, help="Log events to file instead of stdout")
    return parser.parse_args()


def main(user: Optional[str], password: Optional[str], mailbox: str,
         since: datetime, till: datetime, out_dir: str, remove: bool, dl_meta: bool, log: Optional[str]) -> None:
    if not user:
        raise ValueError("Env var GMAIL_USER is not set")
    if not password:
        raise ValueError("Env var GMAIL_PASSWORD is not set")
    if not mailbox:
        raise ValueError("Box parameter must not be empty")
    if since > till:
        raise ValueError("Since date {} is after till date {}".format(since.isoformat(), till.isoformat()))
    out_dir = path.abspath(out_dir)
    if not path.isdir(out_dir):
        raise ValueError("{} doest not exist or is not a directory".format(out_dir))
    setup_logger(log_file=log)
    _start(user, password, since, till, out_dir, remove, dl_meta)


def cli_main() -> None:
    try:
        args = parse_args()
        till_dt = parse(args.till).date() if args.till is not None else datetime.utcnow().date()
        since_dt = parse(args.since).date() if args.since is not None else till_dt - timedelta(days=1)
        main(user=os.getenv("GMAIL_USER"), password=os.getenv("GMAIL_PASSWORD"), mailbox=args.box,
             since=since_dt, till=till_dt, out_dir=args.dir, remove=args.rm, dl_meta=args.meta, log=args.log)
        exit(0)
    except Exception as e:
        print("Error: {}".format(e))
        exit(1)


if __name__ == "__main__":
    cli_main()
