#!/usr/bin/env python

import re
import sys
import json
import time

'''Reads Swift+Coaster log file and returns a json file with timestamps of each
task's state and a summary of the run properties
'''

__author__ = "Matteo Turilli"
__copyright__ = "Copyright 2015, The AIMES Project"
__license__ = "MIT"


# -----------------------------------------------------------------------------
class Run(object):
    def __init__(self, conf):
        self.id = time.clock()
        self.conf = conf
        self.logs = self._partition_logs(conf['file_logs'])
        self.dtpattern = conf['date_time_pattern']
        self.session = Session(self)

    def _partition_logs(self, lfile):
        plogs = {}
        logs = [line.strip() for line in open(lfile)]
        for tag in self.conf['re']:
            plogs[tag] = self._grep_logs(logs, self.conf['re'][tag])
        return plogs

    def _grep_logs(self, lfile, regex):
        logs = []
        if "%s" in regex:
            regex = regex % ".*"
        lfilter = re.compile(regex)
        for line in lfile:
            m = re.search(lfilter, line)
            if m:
                logs.append(line)
        return logs

    def _make_re(self, res):
        re = ''
        for tag in res:
            re += run.conf['re'][tag]
        return re

    def add_state(self, obj, name):
        regex = self._make_re(['date', 'time', name])
        if type(obj) == Task:
            regex = regex % obj.id
        state = State(name, regex, self)
        if state.name == 'failed' and state.tstamp.stamp:
            self.session.failed += 1
        elif state.name == 'completed' and state.tstamp.stamp:
            self.session.completed += 1
        obj.states.append(state)

    def save_to_json(self):
        d = {}
        d["Run"] = {"ID": self.id}
        d["Session"] = {"ID": self.session.id,
                        "hosts": self.session.hosts,
                        "ntasks": self.session.ntasks,
                        "failed": self.session.failed,
                        "completed": self.session.completed}
        d["Tasks"] = {}
        for state in self.session.states:
            d["Session"][state.name] = state.tstamp.epoch
        for task in self.session.tasks:
            d["Tasks"][task.id] = {}
            d["Tasks"][task.id]["host"] = task.host
            for state in task.states:
                d["Tasks"][task.id][state.name] = state.tstamp.epoch
        fout = open(conf['file_json'], 'w')
        json.dump(d, fout, indent=4)


# -----------------------------------------------------------------------------
class Session(object):
    def __init__(self, run):
        self.run = run
        self.states = []
        self.ntasks = None
        self.hosts = []
        self.failed = 0
        self.completed = 0
        self.id = self._get_id('runid')
        self.jobs = self._get_jobs('jobid')
        self.tasks = self._get_tasks('taskid')

    def _get_id(self, retag):
        runid = None
        regex = re.compile(self.run.conf['re'][retag])
        for line in self.run.logs[retag]:
            m = re.search(regex, line)
            if m and not runid:
                runid = m.group(1)
                break
        return runid

    def _get_jobs(self, retag):
        ids = []
        jobs = []
        jobid = re.compile(self.run.conf['re'][retag])
        for line in self.run.logs[retag]:
            m = re.search(jobid, line)
            if m and m.group(1) not in ids:
                ids.append(m.group(1))
                jobs.append(Job(m.group(1), self.run))
        for job in jobs:
            if job.host not in self.hosts:
                self.hosts.append(job.host)
        return jobs

    def _get_tasks(self, retag):
        ids = []
        tasks = []
        taskid = re.compile(self.run.conf['re'][retag])
        for line in self.run.logs[retag]:
            m = re.search(taskid, line)
            if m and m.group(1) not in ids:
                ids.append(m.group(1))
                tasks.append(Task(m.group(1), self.run, self.jobs))
        self.ntasks = len(tasks)
        return tasks


