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
class Log(object):
    def __init__(self, flog, regexs):
        self.entries = [line.strip() for line in open(flog)]
        self.regexs = regexs
        self.partitions = self._partition_logs()

    def _partition_logs(self):
        partitions = []
        filters = []
        for regex in self.regexs:
            if regex.filter and regex.filter not in filters:
                filters.append(regex.filter)
                # print "DEBUG: _partition_logs:\n\tfilters = %s" % filters
                # print "DEBUG: _partition_logs:\n\tre.id = %s;\n\tre.entity = %s;\n\tre.filter = %s\n" % (regex.id, regex.entity, regex.filter)
                regex.lpartition = self._grep_logs(regex.filter)
                partitions.append(regex.lpartition)
        return partitions

    def _grep_logs(self, lfilter):
        partition = []
        # clf = re.compile(lfilter)
        for line in self.entries:
            m = re.search(lfilter, line)
            if m:
                partition.append(line)
        # print "DEBUG: _grep_logs:\n\tfilter = %s;\n\tpartition = %s\n\n" % (lfilter, partition)
        return partition


# -----------------------------------------------------------------------------
class Run(object):
    def __init__(self, flog, regexs, dtpattern):
        self.res = regexs
        self.dtpattern = dtpattern
        self.log = Log(flog, self.res)
        self.session = Session(self)

    # def _make_re(self, res):
    #     re = ''
    #     for tag in res:
    #         re += run.re[tag]
    #     return re

    def get_res(self, entityid):
        res = []
        for regex in self.res:
            if regex.entityid == entityid:
                res.append(regex)
        return res

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

    def save_to_json(self, jfile):
        d = {}
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
        fout = open(jfile, 'w')
        json.dump(d, fout, indent=4)


# -----------------------------------------------------------------------------
class Re(object):
    def __init__(self, entityid, name, pattern, lfilter=None):
        self.id = name
        self.entityid = entityid
        self.pattern = pattern
        self.filter = lfilter
        self.compiled = None
        self.lpartition = None


# -----------------------------------------------------------------------------
class Session(object):
    def __init__(self, run):
        self.run = run
        self.states = []
        self.ntasks = None
        self.hosts = []
        self.failed = 0
        self.completed = 0
        self.res = self.run.get_res('session')
        self.id = self._get_id()
        self.jobs = self._get_jobs()
        self.tasks = self._get_tasks()
        self.blocks = self._get_blocks()

        # print len(self.blocks)
        # for block in self.blocks:
        #     print block.id
        #     print
        sys.exit(0)

        self.workers = self._get_workers()

    def _get_id(self):
        sid = None
        logs = self.run.log.entries
        for regex in self.res:
            if regex.id == 'id':
                if regex.lpartition:
                    logs = regex.lpartition
                for line in logs:
                    m = re.search(regex.pattern, line)
                    if m and not sid:
                        sid = m.group(1)
                        break
        return sid

    def _get_jobs(self):
        ids = []
        jobs = []
        res = self.run.get_res('job')
        logs = self.run.log.entries
        for regex in res:
            if regex.id == 'id':
                if regex.lpartition:
                    logs = regex.lpartition
                for line in logs:
                    m = re.search(regex.pattern, line)
                    if m and m.group(1) not in ids:
                        ids.append(m.group(1))
                        jobs.append(Job(m.group(1), res, self.run))
        for job in jobs:
            if job.host not in self.hosts:
                self.hosts.append(job.host)
        return jobs

    def _get_tasks(self):
        ids = []
        tasks = []
        res = self.run.get_res('task')
        logs = self.run.log.entries
        for regex in res:
            if regex.id == 'id':
                if regex.lpartition:
                    logs = regex.lpartition
                for line in logs:
                    m = re.search(regex.pattern, line)
                    if m and m.group(1) not in ids:
                        ids.append(m.group(1))
                        tasks.append(Task(m.group(1), res, self.run))
        for job in self.jobs:
            for task in tasks:
                if job.tid == task.id:
                    task.host = job.host
                    task.jid = job.id
        self.ntasks = len(tasks)
        return tasks

    def _get_blocks(self):
        pass

    def _get_workers(self):
        pass


