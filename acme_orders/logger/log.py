__author__ = 'david'
"""
Created on 06/17/2016

@author David Pinheiro

Module responsible for provinding logging features.
"""

import os
import logging
from logging import StreamHandler
from logging.handlers import RotatingFileHandler
import inspect

from acme_orders import app


if not os.path.exists(app.config['LOG_LOCATION']):
    os.makedirs(app.config['LOG_LOCATION'])

formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(name)s.%(funcName)s - PID:%(process)d - TID:%(thread)d - %(message)s')


def create_logger(class_name):
    """create logger based on class_name"""
    
    logger = logging.getLogger('{0}'.format(class_name))
    has_stream_handler = False
    has_file_handler = False
    handlers = []
    
    for log_handler in logger.handlers:
        has_stream_handler = True if isinstance(log_handler, StreamHandler) else has_stream_handler
        has_file_handler = True if isinstance(log_handler, RotatingFileHandler) else has_file_handler

    if not has_stream_handler:
        handlers.append(StreamHandler())
    if not has_file_handler:
        location = app.config['LOG_LOCATION'] + app.config['LOG_NAME']
        handlers.append(RotatingFileHandler(location, maxBytes=10000000, backupCount=10))

    for handler in handlers:
        handler.setLevel(logging.INFO)
        handler.setFormatter(formatter)
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)        

    return logger


def log(logger, uuid_value, response, level="info", params=None):
    """defines a standard to messages and log them"""

    method = inspect.stack()[1][0].f_code.co_name
    msg = ('uuid={}, caller={}, calling_method={}, params={}, msg={}'
        .format(uuid_value, '', method, params, response))

    getattr(logger, level)(msg)
