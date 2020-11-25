# -*- coding: utf-8 -*-

from pynput import keyboard
from pynput import mouse
import time
import logging
import wx

import pathlib
import pickle
import traceback

from mmlog import log
from mmfsm import fsm, mc, mf
import mu
from mmMacro import MMMacroFSM, MMRecorder, MMPlayer, event_thread_play


logger = log.get_logger('{0}.{1}'.format(mc.k_name_header, __name__), logging.DEBUG)

def record(self: MMMacroFSM, *args, **kwargs):
    self.recorder = MMRecorder(self)
    self.recorder.lk.start()
    self.recorder.lm.start()
    
    if self.UI:
        self.UI.Iconize()
        wx.PostEvent(self.UI, mu.event_mmm_ui(**{
            mu.k_command: mu.k_clear_records
        }))

    return {
        mc.k_rcode: mc.fsm_rcode_ack,
        mc.k_args: [],
        mc.k_kwargs: {}
    }

def play(self: MMMacroFSM, *args, **kwargs):
    event_thread_play.set()
    self.player = MMPlayer(self)
    self.player.terminate_play = False
    self.player.start()
    
    if self.UI:
        self.UI.Iconize()

    return {
        mc.k_rcode: mc.fsm_rcode_ack,
        mc.k_args: [],
        mc.k_kwargs: {}
    }

def loop(self: MMMacroFSM, *args, **kwargs):
    if self.UI:
        e = kwargs[mu.k_arg_event]
        checkbox = e.GetEventObject()
        self.allow_loop = checkbox.IsChecked()
        logger.info('Loop is [{0}]'.format('checked' if self.allow_loop else 'unchecked'))
    else:
        self.allow_loop = kwargs[mu.k_arg_event]
        logger.info('Loop is [{0}]'.format('True' if self.allow_loop else 'False'))

    return {
        mc.k_rcode: mc.fsm_rcode_ack,
        mc.k_args: [],
        mc.k_kwargs: {}
    }

def save(self: MMMacroFSM, *args, **kwargs):
    if self.UI:
        wildcard = "MMMacro file (*{0})|*{0}".format(mu.k_extension_mmm)
        path_filetree = self.UI.files.filetree.GetPath()
        path = pathlib.Path(path_filetree)
        if path.is_dir():
            path_dialog = str(path)
        elif path.is_file():
            path_dialog = str(path.parent)
        else:
            path_dialog = str(pathlib.Path.cwd() / mu.k_dirpath_macro)

        dialog = wx.FileDialog(
            self.UI,
            message="Name a MMMacro file",
            defaultDir=path_dialog,
            defaultFile="",
            wildcard=wildcard,
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        )
        if dialog.ShowModal() == wx.ID_OK:
            path_selected = dialog.GetPath()
        else:
            logger.info('Canceled save')

            return {
                mc.k_rcode: mc.fsm_rcode_nak,
                mc.k_args: [],
                mc.k_kwargs: {}
            }
    else:
        path_selected = kwargs[mu.k_arg_event]

    return save_file(self, path_selected)

def save_file(self: MMMacroFSM, filepath):
    path = pathlib.Path(filepath)
    if not path.exists():
        if path.suffix == mu.k_extension_mmm:
            try:
                with open(path, 'wb') as f:
                    pickle.dump(self.kms, f)
                logger.info('Saved MMMacro: [{0}]'.format(path))
            except Exception as e:
                logger.error('{0} [{1}]\n{2}\n{3}'.format('Cannot save', path, str(e), ''.join(traceback.format_tb(e.__traceback__))))
                return {
                    mc.k_rcode: mc.fsm_rcode_nak,
                    mc.k_args: [],
                    mc.k_kwargs: {}
                }

            if self.UI:
                wx.PostEvent(self.UI, mu.event_mmm_ui(**{
                    mu.k_command: mu.k_refresh_records,
                    mu.k_arg_path: path
                }))

            return {
                mc.k_rcode: mc.fsm_rcode_ack,
                mc.k_args: [],
                mc.k_kwargs: {}
            }
        else:
            logger.error('[{0}] is not MMMacro'.format(path))
    else:
        logger.error('[{0}] exist'.format(path))

    return {
        mc.k_rcode: mc.fsm_rcode_nak,
        mc.k_args: [],
        mc.k_kwargs: {}
    }

