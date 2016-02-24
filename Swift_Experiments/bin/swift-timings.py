"""
Extracts timings from the given Swift log json files. File created with
swift-timings.py
"""

import os
import sys
import csv
import json
import pprint

__author__ = "Matteo Turilli"
__copyright__ = "Copyright 2015, The AIMES Project"
__license__ = "MIT"


# -----------------------------------------------------------------------------
def usage(msg=None, noexit=False):

    if msg:
        print "\nError: %s" % msg

    print """
    usage   : %s <dir> [<timing>]
    example : %s durations.json [TTC]

    arguments
        <dir>      : Directory with the json files produced by swift-timings.py
        [<timing>] : optional -- type of timing (**not implemented yet**)

    The tool extracts timings from the Swift durations files in the given
    directory. By default, the tool output all the available timings. If a
    timing is specified, only that timing is outputted.

    Current timings are:

    | Name | Owner   | Entities       | Duration      | Start tag | End tag   |
    |------|---------|----------------|---------------|-----------|-----------|
    | TTC* | Swift   | Session        | Total         | start     | end       |
    | Tss  | Swift   | Jobs           | Setting_up    | init      | task      |
    | Tse  | Swift   | Jobs           | Executing     | task      | end       |
    | Tw   | Coaster | Jobs/Tasks     | Submitting    | task      | active    |
    | Te * | Coaster | Tasks          | Executing     | active    | completed |
    | Tsi  | Coaster | Tasks          | Staging_in    | stage_in  | active    |
    | Tso  | Coaster | Tasks          | Staging_out   | stage_out | completed |
    | Tq * | Coaster | Blocks         | Queuing       | requested | active    |
    | Ta   | Coaster | Blocks         | Executing     | active    | done      |
    | Tb   | Coaster | Blocks/Workers | Bootstrapping | active    | active    |
    | Twe  | Coaster | Workers        | Executing     | active    | shutdown  |

    - TTC : total time to completion of the whole session.
    - Tss : Time taken by Swift to set up each task for execution. Can be used
            to determine the percentage of TTC spent on interpreting the given
            swift script.
    - Tse : Time taken to execute each task as logged by Swift. It can be
            compared to the executing time recorded by Coaster for
            sanity/consistency check purposes.
    - Tw  : Time taken by Coaster to queue/schedule each task to a pilot. It can
            be used to determine the overhead of Coaster independently from
            those of the resource.
    - Te  : Time taken by Coaster to execute each task on a worker (i.e.,
            pilot). This is the equivalent of AIMES Tx.
    - Tsi : Time taken by Coaster to stage the task's input file(s) if any.
            Useful if we will decide to include data-related timings in the
            paper.
    - Tso : Time taken by Coaster to stage the task's output file(s).  Useful to
            measure Coaster's overhead in saving STD* files after task
            execution.
    - Tq  : Time spent by each Block, i.e. pilot job, in the resource's queue.
            NOTE: All the time stamps recording by RemoteLogHandler may be
            inaccurate. This needs further verification.
    - Ta  : Time spent by each block, i.e. pilot job, executing. NOTE: All the
            time stamps recording by RemoteLogHandler may be inaccurate. This
            needs further verification.
    - Tb  : Time required by the worker, i.e. pilot agent, to bootstrap. NOTE:
            All the time stamps recording by RemoteLogHandler may be inaccurate.
            This needs further verification.
    - Twe : Time spent by each worker, i.e, pilot agent, executing. NOTE: All
            the time stamps recording by RemoteLogHandler may be inaccurate.
            This needs further verification.

    For more documentation see:
        https://github.com/radical-experiments/AIMES-Swift/tree/master/Swift_Experiments

    """ % (sys.argv[0], sys.argv[0])

    if msg:
        sys.exit(1)

    if not noexit:
        sys.exit(0)


