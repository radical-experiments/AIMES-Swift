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
    def __init__(self, flog, res, dtpattern):
        self.res = res
        self.dtpattern = dtpattern
        self.log = Log(flog, self)
        self.session = Session(self)

    # worker, 'worker', state, code, (worker.bid, worker.id)
    def add_state(self, entity, ename, sname, code, args=None):
        logs = self.log.entries
        pattern = self.res[ename][sname]['pattern']
        if args:
            pattern = pattern % args
        if not self.res[ename][sname]['cpattern']:
            cpattern = re.compile(pattern)
        flogs = self.res[ename][sname]['flogs']
        if flogs:
            logs = flogs
        state = State(sname, ename, cpattern, logs, self)
        if state.id == 'failed' and state.tstamp.stamp:
            self.session.failed += 1
        elif state.id == 'completed' and state.tstamp.stamp:
            self.session.completed += 1
        entity.states.append(state)

    def save_to_json(self, jfile):
        d = {}
        d['Session'] = {'ID': self.session.id,
                        'hosts': self.session.hosts,
                        'ntasks': self.session.ntasks,
                        'failed': self.session.failed,
                        'completed': self.session.completed}
        d['Tasks'] = {}
        for state in self.session.states:
            d['Session'][state.id] = state.tstamp.epoch
        for task in self.session.tasks:
            d['Tasks'][task.id] = {}
            d['Tasks'][task.id]['host'] = task.host
            for state in task.states:
                d['Tasks'][task.id][state.id] = state.tstamp.epoch
        fout = open(jfile, 'w')
        json.dump(d, fout, indent=4)

    def save_to_json_full(self, jfile):
        d = {}
        d['Session'] = {'ID': self.session.id,
                        'hosts': self.session.hosts,
                        'ntasks': self.session.ntasks,
                        'failed': self.session.failed,
                        'completed': self.session.completed}
        for state in self.session.states:
            d['Session'][state.id] = state.tstamp.epoch
        d['Jobs'] = {}
        for job in self.session.jobs:
            d['Jobs'][job.id] = {}
            d['Jobs'][job.id]['host'] = job.host
            d['Jobs'][job.id]['task_id'] = job.tid
            for state in job.states:
                d['Jobs'][job.id][state.id] = state.tstamp.epoch
        d['Tasks'] = {}
        for task in self.session.tasks:
            d['Tasks'][task.id] = {}
            d['Tasks'][task.id]['host'] = task.host
            for state in task.states:
                d['Tasks'][task.id][state.id] = state.tstamp.epoch
        d['Blocks'] = {}
        for block in self.session.blocks:
            d['Blocks'][block.id] = {}
            d['Blocks'][block.id]['host'] = block.host
            d['Blocks'][block.id]['nodes'] = block.nodes
            d['Blocks'][block.id]['workers'] = block.workers
            d['Blocks'][block.id]['cores'] = block.cores
            d['Blocks'][block.id]['cores_per_worker'] = block.coresworker
            d['Blocks'][block.id]['walltime'] = block.walltime
            d['Blocks'][block.id]['utilization'] = block.utilization
            for state in block.states:
                d['Blocks'][block.id][state.id] = state.tstamp.epoch
        d['Workers'] = {}
        for worker in self.session.workers:
            d['Workers'][worker.id] = {}
            d['Workers'][worker.id]['tasks'] = worker.tasks
            d['Workers'][worker.id]['block'] = worker.bid
            d['Workers'][worker.id]['node'] = worker.node
            d['Workers'][worker.id]['cores_node'] = worker.coresnode
            for state in worker.states:
                d['Workers'][worker.id][state.id] = state.tstamp.epoch
        fout = open(jfile, 'w')
        json.dump(d, fout, indent=4)


