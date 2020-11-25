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

from . import playing, stoping


logger = log.get_logger('{0}.{1}'.format(mc.k_name_header, __name__), logging.DEBUG)

def pause(self: MMMacroFSM, *args, **kwargs):
    event_thread_play.set()
    
    return {
        mc.k_rcode: mc.fsm_rcode_ack,
        mc.k_args: [],
        mc.k_kwargs: {}
    }

def stop(self: MMMacroFSM, *args, **kwargs):
    event_thread_play.set()
    return playing.stop(self, *args, **kwargs)

def loop(self: MMMacroFSM, *args, **kwargs):
    return stoping.loop(self, *args, **kwargs)

def velocity(self: MMMacroFSM, *args, **kwargs):
    return stoping.velocity(self, *args, **kwargs)
