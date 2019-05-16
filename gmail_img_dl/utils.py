import logging
import time
from datetime import datetime
from os import path
from typing import Optional

ISO_8601_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logger(level: int = logging.INFO, log_file: Optional[str] = None) -> None:
    if log_file is not None:
        log_directory = path.dirname(path.abspath(log_file))
        if path.exists(log_directory):
            logging.basicConfig(format='%(levelname)s | %(asctime)s UTC | %(message)s', level=level, filename=log_file)
        else:
            print("Can not create log file; directory {} does not exists; will use stdout!".format(log_directory))
            logging.basicConfig(format='%(levelname)s | %(asctime)s UTC | %(message)s', level=level)
    else:
        logging.basicConfig(format='%(levelname)s | %(asctime)s UTC | %(message)s', level=level)
    logging.Formatter.converter = time.gmtime


def utc_datetime_to_iso_format(dt: datetime) -> str:
    return dt.strftime(ISO_8601_TIME_FORMAT)


def utc_iso_format_to_datetime(iso_dt: str) -> datetime:
    return datetime.strptime(iso_dt, ISO_8601_TIME_FORMAT)


def seconds_between(start_time_point: datetime, end_time_point: datetime = None, precision: int = 3):
    end_time_point = end_time_point or datetime.utcnow()
    return round((end_time_point - start_time_point).total_seconds(), precision)