def velocity(self: MMMacroFSM, *args, **kwargs):
    if self.UI:
        e = kwargs[mu.k_arg_event]
        slider = e.GetEventObject()
        value = slider.GetValue()
        mu.velocity = (mu.maximum_velocity - mu.minimum_velocity) / (mu.maximum_slider_velocity - mu.minimum_slider_velocity) * (value - mu.minimum_slider_velocity) +  mu.minimum_velocity
        mu.term_sleep = mu.term_basic_sleep / mu.velocity
        logger.info('Set velocity: [{0}]'.format(round(mu.velocity, 3)))
    else:
        try:
            value = float(kwargs[mu.k_arg_event])
            if value < mu.minimum_velocity or value > mu.maximum_velocity:
                logger.error('Parameter velocity must be equal or greater than {0} and equal or less than {1}'.format(mu.minimum_velocity, mu.maximum_velocity))
                return {
                    mc.k_rcode: mc.fsm_rcode_nak,
                    mc.k_args: [],
                    mc.k_kwargs: {}
                }
        except:
            logger.error('Parameter velocity [{0}] is not float type'.format(kwargs[mu.k_arg_event]))
            return {
                mc.k_rcode: mc.fsm_rcode_nak,
                mc.k_args: [],
                mc.k_kwargs: {}
            }

        mu.velocity = value
        mu.term_sleep = mu.term_basic_sleep / mu.velocity
        logger.info('Set velocity: [{0}]'.format(round(mu.velocity, 3)))

    return {
        mc.k_rcode: mc.fsm_rcode_ack,
        mc.k_args: [],
        mc.k_kwargs: {}
    }

def load(self: MMMacroFSM, *args, **kwargs):
    if self.UI:
        e = kwargs[mu.k_arg_event]
        genericDirCtrl = e.GetEventObject()
        path_selected = genericDirCtrl.GetPath()
    else:
        path_selected = kwargs[mu.k_arg_event]

    return load_file(self, path_selected)

def load_file(self: MMMacroFSM, filepath):
    path = pathlib.Path(filepath)
    if path.exists():
        if path.is_file():
            if path.suffix == mu.k_extension_mmm:
                try:
                    with open(path, 'rb') as f:
                        self.kms = pickle.load(f)
                    logger.info('Loaded MMMacro: [{0}]'.format(path))
                except Exception as e:
                    logger.error('{0} [{1}]\n{2}\n{3}'.format('Cannot load', path, str(e), ''.join(traceback.format_tb(e.__traceback__))))
                    return {
                        mc.k_rcode: mc.fsm_rcode_nak,
                        mc.k_args: [],
                        mc.k_kwargs: {}
                    }

                if self.UI:
                    wx.PostEvent(self.UI, mu.event_mmm_ui(**{
                        mu.k_command: mu.k_load_records
                    }))

                return {
                    mc.k_rcode: mc.fsm_rcode_ack,
                    mc.k_args: [],
                    mc.k_kwargs: {}
                }
            else:
                logger.error('[{0}] is not MMMacro'.format(path))
        else:
            logger.error('[{0}] is not file'.format(path))
    else:
        logger.error('[{0}] does not exist'.format(path))

    return {
        mc.k_rcode: mc.fsm_rcode_nak,
        mc.k_args: [],
        mc.k_kwargs: {}
    }

def check(self: MMMacroFSM, *args, **kwargs):
    arg = kwargs[mu.k_arg_event][mu.k_arg_lambdas_arg]
    for lam in kwargs[mu.k_arg_event][mu.k_arg_lambdas]:
        if not lam[0](arg):
            logger.error(lam[1])
            return {
                mc.k_rcode: mc.fsm_rcode_nak,
                mc.k_args: [],
                mc.k_kwargs: {}
            }

    return {
        mc.k_rcode: mc.fsm_rcode_ack,
        mc.k_args: [],
        mc.k_kwargs: {}
    }
