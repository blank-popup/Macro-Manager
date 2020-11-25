# -*- coding: utf-8 -*-

import wx
import os
import sys
import logging
import threading
import pathlib

from mmlog import log
from mmfsm import fsm, mc, mf
import mu
from mmMacro import MMMacroFSM


class KMPanel(wx.Panel):
    def __init__(self, parent):
        super(wx.Panel, self).__init__(parent, id=mu.id_window[mu.k_panel_KM])
        self.KM = wx.ListCtrl(self, id=mu.id_window[mu.k_KM], style=wx.LC_REPORT)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.KM, 1, wx.EXPAND)
        self.SetSizer(self.sizer)

        self.KM.InsertColumn(0, '#', format=wx.LIST_FORMAT_RIGHT)
        self.KM.InsertColumn(1, 'Category')
        self.KM.InsertColumn(2, 'Action')
        self.KM.InsertColumn(3, 'Value')
        self.KM.InsertColumn(4, 'Position')
        self.KM.InsertColumn(5, 'Pressed')
        self.KM.InsertColumn(6, 'Timing')

        self.KM.SetColumnWidth(0, 40)
        self.KM.SetColumnWidth(1, 70)
        self.KM.SetColumnWidth(2, 70)
        self.KM.SetColumnWidth(3, 90)
        self.KM.SetColumnWidth(4, 90)
        self.KM.SetColumnWidth(5, 150)
        self.KM.SetColumnWidth(6, 60)


class FileTreePanel(wx.Panel):
    def __init__(self, parent):
        super(wx.Panel, self).__init__(parent, id=mu.id_window[mu.k_panel_filetree])
        self.filetree = wx.GenericDirCtrl(self, id=mu.id_window[mu.k_filetree], style=wx.LC_REPORT)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.filetree, 1, wx.EXPAND)
        self.SetSizer(self.sizer)

        dirpath_macro = pathlib.Path.cwd() / mu.k_dirpath_macro
        pathlib.Path(dirpath_macro).mkdir(parents=True, exist_ok=True)
        self.filetree.SetPath(str(dirpath_macro))
        self.filetree.Bind(wx.EVT_DIRCTRL_FILEACTIVATED, parent.Parent.Parent.on_dirctl_fileactivated)


class MessagePanel(wx.Panel):
    def __init__(self, parent):
        super(wx.Panel, self).__init__(parent, id=mu.id_window[mu.k_panel_message])
        self.message = wx.TextCtrl(self, id=mu.id_window[mu.k_message], style=wx.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.message, 1, wx.EXPAND)
        self.SetSizer(self.sizer)