# -----------------------------------------------------------------------------
def collapse_ranges(ranges):
    '''
    Input:  [[%f,%f],[%f,%f],[%f,%f],...]
    Output: [[%f,%f]]

    given be a set of ranges (as a set of pairs of floats [start, end] with
    'start <= end'. This algorithm will then collapse that set into the
    smallest possible set of ranges which cover the same, but not more nor
    less, of the domain (floats).

    We first sort the ranges by their starting point. We then start with the
    range with the smallest starting point [start_1, end_1], and compare to the
    next following range [start_2, end_2], where we now know that start_1 <=
    start_2. We have now two cases:

    a) when start_2 <= end_1, then the ranges overlap, and we collapse them
       into range_1: range_1 = [start_1, max[end_1, end_2]

    b) when start_2 > end_2, then ranges don't overlap. Importantly, none of
       the other later ranges can ever overlap range_1. So we move range_1 to
       the set of final ranges, and restart the algorithm with range_2 being
       the smallest one.

    Termination condition is if only one range is left -- it is also moved to
    the list of final ranges then, and that list is returned.
    '''
    final = []

    # sort ranges into a copy list
    _ranges = sorted(ranges, key=lambda x: x[0])
    START = 0
    END = 1

    # smallest range
    base = _ranges[0]
    for _range in _ranges[1:]:
        if _range[START] <= base[END]:

            # ranges overlap -- extend the base
            base[END] = max(base[END], _range[END])
        else:

            # ranges don't overlap -- move base to final, and current _range
            # becomes the new base
            final.append(base)
            base = _range

    # termination: push last base to final
    final.append(base)
    return final


# -----------------------------------------------------------------------------
def get_ranges(log, s_entities, s_state_name, e_entities, e_state_name):
    overlaps = []
    for seid in log[s_entities].keys():
        for eeid in log[e_entities].keys():
            if s_entities == e_entities:
                if seid == eeid:
                    overlap = get_overlap(log, s_entities, seid, s_state_name,
                                          e_entities, eeid, e_state_name)
                    if overlap:
                        overlaps.append(overlap)
            elif s_entities == 'Jobs' and e_entities == 'Tasks':
                if seid == log[e_entities][eeid]['jobid']:
                    overlap = get_overlap(log, s_entities, seid, s_state_name,
                                          e_entities, eeid, e_state_name)
                    if overlap:
                        overlaps.append(overlap)
            elif s_entities == 'Blocks' and e_entities == 'Workers':
                if seid == log[e_entities][eeid]['block']:
                    overlap = get_overlap(log, s_entities, seid, s_state_name,
                                          e_entities, eeid, e_state_name)
                    if overlap:
                        overlaps.append(overlap)
    start_end = collapse_ranges(overlaps)
    return start_end[0][1] - start_end[0][0]

# -----------------------------------------------------------------------------
def get_overlap(log, s_entities, seid, s_state_name, e_entities, eeid, e_state_name):
    overlap = None
    start = log[s_entities][seid]['states'][s_state_name]
    end = log[e_entities][eeid]['states'][e_state_name]
    if start and end:
        overlap = [start,end]
    else:
        sw = "\n\tEntity '%s' state '%s' is %s" % (seid, s_state_name, start)
        ew = "\n\tEntity '%s' state '%s' is %s" % (eeid, e_state_name, end)
        print "\nDEBUG: undefined entities %s%s" % (sw, ew)
    return overlap

# -----------------------------------------------------------------------------
def get_range(log, entity, start_state_name, end_state_name):
    start = log[entity]['states'][start_state_name]
    end = log[entity]['states'][end_state_name]
    if start and end:
        _range = end - start
    else:
        print "ERROR: The entity %s has no '%s' state:\n%s" % \
            (entity, end_state_name, log[entity])
        sys.exit(1)
    return _range


# -----------------------------------------------------------------------------
def store_range(_range, timing, ntask, store):
    '''
    Adds range to the list of previously calculated ranges of type timing for
    the same BoT size ntask. If it is the first time we calculate this type of
    range for this BoT size, it creates a dedicated list in outputs[timing].
    '''
    if ntask not in store[timing].keys():
        store[timing][ntask] = []
    store[timing][ntask].append(_range)


# -----------------------------------------------------------------------------
def store_property(prop, _property, ntask, store):
    if _property in ['Blocks_per_host', 'Workers_per_host', 'Tasks_per_host']:
        # Entities' properties can be null when the entity has been instantiated
        # but for some reason it did not reached the state in which one or more
        # properties are recorded. For example, a task that has been scheduled
        # but failed, or a block that has been requested but never went active.
        if prop:
            for host, nentities in prop.iteritems():
                phost = _property+'_'+host
                if phost not in store.keys():
                    store[phost] = {}
                if ntask not in store[phost].keys():
                    store[phost][ntask] = []
                store[phost][ntask].append(nentities)
    else:
        if ntask not in store[_property].keys():
            store[_property][ntask] = []
        store[_property][ntask].append(prop)


