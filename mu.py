# -*- coding: utf-8 -*-

from pynput import keyboard
from pynput import mouse

from enum import Enum
from dataclasses import dataclass, field
from typing import Any

import wx.adv


class KMCommand(Enum):
    GUI = 0
    PLAY = 1
    RECORD = 2


class KMTarget(Enum):
    KM = 0
    K = 1
    M = 2


class KMType(Enum):
    PRESS = 0
    RELEASE = 1
    CLICK = 2
    MOVE = 3
    SCROLL = 4


@dataclass
class KMData:
    sequence: int = 0
    category: KMType = KMType.PRESS
    action: bool = False
    value: Any = field(default_factory=tuple)
    position: tuple = field(default_factory=tuple)
    keys: list = field(default_factory=list)
    buttons: list = field(default_factory=list)
    timing: float = 0


def wx_notify(title, message, timeout):
    notify = wx.adv.NotificationMessage(
        title=title,
        message=message,
        parent=None,
        flags=wx.ICON_INFORMATION
    )

    notify.Show(timeout=5)


critical_difference = 180

k_dirpath_log = 'log'
k_dirpath_macro = 'macro'
k_extension_mmm = '.mmm'


import wx.lib.newevent

k_command = 'command'
event_mmm_ui, EVENT_MMM_UI = wx.lib.newevent.NewEvent()
k_clear_records = 'clear_records'
k_load_records = 'load_records'
k_refresh_records = 'refresh_records'
k_append_record = 'append_record'
k_insert_record = 'insert_record'
k_delete_record = 'delete_record'
k_remove_record = 'remove_record'
k_arg_km = 'arg_km'
k_arg_index = 'arg_index'
k_arg_path = 'arg_path'
k_arg_event = 'arg_event'
k_arg_lambdas = 'arg_lambdas'
k_arg_lambdas_arg = 'arg_lambdas_arg'

# state
k_recording_gui = 'recording_gui'
k_playing_gui = 'playing_gui'
k_pausing_gui = 'pausing_gui'
k_stoping_gui = 'stoping_gui'
k_recording_cli = 'recording_cli'
k_playing_cli = 'playing_cli'
k_pausing_cli = 'pausing_cli'
k_stoping_cli = 'stoping_cli'

# window
k_main_frame = 'main_frame'
k_menu = 'menu'
k_toolbar = 'toolbar'
k_statusbar = 'statusboar'
k_panel_KM = 'panel_KM'
k_KM = 'KM'
k_panel_filetree = 'panel_filetree'
k_filetree = 'filetree'
k_panel_message = 'panel_message'
k_message = 'message'

# main_frame
k_close = 'close'

# menu

# toolbar
k_record = 'record'
k_play = 'play'
k_pause = 'pause'
k_stop = 'stop'
k_loop = 'loop'
k_load = 'load'
k_save = 'save'
k_velocity = 'velocity'

# statusbar

# KM

# explorer

# information

# etc
k_check = 'check'

id_window = {
    k_main_frame: 11000,
    k_menu: 12000,
    k_toolbar: 13000,
    k_statusbar: 14000,
    k_panel_KM: 15000,
    k_KM: 15100,
    k_panel_filetree: 16000,
    k_filetree: 16100,
    k_panel_message: 17000,
    k_message: 17100,
}

ID = {
    k_main_frame: {
        k_close: id_window[k_main_frame] + 10,
    },
    k_menu: {
    },
    k_toolbar: {
        k_record: id_window[k_toolbar] + 10,
        k_play: id_window[k_toolbar] + 20,
        k_pause: id_window[k_toolbar] + 30,
        k_stop: id_window[k_toolbar] + 40,
        k_loop: id_window[k_toolbar] + 50,
        k_save: id_window[k_toolbar] + 60,
        k_velocity: id_window[k_toolbar] + 70,
    },
    k_statusbar: {
    },
    k_KM: {
    },
    k_filetree: {
    },
    k_message: {
    },
}

# shortcut
KEY_PAUSE = keyboard.Key.scroll_lock
KEY_STOP = keyboard.Key.pause

# default setting
minimum_slider_velocity = 0
maximum_slider_velocity = 90
term_basic_sleep = 0.1
minimum_velocity = 0.5
maximum_velocity = 5

command = KMCommand.GUI
target = KMTarget.KM
path = ''
loglevel = 20
velocity = 3.0
term_sleep = term_basic_sleep / velocity
loop = False

@dataclass
class SaveData:
    target: KMTarget = KMTarget.KM
    loglevel: int = loglevel
    velocity: float = velocity
    term_sleep: float = term_sleep
    loop: bool = False
    KMs: list = field(default_factory=list)