class MMMacroFrame(wx.Frame):
    def __init__(self, fsmpath):
        super(MMMacroFrame, self).__init__(None, id=mu.id_window[mu.k_main_frame])
        self.create_content_panel()
        self.logger = log.get_logger('{0}.{1}'.format(mc.k_name_header, __name__), logging.DEBUG)
        self.create_bars()
        self.macroFSM = MMMacroFSM(self, fsmpath)

    def create_content_panel(self):
        self.splitter_information = wx.SplitterWindow(self, style=wx.SP_BORDER|wx.SP_LIVE_UPDATE)
        self.splitter_information.SetMinimumPaneSize(50)

        self.splitter_filetree = wx.SplitterWindow(self.splitter_information, style=wx.SP_BORDER|wx.SP_LIVE_UPDATE)
        self.splitter_filetree.SetMinimumPaneSize(50)

        self.records = KMPanel(self.splitter_filetree)
        self.files = FileTreePanel(self.splitter_filetree)
        self.splitter_filetree.SplitVertically(self.records, self.files)

        self.information = MessagePanel(self.splitter_information)
        self.splitter_information.SplitHorizontally(self.splitter_filetree, self.information)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.splitter_information, 1, wx.EXPAND)
        self.SetSize(1000, 500)
        self.SetSizer(self.sizer)

        self.SetTitle("MikeMary Macro")
        self.Center()

        self.ratio_sash_main = 0.59
        self.ratio_sash_macro = 0.59

        self.Bind(mu.EVENT_MMM_UI, self.handler_event_mmm_ui)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGED, self.on_splitter_sash_pos_changed)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    @classmethod
    def scale_bitmap(cls, bitmap, width, height):
        image = bitmap.ConvertToImage()
        image = image.Scale(width, height, wx.IMAGE_QUALITY_HIGH)
        return wx.Bitmap(image)

    def create_bars(self):
        tb:wx.ToolBar = self.CreateToolBar(style=wx.TB_HORIZONTAL|wx.NO_BORDER|wx.TB_FLAT, id=mu.id_window[mu.k_toolbar])

        record = tb.AddTool(mu.ID[mu.k_toolbar][mu.k_record], 'Record', MMMacroFrame.scale_bitmap(wx.Bitmap('images/round_fiber_manual_record_black_48dp.png'), 24, 24), shortHelp='Record')
        tb.AddSeparator()
        play = tb.AddTool(mu.ID[mu.k_toolbar][mu.k_play], 'Play', MMMacroFrame.scale_bitmap(wx.Bitmap('images/baseline_play_arrow_black_48dp.png'), 24, 24), shortHelp='Play')
        pause = tb.AddTool(mu.ID[mu.k_toolbar][mu.k_pause], 'Pause', MMMacroFrame.scale_bitmap(wx.Bitmap('images/baseline_pause_black_48dp.png'), 24, 24), shortHelp='Pause')
        stop = tb.AddTool(mu.ID[mu.k_toolbar][mu.k_stop], 'Stop', MMMacroFrame.scale_bitmap(wx.Bitmap('images/baseline_stop_black_48dp.png'), 24, 24), shortHelp='Stop')
        tb.AddSeparator()
        text_loop = wx.StaticText(tb, label='Loop ')
        tb.AddControl(text_loop)
        self.loop = wx.CheckBox(tb, mu.ID[mu.k_toolbar][mu.k_loop])
        tb.AddControl(self.loop)
        tb.AddSeparator()
        save = tb.AddTool(mu.ID[mu.k_toolbar][mu.k_save], 'Save', MMMacroFrame.scale_bitmap(wx.Bitmap('images/baseline_save_black_48dp.png'), 24, 24), shortHelp='Save')
        tb.AddSeparator()
        text_velocity = wx.StaticText(tb, label='Velocity ')
        tb.AddControl(text_velocity)
        value_default_velocity = int((mu.maximum_slider_velocity - mu.minimum_slider_velocity) / (mu.maximum_velocity - mu.minimum_velocity) * (mu.velocity - mu.minimum_velocity) + mu.minimum_slider_velocity)
        self.velocity = wx.Slider(tb, mu.ID[mu.k_toolbar][mu.k_velocity], value_default_velocity, mu.minimum_slider_velocity, mu.maximum_slider_velocity)
        tb.AddControl(self.velocity)
        tb.Realize()

        self.Bind(wx.EVT_TOOL, self.on_macro_record, record)
        self.Bind(wx.EVT_TOOL, self.on_macro_play, play)
        self.Bind(wx.EVT_TOOL, self.on_macro_pause, pause)
        self.Bind(wx.EVT_TOOL, self.on_macro_stop, stop)
        self.Bind(wx.EVT_CHECKBOX, self.on_macro_loop, self.loop)
        self.Bind(wx.EVT_TOOL, self.on_macro_save, save)
        self.Bind(wx.EVT_SCROLL, self.on_macro_velocity, self.velocity)

        self.CreateStatusBar(id=mu.id_window[mu.k_statusbar])
        # sb = self.CreateStatusBar()
        # sb.SetStatusText(os.getcwd())

    def on_size(self, e):
        self.splitter_information.SetSashPosition(int(self.ratio_sash_main * self.GetSize().y))
        self.splitter_filetree.SetSashPosition(int(self.ratio_sash_macro * self.GetSize().x))
        e.Skip()

    def on_splitter_sash_pos_changed(self, e):
        self.ratio_sash_main = self.splitter_information.GetSashPosition() / self.GetSize().y
        self.ratio_sash_macro = self.splitter_filetree.GetSashPosition() / self.GetSize().x
        self.logger.info('Set SASH: [{0} {1}]'.format(self.ratio_sash_main, self.ratio_sash_macro))
        e.Skip()

    def on_dirctl_fileactivated(self, e):
        MMMacroFrame.make_thread(self.macroFSM.load, (e.Clone(),))
        # e.Skip()

    def handler_event_mmm_ui(self, e):
        if e.command == mu.k_clear_records:
            self.clear_records()
        elif e.command == mu.k_load_records:
            self.load_records()
        elif e.command == mu.k_refresh_records:
            self.refresh_records(e.arg_path)
        elif e.command == mu.k_append_record:
            self.append_record(e.arg_km)
        elif e.command == mu.k_insert_record:
            self.insert_record(e.arg_index, e.arg_km)
        elif e.command == mu.k_delete_record:
            self.delete_record(e.arg_index)
        elif e.command == mu.k_remove_record:
            self.remove_record(e.arg_km)
        else:
            pass

    def clear_records(self):
        self.records.KM.DeleteAllItems()

    def load_records(self):
        self.clear_records()
        for km in self.macroFSM.kms:
            self.append_record(km)

    def refresh_records(self, path):
        self.files.filetree.ReCreateTree()
        self.files.filetree.SelectPath(path)

    def append_record(self, km):
        self.records.KM.InsertItem(km.sequence, str(km.sequence + 1))
        self.records.KM.SetItem(km.sequence, 1, km.category.name)
        action = '' if km.action is None else 'Press' if km.action == True else 'Release'
        position = '' if km.position is None else str(km.position)
        value = '' if km.value is None else str(km.value)
        self.records.KM.SetItem(km.sequence, 2, action)
        self.records.KM.SetItem(km.sequence, 3, value)
        self.records.KM.SetItem(km.sequence, 4, position)
        self.records.KM.SetItem(km.sequence, 5, str(km.keys + km.buttons))
        self.records.KM.SetItem(km.sequence, 6, str(round(km.timing, 3)))

        endpoint = self.records.KM.GetItemCount() - 1
        self.records.KM.EnsureVisible(endpoint)

    def insert_record(self, index, km):
        pass

    def delete_record(self, index):
        pass

    def remove_record(self, km):
        pass

    def OnExit(self, e):
        self.Close(True)

    def OnClose(self, e):
        self.Destroy()

    @classmethod
    def make_thread(cls, function, args):
        thread = threading.Thread(target=function, args=args)
        thread.start()

    def on_macro_record(self, e):
        MMMacroFrame.make_thread(self.macroFSM.record, (e.Clone(),))

    def on_macro_play(self, e):
        MMMacroFrame.make_thread(self.macroFSM.play, (e.Clone(),))
        
    def on_macro_pause(self, e):
        MMMacroFrame.make_thread(self.macroFSM.pause, (e.Clone(),))

    def on_macro_stop(self, e):
        MMMacroFrame.make_thread(self.macroFSM.stop, (e.Clone(),))

    def on_macro_loop(self, e):
        MMMacroFrame.make_thread(self.macroFSM.loop, (e.Clone(),))

    def on_macro_save(self, e):
        MMMacroFrame.make_thread(self.macroFSM.save, (e.Clone(),))

    def on_macro_velocity(self, e):
        MMMacroFrame.make_thread(self.macroFSM.velocity, (e.Clone(),))

