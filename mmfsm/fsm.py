# -*- coding: utf-8 -*-

import sys
import os
import json
import logging
import logging.config

from . import mc, mf
from mmlog import log


class MMFSM(object):
    mmcv_instance = None

    @classmethod
    def _getInstance(cls, fsmpath, *args, **kwargs):
        return cls.mmcv_instance

    @classmethod
    def instance(cls, fsmpath, *args, **kwargs):
        cls.mmcv_instance = cls(owner, fsmpath, *args, **kwargs)
        cls.instance = cls._getInstance
        return cls.mmcv_instance

    def __init__(self, fsmpath, *args, **kwargs):
        # constant
        self.mmiv_fsmpath = fsmpath
        self.mmiv_args = args
        self.mmiv_kwargs = kwargs
        self.mmiv_root_entry = ''

        # variable
        self.mmiv_table = {}
        self.mmiv_entry = ''
        self.mmiv_state = ''
        self.mmiv_event = ''
        self.mmiv_data = {}
        self.mmiv_status = []

        self.mmif_initialize_instance_value()
        self.mmif_set_logger()
        self.mmif_set_fsm_from_file(self.mmiv_fsmpath, self.mmiv_entry)

        self.mmif_run_once(**{
            mc.k_event: self.mmiv_event,
            mc.k_state: self.mmiv_state,
            mc.k_entry: self.mmiv_entry
        })

    def __repr__(self):
        return 'MMFSM("{0}", {1}, {2})'.format(self.mmiv_fsmpath, self.mmiv_args, self.mmiv_kwargs)

    def mmif_initialize_instance_value(self):
        self.mmiv_event = mc.k_base
        self.mmiv_state = mc.k_initializing
        self.mmiv_entry = self.mmif_convert_fsmpath_to_entry(self.mmiv_fsmpath)
        self.mmiv_root_entry = self.mmiv_entry

    def mmif_convert_fsmpath_to_entry(self, fsmpath, event=None, state=None, entry=None):
        path = fsmpath.replace('/', '.').replace('\\', '.')
        paths = path.split('.')
        assert len(paths) >= mc.fsm_min_length_fsmpath, \
            "The length of the path[{0}]" \
            " in (entry[{1}], state[{2}], event[{3}])" \
            " is less than {4}" \
            .format(path, entry, state, event, mc.fsm_min_length_fsmpath)
        return '.'.join(paths[0:len(paths) - 1])

    def mmif_convert_entry_to_fsmpath(self, nentry, rcode=None, event=None, state=None, entry=None):
        fsmpath = '{0}.json'.format(nentry.replace('.', '/'))
        assert os.path.isfile(fsmpath), \
            "The FSM file of next entry[{0}]" \
            " in (entry[{1}], state[{2}], event[{3}], {4}, rcode[{5}])" \
            " does not exist" \
            .format(nentry, entry, state, event, mc.k_result, rcode)
        return fsmpath

    def mmif_set_logger(self):
        self.mmiv_logger = log.get_logger('{0}.{1}'.format(mc.k_name_header, __name__), logging.DEBUG)

    def mmif_set_fsm_from_file(self, path, entry):
        if entry in self.mmiv_table:
            return

        self.mmiv_table[entry] = mf.read_file_json(path)
        Entry = self.mmiv_table[entry]

        assert mc.k_initializing in Entry, \
            "The entry[{0}] does not include state[{1}]" \
            .format(entry, mc.k_initializing)
        assert mc.k_finalizing in Entry, \
            "The entry[{0}] does not include state[{1}]" \
            .format(entry, mc.k_finalizing)

        for state in Entry:
            State = Entry[state]
            for event in State:
                Event = State[event]

                assert mc.k_action in Event, \
                    "The event[{0}] in (entry[{1}], state[{2}])" \
                    " does not include [{3}]" \
                    .format(event, entry, state, mc.k_action)
                Action = Event[mc.k_action]
                self.mmif_set_fsm_action(Action, event, state, entry)

                assert mc.k_result in Event, \
                    "The event[{0}] in (entry[{1}], state[{2}])" \
                    " does not include [{3}]" \
                    .format(event, entry, state, mc.k_result)
                Result = Event[mc.k_result]
                self.mmif_verify_fsm_result(Result, event, state, entry)

    def mmif_set_fsm_action(self, Action, event, state, entry):
        assert mc.k_path in Action, \
            "The action in (entry[{0}], state[{1}], event[{2}])" \
            " does not include [{3}]" \
            .format(entry, state, event, mc.k_path)
        assert mc.k_args in Action, \
            "The action in (entry[{0}], state[{1}], event[{2}])" \
            " does not include [{3}]" \
            .format(entry, state, event, mc.k_args)
        assert mc.k_kwargs in Action, \
            "The action in (entry[{0}], state[{1}], event[{2}])" \
            " does not include [{3}]" \
            .format(entry, state, event, mc.k_kwargs)
        path = Action[mc.k_path]
        paths = path.split('.')
        assert len(paths) >= mc.fsm_min_length_action, \
            "The length of the path[{0}]" \
            " in (entry[{1}], state[{2}], event[{3}], {4})" \
            " is less than {5}" \
            .format(path, entry, state, event, mc.k_action, mc.fsm_min_length_action)
        filepath = '.'.join(paths[0:len(paths) - 1])
        filename = paths[-2]
        function = paths[-1]
        mod = __import__(filepath, fromlist=[filename])
        Action[mc.k_method] = getattr(mod, function)

    def mmif_verify_fsm_result(self, Result, event, state, entry):
        for rcode in Result:
            Rcode = Result[rcode]
            assert mc.k_entry in Rcode, \
                "The result code[{0}] in (entry[{1}], state[{2}], event[{3}], result)" \
                " does not include {4}" \
                .format(rcode, entry, state, event, mc.k_entry)
            assert mc.k_event in Rcode, \
                "The result code[{0}] in (entry[{1}], state[{2}], event[{3}], result)" \
                " does not include {4}" \
                .format(rcode, entry, state, event, mc.k_event)
            assert mc.k_state in Rcode, \
                "The result code[{0}] in (entry[{1}], state[{2}], event[{3}], result)" \
                " does not include {4}" \
                .format(rcode, entry, state, event, mc.k_state)
            assert mc.k_args in Rcode, \
                "The result code[{0}] in (entry[{1}], state[{2}], event[{3}], result)" \
                " does not include {4}" \
                .format(rcode, entry, state, event, mc.k_args)
            assert mc.k_kwargs in Rcode, \
                "The result code[{0}] in (entry[{1}], state[{2}], event[{3}], result)" \
                " does not include {4}" \
                .format(rcode, entry, state, event, mc.k_kwargs)
            nevent = Rcode[mc.k_event]
            nstate = Rcode[mc.k_state]
            nentry = Rcode[mc.k_entry]
            if nentry is not None:
                if nentry not in self.mmiv_table:
                    fsmpath = self.mmif_convert_entry_to_fsmpath(nentry, rcode, event, state, entry)
                    self.mmif_set_fsm_from_file(fsmpath, nentry)
            else:
                nentry = entry
            if nstate is not None:
                assert nstate in self.mmiv_table[nentry], \
                    "The entry[{0}] does not include state[{1}]" \
                    .format(nentry, nstate)
            else:
                nstate = state
            if nevent is not None:
                assert nevent in self.mmiv_table[nentry][nstate], \
                    "The state[{0}] in (entry[{1}]) does not include event[{2}]" \
                    .format(nstate, nentry, nevent)

    def mmif_run(self, *args, **kwargs):
        event = kwargs[mc.k_event]
        state = kwargs[mc.k_state]
        entry = kwargs[mc.k_entry]

        Action = self.mmiv_table[entry][state][event][mc.k_action]
        function = Action[mc.k_method]
        self.mmiv_status.append({})
        self.mmiv_status[-1][mc.k_entry] = entry
        self.mmiv_status[-1][mc.k_state] = state
        self.mmiv_status[-1][mc.k_event] = event
        self.mmiv_status[-1][mc.k_method_input] = {mc.k_args: args, mc.k_kwargs: kwargs}
        self.mmiv_status[-1][mc.k_fsm_action] = {mc.k_args: Action[mc.k_args], mc.k_kwargs: Action[mc.k_kwargs]}
        result = function(self, *args, **kwargs)
        rcode = result[mc.k_rcode]
        Result = self.mmiv_table[entry][state][event][mc.k_result]
        self.mmiv_status[-1][mc.k_rcode] = rcode
        self.mmiv_status[-1][mc.k_method_output] = {mc.k_args: result[mc.k_args], mc.k_kwargs: result[mc.k_kwargs]}
        self.mmiv_status[-1][mc.k_fsm_result] = {mc.k_args: Result[rcode][mc.k_args], mc.k_kwargs: Result[rcode][mc.k_kwargs]}

        if len(self.mmiv_status) > mc.count_status:
            self.mmiv_status = self.mmiv_status[len(self.mmiv_status) - mc.count_status : len(self.mmiv_status)]

    def mmif_get_next_step(self, rcode, event, state, entry):
        Result = self.mmiv_table[entry][state][event][mc.k_result]
        nevent = Result[rcode][mc.k_event]
        nstate = Result[rcode][mc.k_state] if Result[rcode][mc.k_state] is not None else state
        nentry = Result[rcode][mc.k_entry] if Result[rcode][mc.k_entry] is not None else entry
        return nevent, nstate, nentry

    def mmif_run_once(self, *args, **kwargs):
        check_event = mc.k_event in kwargs and kwargs[mc.k_event]
        check_state = mc.k_state in kwargs and kwargs[mc.k_state]
        check_entry = mc.k_entry in kwargs and kwargs[mc.k_entry]

        if not check_event:
            self.mmiv_logger.error('Event is None')
            return
        if check_entry and not check_state:
            self.mmiv_logger.error('Entry is not None, and State is None')
            return
        event = kwargs[mc.k_event]
        state = kwargs[mc.k_state] if check_state else self.mmiv_state
        entry = kwargs[mc.k_entry] if check_entry else self.mmiv_entry
        self.mmiv_logger.info('{0} :: [{1} : {2} : {3}]'.format('FSM', entry, state, event))

        if event in self.mmiv_table[entry][state]:
            kwargs = dict(kwargs, **{
                    mc.k_event: event,
                    mc.k_state: state,
                    mc.k_entry: entry
            })
            self.mmif_run(*args, **kwargs)

            rcode = self.mmiv_status[-1][mc.k_rcode]
            self.mmif_set_event_state_entry(*self.mmif_get_next_step(rcode, event, state, entry))
            if entry == self.mmiv_root_entry and state == mc.k_finalizing:
                self.mmiv_logger.info('{0} :: [{1}] -> {2}'.format('FSM', rcode, 'Finalized'))
            else:
                self.mmiv_logger.info('{0} :: [{1}] -> [{2} : {3} : {4}]'.format(
                        'FSM', rcode, self.mmiv_entry, self.mmiv_state, self.mmiv_event
                    )
            )
        else:
            self.mmiv_logger.info('{0} [{1} : {2}] does not include {3}'.format(
                    'FSM', entry, state, event
                )
            )

    def mmif_set_event_state_entry(self, event, state, entry):
        self.mmiv_event = event
        self.mmiv_state = state
        self.mmiv_entry = entry

    def mmif_run_consecutively(self, *args, **kwargs):
        while self.mmiv_event is not None:
            self.mmif_run_once(**{
                mc.k_event: self.mmiv_event,
                mc.k_state: self.mmiv_state,
                mc.k_entry: self.mmiv_entry
            })

    def mmif_run_nothing(self):
        pass

    def mmif_get_status(self):
        return self.mmiv_status
