# -*- coding: utf-8 -*-

from pynput import keyboard
from pynput import mouse
import time
import logging
import wx

import datetime
import threading
import pathlib

from mmlog import log
from mmfsm import fsm, mc, mf
import mu


event_thread_play = threading.Event()

class MMPlayer(threading.Thread):
    def __init__(self, macroFSM):
        super(MMPlayer, self).__init__()
        self.logger = log.get_logger('{0}.{1}'.format(mc.k_name_header, __name__), logging.DEBUG)
        self.macroFSM = macroFSM
        self.ck = keyboard.Controller()
        self.cm = mouse.Controller()
        self.index_playing = 0
        self.count_sleep = 0
        self.terminate_play = False
        self.lk = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        self.lk.start()
        self.lm = mouse.Listener(on_click=self.on_click, on_move=self.on_move, on_scroll=self.on_scroll)
        self.lm.start()

    def on_press(self, key):
        if key == mu.KEY_PAUSE:
            self.macroFSM.mmif_run_once(**{
                mc.k_event: mu.k_pause
            })
        elif key == mu.KEY_STOP:
            self.macroFSM.mmif_run_once(**{
                mc.k_event:mu.k_stop
            })
    
    def on_release(self, key):
        pass

    def on_click(self, x, y, button, pressed):
        pass
    
    def on_move(self, x, y):
        pass
    
    def on_scroll(self, x, y, dx, dy):
        pass

    def run(self):
        while True:
            for ii in range(0, len(self.macroFSM.kms)):
                self.index_playing = ii
                km = self.macroFSM.kms[ii]
                total_sleep = int(km.timing / mu.term_basic_sleep)
                for jj in range(0, total_sleep):
                    if self.terminate_play:
                        return
                    event_thread_play.wait()
                    self.count_sleep = jj
                    position_next = self.get_next_position(km, jj)
                    self.cm.move(position_next[0] - self.cm.position[0], position_next[1] - self.cm.position[1])
                    time.sleep(mu.term_sleep)
                if self.terminate_play:
                    return
                event_thread_play.wait()
                self.cm.move(km.position[0] - self.cm.position[0], km.position[1] - self.cm.position[1])
                time.sleep(mu.term_basic_sleep)
                self.play_km(km)
            if not self.macroFSM.allow_loop and not self.terminate_play:
                self.macroFSM.mmif_run_once(**{
                    mc.k_event: mu.k_stop
                })
                return

    def get_next_position(self, km, jj):
        remain_sleep = km.timing - jj * mu.term_basic_sleep
        x = int((self.cm.position[0] * (remain_sleep - mu.term_basic_sleep) + km.position[0] * mu.term_basic_sleep) / remain_sleep)
        y = int((self.cm.position[1] * (remain_sleep - mu.term_basic_sleep) + km.position[1] * mu.term_basic_sleep) / remain_sleep)
        return (x, y)

    def play_km(self, km):
        self.cm.move(km.position[0] - self.cm.position[0], km.position[1] - self.cm.position[1])
        if km.category == mu.KMType.PRESS:
            self.ck.press(km.value)
        elif km.category == mu.KMType.RELEASE:
            self.ck.release(km.value)
        elif km.category == mu.KMType.CLICK:
            if km.action == True:
                self.cm.press(km.value)
            else:
                self.cm.release(km.value)
        elif km.category == mu.KMType.MOVE:
            pass
        elif km.category == mu.KMType.SCROLL:
            self.cm.scroll(*km.value)
        else:
            pass


