#!/usr/bin/env python

import re
import sys
import json
import time

'''Read Swift log file and return a json file with its states and their
timings'''


# -----------------------------------------------------------------------------
class Run(object):
    def __init__(self, **kwargs):
        self.logs = [line.strip() for line in open(kwargs['flog'])]
        self.dtpattern = kwargs['dtpattern']
        self.id = None
        self.tasks = []
        self.states = []

    def set_id(self, **kwargs):
        runid = None
        regex = re.compile(kwargs['regex'])
        flogs = self._filter_logs(kwargs['patterns'])
        for line in flogs:
            if runid:
                break
            m = re.match(regex, line)
            if m:
                runid = m.group(1)
        self.id = runid

    def add_state(self, **kwargs):
        regex = re.compile(kwargs['regex'])
        flogs = self._filter_logs(kwargs['patterns'])
        self.states.append(State(kwargs['name'], regex, flogs, self))

    def add_tasks(self, **kwargs):
        ids = []
        tasks = []
        taskid = re.compile(kwargs['regex'])
        flogs = self._filter_logs(kwargs['patterns'])
        for line in flogs:
            m = re.match(taskid, line)
            if m and m.group(1) not in ids:
                ids.append(m.group(1))
                tasks.append(Task(m.group(1), self))
        self.tasks = tasks
        return tasks

    def save_to_json(self, fout):
        d = {}
        d["Run"] = {"ID": self.id}
        d["Tasks"] = {}
        for state in self.states:
            d["Run"][state.name] = state.tstamp.epoch
        for task in self.tasks:
            d["Tasks"][task.id] = {}
            for state in task.states:
                d["Tasks"][task.id][state.name] = state.tstamp.epoch
        f = open(fout, 'w')
        json.dump(d, f, indent=4)

    def _filter_logs(self, patterns):
        flogs = []
        for line in self.logs:
            if all(pattern in line for pattern in patterns):
                flogs.append(line)
        return flogs


# -----------------------------------------------------------------------------
class Task(object):
    def __init__(self, tid, run):
        self.run = run
        self.id = tid
        self.states = []

    def _make_re(self, res):
        re = ''
        for tag in res:
            re += run.conf['re'][tag]+'.*'
        return re

    def add_state(self, **kwargs):
        regex = re.compile(kwargs['regex'])
        flogs = self.run._filter_logs(kwargs['patterns'])
        self.states.append(State(kwargs['name'], regex, flogs, self.run))


# -----------------------------------------------------------------------------
class State(object):
    def __init__(self, name, regex, logs, run):
        self.name = name
        self.tstamp = TimeStamp(regex, logs, self, run)


# -----------------------------------------------------------------------------
class TimeStamp(object):
    def __init__(self, regex, logs, state, run):
        self.state = state
        self.run = run
        self.stamp = self._get_stamp(regex, logs)
        self.epoch = int(time.mktime(time.strptime(self.stamp,
                         self.run.dtpattern)))

    def _get_stamp(self, regex, logs):
        stamp = None
        for line in logs:
            if stamp:
                break
            m = re.match(regex, line)
            if m:
                stamp = "%s %s" % (m.group(1), m.group(2))
        return stamp


# -----------------------------------------------------------------------------
def usage(msg=None, noexit=False):

    if msg:
        print "\nError: %s" % msg

    print """
    usage   : %s <swift_log_file>.json <swift_durations>.json
    """ % (sys.argv[0])

    if msg:
        sys.exit(1)

    if not noexit:
        sys.exit(0)


# ------------------------------------------------------------------------------
if __name__ == "__main__":

    if len(sys.argv) <= 2:
        usage("insufficient arguments -- need Swift log file and output file")

    if len(sys.argv) > 3:
        usage("too many arguments -- no more than 2")

    d = '(\d+-\d+-\d+)'
    t = '(\d:\d+:\d+),\d+[-,+]\d+'
    tcodes = {'Submitting': 8, 'Submitted': 1, 'Active': 2, 'Completed': 7}

    run = Run(flog=sys.argv[1], dtpattern="%Y-%m-%d %H:%M:%S")

    run.set_id(patterns=['RUN_ID'], regex=".*%s.*(run\d{3})" % 'RUN_ID')

    run.add_state(name='Start', patterns=['JAVA'],
                  regex="%s.*%s.*%s" % (d, t, 'JAVA'))

    run.add_state(name='Finish', patterns=['Swift finished with no errors'],
                  regex="%s.*%s.*%s" % (d, t,
                                        'Swift finished with no errors'))

    tasks = run.add_tasks(patterns=['JOB_TASK', 'taskid=urn:'],
                          regex='.*%s.*%s(R-\d+[-,x]\d+[-,x]\d+).*' % ('JOB_TASK', 'taskid=urn:'))

    for task in tasks:

        task.add_state(name='New', patterns=['JOB_TASK', 'taskid=urn:', task.id],
                       regex="%s.*%s.*%s.*%s%s" % (d, t, 'JOB_TASK', 'taskid=urn:', task.id))

        for sid, code in tcodes.iteritems():
            task.add_state(name=sid, patterns=['TASK_STATUS_CHANGE', 'taskid=urn:', task.id, "status=%s" % code],
                           regex="%s.*%s.*%s %s%s status=%s" % (d, t, 'TASK_STATUS_CHANGE', 'taskid=urn:', task.id, code))

    run.save_to_json(sys.argv[2])