# -----------------------------------------------------------------------------
class Log(object):
    def __init__(self, flog, run):
        self.entries = [line.strip() for line in open(flog)]
        self.run = run
        self._partition_logs()

    def _partition_logs(self):
        filters = []
        for entity, value in self.run.res.iteritems():
            for tag, patterns in value.iteritems():
                if patterns['lfilter'] and patterns['lfilter'] not in filters:
                    filters.append(patterns['lfilter'])
                    # print "DEBUG: _partition_logs:\n\tfilters = %s" % filters
                    # print "DEBUG: _partition_logs:\n\tre.id = %s;\n\tre.entity = %s;\n\tre.filter = %s\n" % (tag, entity, patterns['lfilter'])
                    partition = self._grep_logs(patterns['lfilter'])
                    patterns['flogs'] = partition

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
class Session(object):
    def __init__(self, run):
        self.run = run
        self.states = []
        self.hosts = []
        self.failed = 0
        self.completed = 0
        self.id = self._get_entity('session')
        self.jobs = self._get_entity('job')
        self.tasks = self._get_entity('task')
        self.blocks = self._get_entity('block')
        self.workers = self._get_entity('worker')
        self.ntasks = len(self.tasks)
        self._set_tasks_host_jid()

    def _get_entity(self, entity):
        ids = []
        entities = []
        logs = self.run.log.entries
        pattern = self.run.res[entity]['id']['pattern']
        flogs = self.run.res[entity]['id']['flogs']
        if flogs:
            logs = flogs
        for line in logs:
            m = re.search(pattern, line)
            if m and m.group(1) not in ids:
                eid = m.group(1)
                if entity == 'session':
                    return eid
                elif entity == 'job':
                    job = Job(eid, self.run)
                    if job.host not in self.hosts:
                        self.hosts.append(job.host)
                    entities.append(job)
                elif entity == 'task':
                    entities.append(Task(eid, self.run))
                elif entity == 'block':
                    entities.append(Block(eid, self.run))
                elif entity == 'worker':
                    entities.append(Worker(eid, self.run))
                else:
                    print "ERROR: Uknown entity"
                    sys.exit(1)
                ids.append(eid)
        return entities

    def _set_tasks_host_jid(self):
        for job in self.jobs:
            for task in self.tasks:
                if job.tid == task.id:
                    task.host = job.host
                    task.jid = job.id


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

    def __init__(self, jid, run):
        self.run = run
        self.id = jid
        self.states = []
        self.host = self._get_host()
        self.tid = self._get_task_id()

    def _get_host(self):
        logs = self.run.log.entries
        pattern = self.run.res['job']['host']['pattern'] % self.id
        flogs = self.run.res['job']['host']['flogs']
        if flogs:
            logs = flogs
        for line in logs:
            m = re.search(pattern, line)
            if m and m.group(1):
                return m.group(1)
        return None

    def _get_task_id(self):
        logs = self.run.log.entries
        pattern = self.run.res['job']['taskid']['pattern'] % self.id
        flogs = self.run.res['job']['host']['flogs']
        if flogs:
            logs = flogs
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
    def __init__(self, tid, run):
        self.run = run
        self.id = tid
        self.jid = None
        self.host = None
        self.states = []


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
    def __init__(self, bid, run):
        self.id = bid
        self.run = run
        self.host = None
        self.states = []
        self.nodes = []
        self.workers = []
        self.cores = self._get_property('cores')
        self.coresworker = self._get_property('coresworker')
        self.walltime = self._get_property('walltime')
        self.utilization = self._get_property('utilization')

    def _get_property(self, tag):
        logs = self.run.log.entries
        pattern = self.run.res['block'][tag]['pattern'] % self.id
        flogs = self.run.res['block'][tag]['flogs']
        if flogs:
            logs = flogs
        for line in logs:
            m = re.search(pattern, line)
            if m and m.group(1):
                return m.group(1)
        return None


