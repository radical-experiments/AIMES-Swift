#!/usr/bin/env python

import re
import sys
import json
import time

'''Reads Swift+Coaster log file and returns a json file with timestamps of each
job, task, block and worker's state and the key properties of the run.
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

    def add_property(self, entity, tag, args=None):
        logs = self.log.entries
        pattern = self.res[entity][tag]['pattern']
        if args:
            pattern = pattern % args
        flogs = self.res[entity][tag]['flogs']
        if flogs:
            logs = flogs
        for line in logs:
            m = re.search(pattern, line)
            if m and m.group(1):
                return m.group(1)
        return None

    def add_state(self, entity, ename, sname, args=None):
        logs = self.log.entries
        pattern = self.res[ename][sname]['pattern']
        flogs = self.res[ename][sname]['flogs']
        if args:
            pattern = pattern % args
        if flogs:
            logs = flogs
        state = State(sname, ename, pattern, logs, self)
        if state.id == 'failed' and state.tstamp.stamp:
            self.session.tasks_failed += 1
        if state.id == 'completed' and state.tstamp.stamp:
            self.session.tasks_completed += 1
        entity.states.append(state)


# -----------------------------------------------------------------------------
class Log(object):
    def __init__(self, flog, run):
        self.entries = [line.strip() for line in open(flog)]
        self.run = run
        self.partitions = self._partition_logs()

    def _partition_logs(self):
        partitions = {}
        for entity, value in self.run.res.iteritems():
            for tag, patterns in value.iteritems():
                if patterns['lfilter']:
                    partition = self._grep_logs(patterns['lfilter'])
                    patterns['flogs'] = partition
                    partitions[entity+'-'+tag] = partition
        return partitions

    def _grep_logs(self, lfilter):
        partition = []
        for line in self.entries:
            m = re.search(lfilter, line)
            if m:
                partition.append(line)
        if not partition:
            partition.append('empty')
        return partition


# -----------------------------------------------------------------------------
class Session(object):
    def __init__(self, run):
        self.run = run
        self.states = []
        self.hosts = []
        self.tasks_failed = 0
        self.tasks_completed = 0
        self.id = self.run.add_property('session', 'id')
        self.jobs = self._get_entity('job')
        self.tasks = self._get_entity('task')
        self.blocks = self._get_entity('block')
        self.workers = self._get_entity('worker')
        self._set_tasks_host_jid()
        self._set_workers_tasks_host()
        self._set_blocks_workers_nodes_host()
        # self._set_tasks_failed_completed()

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
            # if m:
            if m and m.group(1) not in ids:
                eid = m.group(1)
                if entity == 'job':
                    job = Job(eid, self.run)
                    if job.host not in self.hosts:
                        self.hosts.append(job.host)
                    entities.append(job)
                elif entity == 'task':
                    entities.append(Task(eid, self.run))
                elif entity == 'block':
                    entities.append(Block(eid, self.run))
                elif entity == 'worker':
                    bid = eid
                    lid = m.group(2)
                    eid = "%s:%s" % (eid, lid)
                    entities.append(Worker(eid, lid, bid, self.run))
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

    def _set_workers_tasks_host(self):
        for task in self.tasks:
            for worker in self.workers:
                if task.wid == worker.id:
                    worker.tasks.append(task.id)
                    if not worker.host:
                        worker.host = task.host

    def _set_blocks_workers_nodes_host(self):
        for block in self.blocks:
            for worker in self.workers:
                if worker.bid == block.id:
                    block.workers.append(worker.id)
                    block.nodes.append(worker.node)
                    if not block.host:
                        block.host = worker.host

    # def _set_tasks_failed_completed(self):
    #     for task in self.tasks:
    #         for state in task.states:


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
        self.host = self.run.add_property('job', 'host', self.id)
        self.tid = self.run.add_property('job', 'taskid', self.id)


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
        self.host = None
        self.states = []
        self.jid = self.run.add_property('task', 'jobid', self.id)
        self.bid = self.run.add_property('task', 'blockid', self.id)
        self.wid = self.run.add_property('task', 'workerid', (self.id, self.bid))


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
        self.cores = self.run.add_property('block', 'cores', self.id)
        self.coresworker = self.run.add_property('block', 'coresworker', self.id)
        self.walltime = self.run.add_property('block', 'walltime', self.id)
        self.utilization = self.run.add_property('block', 'utilization', self.id)


# -----------------------------------------------------------------------------
class Worker(object):
    '''A worker is a pilot agent in the Coaster lingo. Each worker belong to a
    block, i.e. a job scheduled on a resource.

    States:
        WORKER_ACTIVE
        WORKER_LOST
        WORKER_SHUTDOWN
    '''
    def __init__(self, wid, lid, bid, run):
        self.id = wid
        self.lid = lid
        self.bid = bid
        self.run = run
        self.host = None
        self.tasks = []
        self.states = []
        self.node = self.run.add_property('worker', 'node', (self.bid, self.lid))
        self.coresnode = self.run.add_property('worker', 'coresnode', (self.bid, self.lid))


# -----------------------------------------------------------------------------
class State(object):
    def __init__(self, sname, ename, pattern, logs, run):
        self.id = sname
        self.eid = ename

        # Some ugly minor optimizations.
        # if len(logs) == 0:
        #     self.stamp = None
        if self.eid == 'session' and self.id == 'start':
            self.tstamp = TimeStamp(pattern, logs[:10], self, run)
        elif self.eid == 'session' and self.id == 'finish':
            self.tstamp = TimeStamp(pattern, list(reversed(logs)), self, run)
        else:
            self.tstamp = TimeStamp(pattern, logs, self, run)


# -----------------------------------------------------------------------------
class TimeStamp(object):
    def __init__(self, pattern, logs, state, run):
        self.state = state
        self.cpattern = pattern
        self.logs = logs
        self.run = run
        self.epoch = None
        self.stamp = self._get_stamp()

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
class Reporter(object):
    def __init__(self, run):
        self.run = run
        self.session = self.run.session

    def write_json(self, jfile):
        d = {}
        d['Session'] = {'ID': self.session.id,
                        'hosts': self.session.hosts,
                        'njobs': len(self.session.jobs),
                        'ntasks': len(self.session.tasks),
                        'nblocks': len(self.session.blocks),
                        'nworkers': len(self.session.workers),
                        'tasks_failed': self.session.tasks_failed,
                        'tasks_completed': self.session.tasks_completed,
                        'states' : {}}
        for state in self.session.states:
            d['Session']['states'][state.id] = state.tstamp.epoch
        d['Jobs'] = {}
        for job in self.session.jobs:
            d['Jobs'][job.id] = {'host': job.host,
                                 'task_id': job.tid,
                                 'states': {}}
            for state in job.states:
                d['Jobs'][job.id]['states'][state.id] = state.tstamp.epoch
        d['Tasks'] = {}
        for task in self.session.tasks:
            d['Tasks'][task.id] = {'host': task.host,
                                   'jobid': task.jid,
                                   'blockid': task.bid,
                                   'workerid': task.wid,
                                   'states': {}}
            for state in task.states:
                d['Tasks'][task.id]['states'][state.id] = state.tstamp.epoch
        d['Blocks'] = {}
        for block in self.session.blocks:
            d['Blocks'][block.id] = {'host': block.host,
                                     'nodes': block.nodes,
                                     'workers': block.workers,
                                     'cores': block.cores,
                                     'cores_per_worker': block.coresworker,
                                     'walltime': block.walltime,
                                     'utilization': block.utilization,
                                     'states': {}}
            for state in block.states:
                d['Blocks'][block.id]['states'][state.id] = state.tstamp.epoch
        d['Workers'] = {}
        for worker in self.session.workers:
            d['Workers'][worker.id] = {'host': worker.host,
                                       'tasks': worker.tasks,
                                       'block': worker.bid,
                                       'node': worker.node,
                                       'cores_node': worker.coresnode,
                                       'states': {}}
            for state in worker.states:
                d['Workers'][worker.id]['states'][state.id] = state.tstamp.epoch
        fout = open(jfile, 'w')
        json.dump(d, fout, indent=4)


# -----------------------------------------------------------------------------
class Profiler(object):
    '''
    import datetime

    if ename == 'job':
        print "%s - DEBUG State Job %s IN" % \
            (datetime.datetime.now().time(), sname)
    if ename == 'task':
        print "%s - DEBUG State Task %s IN" % \
            (datetime.datetime.now().time(), sname)
    if self.eid == 'job':
        print "%s - DEBUG State Job %s OUT" % \
            (datetime.datetime.now().time(), self.id)
    if self.eid == 'task':
        print "%s - DEBUG State Task %s OUT" % \
            (datetime.datetime.now().time(), self.id)

    if state.eid == 'job':
        print "%s - DEBUG TimeStamp Job %s IN" % \
            (datetime.datetime.now().time(), state.id)
    if state.eid == 'task':
        print "%s - DEBUG TimeStamp Task %s IN" % \
            (datetime.datetime.now().time(), state.id)
    if state.eid == 'job':
        print "%s - DEBUG TimeStamp Job %s OUT" % \
            (datetime.datetime.now().time(), state.eid)
    if state.eid == 'task':
        print "%s - DEBUG TimeStamp Task %s OUT" % \
            (datetime.datetime.now().time(), state.eid)

    if self.state.eid == 'job':
        print "%s - DEBUG _get_stamp Job %s; %s log lines IN" % \
            (datetime.datetime.now().time(), self.state.id, len(self.logs))
    if self.state.eid == 'task':
        print "%s - DEBUG _get_stamp Task %s; %s log lines IN" % \
            (datetime.datetime.now().time(), self.state.id, len(self.logs))
    if self.state.eid == 'job':
        print "%s - DEBUG _get_stamp Job %s; %s log lines OUT" % \
            (datetime.datetime.now().time(), self.state.id, len(self.logs))
    if self.state.eid == 'task':
        print "%s - DEBUG _get_stamp Task %s; %s log lines OUT" % \
            (datetime.datetime.now().time(), self.state.id, len(self.logs))
    '''

    def __init__(self, run):
        self.run = run
        self.log = self.run.log
        self.jobs = self.run.session.jobs
        self.tasks = self.run.session.tasks
        self.blocks = self.run.session.blocks
        self.workers = self.run.session.workers

    def log_partitions(self):
        stats = {'logs': len(self.log.entries)}
        for name, partition in self.log.partitions.iteritems():
            stats[name] = len(partition)
        return stats


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
    DT = "(\d+-\d+-\d+) (\d+:\d+:\d+),\d+[-,+]\d{4}[\w\s]+?"

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
                            'flogs'   : None},
                 'finish': {'pattern' : DT+'finished with no errors',
                            'lfilter' : None,
                            'flogs'   : None}}

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
                         'flogs'   : None},
             'sselect': {'pattern' : DT+'JOB_SITE_SELECT jobid=%s',
                         'lfilter' : 'JOB_SITE_SELECT jobid=',
                         'flogs'   : None},
             'start'  : {'pattern' : DT+'JOB_START jobid=%s',
                         'lfilter' : 'JOB_START jobid=',
                         'flogs'   : None},
             'task'   : {'pattern' : DT+'JOB_TASK jobid=%s taskid=urn:%s',
                         'lfilter' : 'JOB_TASK jobid=',
                         'flogs'   : None},
             'end'    : {'pattern' : DT+'JOB_END jobid=%s',
                         'lfilter' : 'JOB_END jobid=',
                         'flogs'   : None}}

    retask = {'id'      : {'pattern': 'JOB_TASK jobid=[\w-]+\s+taskid=urn:(R-\d+[-,x]\d+[-,x]\d+)',
                           'lfilter': 'JOB_TASK jobid=',
                           'flogs'  : None},
              'jobid'   : {'pattern': 'JOB_TASK jobid=([\w-]+)\s+taskid=urn:%s',
                           'lfilter': 'JOB_TASK jobid=',
                           'flogs'  : None},
              'blockid' : {'pattern': 'taskid=urn:%s\s+status=2\s+workerid=([\d\-]+):',
                           'lfilter': 'TASK_STATUS_CHANGE taskid=urn:R-\d+[-,x]\d+[-,x]\d+ status=2',
                           'flogs'  : None},
              'workerid': {'pattern': 'taskid=urn:%s\s+status=2\s+workerid=(%s:\d+)',
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
                               'flogs'   : None},
               'active'     : {'pattern' : DT+'BLOCK_ACTIVE id=%s',
                               'lfilter' : 'BLOCK_ACTIVE id=',
                               'flogs'   : None},
               'shutdown'   : {'pattern' : DT+'BLOCK_SHUTDOWN id=%s',
                               'lfilter' : 'BLOCK_SHUTDOWN id=',
                               'flogs'   : None},
               'done'       : {'pattern' : DT+'BLOCK_DONE id=%s',
                               'lfilter' : 'BLOCK_DONE id=',
                               'flogs'   : None}}

    reworker = {'id'       : {'pattern' : 'WORKER_ACTIVE blockid=([\d\-]+) id=(\d+)',
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
                              'flogs'   : None},
                'lost'     : {'pattern' : DT+'WORKER_LOST blockid=%s id=%s',
                              'lfilter' : 'WORKER_LOST blockid=',
                              'flogs'   : None},
                'shutdown' : {'pattern' : DT+'WORKER_SHUTDOWN blockid=%s id=%s',
                              'lfilter' : 'WORKER_SHUTDOWN blockid=',
                              'flogs'   : None}}

    for name, code in states['task'].iteritems():
        if code in [16, 2]:
            status = "status=%s" % code
            retask[name] = {'pattern': DT+'TASK_STATUS_CHANGE taskid=urn:%s '+status+' workerid=%s',
                            'lfilter': 'TASK_STATUS_CHANGE taskid=urn:R-\d+[-,x]\d+[-,x]\d+ '+status+' workerid=[\d\-:]+',
                            'flogs'   : None}
        else:
            status = "status=%s" % code
            retask[name] = {'pattern': DT+'TASK_STATUS_CHANGE taskid=urn:%s '+status,
                            'lfilter': 'TASK_STATUS_CHANGE taskid=urn:R-\d+[-,x]\d+[-,x]\d+ '+status+'$',
                            'flogs'   : None}

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
        run.add_state(run.session, 'session', state)

    for job in run.session.jobs:
        # print "\n%s - DEBUG JobState %s" % (datetime.datetime.now().time(), job.id)
        for state, code in stjob.iteritems():
            if state == 'task':
                run.add_state(job, 'job', state, (job.id, job.tid))
                continue
            run.add_state(job, 'job', state, job.id)

    for task in run.session.tasks:
        # print "\n%s - DEBUG TaskState %s" % (datetime.datetime.now().time(), task.id)
        for state, code in sttask.iteritems():
            if code in [16, 2]:
                run.add_state(task, 'task', state, (task.id, task.wid))
            else:
                run.add_state(task, 'task', state, task.id)

    for block in run.session.blocks:
        for state, code in stblock.iteritems():
            run.add_state(block, 'block', state, block.id)

    for worker in run.session.workers:
        for state, code in stworker.iteritems():
            run.add_state(worker, 'worker', state, (worker.bid, worker.lid))

    # Save the timestamps to a json file.
    reporter = Reporter(run)
    reporter.write_json(fjson)

    # Profile logs
    # import pprint
    # profiler = Profiler(run)
    # pprint.pprint(profiler.log_partitions())

    sys.exit(0)