class MMRecorder(object):
    def __init__(self, macroFSM):
        self.logger = log.get_logger('{0}.{1}'.format(mc.k_name_header, __name__), logging.DEBUG)
        self.macroFSM = macroFSM
        self.position_previous = mouse.Controller().position
        self.keys = []
        self.buttons = []
        self.kms = []
        self.time_previous = time.time()
        self.lk = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        self.lm = mouse.Listener(on_click=self.on_click, on_move=self.on_move, on_scroll=self.on_scroll)

    def on_press(self, key):
        if key not in self.keys:
            self.keys.append(key)
            position = mouse.Controller().position
            timing = self.get_timing()
            self.append_km(mu.KMData(sequence=len(self.kms), category=mu.KMType.PRESS, action=None, value=key, position=position, timing=timing, keys=self.keys[:], buttons=self.buttons[:]))
    
    def on_release(self, key):
        if key in self.keys:
            position = mouse.Controller().position
            timing = self.get_timing()
            self.append_km(mu.KMData(sequence=len(self.kms), category=mu.KMType.RELEASE, action=None, value=key, position=position, timing=timing, keys=self.keys[:], buttons=self.buttons[:]))
            self.keys.remove(key)
    
    def on_click(self, x, y, button, pressed):
        if pressed == True:
            if button not in self.buttons:
                self.buttons.append(button)
                position = (x, y)
                timing = self.get_timing()
                self.append_km(mu.KMData(sequence=len(self.kms), category=mu.KMType.CLICK, action=pressed, value=button, position=position, timing=timing, keys=self.keys[:], buttons=self.buttons[:]))
        else:
            if button in self.buttons:
                position = (x, y)
                timing = self.get_timing()
                self.append_km(mu.KMData(sequence=len(self.kms), category=mu.KMType.CLICK, action=pressed, value=button, position=position, timing=timing, keys=self.keys[:], buttons=self.buttons[:]))
                self.buttons.remove(button)
    
    def on_move(self, x, y):
        if self.keys == [] and self.buttons == []:
            if self.macroFSM.mmiv_state == mu.k_recording_gui or self.macroFSM.mmiv_state == mu.k_recording_cli:
                difference_x = x - self.position_previous[0]
                differenct_y = y - self.position_previous[1]
                if difference_x > mu.critical_difference or difference_x < - mu.critical_difference \
                or differenct_y > mu.critical_difference or differenct_y < - mu.critical_difference:
                    self.macroFSM.mmif_run_once(**{
                        mc.k_event: mu.k_stop
                    })
        self.position_previous = (x, y)
    
    def on_scroll(self, x, y, dx, dy):
        value = (dx, dy)
        position = (x, y)
        timing = self.get_timing()
        self.append_km(mu.KMData(sequence=len(self.kms), category=mu.KMType.SCROLL, action=None, value=value, position=position, timing=timing, keys=self.keys[:], buttons=self.buttons[:]))

    def get_timing(self):
        time_current = time.time()
        time_previous = self.time_previous
        self.time_previous = time_current
        return time_current - time_previous
    
    def append_km(self, km):
        self.kms.append(km)
        if self.macroFSM.UI:
            kwargs = {
                mu.k_command: mu.k_append_record,
                mu.k_arg_index: None,
                mu.k_arg_km: km,
            }
            wx.PostEvent(self.macroFSM.UI, mu.event_mmm_ui(**kwargs))


class MMMacroFSM(fsm.MMFSM):
    def __init__(self, UI, fsmpath, *args, **kwargs):
        self.logger = log.get_logger('{0}.{1}'.format(mc.k_name_header, __name__), logging.DEBUG)
        self.UI = UI
        self.args = args
        self.kwargs = kwargs
        self.player = None
        self.recorder = None

        super(MMMacroFSM, self).__init__(fsmpath, *args, **kwargs)

    def record(self, e):
        self.mmif_run_once(**{
            mc.k_event: mu.k_record,
            mu.k_arg_event: e
        })

    def play(self, e):
        self.mmif_run_once(**{
            mc.k_event: mu.k_play,
            mu.k_arg_event: e
        })

    def pause(self, e):
        self.mmif_run_once(**{
            mc.k_event: mu.k_pause,
            mu.k_arg_event: e
        })

    def stop(self, e):
        self.mmif_run_once(**{
            mc.k_event: mu.k_stop,
            mu.k_arg_event: e
        })

    def loop(self, e):
        self.mmif_run_once(**{
            mc.k_event: mu.k_loop,
            mu.k_arg_event: e
        })
    
    def save(self, e):
        self.mmif_run_once(**{
            mc.k_event: mu.k_save,
            mu.k_arg_event: e
        })

    def velocity(self, e):
        self.mmif_run_once(**{
            mc.k_event: mu.k_velocity,
            mu.k_arg_event: e
        })

    def load(self, e):
        self.mmif_run_once(**{
            mc.k_event: mu.k_load,
            mu.k_arg_event: e
        })

    def base(self, e):
        self.mmif_run_once(**{
            mc.k_event: mc.k_base,
            mu.k_arg_event: e
        })

    def check(self, e):
        self.mmif_run_once(**{
            mc.k_event: mu.k_check,
            mu.k_arg_event: e
        })

    def append_km(self, km):
        self.kms.append(km)
        if self.UI:
            kwargs = {
                mu.k_command: mu.k_append_record,
                mu.k_arg_index: None,
                mu.k_arg_km: km,
            }
            wx.PostEvent(self.UI, mu.event_mmm_ui(**kwargs))

    def insert_km(self, index, km):
        self.kms.insert(index, km)
        if self.UI:
            kwargs = {
                mu.k_command: mu.k_insert_record,
                mu.k_arg_index: index,
                mu.k_arg_km: km,
            }
            wx.PostEvent(self.UI, mu.event_mmm_ui(**kwargs))
    
    def del_km(self, index):
        del self.kms[index]
        if self.UI:
            kwargs = {
                mu.k_command: mu.k_delete_record,
                mu.k_arg_index: index,
                mu.k_arg_km: None,
            }
            wx.PostEvent(self.UI, mu.event_mmm_ui(**kwargs))

    def remove_km(self, km):
        self.kms.remove(km)
        if self.UI:
            kwargs = {
                mu.k_command: mu.k_remove_record,
                mu.k_arg_index: None,
                mu.k_arg_km: km,
            }
            wx.PostEvent(self.UI, mu.event_mmm_ui(**kwargs))
    