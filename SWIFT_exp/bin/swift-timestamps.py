#!/usr/bin/env python

import re
import sys
import json
import time

'''Read Swift log file and return a json file with its states and their
timings'''


class Run(object):
    def __init__(self, conf):
        self.conf = conf
        self.logs = self._partition_logs(conf['file_logs'])
        self.dtpattern = conf['date_time_pattern']
        self.states = []
        self.ntasks = None
        self.hosts = []
        self.failed = 0
        self.completed = 0
        self.id = self._get_id('runid')
        self.jobs = self._get_jobs('jobid')
        self.tasks = self._get_tasks('taskid')

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

    def _get_id(self,retag):
        runid = None
        regex = re.compile(self.conf['re'][retag])
        for line in self.logs[retag]:
            m = re.search(regex, line)
            if m and not runid:
                runid = m.group(1)
                break
        return runid

    def _get_jobs(self, retag):
        ids = []
        jobs = []
        jobid = re.compile(self.conf['re'][retag])
        for line in self.logs[retag]:
            m = re.search(jobid, line)
            if m and m.group(1) not in ids:
                ids.append(m.group(1))
                jobs.append(Job(m.group(1), self))
        for job in jobs:
            if job.host not in self.hosts:
                self.hosts.append(job.host)
        return jobs

    def _get_tasks(self, retag):
        ids = []
        tasks = []
        taskid = re.compile(self.conf['re'][retag])
        for line in self.logs[retag]:
            m = re.search(taskid, line)
            if m and m.group(1) not in ids:
                ids.append(m.group(1))
                tasks.append(Task(m.group(1), self, self.jobs))
        self.ntasks = len(tasks)
        return tasks

    def _make_re(self, retags):
        re = ''
        for tag in retags:
            re += run.conf['re'][tag]+'.*'
        return re

    def add_state(self, name):
        regex = self._make_re(['date', 'time', name])
        state = State(name, regex, self)
        self.states.append(state)

    def save_to_json(self):
        d = {}
        d["Run"] = {"ID": self.id, "hosts": self.hosts, "ntasks": self.ntasks,
                    "failed": self.failed, "completed": self.completed}
        d["Tasks"] = {}
        for state in self.states:
            d["Run"][state.name] = state.tstamp.epoch
        for task in self.tasks:
            d["Tasks"][task.id] = {}
            d["Tasks"][task.id]["host"] = task.host
            for state in task.states:
                d["Tasks"][task.id][state.name] = state.tstamp.epoch
        fout = open(conf['file_json'], 'w')
        json.dump(d, fout, indent=4)


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

    def _make_re(self, res):
        re = ''
        for tag in res:
            re += run.conf['re'][tag]
        return re

    def add_state(self, name, taskid):
        regex = self._make_re(['date', 'time', name])
        regex = regex % taskid
        # print "Task %s; state %s; regex %s: Adding..." % (self.id, name, regex)
        state = State(name, regex, self.run)
        if state.name == 'failed' and state.tstamp.stamp:
            self.run.failed += 1
        elif state.name == 'completed' and state.tstamp.stamp:
            self.run.completed += 1
        # print "Task %s; state %s: Added." % (self.id, name)
        self.states.append(state)


class State(object):
    def __init__(self, name, regex, run):
        self.name = name
        self.tstamp = TimeStamp(regex, self, run)


class TimeStamp(object):
    def __init__(self, regex, state, run):
        self.regex = re.compile(regex)
        self.state = state
        self.run = run
        self.epoch = None
        self.stamp = self._get_stamp()
        # print "DEBUG: TimeStamp: state = %s; stamp = %s" % (self.state.name,
        #                                                     self.stamp)

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
    """
    status codes:
    COASTER_STATUS_UNSUBMITTED = 0,
    COASTER_STATUS_SUBMITTING = 8,
    COASTER_STATUS_SUBMITTED = 1,
    COASTER_STATUS_ACTIVE = 2,
    COASTER_STATUS_SUSPENDED = 3,
    COASTER_STATUS_RESUMED = 4,
    COASTER_STATUS_FAILED = 5,
    COASTER_STATUS_CANCELED = 6,
    COASTER_STATUS_COMPLETED = 7,
    COASTER_STATUS_STAGE_IN = 16,
    COASTER_STATUS_STAGE_OUT = 17,
    COASTER_STATUS_UNKNOWN = 9999
    """

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
    run.add_state('start')
    run.add_state('finish')

    for task in run.tasks:
        task.add_state('new', task.id)
        for name, code in conf['tcodes'].iteritems():
            task.add_state(name, task.id)

    run.save_to_json()
