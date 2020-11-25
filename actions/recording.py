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

def stop(self: MMMacroFSM, *args, **kwargs):
    self.recorder.lk.stop()
    self.recorder.lm.stop()
    self.kms = self.recorder.kms
    
    if self.UI:
        self.UI.Restore()

    return {
        mc.k_rcode: mc.fsm_rcode_ack,
        mc.k_args: [],
        mc.k_kwargs: {}
    }

