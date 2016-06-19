__author__ = 'david'
"""
Created on 06/17/2016

@author David Pinheiro

Module responsible for provinding logging features.
"""

import os
import logging
from logging import StreamHandler
import inspect

from acme_orders.config import general_config


formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(name)s.%(funcName)s - PID:%(process)d - TID:%(thread)d - %(message)s')

handler_console = StreamHandler()
handler_console.setLevel(logging.DEBUG)
handler_console.setFormatter(formatter)


def create_logger(class_name):
    """create logger based on class_name"""

    logger = logging.getLogger('{0}'.format(class_name))
    logger.setLevel(logging.INFO)
    logger.addHandler(handler_console)

    return logger


def log(logger, uuid_value, response, level="info", params=None):
    """defines a standard to messages and log them"""

    method = inspect.stack()[1][0].f_code.co_name
    msg = ('uuid={}, caller={}, calling_method={}, params={}, msg={}'
        .format(uuid_value, '', method, params, response))

    getattr(logger, level)(msg)
