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
        [<timing>] : optional -- type of timing

    The tool extracts timings from the Swift durations files in the given
    directory. By default, the tool output all the available timings. If a
    timing is specified, only that timing is outputted.

    Current timings are:
        - TTC : total time to completion of the whole session.
        - Tss : Job set up time as recorded by Swift.
        - Tse : Job execution time as recorded by Swift.
        - Tw  : Task waiting time before execution. From Swift submission time
                to Coaster scheduling it on a worker.
        - Te  : Task executing time as recorded by Coaster. From status 2
                (active) to status 7 (completed). We assume no other final
                state as we discard runs with failed/canceled jobs.
        - Tsi : Task staging in time. From status 16 (stage_in) to status 2
                (active).
        - Tso : Task staging out time. From status 17 (active) to status 7
                (completed).
        - Tq  : Block queuing time as recorded by the RemoteLogHandler (Swift or
                Coaster?). NOTE: the accuracy of this timing needs to be
                verified.
        - Ta  : Block active time as recorded by the RemoteLogHandler (Swift or
                Coaster?). NOTE: the accuracy of this timing needs to be
                verified.
        - Tb  : Worker bootstrapping time as recorded by the RemoteLogHandler
                (Swift or Coaster?). NOTE: the accuracy of this timing needs
                to be verified.
        - Twe : Worker executing time as recorded by the RemoteLogHandler
                (Swift or Coaster?). NOTE: the accuracy of this timing needs
                to be verified.

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

    base = _ranges[0] # smallest range

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
def get_ranges(log, entities, start_state_name, end_state_name):
    overlap = []
    for eid, v in log[entities].iteritems():
        if (log[entities][eid]['states'][start_state_name] and
            log[entities][eid]['states'][end_state_name]):
            overlap.append([log[entities][eid]['states'][start_state_name],
                            log[entities][eid]['states'][end_state_name]])
        else:
            print "WARNING: Entity '%s' states '%s' and '%s' are %s and %s:\n%s" % \
                (eid,
                 start_state_name,
                 end_state_name,
                 log[entities][eid]['states'][start_state_name],
                 log[entities][eid]['states'][end_state_name],
                 log[entities][eid])
    start_end = collapse_ranges(overlap)
    return start_end[0][1] - start_end[0][0]


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
    if ntask not in outputs[timing].keys():
        outputs[timing][ntask] = []
    outputs[timing][ntask].append(_range)


# -----------------------------------------------------------------------------
def csv_append_range(store, timing):
    '''Appends a range to a dedicated cvs file.'''
    keys = sorted(store[timing].keys())
    fcsv = timing+'.csv'
    with open(fcsv, "wb") as outfile:
        writer = csv.writer(outfile)
        writer.writerow(keys)
        writer.writerows(zip(*[store[timing][key] for key in keys]))


# -----------------------------------------------------------------------------
if __name__ == '__main__':
    '''
    TODO:
    - Calculate the ideal Te by fetching the workload properties.
    '''

    timing = None
    timings = {}

    if len(sys.argv) <= 1:
        usage("insufficient arguments -- need dir of json files")

    if len(sys.argv) > 3:
        usage("too many arguments -- no more than 2")

    if len(sys.argv) > 2:
        timing = sys.argv[2]

    # Make a list of the json files in the given directory.
    inputs = [f for f in os.listdir(sys.argv[1]) if os.path.isfile(os.path.join(sys.argv[1], f)) and '.json' in f]

    print "DEBUG: Selected input files = %s" % inputs
    timings = ['TTC', 'Tse', 'Tw', 'Te', 'Tsi', 'Tso', 'Tq']
    # timings = ['TTC']
    outputs = {}

    for timing in timings:
        outputs[timing] = {}

    # Read through all the json file in the given directory.
    for f in inputs:
        for timing in timings:
            with open(f) as jdata:
                slog = json.load(jdata)

            # Get the size of the workload.
            ntask = slog["Session"]["tasks_completed"]

            # Calculate every timing set by name in timings.
            if timing == 'TTC':
                TTC = get_range(slog, 'Session', 'start', 'finish')
                store_range(TTC, timing, ntask, outputs)
                csv_append_range(outputs, timing)

            if timing == 'Tse':
                Tse = get_ranges(slog, 'Jobs', 'start', 'end')
                store_range(Tse, timing, ntask, outputs)
                csv_append_range(outputs, timing)

            if timing == 'Tw':
                Tw = get_ranges(slog, 'Jobs', 'init', 'start')
                store_range(Tw, timing, ntask, outputs)
                csv_append_range(outputs, timing)

            if timing == 'Te':
                Te = get_ranges(slog, 'Tasks', 'active', 'completed')
                store_range(Te, timing, ntask, outputs)
                csv_append_range(outputs, timing)

            if timing == 'Tsi':
                Tsi = get_ranges(slog, 'Tasks', 'stage_in', 'active')
                store_range(Tsi, timing, ntask, outputs)
                csv_append_range(outputs, timing)

            if timing == 'Tso':
                Tso = get_ranges(slog, 'Tasks', 'stage_out', 'completed')
                store_range(Tso, timing, ntask, outputs)
                csv_append_range(outputs, timing)

            if timing == 'Tq':
                Tq = get_ranges(slog, 'Blocks', 'requested', 'active')
                store_range(Tq, timing, ntask, outputs)
                csv_append_range(outputs, timing)

    pprint.pprint("DEBUG: Timings = %s" % outputs)

