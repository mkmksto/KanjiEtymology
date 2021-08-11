# -*- coding: utf-8 -*-
# Copyright: Tanaka Aiko (https://github.com/aiko-tanaka)
# License: GNU AGPL, version 3 or later; https://www.gnu.org/licenses/agpl-3.0.en.html

from aqt.addons import AddonManager
from aqt import mw

import logging
import os
import sys

from functools import wraps
from time import time

FORMAT = logging.Formatter('%(levelname)s \t| %(asctime)s: \t%(message)s')


def setup_logger(name, log_file, _format=FORMAT, level=logging.DEBUG):
    """Create two or more loggers because writing to a CSV
    Causes the Characters to become messed up even with the
    correct encoding
    Note that the log files are always in UTF-8, never
    set by the user, i.e. even if the files read are in shift JIS
    the log files are still in UTF-8
    Args:
        name:           Name of the logger
        log_file:       Path to the log file
        _format:        String format
        level:          DEBUG by default
    """
    handler = logging.FileHandler(log_file)
    handler.setFormatter(_format)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger

# TODO: not yet usable, you should still create a config.py and config.md that pulls things like log path,
# and other config settings

addon_mgr_instance = AddonManager(mw)
ADD_ON_PATH = addon_mgr_instance.addonsFolder()
# TODO: dynamically determine the name of the addon instead of r'\push_existing'
PUSH_EXISTING_PATH = ADD_ON_PATH + r'\push_existing'

if not os.path.exists(PUSH_EXISTING_PATH):
    os.makedirs(PUSH_EXISTING_PATH)
NEW_PATH = os.path.join(ADD_ON_PATH, 'push_existing')
LOG_PATH = os.path.join(NEW_PATH, 'push_existing.log')
CALL_LOG_PATH = os.path.join(NEW_PATH, 'debug_call_log.log')
# I don't know why, but if you set the name of the logger to main_logger (same as main.py)
# logging entries double up
speed_logger = setup_logger('speed_logger', LOG_PATH)

del addon_mgr_instance


# https://stackoverflow.com/questions/11731136/python-class-method-decorator-w-self-arguments
# NOTE: if you wan't to use this decorator on a function, you must enclose the signal in a lambda
# That way, it passes the function itself as an argument instead of a flag (bool)
def calculate_time(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        before = time()
        result = f(*args, **kwargs)
        elapsed = time() - before
        speed_logger.info('function "{}" took {} seconds | self = {}'
                          .format(f.__name__, elapsed, args[0].__name__))
        return result
    return wrap


call_logger = setup_logger('call_logger', CALL_LOG_PATH)


# I'm not sure but just in case the decorated function has a return value, return result ensures that
# the value is passed?

# note to self: if the function passed is an object, 'self' would be part of *args
def trace_calls(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        result = f(*args, **kwargs)
        call_logger.info('function: "{}" | args: {} | kwargs: {}'
                         .format(f.__name__, args, kwargs))
        return result
    return wrap


# https://stackoverflow.com/questions/11232230/logging-to-two-files-with-different-settings
def open_log_file(path):
    """Opens either the Report Log or the CSV container
    for vocabs without any matches
    The senders specify a different path depending on the button
    Args:
        path:       path to the log file (~\Documents\Anki\addons\push_existing)
    """
    if sys.version_info[0] == 3:
        from webbrowser import open
        open(path)

    elif sys.version_info[0] == 2:
        os.startfile(path)