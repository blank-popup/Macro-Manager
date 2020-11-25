# -*- coding: utf-8 -*-

import logging
import logging.handlers
import threading
import sys

from mmfsm import mc


format_basic = '[%(asctime)s][%(name)s][%(levelname)s] %(message)s'


class TlsSMTPHandler(logging.handlers.SMTPHandler):
    def emit(self, record):
        try:
            import smtplib
            from email.utils import formatdate
            port = self.mailport
            if not port:
                port = smtplib.SMTP_PORT
            smtp = smtplib.SMTP(self.mailhost, port)
            msg = self.format(record)
            msg = 'From: {0}\r\nTo: {1}\r\nSubject: {2}\r\nDate: {3}\r\n\r\n{4}'.format(
                self.fromaddr,
                ','.join(self.toaddrs),
                self.getSubject(record),
                formatdate(),
                msg
            )
            if self.username:
                smtp.ehlo()
                smtp.starttls()
                smtp.ehlo()
                smtp.login(self.username, self.password)
            smtp.sendmail(self.fromaddr, self.toaddrs, msg)
            smtp.quit()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)


class TextCtrlHandler(logging.StreamHandler):
    def __init__(self, textctrl):
        logging.StreamHandler.__init__(self)
        self.textctrl = textctrl
        
    def emit(self, record):
        msg = self.format(record)
        self.textctrl.WriteText(msg + "\n")
        self.flush()


logger = logging.getLogger('{0}.{1}'.format(mc.k_name_header, __name__))
old_excepthook = sys.excepthook

def exhook(logger, excType, excValue, traceback):
    logger.critical('Exception sys.excepthook', exc_info=(excType, excValue, traceback))

def set_sys_excepthook(logger):
    sys.excepthook = lambda excType, excValue, traceback: exhook(logger, excType, excValue, traceback)

def set_threading_excepthook():
    init_original = threading.Thread.__init__

    def init(self, *args_init, **kwargs_init):
        init_original(self, *args_init, **kwargs_init)
        run_original = self.run

        def run_with_except_hook(*args_run, **kwargs_run):
            try:
                run_original(*args_run, **kwargs_run)
            except Exception:
                sys.excepthook(*sys.exc_info())

        self.run = run_with_except_hook

    threading.Thread.__init__ = init

def get_logger(name, level=logging.DEBUG):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    return logger

def set_logger_console_handler(logger, formatter, level=logging.DEBUG):
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatter)
    streamHandler.setLevel(level)
    logger.addHandler(streamHandler)

def set_logger_textctrl_handler(logger, textCtrl, formatter, level=logging.DEBUG):
    textctrlHandler = TextCtrlHandler(textCtrl)
    textctrlHandler.setFormatter(formatter)
    textctrlHandler.setLevel(level)
    logger.addHandler(textctrlHandler)

def set_logger_file_handler(logger, formatter, filepath, level=logging.DEBUG):
    fileHandler = logging.handlers.RotatingFileHandler(filepath, mode='a', maxBytes=1048576, backupCount=100, encoding="utf-8")
    fileHandler.setFormatter(formatter)
    fileHandler.setLevel(level)
    logger.addHandler(fileHandler)

def set_logger_smtp_handler(logger, formatter, receivers, subject, level=logging.ERROR):
    smtpHandler = TlsSMTPHandler(('smtp.gmail.com', 587), 'fromemail@gmail.com', receivers, subject, ('fromemail@gmail.com', 'password'))
    smtpHandler.setFormatter(formatter)
    smtpHandler.setLevel(level)
    logger.addHandler(smtpHandler)
