import datetime
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

import pytz

from podcasts.models import LoggingFilePath

SYS_LOG_HANDLER_NAME = "sys"

date_timezone = pytz.timezone('US/Pacific')

error_logging_level = logging.ERROR

warn_logging_level = logging.WARNING

class YoutubeDLPDebugStreamHandler(logging.StreamHandler):

    def __init__(self, stream=None):
        logging.StreamHandler.__init__(self, stream=stream)

    def emit(self, record):
        if record.levelno < error_logging_level:
            logging.StreamHandler.emit(self, record)

class ErrorHandler(logging.StreamHandler):

    def __init__(self, stream=None):
        logging.StreamHandler.__init__(self, stream=stream)

    def emit(self, record):
        if record.levelno > warn_logging_level:
            logging.StreamHandler.emit(self, record)

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
        if logger_name in cls.logger_list_indices:
            return cls.loggers[cls.logger_list_indices[logger_name]]
        else:
            return cls._add_logger(cls._setup_logger(logger_name))

    @classmethod
    def _add_logger(cls, logger):
        cls.loggers.insert(0, logger)
        cls.logger_list_indices = {}
        for (index, saved_logger) in enumerate(cls.loggers):
            cls.logger_list_indices[saved_logger.name] = index
        return logger



    @classmethod
    def _setup_debug_file_handlers(cls, debug_log_file_absolute_path, logger):
        debug_filehandler = RotatingFileHandler(
            debug_log_file_absolute_path, maxBytes=MAX_BYTES_LOG_FILE,
            backupCount=MAX_NUMBER_OF_LOG_FILES
        )
        debug_filehandler.setLevel(logging.DEBUG)
        debug_filehandler.setFormatter(sys_stream_formatting)
        logger.addHandler(debug_filehandler)

    @classmethod
    def _setup_info_file_handlers(cls, info_log_file_absolute_path, logger):
        info_filehandler = RotatingFileHandler(
            info_log_file_absolute_path, maxBytes=MAX_BYTES_LOG_FILE,
            backupCount=MAX_NUMBER_OF_LOG_FILES
        )
        info_filehandler.setLevel(logging.INFO)
        info_filehandler.setFormatter(sys_stream_formatting)
        logger.addHandler(info_filehandler)

    @classmethod
    def _setup_warn_file_handlers(cls, warn_log_file_absolute_path, logger):
        warn_filehandler = RotatingFileHandler(
            warn_log_file_absolute_path,
            maxBytes=MAX_BYTES_LOG_FILE,
            backupCount=MAX_NUMBER_OF_LOG_FILES
        )
        warn_filehandler.setFormatter(sys_stream_formatting)
        warn_filehandler.setLevel(warn_logging_level)
        logger.addHandler(warn_filehandler)


    @classmethod
    def _setup_error_file_handlers(cls, error_log_file_absolute_path, logger):
        error_filehandler = RotatingFileHandler(
            error_log_file_absolute_path,
            maxBytes=MAX_BYTES_LOG_FILE,
            backupCount=MAX_NUMBER_OF_LOG_FILES
        )
        error_filehandler.setFormatter(sys_stream_formatting)
        error_filehandler.setLevel(error_logging_level)
        logger.addHandler(error_filehandler)



    @classmethod
    def _setup_logger(cls, service_name):
        """
        Creates a logger for the specified service that prints to a file and the sys.stdout
        and sys.stderr
        :param service_name: the name of the service that is initializing the logger
        :return: the logger
        """
        date = datetime.datetime.now(date_timezone).strftime(date_formatting_in_filename)
        if not os.path.exists(f"logs/{date}"):
            os.makedirs(f"logs/{date}")
        debug_log_file_absolute_path = f"logs/{date}/debug.log"
        info_log_file_absolute_path = f"logs/{date}/info.log"
        warn_log_file_absolute_path = f"logs/{date}/warn.log"
        error_log_file_absolute_path = f"logs/{date}/error.log"

        logger = logging.getLogger(service_name)
        logger.setLevel(logging.DEBUG)


        # setup debug file handlers
        cls._setup_debug_file_handlers(debug_log_file_absolute_path, logger)

        # setup info file handler
        cls._setup_info_file_handlers(info_log_file_absolute_path, logger)

        # setup warn file handler
        cls._setup_warn_file_handlers(warn_log_file_absolute_path, logger)

        # setup error file handler
        cls._setup_error_file_handlers(error_log_file_absolute_path, logger)

        # setup stdout stream handler
        sys.stdout = sys.__stdout__
        sys_stdout_stream_handler = YoutubeDLPDebugStreamHandler(sys.stdout)
        sys_stdout_stream_handler.setFormatter(sys_stream_formatting)
        sys_stdout_stream_handler.setLevel(logging.DEBUG)
        logger.addHandler(sys_stdout_stream_handler)
        sys.stdout = LoggerWriter(logger.info)

        LoggingFilePath(
            error_file_path=error_log_file_absolute_path,
            warn_file_path=warn_log_file_absolute_path,
            debug_file_path=debug_log_file_absolute_path
        ).save()


        sys.stderr = sys.__stderr__
        sys_stderr_stream_handler = ErrorHandler(sys.stderr)
        sys_stderr_stream_handler.setFormatter(sys_stream_formatting)
        sys_stderr_stream_handler.setLevel(warn_logging_level)
        logger.addHandler(sys_stderr_stream_handler)
        sys.stderr = LoggerWriter(logger.error)
        # sys_stderr_stream_handler = YoutubeDLPWarnErrorHandler(
        #     sys.stderr,
        #     debug_file_name=debug_log_file_absolute_path,
        #     info_file_name=info_log_file_absolute_path,
        #     warn_file_name=warn_log_file_absolute_path,
        #     error_file_name=error_log_file_absolute_path
        # )
        # sys_stderr_stream_handler.setFormatter(sys_stream_formatting)
        # sys_stderr_stream_handler.setLevel(warn_logging_level)
        # logger.addHandler(sys_stderr_stream_handler)
        # sys.stderr = LoggerWriter(logger.error)

        return logger


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