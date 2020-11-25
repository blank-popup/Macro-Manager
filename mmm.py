# -*- coding: utf-8 -*-

# import sys
import wx
import pathlib
import argparse
import logging
import datetime

from mmMacroFrame import MMMacroFrame
from mmMacro import MMMacroFSM
from mmfsm import fsm, mc, mf
from mmlog import log
import mu


def add_parser_group(parser, required, name, default, options):
    parser_sub = parser.add_mutually_exclusive_group(required=required)
    for option in options:
        parser_sub.add_argument(*option[0], dest=name, action='store_const', const=option[1], help=option[2])
    parser.set_defaults(**{name:default})

class ActionFloatRange(argparse.Action):
    def __init__(self, minimum=None, maximum=None, *args, **kwargs):
        self.min = minimum
        self.max = maximum
        super(ActionFloatRange, self).__init__(*args, **kwargs)

    def __call__(self, parser, namespace, value, option_string=None):
        if not (self.min <= value <= self.max):
            msg = 'Invalid choice: {0} (choose from [{1}-{2}])'.format(value, self.min, self.max)
            raise argparse.ArgumentError(self, msg)
        setattr(namespace, self.dest, value)

def parse_args():
    parser = argparse.ArgumentParser()
    add_parser_group(parser, False, 'command', mu.command, [
        [('-cg', '--gui'), mu.KMCommand.GUI, 'Run in GUI mode'],
        [('-cp', '--play',), mu.KMCommand.PLAY, 'Run play in CGI mode'],
        [('-cr', '--record'), mu.KMCommand.RECORD, 'Run record in CGI mode'],
    ])
    add_parser_group(parser, False, 'target', mu.target, [
        [('-ta', '--both'), mu.KMTarget.KM, 'Both keyboard and mouse target'],
        [('-tk', '--keyboard',), mu.KMTarget.K, 'Keyboard target'],
        [('-tm', '--mouse'), mu.KMTarget.M, 'Mouse target'],
    ])
    parser.add_argument('-p', '--path', type=str, default=mu.path, required=('play' in argparse._sys.argv or 'record' in argparse._sys.argv), help='filepath(.mmm) saved macro in')
    parser.add_argument('-v', '--velocity', type=float, default=mu.velocity, action=ActionFloatRange, minimum=mu.minimum_velocity, maximum=mu.maximum_velocity, help='Choose value between {0} and {1}'.format(mu.minimum_velocity, mu.maximum_velocity))
    add_parser_group(parser, False, 'loop', mu.loop, [
        [('-l', '--loop'), True, 'Play infinitely'],
        [('--no-loop',), False, 'Play once'],
    ])
    add_parser_group(parser, False, 'loglevel', mu.loglevel, [
        [('-l10', '--loglevel-debug'), logging.DEBUG, 'log level: logging.DEBUG'],
        [('-l20', '--loglevel-info'), logging.INFO, 'log level: logging.INFO'],
        [('-l30', '--loglevel-warning'), logging.WARNING, 'log level: logging.WARNING'],
        [('-l40', '--loglevel-error'), logging.ERROR, 'log level: logging.ERROR'],
        [('-l50', '--loglevel-critical'), logging.CRITICAL, 'log level: logging.CRITICAL'],
    ])

    args = parser.parse_args()
    mu.command = args.command
    mu.target = args.target
    mu.path = args.path
    mu.loglevel = args.loglevel
    mu.velocity = args.velocity
    mu.term_sleep = mu.term_basic_sleep  / mu.velocity
    mu.loop = args.loop


def gui():
    app = wx.App()
    macroFrame = MMMacroFrame('actions/fsm.json')
    log.set_logger_textctrl_handler(logger, macroFrame.information.message, formatter, mu.loglevel)
    macroFrame.Show()
    app.MainLoop()

def cli_play():
    log.set_logger_console_handler(logger, formatter, mu.loglevel)
    macroFSM = MMMacroFSM(None, 'actions/fsm.json')

    macroFSM.check({
        mu.k_arg_lambdas_arg: mu.path,
        mu.k_arg_lambdas: [
            [lambda x: pathlib.Path(x).exists(), '[{0}] does not exist'.format(mu.path)],
            [lambda x: pathlib.Path(x).is_file(), '[{0}] is not file'.format(mu.path)],
            [lambda x: pathlib.Path(x).suffix == mu.k_extension_mmm, '[{0}] is not MMMacro'.format(mu.path)],
        ]
    })

    if macroFSM.mmif_get_status()[-1][mc.k_rcode] == mc.fsm_rcode_ack:
        macroFSM.velocity(mu.velocity)
        macroFSM.loop(mu.loop)
        macroFSM.load(mu.path)
        macroFSM.play(None)
        macroFSM.player.join()
    macroFSM.base(None)

def cli_record():
    log.set_logger_console_handler(logger, formatter, mu.loglevel)
    macroFSM = MMMacroFSM(None, 'actions/fsm.json')

    macroFSM.check({
        mu.k_arg_lambdas_arg: mu.path,
        mu.k_arg_lambdas: [
            [lambda x: not pathlib.Path(x).exists(), '[{0}] exist'.format(mu.path)],
            [lambda x: pathlib.Path(x).suffix == mu.k_extension_mmm, '[{0}] is not MMMacro'.format(mu.path)],
        ]
    })

    if macroFSM.mmif_get_status()[-1][mc.k_rcode] == mc.fsm_rcode_ack:
        macroFSM.record(None)
        macroFSM.recorder.lk.join()
        macroFSM.recorder.lm.join()
        macroFSM.save(mu.path)
    macroFSM.base(None)


if __name__ == '__main__':
    args = parse_args()
    logger = log.get_logger(mc.k_name_header, logging.DEBUG)
    log.set_sys_excepthook(logger)
    log.set_threading_excepthook()
    formatter = logging.Formatter(log.format_basic)
    dirpath_log = pathlib.Path.cwd() / mu.k_dirpath_log
    pathlib.Path(dirpath_log).mkdir(parents=True, exist_ok=True)
    now = datetime.datetime.now()
    filepath_log = dirpath_log / '{0}_{1}.{2}'.format('MMMacro', now.strftime('%Y%m%d'), 'log')
    log.set_logger_file_handler(logger, formatter, filepath_log, mu.loglevel)

    if mu.command == mu.KMCommand.PLAY:
        cli_play()
    elif mu.command == mu.KMCommand.RECORD:
        cli_record()
    elif mu.command == mu.KMCommand.GUI:
        gui()

