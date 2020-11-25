# -*- coding: utf-8 -*-

from pynput import keyboard
from pynput import mouse
import time
import logging
import wx

from mmlog import log
from mmfsm import fsm, mc, mf
import mu
from mmMacro import MMMacroFSM, MMRecorder, MMPlayer, event_thread_play


logger = log.get_logger('{0}.{1}'.format(mc.k_name_header, __name__), logging.DEBUG)

def finalize(self: MMMacroFSM, *args, **kwargs):

    return {
        mc.k_rcode: mc.fsm_rcode_ack,
        mc.k_args: [],
        mc.k_kwargs: {}
    }