# -----------------------------------------------------------------------------
class Job(object):
    def __init__(self, jid, run):
        self.run = run
        self.id = jid
        self.host = self._get_host('jobidhost')
        self.tids = self._get_task_ids('jobidtaskid')

    def _get_host(self, retag):
        regex = self.run.conf['re'][retag] % self.id
        logs = self.run._grep_logs(self.run.logs['jobid'], regex)
        host = re.compile(regex)
        for line in logs:
            m = re.search(host, line)
            if m and m.group(1):
                return m.group(1)
        return None

    def _get_task_ids(self, retag):
        regex = self.run.conf['re'][retag] % self.id
        logs = self.run._grep_logs(self.run.logs['jobtaskid'], regex)
        jobtaskid = re.compile(regex)
        tids = []
        for line in logs:
            m = re.search(jobtaskid, line)
            if m and m.group(1) not in tids:
                tids.append(m.group(1))
        return tids


# -----------------------------------------------------------------------------
class Task(object):
    def __init__(self, tid, run, jobs):
        self.run = run
        self.id = tid
        self.states = []
        self.host = self._get_task_host(jobs)

    def _get_task_host(self, jobs):
        for job in jobs:
            if self.id in job.tids:
                return job.host


# -----------------------------------------------------------------------------
class State(object):
    def __init__(self, name, regex, run):
        self.name = name
        self.tstamp = TimeStamp(regex, self, run)


# -----------------------------------------------------------------------------
class TimeStamp(object):
    def __init__(self, regex, state, run):
        self.regex = re.compile(regex)
        self.state = state
        self.run = run
        self.epoch = None
        self.stamp = self._get_stamp()

    def _get_stamp(self):
        stamp = None
        for line in self.run.logs[self.state.name]:
            m = re.search(self.regex, line)
            if m:
                stamp = "%s %s" % (m.group(1), m.group(2))
                self.epoch = int(time.mktime(time.strptime(stamp,
                                 self.run.dtpattern)))
                break

        return stamp


# -----------------------------------------------------------------------------
def usage(msg=None, noexit=False):

    if msg:
        print "\nError: %s" % msg

    print """
    usage   : %s <swift_log_file>.log <swift_durations_output>.json
    """ % (sys.argv[0])

    if msg:
        sys.exit(1)

    if not noexit:
        sys.exit(0)


# ------------------------------------------------------------------------------
if __name__ == "__main__":

    if len(sys.argv) <= 2:
        usage("insufficient arguments -- need swift log file and output file")

    if len(sys.argv) > 3:
        usage("too many arguments -- no more than 2")

    conf = {}
    conf['re'] = {}
    conf['file_logs'] = sys.argv[1]
    conf['file_json'] = sys.argv[2]
    conf['tcodes'] = {'unsubmitted': 0, 'submitting': 8, 'submitted': 1,
                      'active': 2, 'suspended': 3, 'resumed': 4, 'failed': 5,
                      'canceled': 6, 'completed': 7, 'stage_in': 16,
                      'stage_out': 17, 'unknown': 9999}

    conf['date_time_pattern'] = "%Y-%m-%d %H:%M:%S"

    conf['re']['date'] = "(\d+-\d+-\d+) "
    conf['re']['time'] = "(\d+:\d+:\d+),\d+[-,+]\d+.*"
    conf['re']['start'] = "INFO  Loader JAVA"
    conf['re']['finish'] = "INFO  Loader Swift finished with no errors"
    conf['re']['runid'] = "RUN_ID (run\d{3})"
    conf['re']['taskid'] = "taskid=urn:(R-\d+[-,x]\d+[-,x]\d+)"
    conf['re']['jobid'] = "JOB_START jobid=([\d\w-]+) tr"
    conf['re']['jobidhost'] = "JOB_START jobid=%s.*host=(.*)"
    conf['re']['jobtaskid'] = "JOB_TASK jobid=([\d\w-]+).*"+conf['re']['taskid']
    conf['re']['jobidtaskid'] = "JOB_TASK jobid=%s.*"+conf['re']['taskid']
    conf['re']['new'] = "JOB_TASK jobid=[\d\w-]+ taskid=urn:%s"

    for name, code in conf['tcodes'].iteritems():
        status = "status=%s" % code
        conf['re'][name] = "TASK_STATUS_CHANGE taskid=urn:%s.*"+status

    run = Run(conf)
    run.add_state(run.session, 'start')
    run.add_state(run.session, 'finish')

    for task in run.session.tasks:
        run.add_state(task, 'new')
        for name, code in conf['tcodes'].iteritems():
            run.add_state(task, name)

    run.save_to_json()