# -----------------------------------------------------------------------------
def csv_append_property(store, properties, prop):
    props = []
    keys = []
    # Check whether there are _host sub-properties. Discard the base property if
    # there are.
    for key in store.keys():
        if prop in key and prop != key:
            props.append(key)
    # If there are not _host keys, use the base. This covers for those
    # properties for which no _host sub-properties are used.
    if not props and prop in store.keys():
        keys.append(prop)
    # This implicitly verifies that the two _host sub-properties have the same
    # set of keys. When they do not have it, something bad(tm) will happen with
    # zip.
    for p in props:
        for k in store[p].keys():
            if k not in keys:
                keys.append(k)
    keys = sorted(keys)
    for p in props:
        with open(p+'.csv', "wb") as outfile:
            writer = csv.writer(outfile)
            writer.writerow(keys)
            writer.writerows(zip(*[store[p][key] for key in keys]))


# -----------------------------------------------------------------------------
def csv_append_range(store, timings, timing):
    '''Appends a range to a dedicated cvs file.'''
    keys = sorted(store[timing].keys())
    fcsv = timing+'.csv'
    with open(fcsv, "wb") as outfile:
        writer = csv.writer(outfile)
        writer.writerow(keys)
        writer.writerows(zip(*[store[timing][key] for key in keys]))


# -----------------------------------------------------------------------------
def get_tasks_per_worker(slog):
    tw = 0
    for worker in slog['Workers'].keys():
        tw += len(slog['Workers'][worker]['tasks'])
    return float(tw)/float(len(slog['Workers'].keys()))


# -----------------------------------------------------------------------------
def get_entities_per_host(slog, entities):
    hosts = {}
    for host in slog['Session']['hosts']:
        hosts[host] = 0
    for entity in slog[entities].keys():
        if slog[entities][entity]['host']:
            hosts[str(slog[entities][entity]['host'])] += 1
    print "%s hosts %s" % (entities, hosts)
    return hosts


