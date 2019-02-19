import structlog
import logging
import os
import datetime


class Logger:
    NAME = 'ROOT'
    DEFAULT_PATH = './logs'
    IS_ROOT_SETUP = True
    IS_DEBUG = False

    @staticmethod
    def get_logger():
        """
        Gets a logger.
        :return: The logger proxy.
        """
        if Logger.IS_ROOT_SETUP:
            Logger._setup_root_logger()
            Logger.IS_ROOT_SETUP = False

        return structlog.get_logger(Logger.NAME)

    @staticmethod
    def _setup_root_logger():
        """
        Setup the root logger to beautify the logging process.
        """
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
                structlog.stdlib.ProcessorFormatter.wrap_for_formatter
            ],
            context_class=structlog.threadlocal.wrap_dict(dict),
            logger_factory=structlog.stdlib.LoggerFactory()
        )
        formatter = structlog.stdlib.ProcessorFormatter(
            processor=structlog.dev.ConsoleRenderer()
        )
        formatter_file = structlog.stdlib.ProcessorFormatter(
            processor=structlog.dev.ConsoleRenderer(colors=False)
        )

        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        file_handler = logging.FileHandler(os.path.join(
            Logger.DEFAULT_PATH,
            f'{Logger.NAME}-{datetime.datetime.today().strftime("%Y-%m-%d-%H-%M-%S")}.log'))
        file_handler.setFormatter(formatter_file)
        logger = logging.getLogger(Logger.NAME)
        logger.addHandler(handler)
        logger.addHandler(file_handler)
        logger.setLevel(logging.DEBUG if Logger.IS_DEBUG else logging.INFO)
