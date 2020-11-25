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

def initialize(self: MMMacroFSM, *args, **kwargs):
    self.player = None
    self.allow_loop = False
    self.recorder = None
    self.kms = []

    if mu.command == mu.KMCommand.GUI:
        if mu.path:
            stoping.load_file(self, mu.path)
        return {
            mc.k_rcode: 'ack_gui',
            mc.k_args: [],
            mc.k_kwargs: {}
        }
    elif mu.command == mu.KMCommand.PLAY:
        return {
            mc.k_rcode: 'ack_cli',
            mc.k_args: [],
            mc.k_kwargs: {}
        }
    elif mu.command == mu.KMCommand.RECORD:
        return {
            mc.k_rcode: 'ack_cli',
            mc.k_args: [],
            mc.k_kwargs: {}
        }
    else:
        return {
            mc.k_rcode: mc.fsm_rcode_nak,
            mc.k_args: [],
            mc.k_kwargs: {}
        }
