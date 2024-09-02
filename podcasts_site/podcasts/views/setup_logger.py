import datetime
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

import pytz

from podcasts.views.youtube_dlp_error_handler import YoutubeDLPErrorHandler

SYS_LOG_HANDLER_NAME = "sys"

date_timezone = pytz.timezone('US/Pacific')

error_logging_level = logging.ERROR

warn_logging_level = logging.WARNING

# class YoutubeDLPWarnStreamHandler(logging.StreamHandler):
#     def emit(self, record):
#         if record.levelno < error_logging_level:
#             super().emit(record)
#
#
class YoutubeDLPDebugStreamHandler(logging.StreamHandler):
    def emit(self, record):
        if record.levelno < warn_logging_level:
            super().emit(record)

class PSTFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None, tz=None):
        super(PSTFormatter, self).__init__(fmt, datefmt)
        self.tz = tz

    def formatTime(self, record, datefmt=None):  # noqa: N802
        """

        :param record:
        :param datefmt:
        :return:
        """
        dt = datetime.datetime.fromtimestamp(record.created, self.tz)
        if datefmt:
            return dt.strftime(datefmt)
        else:
            return str(dt)


REDIRECT_STD_STREAMS = True
date_formatting_in_log = '%Y-%m-%d %H:%M:%S'
date_formatting_in_filename = "%Y_%m_%d_%H_%M_%S"
sys_stream_formatting = PSTFormatter(
    '%(asctime)s = %(levelname)s = %(name)s = %(message)s', date_formatting_in_log, tz=date_timezone
)

MAX_BYTES_LOG_FILE = 536870912  # half a gigabyte
MAX_NUMBER_OF_LOG_FILES = 5


class Loggers:
    loggers = []
    logger_list_indices = {}

    @classmethod
    def get_logger(cls, logger_name):
        """
        Initiates and returns a logger for the specific logger_name
        :param logger_name: the name to assign to the returned logic
        :return:the logger
        """
        # if logger_name == SYS_LOG_HANDLER_NAME:
        #     return cls._setup_sys_logger()
        # else:
        if logger_name in cls.logger_list_indices:
            return cls.loggers[cls.logger_list_indices[logger_name]]
        else:
            return cls._add_logger(cls._setup_logger(logger_name))

    @classmethod
    def _add_logger(cls, logger):
        logger = logger[0]
        cls.loggers.insert(0, logger)
        cls.logger_list_indices = {}
        for (index, saved_logger) in enumerate(cls.loggers):
            cls.logger_list_indices[saved_logger.name] = index
        return logger

    @classmethod
    def _setup_logger(cls, service_name):
        """
        Creates a logger for the specified service that prints to a file and the sys.stdout
        and sys.stderr
        :param service_name: the name of the service that is initializing the logger
        :return: the logger
        """
        date = datetime.datetime.now(date_timezone).strftime(date_formatting_in_filename)
        if not os.path.exists(f"logs/{service_name}"):
            os.makedirs(f"logs/{service_name}")
        debug_log_file_absolute_path = f"logs/{service_name}/{date}_debug.log"
        warn_log_file_absolute_path = f"logs/{service_name}/{date}_warn.log"
        error_log_file_absolute_path = f"logs/{service_name}/{date}_error.log"

        logger = logging.getLogger(service_name)
        logger.setLevel(logging.DEBUG)


        # setup debug file handlers
        debug_filehandler = RotatingFileHandler(
            debug_log_file_absolute_path, maxBytes=MAX_BYTES_LOG_FILE,
            backupCount=MAX_NUMBER_OF_LOG_FILES
        )
        debug_filehandler.setLevel(logging.DEBUG)
        debug_filehandler.setFormatter(sys_stream_formatting)
        logger.addHandler(debug_filehandler)

        # setup error file handler
        error_filehandler = RotatingFileHandler(
            error_log_file_absolute_path,
            maxBytes=MAX_BYTES_LOG_FILE,
            backupCount=MAX_NUMBER_OF_LOG_FILES
        )
        error_filehandler.setFormatter(sys_stream_formatting)
        error_filehandler.setLevel(error_logging_level)
        logger.addHandler(error_filehandler)

        # setup warn file handler
        warn_filehandler = RotatingFileHandler(
            warn_log_file_absolute_path,
            maxBytes=MAX_BYTES_LOG_FILE,
            backupCount=MAX_NUMBER_OF_LOG_FILES
        )
        warn_filehandler.setFormatter(sys_stream_formatting)
        warn_filehandler.setLevel(warn_logging_level)
        logger.addHandler(warn_filehandler)

        # setup stdout stream handler
        sys.stdout = sys.__stdout__
        sys_stdout_stream_handler = YoutubeDLPDebugStreamHandler(sys.stdout)
        sys_stdout_stream_handler.setFormatter(sys_stream_formatting)
        sys_stdout_stream_handler.setLevel(logging.DEBUG)
        logger.addHandler(sys_stdout_stream_handler)
        sys.stdout = LoggerWriter(logger.info)


        sys.stderr = sys.__stderr__
        sys_stderr_stream_handler = YoutubeDLPErrorHandler(
            sys.stderr,
            debug_file_name=debug_log_file_absolute_path,
            warn_file_name=warn_log_file_absolute_path,
            error_file_name=error_log_file_absolute_path
        )
        sys_stderr_stream_handler.setFormatter(sys_stream_formatting)
        sys_stderr_stream_handler.setLevel(logging.ERROR) # change this to ERROR
        logger.addHandler(sys_stderr_stream_handler)
        sys.stderr = LoggerWriter(logger.error)

        return (
            logger, debug_log_file_absolute_path, warn_log_file_absolute_path, error_log_file_absolute_path
        )


class LoggerWriter:
    def __init__(self, level):
        """
        User to direct the sys.stdout/err to the specified log level
        :param level:
        """
        self.level = level

    def write(self, message):
        """
        writes from the sys.stdout/err to the logger object for sys_logger
        :param message: the message to write to the log
        :return:
        """
        if message != '\n':
            # removing newline that is created [I believe] when stdout automatically adds a newline to the string
            # before passing it to this method, and self.level itself also adds a newline
            message = message[:-1] if message[-1:] == "\n" else message
            self.level(message)

    def flush(self):
        pass