# -----------------------------------------------------------------------------
class Worker(object):
    '''A worker is a pilot agent in the Coaster lingo. Each worker belong to a
    block, i.e. a job scheduled on a resource.

    States:
        WORKER_ACTIVE
        WORKER_LOST
        WORKER_SHUTDOWN
    '''
    def __init__(self, wid, run):
        self.id = wid
        self.run = run
        self.tasks = None
        self.states = []
        self.bid = self._get_property('blockid')
        self.node = self._get_property('node', (self.bid, self.id))
        self.coresnode = self._get_property('coresnode', (self.bid, self.id))

    def _get_property(self, tag, args=None):
        logs = self.run.log.entries
        pattern = self.run.res['worker'][tag]['pattern']
        if args:
            pattern = pattern % args
        flogs = self.run.res['worker'][tag]['flogs']
        if flogs:
            logs = flogs
        for line in logs:
            m = re.search(pattern, line)
            if m and m.group(1):
                return m.group(1)
        return None


# -----------------------------------------------------------------------------
class State(object):
    def __init__(self, sname, ename, cpattern, logs, run):
        self.id = sname
        self.eid = ename
        self.tstamp = TimeStamp(cpattern, logs, self, run)


# -----------------------------------------------------------------------------
class TimeStamp(object):
    def __init__(self, cpattern, logs, state, run):
        self.state = state
        self.cpattern = cpattern
        self.logs = logs
        self.run = run
        self.epoch = None
        self.stamp = self._get_stamp()
        if self.state.eid == 'job' and self.state.id == 'end':
            print "DEBUG:TimeStamp:\n\tentity = %s;\n\tstate = %s;\n\tstamp = %s" % (self.state.eid, self.state.id, self.stamp)

    def _get_stamp(self):
        stamp = None
        for line in self.logs:
            m = re.search(self.cpattern, line)
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
    DT = "(\d+-\d+-\d+) (\d+:\d+:\d+),\d+[-,+]\d{4}[\w\s]+"

    # Check whether the parser is run with the required arguments.
    if len(sys.argv) <= 2:
        usage("insufficient arguments -- need swift log file and output file")

    if len(sys.argv) > 3:
        usage("too many arguments -- no more than 2")

    # Input swift log and json output files.
    flogs = sys.argv[1]
    fjson = sys.argv[2]

    # Entities' states.
    stsession = {'start': None, 'finish': None}

    stjob = {'init': None, 'sselect': None, 'start': None, 'task': None,
             'end': None}

    sttask = {'unsubmitted': 0 , 'submitting': 8 , 'submitted': 1,
              'active'     : 2 , 'suspended' : 3 , 'resumed'  : 4,
              'failed'     : 5 , 'canceled'  : 6 , 'completed': 7,
              'stage_in'   : 16, 'stage_out' : 17, 'unknown'  : 9999}

    stblock = {'requested': None, 'active': None, 'shutdown': None,
               'done': None}

    stworker = {'active': None, 'lost': None, 'shutdown': None}

    states = {'session': stsession,
              'job'    : stjob,
              'task'   : sttask,
              'block'  : stblock,
              'worker' : stworker}

    # Patterns, log filters, and filtered logs for Entities' properties and
    # states.
    resession = {'id'    : {'pattern' : 'RUN_ID (run\d{3})',
                            'lfilter' : None,
                            'flogs'   : None},
                 'start' : {'pattern' : DT+'INFO  Loader JAVA',
                            'lfilter' : None,
                            'flogs'   : None,
                            'cpattern': None},
                 'finish': {'pattern' : DT+'finished with no errors',
                            'lfilter' : None,
                            'flogs'   : None,
                            'cpattern': None}}

    rejob = {'id'     : {'pattern' : 'JOB_START jobid=([\w-]+) tr',
                         'lfilter' : 'JOB_START jobid=',
                         'flogs'   : None},
             'host'   : {'pattern' : 'JOB_START jobid=%s[\w\s/:.\-=\+\[\]]*host=([\w.]*)',
                         'lfilter' : 'JOB_START jobid=',
                         'flogs'   : None},
             'taskid' : {'pattern' : 'JOB_TASK jobid=%s\s+taskid=urn:(R-\d+[-,x]\d+[-,x]\d+)',
                         'lfilter' : 'JOB_TASK jobid=',
                         'flogs'   : None},
             'init'   : {'pattern' : DT+'JOB_INIT jobid=%s',
                         'lfilter' : 'JOB_INIT jobid=',
                         'flogs'   : None,
                         'cpattern': None},
             'sselect': {'pattern' : DT+'JOB_SITE_SELECT jobid=%s',
                         'lfilter' : 'JOB_SITE_SELECT jobid=',
                         'flogs'   : None,
                         'cpattern': None},
             'start'  : {'pattern' : DT+'JOB_START jobid=%s',
                         'lfilter' : 'JOB_START jobid=',
                         'flogs'   : None,
                         'cpattern': None},
             'task'   : {'pattern' : DT+'JOB_TASK jobid=%s taskid=urn:%s',
                         'lfilter' : 'JOB_TASK jobid=',
                         'flogs'   : None,
                         'cpattern': None},
             'end'    : {'pattern' : DT+'JOB_END jobid=%s',
                         'lfilter' : 'JOB_END jobid=',
                         'flogs'   : None,
                         'cpattern': None}}

    retask = {'id'      : {'pattern': 'JOB_TASK jobid=[\w-]+\s+taskid=urn:(R-\d+[-,x]\d+[-,x]\d+)',
                           'lfilter': 'JOB_TASK jobid=',
                           'flogs'  : None},
              'jobid'   : {'pattern': 'JOB_TASK jobid=([\w-]+)\s+taskid=urn:%s',
                           'lfilter': 'JOB_TASK jobid=',
                           'flogs'  : None},
              'blockid' : {'pattern': 'taskid=urn:%s\s+status=2\s+workerid=([\d\-]+):',
                           'lfilter': 'TASK_STATUS_CHANGE taskid=urn:R-\d+[-,x]\d+[-,x]\d+ status=2',
                           'flogs'  : None},
              'workerid': {'pattern': 'taskid=urn:%s\s+status=2\s+workerid=%s:(\d+)',
                           'lfilter': 'TASK_STATUS_CHANGE taskid=urn:R-\d+[-,x]\d+[-,x]\d+ status=2',
                           'flogs'  : None}}

    reblock = {'id'         : {'pattern' : 'BLOCK_REQUESTED id=([\d\-]+),',
                               'lfilter' : 'BLOCK_REQUESTED id=',
                               'flogs'   : None},
               'cores'      : {'pattern' : 'BLOCK_REQUESTED id=%s, cores=(\d+),',
                               'lfilter' : 'BLOCK_REQUESTED id=',
                               'flogs'   : None},
               'coresworker': {'pattern' : 'BLOCK_REQUESTED id=%s[\w\s,=]+coresPerWorker=(\d+),',
                               'lfilter' : 'BLOCK_REQUESTED id=',
                               'flogs'   : None},
               'walltime'   : {'pattern' : 'BLOCK_REQUESTED id=%s[\w\s,=]+walltime=(\d+)',
                               'lfilter' : 'BLOCK_REQUESTED id=',
                               'flogs'   : None},
               'utilization': {'pattern' : 'BLOCK_UTILIZATION id=%s, u=([\d\.]+)',
                               'lfilter' : 'BLOCK_UTILIZATION id=',
                               'flogs'   : None},
               'requested'  : {'pattern' : DT+'BLOCK_REQUESTED id=%s',
                               'lfilter' : 'BLOCK_REQUESTED id=',
                               'flogs'   : None,
                               'cpattern': None},
               'active'     : {'pattern' : DT+'BLOCK_ACTIVE id=%s',
                               'lfilter' : 'BLOCK_ACTIVE id=',
                               'flogs'   : None,
                               'cpattern': None},
               'shutdown'   : {'pattern' : DT+'BLOCK_SHUTDOWN id=%s',
                               'lfilter' : 'BLOCK_SHUTDOWN id=',
                               'flogs'   : None,
                               'cpattern': None},
               'done'       : {'pattern' : DT+'BLOCK_DONE id=%s',
                               'lfilter' : 'BLOCK_DONE id=',
                               'flogs'   : None,
                               'cpattern': None}}

    reworker = {'id'       : {'pattern' : 'WORKER_ACTIVE blockid=[\d\-]+ id=(\d+)',
                              'lfilter' : 'WORKER_ACTIVE blockid=',
                              'flogs'   : None},
                'blockid'  : {'pattern' : 'WORKER_ACTIVE blockid=([\d\-]+)',
                              'lfilter' : 'WORKER_ACTIVE blockid=',
                              'flogs'   : None},
                'node'     : {'pattern' : 'WORKER_ACTIVE blockid=%s id=%s node=([\w\d\-\.]+)',
                              'lfilter' : 'WORKER_ACTIVE blockid=',
                              'flogs'   : None},
                'coresnode': {'pattern' : 'WORKER_ACTIVE blockid=%s id=%s[\w\d\s\-\.=]+cores=(\d+)',
                              'lfilter' : 'WORKER_ACTIVE blockid=',
                              'flogs'   : None},
                'active'   : {'pattern' : DT+'WORKER_ACTIVE blockid=%s id=%s',
                              'lfilter' : 'WORKER_ACTIVE blockid=',
                              'flogs'   : None,
                              'cpattern': None},
                'lost'     : {'pattern' : DT+'WORKER_LOST blockid=%s id=%s',
                              'lfilter' : 'WORKER_LOST blockid=',
                              'flogs'   : None,
                              'cpattern': None},
                'shutdown' : {'pattern' : DT+'WORKER_SHUTDOWN blockid=%s id=%s',
                              'lfilter' : 'WORKER_SHUTDOWN blockid=',
                              'flogs'   : None,
                              'cpattern': None}}

    for name, code in states['task'].iteritems():
        status = "status=%s" % code
        retask[name] = {'pattern': DT+'TASK_STATUS_CHANGE taskid=urn:%s[\w\s\-]*'+status,
                        'lfilter': 'TASK_STATUS_CHANGE taskid=urn:R-\d+[-,x]\d+[-,x]\d+ '+status,
                        'flogs'   : None,
                        'cpattern': None}

    res = {'session': resession,
           'job'    : rejob,
           'task'   : retask,
           'block'  : reblock,
           'worker' : reworker}

    # Run initialization instantiate a session with all its jobs, tasks, blocks,
    # and workers. Each object initialization sets the object's IDs.
    run = Run(flogs, res, DTPATTERN)

    # Calculate time stamps for all the states of Swift components as logged in
    # swift.log
    for state, code in stsession.iteritems():
        run.add_state(run.session, 'session', state, code)

    for job in run.session.jobs:
        for state, code in stjob.iteritems():
            if state == 'task':
                run.add_state(job, 'job', state, code, (job.id, job.tid))
                continue
            run.add_state(job, 'job', state, code, job.id)

    for task in run.session.tasks:
        for state, code in sttask.iteritems():
            run.add_state(task, 'task', state, code, task.id)

    for block in run.session.blocks:
        for state, code in stblock.iteritems():
            run.add_state(block, 'block', state, code, block.id)

    for worker in run.session.workers:
        for state, code in stworker.iteritems():
            run.add_state(worker, 'worker', state, code, (worker.bid, worker.id))

    # Save the timestamps to a json file.
    run.save_to_json(fjson)
    run.save_to_json_full(fjson+'.full')

    sys.exit(0)
