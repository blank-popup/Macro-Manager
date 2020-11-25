# -*- coding: utf-8 -*-

import logging
import json

from . import mc
from mmlog import log

logger = log.get_logger('{0}.{1}'.format(mc.k_name_header, __name__), logging.DEBUG)

def write_file_json(path, j):
    with open(path, 'w') as f:
        json.dump(j, f, indent='    ')

def read_file_json(path):
    with open(path, 'r') as f:
        j = json.load(f)
    return j