# -----------------------------------------------------------------------------
class Job(object):
    '''A job is a task in the Swift lingo.

    States:
        JOB_INIT
        JOB_SITE_SELECT
        JOB_START
        JOB_TASK
        JOB_END
    '''

    def __init__(self, jid, res, run):
        self.run = run
        self.res = res
        self.id = jid
        self.logs = self.run.log.entries
        self.host = self._get_host()
        self.tid = self._get_task_id()

    def _get_host(self):
        logs = self.logs
        for regex in res:
            if regex.id == 'host':
                pattern = regex.pattern % self.id
                if regex.lpartition:
                    logs = regex.lpartition
                for line in logs:
                    m = re.search(pattern, line)
                    if m and m.group(1):
                        return m.group(1)
        return None

    def _get_task_id(self):
        logs = self.logs
        for regex in res:
            if regex.id == 'taskid':
                pattern = regex.pattern % self.id
                if regex.lpartition:
                    logs = regex.lpartition
                for line in logs:
                    m = re.search(pattern, line)
                    if m and m.group(1):
                        return m.group(1)
        return None


# -----------------------------------------------------------------------------
class Task(object):
    '''Coaster gets a job from Swift and calls it a task. Swift uses jobids
    while coaster taskids.

    States:
        | Name        | Code |
        |-------------|------|
        | unsubmitted | 0    |
        | submitting  | 8    |
        | submitted   | 1    |
        | active      | 2    |
        | suspended   | 3    |
        | resumed     | 4    |
        | failed      | 5    |
        | canceled    | 6    |
        | completed   | 7    |
        | stage_in    | 16   |
        | stage_out   | 17   |
        | unknown     | 9999 |
    '''
    def __init__(self, tid, res, run):
        self.run = run
        self.id = tid
        self.jid = None
        self.states = []
        self.host = None


# -----------------------------------------------------------------------------
class Block(object):
    '''A block is a pilot job in the Coaster lingo. Each worker belong to a
    block, i.e. a job scheduled on a resource.

    States:
        BLOCK_REQUESTED
        BLOCK_ACTIVE
        BLOCK_SHUTDOWN
        BLOCK_UTILIZATION
        BLOCK_DONE
    '''
    def __init__(self, run):
        self.run = run
        self.res = self.run.get_res('block')
        self.id = run.get_id(self.res)
        self.workers = None


