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

def pause(self: MMMacroFSM, *args, **kwargs):
    event_thread_play.clear()
    
    return {
        mc.k_rcode: mc.fsm_rcode_ack,
        mc.k_args: [],
        mc.k_kwargs: {}
    }

def stop(self: MMMacroFSM, *args, **kwargs):
    if self.player.index_playing < len(self.kms):
        buttons = self.kms[self.player.index_playing].buttons
        for button in buttons:
            self.player.cm.release(button)
        keys = self.kms[self.player.index_playing].keys
        for key in keys:
            self.player.ck.release(key)
    self.player.lm.stop()
    self.player.lk.stop()
    self.player.terminate_play = True
    import threading
    
    if self.UI:
        self.UI.Restore()
    
    return {
        mc.k_rcode: mc.fsm_rcode_ack,
        mc.k_args: [],
        mc.k_kwargs: {}
    }