# -----------------------------------------------------------------------------
if __name__ == '__main__':
    '''
    TODO:
    - Calculate the ideal Te by fetching the workload properties.
    '''
    timing = None
    if len(sys.argv) <= 1:
        usage("insufficient arguments -- need dir of json files")

    if len(sys.argv) > 3:
        usage("too many arguments -- no more than 2")

    if len(sys.argv) > 2:
        timing = sys.argv[2]

    timings    = {'TTC': 'TTC'             , 'Tss': 'Setting_up'          ,
                  'Tse': 'Executing_job'   , 'Tw' : 'Submitting_task'     ,
                  'Te' : 'Executing_task'  , 'Tsi': 'Staging_in_task'     ,
                  'Tso': 'Staging_out_task', 'Tq' : 'Queuing_block'       ,
                  'Ta' : 'Executing_block' , 'Tb' : 'Bootstrapping_worker',
                  'Twe': 'Executing_worker'}

    properties = {'Pp' : 'Number_blocks'   , 'Pbr': 'Blocks_per_host' ,
                  'Pw' : 'Number_workers'  , 'Pwr': 'Workers_per_host',
                  'Ptw': 'Tasks_per_worker', 'Ptr': 'Tasks_per_host'}

    # Make a list of the json files in the given directory.
    inputs = [f for f in os.listdir(sys.argv[1]) if os.path.isfile(os.path.join(sys.argv[1], f)) and '.json' in f]
    print "DEBUG: Selected input files = %s" % inputs

    outputs = {}
    for _property, name in properties.iteritems():
        outputs[name] = {}
    for timing, name in timings.iteritems():
        outputs[name] = {}

    # Read through all the json file in the given directory.
    for f in inputs:

        # Derive the properties of each run and save each property to a
        # dedicated csv file named named after that property. Each file contains
        # the value of the measured timing for each scale of the given BoTs.
        for prop in properties.keys():
            with open(f) as jdata:
                slog = json.load(jdata)

            # Get the size of the workload.
            ntask = slog["Session"]["tasks_completed"]

            if prop == 'Pp':
                Pp = slog['Session']['nblocks']
                store_property(Pp, properties[prop], ntask, outputs)
                csv_append_property(outputs, properties, properties[prop])

            if prop == 'Pw':
                Pw = slog['Session']['nworkers']
                store_property(Pw, properties[prop], ntask, outputs)
                csv_append_property(outputs, properties, properties[prop])

            if prop == 'Ptw':
                Ptw = get_tasks_per_worker(slog)
                store_property(Ptw, properties[prop], ntask, outputs)
                csv_append_property(outputs, properties, properties[prop])

            # Due to how information is extracted from Swift logs, a host is
            # recorded for a block only when at least a task has been running on
            # its worker(s). For this reason, we can extract only Workers per
            # host, not blocks per host.
            # if prop == 'Pbr':
            #     Pbr = get_blocks_per_host(slog)
            #     store_property(Pbr, properties[prop], ntask, outputs)
            #     csv_append_property(outputs, properties, properties[prop])

            if prop == 'Pwr':
                Pwr = get_entities_per_host(slog, 'Workers')
                print Pwr
                store_property(Pwr, properties[prop], ntask, outputs)
                csv_append_property(outputs, properties, properties[prop])

            if prop == 'Ptr':
                Ptr = get_entities_per_host(slog, 'Tasks')
                store_property(Ptr, properties[prop], ntask, outputs)
                csv_append_property(outputs, properties, properties[prop])


        # Derive the timings of each run and save each timing to a dedicated csv
        # file named named after that timing. Each file contains the value of
        # the measured timing for each scale of the given BoTs.
        for timing in timings.keys():
            with open(f) as jdata:
                slog = json.load(jdata)

            # Get the size of the workload.
            ntask = slog["Session"]["tasks_completed"]

            # Calculate every timing set by name in timings.
            if timing == 'TTC':
                TTC = get_range(slog, 'Session', 'start', 'finish')
                store_range(TTC, timings[timing], ntask, outputs)
                csv_append_range(outputs, timings, timings[timing])

            if timing == 'Tss':
                Tss = get_ranges(slog, 'Jobs', 'init', 'Jobs', 'task')
                store_range(Tss, timings[timing], ntask, outputs)
                csv_append_range(outputs, timings, timings[timing])

            if timing == 'Tse':
                Tse = get_ranges(slog, 'Jobs', 'task', 'Jobs', 'end')
                store_range(Tse, timings[timing], ntask, outputs)
                csv_append_range(outputs, timings, timings[timing])

            if timing == 'Tw':
                Tw = get_ranges(slog, 'Jobs', 'task', 'Tasks', 'active')
                store_range(Tw, timings[timing], ntask, outputs)
                csv_append_range(outputs, timings, timings[timing])

            if timing == 'Te':
                Te = get_ranges(slog, 'Tasks', 'active', 'Tasks', 'completed')
                store_range(Te, timings[timing], ntask, outputs)
                csv_append_range(outputs, timings, timings[timing])

            if timing == 'Tsi':
                Tsi = get_ranges(slog, 'Tasks', 'stage_in', 'Tasks', 'active')
                store_range(Tsi, timings[timing], ntask, outputs)
                csv_append_range(outputs, timings, timings[timing])

            if timing == 'Tso':
                Tso = get_ranges(slog, 'Tasks', 'stage_out', 'Tasks', 'completed')
                store_range(Tso, timings[timing], ntask, outputs)
                csv_append_range(outputs, timings, timings[timing])

            if timing == 'Tq':
                Tq = get_ranges(slog, 'Blocks', 'requested', 'Blocks', 'active')
                store_range(Tq, timings[timing], ntask, outputs)
                csv_append_range(outputs, timings, timings[timing])

            if timing == 'Ta':
                Ta = get_ranges(slog, 'Blocks', 'active', 'Blocks', 'done')
                store_range(Ta, timings[timing], ntask, outputs)
                csv_append_range(outputs, timings, timings[timing])

            if timing == 'Tb':
                Tb = get_ranges(slog, 'Blocks', 'active', 'Workers', 'active')
                store_range(Tb, timings[timing], ntask, outputs)
                csv_append_range(outputs, timings, timings[timing])

            if timing == 'Twe':
                Twe = get_ranges(slog, 'Workers', 'active', 'Workers', 'shutdown')
                store_range(Twe, timings[timing], ntask, outputs)
                csv_append_range(outputs, timings, timings[timing])

    print "DEBUG: Timings"
    pprint.pprint(outputs)