# -----------------------------------------------------------------------------
class Worker(object):
    '''A worker is a pilot agent in the Coaster lingo. Each worker belong to a
    block, i.e. a job scheduled on a resource.

    States:
        WORKER_ACTIVE
        WORKER_LOST
        WORKER_SHUTDOWN
    '''
    def __init__(self, run):
        self.run = run
        self.res = self.run.get_res('job')
        self.id = run.get_id(self.res)
        self.tasks = None


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

    DTPATTERN = "%Y-%m-%d %H:%M:%S"
    DATE = "(\d+-\d+-\d+) "
    TIME = "(\d+:\d+:\d+),\d+[-,+]\d{4}[\w\s]+"

    # Check whether the parser is run with the required arguments.
    if len(sys.argv) <= 2:
        usage("insufficient arguments -- need swift log file and output file")

    if len(sys.argv) > 3:
        usage("too many arguments -- no more than 2")

    # Input swift log and json output files.
    flogs = sys.argv[1]
    fjson = sys.argv[2]

    # Define the identities of the Swift logs and their states.
    states = {'session': ['start'          , 'finish'],
              'job'    : ['init'           , 'site_select'   ,
                          'start'          , 'task'          , 'end'],
              'task'   : {'unsubmitted': 0 , 'submitting': 8 , 'submitted': 1,
                          'active'     : 2 , 'suspended' : 3 , 'resumed'  : 4,
                          'failed'     : 5 , 'canceled'  : 6 , 'completed': 7,
                          'stage_in'   : 16, 'stage_out' : 17, 'unknown'  : 9999},
              'block'  : ['requested'      , 'active'        , 'shutdown',
                          'utilization'    , 'done'],
              'worker' : ['active'         , 'lost'          , 'shutdown']}

    res = [Re('session',
              'id',
              'RUN_ID (run\d{3})'),
           Re('session',
              'start',
              DATE+TIME+'INFO  Loader JAVA'),
           Re('session',
              'finish',
              DATE+TIME+'INFO  Loader Swift finished with no errors'),
           Re('job',
              'id',
              'JOB_START jobid=([\w-]+) tr',
              'JOB_START jobid='),
           Re('job',
              'host',
              'JOB_START jobid=%s[\w\s/:.\-=\+\[\]]*host=([\w.]*)',
              'JOB_START jobid='),
           Re('job',
              'taskid',
              'JOB_TASK jobid=%s\s+taskid=urn:(R-\d+[-,x]\d+[-,x]\d+)',
              'JOB_TASK jobid='),
           Re('job',
              'init',
              DATE+TIME+'JOB_INIT jobid=%s',
              'JOB_INIT jobid='),
           Re('job',
              'siteselect',
              DATE+TIME+'JOB_SITE_SELECT jobid=%s',
              'JOB_SITE_SELECT jobid='),
           Re('job',
              'start',
              DATE+TIME+'JOB_START jobid=%s',
              'JOB_START jobid='),
           Re('job',
              'task',
              DATE+TIME+'JOB_TASK jobid=%s taskid=urn:%s',
              'JOB_TASK jobid='),
           Re('job',
              'end',
              DATE+TIME+'JOB_END jobid=%s',
              'JOB_END jobid='),
           Re('task',
              'id',
              'JOB_TASK jobid=[\w-]+\s+taskid=urn:(R-\d+[-,x]\d+[-,x]\d+)',
              'JOB_TASK jobid='),
           Re('task',
              'jobid',
              'JOB_TASK jobid=([\w-]+)\s+taskid=urn:%s',
              'JOB_TASK jobid='),
           Re('task',
              'blockid',
              'taskid=urn:%s\s+status=2\s+workerid=([\d\-]+):',
              'TASK_STATUS_CHANGE taskid=urn:R-\d+[-,x]\d+[-,x]\d+ status=2'),
           Re('task',
              'workerid',
              'taskid=urn:%s\s+status=2\s+workerid=%s:(\d+)',
              'TASK_STATUS_CHANGE taskid=urn:R-\d+[-,x]\d+[-,x]\d+ status=2'),
           Re('block',
              'id',
              'BLOCK_REQUESTED id=([\d\-]+),',
              'BLOCK_REQUESTED id='),
           Re('block',
              'cores',
              'BLOCK_REQUESTED id=%s, cores=(\d+),',
              'BLOCK_REQUESTED id='),
           Re('block',
              'coresworker',
              'BLOCK_REQUESTED id=%s[\w\s,=]+coresPerWorker=(\d+),',
              'BLOCK_REQUESTED id='),
           Re('block',
              'walltime',
              'BLOCK_REQUESTED id=%s[\w\s,=]+walltime=(\d+)',
              'BLOCK_REQUESTED id='),
           Re('block',
              'utilization',
              'BLOCK_UTILIZATION id=%s, u=([\d\.]+)',
              'BLOCK_UTILIZATION id='),
           Re('block',
              'requested',
              DATE+TIME+'BLOCK_REQUESTED id=%s',
              'BLOCK_REQUESTED id='),
           Re('block',
              'active',
              DATE+TIME+'BLOCK_ACTIVE id=%s',
              'BLOCK_ACTIVE id='),
           Re('block',
              'shutdown',
              DATE+TIME+'BLOCK_SHUTDOWN id=%s',
              'BLOCK_SHUTDOWN id='),
           Re('block',
              'done',
              DATE+TIME+'BLOCK_DONE id=%s',
              'BLOCK_DONE id='),
           Re('worker',
              'id',
              'WORKER_ACTIVE blockid=[\d\-]+ id=(\d+)',
              'WORKER_ACTIVE blockid='),
           Re('worker',
              'blockid',
              'WORKER_ACTIVE blockid=([\d\-]+)',
              'WORKER_ACTIVE blockid='),
           Re('worker',
              'node',
              'WORKER_ACTIVE blockid=%s id=%s node=([\w\d\-\.]+)',
              'WORKER_ACTIVE blockid='),
           Re('worker',
              'coresnode',
              'WORKER_ACTIVE blockid=%s id=%s[\w\d\s\-\.]+cores=(\d+)',
              'WORKER_ACTIVE blockid='),
           Re('worker',
              'active',
              DATE+TIME+'WORKER_ACTIVE blockid=%s id=%s',
              'WORKER_ACTIVE blockid='),
           Re('worker',
              'lost',
              DATE+TIME+'WORKER_LOST blockid=%s id=%s',
              'WORKER_LOST blockid='),
           Re('worker',
              'shutdown',
              DATE+TIME+'WORKER_SHUTDOWN blockid=%s id=%s',
              'WORKER_SHUTDOWN blockid=')]

    for name, code in states['task'].iteritems():
        status = "status=%s" % code
        r = Re('task',
               name,
               DATE+TIME+'TASK_STATUS_CHANGE taskid=urn:%s[\w\s\-]*'+status,
               'TASK_STATUS_CHANGE taskid=urn:R-\d+[-,x]\d+[-,x]\d+ '+status)
        res.append(r)

    # Run initialization instantiate a session with all its jobs, tasks, blocks,
    # and workers. Each object initialization sets the object's IDs.
    run = Run(flogs, res, DTPATTERN)

    sys.exit(0)

    # Add the desired timestamps to each object.
    run.add_state(run.session, 'start')
    run.add_state(run.session, 'finish')

    for task in run.session.tasks:
        run.add_state(task, 'new')
        for name, code in stask.iteritems():
            run.add_state(task, name)

    run.save_to_json(fjson)

