import argparse
import logging
import os
from collections import namedtuple
from datetime import datetime, timedelta, date
from os import path
from time import sleep
from typing import Optional, Tuple

from dateutil.parser import parse

from gmail_img_dl.gmail import GmailClient, GMAIL_MAILBOX, ImapSession
from gmail_img_dl.store import ImageStore
from gmail_img_dl.utils import setup_logger

RETRIES = 5
RETRY_SLEEP_SEC = 1
CHUNK_SIZE = 10

Result = namedtuple("Result", ["downloaded_emails", "retry_count"])


def _start(user: str, password: str, since: date, till: date, out_dir: str, remove: bool, dl_meta: bool,
           retry_limit: int) -> Result:
    downloaded_emails, retries = 0, 0
    session_wrapper = ImapSession(username=user, password=password)
    gmail, store = _initialize(session_wrapper, out_dir)
    try:
        while retries <= retry_limit:
            try:
                email_ids = gmail.select_email_ids(mailbox=GMAIL_MAILBOX, since=since, before=till, for_delete=remove)
                logging.info("Retrieving {} email messages from {} from period {} - {}".format(len(email_ids), user,
                                                                                               since.isoformat(),
                                                                                               till.isoformat()))
                chunk_start, i = datetime.utcnow(), 1
                for email_id in email_ids:
                    email, attach = gmail.fetch(email_id)
                    store.save_attach(email, attach)
                    if dl_meta:
                        store.save_meta(email)
                    if remove:
                        gmail.trash(email_id)
                    if i % CHUNK_SIZE == 0:
                        chunk_took = (datetime.utcnow() - chunk_start).total_seconds()
                        msg = "Fetched emails {} - {} / {} in {:.3f}s...".format(i - CHUNK_SIZE + 1, i,
                                                                                 len(email_ids), chunk_took)
                        logging.info(msg)
                        chunk_start = datetime.utcnow()
                    downloaded_emails += 1
                    i += 1
                return Result(downloaded_emails, retries)
            except KeyboardInterrupt as e:
                logging.warning("Stopping due to keyboard interrupt!")
                raise e
            except Exception as e:
                retries += 1
                logging.warning(
                    "Error: {}, retrying for {} / {} time in {}s...".format(e, retries, retry_limit, RETRY_SLEEP_SEC))
                sleep(RETRY_SLEEP_SEC)
                session_wrapper.close()
                gmail, store = _initialize(session_wrapper, out_dir)
        return Result(downloaded_emails, retries)
    except Exception as e:
        session_wrapper.close()
        raise e


def _initialize(session_wrapper: ImapSession, out_dir: str) -> Tuple[GmailClient, ImageStore]:
    session_wrapper.close()
    session = session_wrapper.open()
    gmail = GmailClient(session)
    store = ImageStore(dir_path=out_dir)
    return gmail, store


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download image attachments from GMail")
    parser.add_argument("dir", type=str, help="Directory where data will be stored")
    parser.add_argument("--box", type=str, default=GMAIL_MAILBOX,
                        help="Mailbox to download emails from; default: {}".format(GMAIL_MAILBOX))
    parser.add_argument("--till", type=str, default=None,
                        help="Upper bound for email selection, i.e. 2019-02-22; defaults: UTC today")
    parser.add_argument("--since", type=str, default=None,
                        help="Lower bound for email selection, i.e. 2019-02-21; default: --till - 1 day")
    parser.add_argument("--days", type=int, default=None,
                        help="How many days before --till of emails to retrieve, i.e. 2; overrides --since")
    parser.add_argument("--meta", action='store_true',
                        help="If set, will download email metadata and store as JSON file, too")
    parser.add_argument("--rm", action='store_true', help="If set, downloaded emails will be deleted")
    parser.add_argument("--log", type=str, default=None, help="Log events to given file instead of stdout")
    return parser.parse_args()


def main(user: Optional[str], password: Optional[str], mailbox: str,
         since: date, till: date, out_dir: str, remove: bool, dl_meta: bool, log: Optional[str]) -> None:
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
    retry_limit = 5
    start_time = datetime.utcnow()
    downloaded_emails, retries = _start(user, password, since, till, out_dir, remove, dl_meta, retry_limit)
    took_sec = (datetime.utcnow() - start_time).total_seconds()
    if retries <= retry_limit:
        logging.info(
            "Stored {} emails from period {}-{} under {} in {:.3f}s ({:.3f}s/email)!".format(downloaded_emails,
                                                                                             since.isoformat(),
                                                                                             till.isoformat(),
                                                                                             out_dir,
                                                                                             took_sec,
                                                                                             took_sec / downloaded_emails if downloaded_emails > 0 else 0))
    else:
        raise RuntimeError(
            "Retries reached limit ({} / {}) after {} downloaded emails and {}s".format(retries, retry_limit,
                                                                                        downloaded_emails, took_sec))


def cli_main() -> None:
    try:
        args = parse_args()
        till_dt = parse(args.till).date() if args.till is not None else datetime.utcnow().date()
        if args.days is not None and args.days > 0:
            since_dt = till_dt - timedelta(days=args.days)
        else:
            since_dt = parse(args.since).date() if args.since is not None else till_dt - timedelta(days=1)
        main(user=os.getenv("GMAIL_USER"), password=os.getenv("GMAIL_PASSWORD"), mailbox=args.box,
             since=since_dt, till=till_dt, out_dir=args.dir, remove=args.rm, dl_meta=args.meta, log=args.log)
        exit(0)
    except Exception as e:
        print("Error: {}".format(e))
        exit(1)


if __name__ == "__main__":
    cli_main()
