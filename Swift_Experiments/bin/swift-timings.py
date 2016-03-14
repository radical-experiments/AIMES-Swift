"""
Extracts timings from the given Swift log JSON files. File created with
swift-timings.py
"""

import os
import sys
import csv
import json
import time
import pprint

__author__ = "Matteo Turilli"
__copyright__ = "Copyright 2015, The AIMES Project"
__license__ = "MIT"

DEBUG = True


# -----------------------------------------------------------------------------
def usage(msg=None, noexit=False):

    if msg:
        print "\nError: %s" % msg

    print """
    usage   : %s <dir>
    example : %s durations.json

    arguments
        <dir>      : Directory with the JSON files produced by swift-timings.py

    The tool extracts timings from the Swift JSON files in the given
    directory.
    """ % (sys.argv[0], sys.argv[0])

    if msg:
        sys.exit(1)

    if not noexit:
        sys.exit(0)


# -----------------------------------------------------------------------------
def write_run_report(slog, session, f):
    tformat = '%Y-%m-%d %H:%M:%S'
    etag = f[:7]
    report = etag+'-analysis.txt'

    with open(report, 'w') as r:
        r.write("Experiment: %s\n" % etag)
        r.write("-" * 19)

        r.write("\nNumber of tasks: %s\n" % slog['Session']['ntasks'])
        r.write("Number of workers: %s\n" % slog['Session']['nworkers'])
        r.write("hosts: %s\n\n" % ", ".join(slog['Session']['hosts']))

        r.write("Averages\n")
        r.write("--------\n")

        for host in slog['Session']['hosts']:
            r.write("Average number of tasks executed on %s: %s\n" %
                    (host, session['Ptr'][host]))
        for host in slog['Session']['hosts']:
            r.write("Average number of workers on %s: %s\n" %
                    (host,  session['Pwr'][host]))

        r.write("Average number of tasks per worker: %s\n\n" %
                session['Ptw'])

        r.write("Workspans\n")
        r.write("---------\n")
        s = slog['Session']['states']['start']
        e = slog['Session']['states']['finish']
        sstart = time.strftime(tformat, time.localtime(s))
        send = time.strftime(tformat, time.localtime(e))

        r.write("Session              : start %s; end %s\n" % (sstart, send))
        workers = {}
        start_end = {}
        for seid in slog['Workers'].keys():
            if slog['Workers'][seid]['host']:
                host = slog['Workers'][seid]['host']
                if host not in workers.keys():
                    workers[host] = []
                start = slog['Workers'][seid]['states']['active']
                end = slog['Workers'][seid]['states']['shutdown']
                workers[host].append([start, end])
        for host in slog['Session']['hosts']:
            start_end[host] = collapse_ranges(workers[host])
            wspstart = time.strftime(tformat,
                                     time.localtime(start_end[host][0][0]))
            wspend = time.strftime(tformat,
                                   time.localtime(start_end[host][-1:][0][1]))
            r.write("Workers on %-10s: start %s; end %s\n" % (host,
                                                              wspstart,
                                                              wspend))

        r.write("\nTimings\n")
        r.write("-------\n")
        r.write("TTC                                        : %ss (%sm)\n" %
                (session['TTC'], session['TTC']/60))
        r.write("TTw (setup + queuing time + bootstrap time): %ss (%sm)\n" %
                (session['Tw'], session['Tw']/60))
        r.write("TTe (stage in + execution time + stage out): %ss (%sm)\n\n" %
                (session['Te'], session['Te']/60))

        r.write("State model\n")
        r.write("-----------\n\n")

        r.write("       | start | init | task | requested | B active | W active | stg_in | T active | stg_out | completed | shutdown | B done | end |\n")
        r.write("|------|---|------|------|---------|-----------|----------|---------|---------|---------|----------|----------|----------|------|--|\n")
        r.write("| TTC* |   |********************************************************************************************************************|  |\n")
        r.write("| Tss  |          |......|                                                                                                         |\n")
        r.write("| Tse  |                 |......................................................................................................|  |\n")
        r.write("| Tw * |                 |******************************************|                                                              |\n")
        r.write("| Te * |                                                            |******************************|                               |\n")
        r.write("| Tsi  |                                                            |.........|                                                    |\n")
        r.write("| Tso  |                                                                                |..........|                               |\n")
        r.write("| Tq   |                           |...........|                                                                                   |\n")
        r.write("| Ta   |                                       |.........................................................................|         |\n")
        r.write("| Tb   |                                       |..........|                                                                        |\n")
        r.write("| Twe  |                                                  |...................................................|                    |\n")

        r.write("\n* = Marks that states we use to measure TTC and its dominant components.\n\n")

        r.write("Timings\n")
        r.write("-------\n\n")

        r.write("| Name | Owner   | Entities       | Duration      | Start tag | End tag   |\n")
        r.write("|------|---------|----------------|---------------|-----------|-----------|\n")
        r.write("| TTC* | Swift   | Session        | TTC           | start     | end       |\n")
        r.write("| Tss  | Swift   | Jobs           | Setting_up    | init      | task      |\n")
        r.write("| Tse  | Swift   | Jobs           | Executing     | task      | end       |\n")
        r.write("| Tw   | Coaster | Jobs/Tasks     | Submitting    | task      | active    |\n")
        r.write("| Te * | Coaster | Tasks          | Executing     | active    | completed |\n")
        r.write("| Tsi  | Coaster | Tasks          | Staging_in    | stage_in  | active    |\n")
        r.write("| Tso  | Coaster | Tasks          | Staging_out   | stage_out | completed |\n")
        r.write("| Tq * | Coaster | Blocks         | Queuing       | requested | active    |\n")
        r.write("| Ta   | Coaster | Blocks         | Executing     | active    | done      |\n")
        r.write("| Tb   | Coaster | Blocks/Workers | Bootstrapping | active    | active    |\n")
        r.write("| Twe  | Coaster | Workers        | Executing     | active    | shutdown  |\n\n")

        r.write("- TTC : total time to completion of the whole session.\n")
        r.write("- Tss : Time taken by Swift to set up each task for execution. Can be used\n")
        r.write("        to determine the percentage of TTC spent on interpreting the given\n")
        r.write("        swift script. In our experiments this is very short.\n")
        r.write("- Tse : Time taken to execute each task as logged by Swift. It can be\n")
        r.write("        compared to the executing time recorded by Coaster for\n")
        r.write("        sanity/consistency check purposes. Did the sanity check, seems fine.\n")
        r.write("- Tw  : Time taken by Coaster to schedule a block (i.e., job) on the local\n")
        r.write("        LRMS + block queuing time of that block. Equivalent to AIMES Tw\n")
        r.write("- Te  : Time taken by Coaster to execute each task on a worker (i.e.,\n")
        r.write("        agent). Includes staging in and out timings. Equivalent to AIMES Te.\n")
        r.write("- Tsi : Time taken by Coaster to stage the task's input file(s) if any.\n")
        r.write("        Useful if we will decide to include data-related timings in the\n")
        r.write("        paper.\n")
        r.write("- Tso : Time taken by Coaster to stage the task's output file(s).  Useful to\n")
        r.write("        measure Coaster's overhead in saving out/err files after task\n")
        r.write("        execution.\n")
        r.write("- Tq  : Time spent by each Block, i.e. pilot, in the resource's queue.\n")
        r.write("        NOTE: All the time stamps recording by RemoteLogHandler may be\n")
        r.write("        inaccurate.\n")
        r.write("- Ta  : Time spent by each block, i.e. pilot, executing. NOTE: All the\n")
        r.write("        time stamps recording by RemoteLogHandler may be inaccurate. This\n")
        r.write("        needs further verification.\n")
        r.write("- Tb  : Time required by the worker, i.e. agent, to bootstrap. NOTE:\n")
        r.write("        This timing is NOT accurate.\n")
        r.write("- Twe : Time spent by each worker, i.e, agent, executing. NOTE: All\n")
        r.write("        the time stamps recording by RemoteLogHandler may be inaccurate.\n")
        r.write("        This needs further verification.\n")

        r.write("For more documentation see:\n")
        r.write("https://github.com/radical-experiments/AIMES-Swift/tree/master/Swift_Experiments\n")


# -----------------------------------------------------------------------------
def collapse_ranges(ranges):
    '''
    Input:  [[%f,%f],[%f,%f],[%f,%f], ...]
    Output: [[%f,%f], [%f,%f], ...)

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

    # Ranges must be unique: we do not count timings when they start and end at
    # exactly the same time. By using a set, we do not repeat ranges.
    final = set()

    # sort ranges into a copy list
    _ranges = sorted(ranges, key=lambda x: x[0])

    if DEBUG:
        print "DEBUG: collapse_ranges\n\tsorted ranges = %s" % _ranges

    START = 0
    END = 1

    # smallest range
    base = _ranges[0]
    for _range in _ranges[1:]:

        # range is 0: we skip it.
        if _range[0] == _range[1]:
            continue

        # ranges overlap -- extend the base
        if _range[START] <= base[END]:
            base[END] = max(base[END], _range[END])
        else:

            # ranges don't overlap -- move base to final, and current _range
            # becomes the new base
            final.add(tuple(base))
            base = _range

    # termination: push last base to final
    final.add(tuple(base))

    if DEBUG:
        print "DEBUG: collapse_ranges\n\tcollapsed ranges = %s" % final

    # Return final as list of list in case a mutable type is needed.
    return [list(b) for b in final]


# -----------------------------------------------------------------------------
def subtract_ranges(bases, rangs):
    '''
    Input:  [[%f,%f],[%f,%f],[%f,%f],...], [[%f,%f],[%f,%f],[%f,%f],...]
    Output: [[%f,%f], [%f,%f], ...]

    Given be two sets one of bases and one of ranges, both represented as sets
    of pairs of floats [start, end] with 'start <= end', this function
    calculates the overlapping of each range on each base. When a range totally
    or partially overlaps with a base, the overlap is subtracted from the base.
    The resulting set of bases is returned.
    '''

    final = set()
    bases = sorted([list(b) for b in bases], key=lambda x: x[0])   # Tw
    rangs = sorted([list(b) for b in rangs], key=lambda x: x[0])   # Te

    if DEBUG:
        print "DEBUG: subtract_ranges\n\tsorted bases = %s" % bases
        print "DEBUG: subtract_ranges\n\tsorted ranges = %s" % rangs

    while bases:
        base = bases[0]
        while rangs:
            rang = rangs[0]

            # Possible overlapping from the left side. We still do not know
            # whether R1 ends within the base.
            if rang[1] > base[0]:

                # Possible overlapping from the right side. We now know there is
                # an overlapping but we don't know whether partial, partial
                # including either B0 or B1, or total including both B0 and B1.
                if rang[0] < base[1]:

                    # The overlapping includes B0 and moves to the right of an
                    # unknown amount.
                    if rang[0] <= base[0]:

                        # total overlapping with both B0 and B1 included. All
                        # the base goes.
                        if rang[1] >= base[1]:
                            del bases[0]
                            break

                        # rang[1] < base[1]. Partial overlapping of the left
                        # side of the base. The rest might overlap with other
                        # ranges on the right. We add that portion of the base
                        # to the other bases to be be checked.
                        else:
                            del bases[0]
                            bases.insert(0, [rang[1], base[1]])
                            del rangs[0]
                            break

                    # rang[0] > base[0]. The overlapping does not include B0. It
                    # can still include B1 or not. We now know that a portion of
                    # the base on the left does not overlap with any range.
                    else:
                        final.add(tuple([base[0], rang[0]]))

                        # From R0 onwards the rest of the base fully overlaps
                        # with the range. We through it away.
                        if rang[1] >= base[1]:
                            del bases[0]
                            del rangs[0]
                            break

                        # rang[1] < base[1]. Partial overlap within the base. We
                        # add the remaining portion of the base at the right of
                        # the range for future checks.
                        else:
                            del bases[0]
                            bases.insert(0, [rang[1], base[1]])
                            break

                # rang[0] > base[1]: No overlapping as R0 ends after the end of
                # the base and therefore so does also R1. The base is therefore
                # at the left of every range and has no overlapping.
                else:
                    final.add(tuple(base))
                    del bases[0]
                    break

            # rang[1] <= base[0]: No overlapping of the range on the left side.
            # Delete range as no other bases can be more to the left than the
            # current one (they are sorted).
            else:
                del rangs[0]
                break

        # Terminate when there are no more ranges to compare for subtraction.
        if not rangs:
            for b in bases:
                final.add(tuple(b))
            bases = []

    if DEBUG:
        print "DEBUG: subtract_ranges\n\tremaining bases = %s" % final

    # Return final as list of list in case a mutable type is needed.
    return [list(b) for b in final]


# -----------------------------------------------------------------------------
def get_ranges(s_entities, s_state_name, e_entities, e_state_name, host, log):
    '''
    timings
    -------
    type: {'name': {'ntasks': {'host': [int, int, int, ...]}}}
    '''
    total = 0
    overlaps = []
    for seid in log[s_entities].keys():
        for eeid in log[e_entities].keys():
            if (log[s_entities][seid]['host'] == host and
                log[e_entities][eeid]['host'] == host):

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

    ranges = collapse_ranges(overlaps)

    if DEBUG:
        print "DEBUG: get_ranges"
        print "\tstart entities: %s;" % s_entities
        print "\tstart state name: %s;" % s_state_name
        print "\tend entities: %s;" % e_entities
        print "\tend state name: %s;" % e_state_name
        print "\thost: %s;" % host
        print "\tranges: %s" % ranges

    # Calculate the total range by summing adjacent ranges. For example, if 66
    # workers with 16 cores each executed a total of 1055 tasks and the max
    # amount of scheduled blocks (with 1 worker for 1 block) is 20, we will have
    # at least 4 adjacent ranges but possibly more depending on the time spent
    # by each block in the LRMS queue. The total range will be then the sum of
    # the ranges, without counting the time between each block that, in the case
    # of this example, is spent waiting for the blocks and their workers to come
    # online. This time is therefore accounted for in Tq.
    for r in ranges:
        total += r[1] - r[0]

    return {'total': total, 'ranges': ranges}


# -----------------------------------------------------------------------------
def get_overlap(log, s_entities, seid, s_state_name, e_entities, eeid, e_state_name):
    overlap = None
    start = log[s_entities][seid]['states'][s_state_name]
    end = log[e_entities][eeid]['states'][e_state_name]

    if DEBUG:
        print "DEBUG: get_overlap"
        print "\tstart '%s' = %s;" % (s_state_name, start)
        print "\tend '%s' = %s;" % (e_state_name, end)

    # Swift fails to log some of the stage_in time stamps. When the task has
    # executed successfully, i.e. the end state is present, we use the time
    # stamp of the nearest adjacent state, i.e. 'active' instead of 'stage_in'.
    # This heuristic should be revised for data intensive experiments.
    if not start and end:
        if s_state_name == 'stage_in':
            s_state_name = 'active'
            start = log[s_entities][seid]['states']['active']
    if start and not end:
        if start:
            if e_state_name == 'stage_in':
                e_state_name = 'active'
                end = log[e_entities][eeid]['states']['active']
    if start and end:
        overlap = [start, end]
    else:
        print "WARNING: get_overlap undefined entities"
        print "\tEntity '%s' state '%s' is %s" % (seid, s_state_name, start)
        print "\tEntity '%s' state '%s' is %s" % (eeid, e_state_name, end)

    return overlap


# -----------------------------------------------------------------------------
def get_range(entity, start_state_name, end_state_name, host, log):
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
def write_timings_csv(elements, names):

    entries = {}
    mnames = []
    scales = []

    for name, ntasks in elements.iteritems():
        for ntask, hosts in ntasks.iteritems():
            if ntask not in scales:
                scales.append(ntask)
            for host, measurements in hosts.iteritems():
                mname = "%s-%s-%s" % (name, names[name], host)
                if mname not in mnames:
                    mnames.append(mname)
                if mname not in entries.keys():
                    entries[mname] = {}
                if ntask not in entries[mname].keys():
                    entries[mname][ntask] = []
                for measurement in measurements:
                    entries[mname][ntask].append(measurement)

    keys = sorted(scales)

    for nm in mnames:
        with open(nm+'.csv', "wb") as outfile:
            writer = csv.writer(outfile)
            writer.writerow(keys)
            writer.writerows(zip(*[entries[nm][key] for key in keys]))


# -----------------------------------------------------------------------------
def aggregate_timings(elements, ranges):
    '''
    timings
    --------
    type:    {'name': {'ntasks': {'host': [int, ...], host: [int, ...], ...}}}
    example: {'Pw': {'2048' : {'stampede': [66], 'gordon': [63]}}}

    ranges
    ------
    type:    {'name': {'ntasks': {'host': set([(flt, flt),...], ...]), ...}}}
    example: {'Tw': {2048: {u'stampede': set([(1453969835, 1453984281)]),
                            u'gordon': set([(1453969835, 1453973305)])}}}
    '''
    if DEBUG:
        print "\n"
        print '-'*79
        print "aggregate_timings"
        print '-'*79

    # Aggregated hosts tag.
    for name, ntasks in elements.iteritems():
        for ntask, hosts in ntasks.iteritems():

            # With less than two hosts there is nothing to aggregate.
            if len(hosts) <= 1:
                return elements
            hostnames = ''
            for host in hosts:
                if hostnames == '':
                    hostnames = host
                else:
                    hostnames = hostnames+'_'+host

            # Add aggregated hostname to the the host list..
            if hostnames not in elements[name][ntask].keys():
                elements[name][ntask][hostnames] = []

    # Aggregate ranges.
    for name, ntasks in elements.iteritems():
        if name != 'TTC':
            for ntask, hosts in ntasks.iteritems():
                for host, measurements in hosts.iteritems():
                    if host != hostnames:

                        # Initialize the list of aggregated values for the aggregated hosts.
                        if len(elements[name][ntask][hostnames]) < len(measurements):
                            elements[name][ntask][hostnames] = [[]]*len(measurements)

                        for idx, measurement in enumerate(measurements):
                            if len(elements[name][ntask][hostnames][idx]) <= idx:
                                elements[name][ntask][hostnames][idx].append(ranges[name][ntask][host][idx])
                            else:
                                for _range in ranges[name][ntask][host][idx]:
                                    elements[name][ntask][hostnames][idx][idx].append(_range)

    if DEBUG:
        print "\nAggregate"
        pprint.pprint(elements)

    # Collapse ranges of the same type of timing across hosts.
    for name, ntasks in elements.iteritems():
        if name != 'TTC':
            for ntask in ntasks.keys():
                for idx, measurement in enumerate(elements[name][ntask][hostnames]):
                    elements[name][ntask][hostnames][idx] = collapse_ranges(measurement[idx])

    if DEBUG:
        print "\nCollapse"
        pprint.pprint(elements)

    # Subtract ranges of the target timing from those of the other timings. This
    # gives us the time ranges during which the system was not performing a
    # target operation. For example, consider an experiment measuring the
    # execution of a bag of tasks. All the time spent not executing tasks can be
    # considered an overhead. We therefore calculate all the time ranges in
    # which the system was not executing tasks (our target operation) by
    # subtracting the time ranges in which the system was executing tasks from
    # all the other time ranges we measured. The target operation can be
    # changed, for example measuring the time the system has spent staging data.
    for ntask in elements['Tw'].keys():
        for idx, measurement in enumerate(elements['Tw'][ntask][hostnames]):
                    tw = elements['Tw'][ntask][hostnames][idx]
                    te = elements['Te'][ntask][hostnames][idx]
                    elements['Tw'][ntask][hostnames][idx] = subtract_ranges(tw, te)

    if DEBUG:
        print "\nSubtract"
        pprint.pprint(elements)

    # Sum each time range for the same type of timing across hosts.
    for name, ntasks in elements.iteritems():
        if name != 'TTC':
            for ntask, hosts in ntasks.iteritems():
                for idx, measurement in enumerate(elements[name][ntask][hostnames]):
                    partial = 0
                    for _range in measurement:
                        partial += _range[1] - _range[0]
                    elements[name][ntask][hostnames][idx] = partial

    if DEBUG:
        print "\nSum"
        pprint.pprint(elements)

    # TTC is recorded from session, not by aggregation. In
    # this way we can control that the sum of the other
    # timings is consistent with the directly observed TTC.
    # if name == 'TTC':
    #     elements[name][ntask][hostnames][idx] = elements[name][ntask][host][idx]
    for name, ntasks in elements.iteritems():
        if name == 'TTC':
            for ntask, hosts in ntasks.iteritems():
                for host, measurements in hosts.iteritems():
                    for idx, measurement in enumerate(elements[name][ntask][hostnames]):
                        elements[name][ntask][hostnames][idx] = elements[name][ntask][host][idx]

    if DEBUG:
        print "\nAdd TTC"
    return elements


# -----------------------------------------------------------------------------
if __name__ == '__main__':
    '''
    TODO:
    - Calculate the ideal Te by fetching the workload properties.
    '''
    timing = None
    if len(sys.argv) <= 1:
        usage("insufficient arguments -- need dir of JSON files")

    if len(sys.argv) > 3:
        usage("too many arguments -- no more than 2")

    if len(sys.argv) > 2:
        timing = sys.argv[2]

    # The label and descriptive name for each property and timing we measure for
    # each experiment. We use these both for brevity and as mnemonic device when
    # sharing our measurements.
    names = {'TTC': 'Time_to_completion', 'Tss': 'Setting_up'          ,
             'Tse': 'Executing_job'     , 'Tw' : 'Submitting_task'     ,
             'Te' : 'Executing_task'    , 'Tsi': 'Staging_in_task'     ,
             'Tso': 'Staging_out_task'  , 'Tq' : 'Queuing_block'       ,
             'Ta' : 'Executing_block'   , 'Tb' : 'Bootstrapping_worker',
             'Twe': 'Executing_worker'}

    # Make a list of the JSON files in the given directory.
    inputs = [f for f in os.listdir(sys.argv[1])
              if os.path.isfile(os.path.join(sys.argv[1], f)) and '.json' in f]
    if DEBUG:
        print "DEBUG: Selected input files = %s" % inputs

    # Name of the timing, number of tasks of the experiment, and hosts on which
    # each experiment has been run. Note: this is used also for experiments with
    # a single host. {'name': {'ntasks': {'host': [int, int, int, ...]}}}
    timings = {}

    # We store the ranges of the timings we calculate for each host. We then sum
    # them instead of collapsing them so to avoid counting the time spent
    # waiting between one timing and the other.
    ranges = {}

    # The timings we want to measure.
    enabled = ['TTC', 'Te', 'Tw']

    # Read through all the JSON file in the given directory. One JSON file for
    # each experiment.
    for f in inputs:
        with open(f) as jdata:
            slog = json.load(jdata)

        # Get the size of the workload.
        ntask = slog['Session']['tasks_completed']

        # Get the host(s) on which the workload has been executed.
        hosts = slog['Session']['hosts']

        # Derive the timings of each experiment.
        for tname in names.keys():
            if tname in enabled:
                for host in hosts:
                    if tname not in timings.keys():
                        timings[tname] = {}
                    if tname not in ranges.keys():
                        ranges[tname] = {}
                    if ntask not in timings[tname].keys():
                        timings[tname][ntask] = {}
                    if ntask not in ranges[tname].keys():
                        ranges[tname][ntask] = {}
                    if host not in timings[tname][ntask].keys():
                        timings[tname][ntask][host] = []
                    if host not in ranges[tname][ntask].keys():
                        ranges[tname][ntask][host] = []

                    if tname == 'TTC':
                        TTC = get_range('Session', 'start', 'finish', host, slog)
                        timings[tname][ntask][host].append(TTC)
                        # ranges[tname][ntask][host].append([[TTC, TTC]])
                        ranges[tname][ntask][host] = TTC

                    # if tname == 'Tss':
                    #     Tss = get_ranges('Jobs', 'init', 'Jobs', 'task', host, slog)
                    #     timings[tname][ntask][host].append(Tss['total'])
                    #     ranges[tname][ntask][host] = Tss['ranges']

                    # if tname == 'Tse':
                    #     Tse = get_ranges('Jobs', 'task', 'Jobs', 'end', host, slog)
                    #     timings[tname][ntask][host].append(Tse['total'])
                    #     ranges[tname][ntask][host] = Tse['ranges']

                    if tname == 'Tw':
                        Tw = get_ranges('Jobs', 'task', 'Tasks', 'stage_in', host, slog)
                        timings[tname][ntask][host].append(Tw['total'])
                        ranges[tname][ntask][host].append(Tw['ranges'])

                    if tname == 'Te':
                        Te = get_ranges('Tasks', 'stage_in', 'Tasks', 'completed', host, slog)
                        timings[tname][ntask][host].append(Te['total'])
                        ranges[tname][ntask][host].append(Te['ranges'])

                    # if tname == 'Tsi':
                    #     Tsi = get_ranges('Tasks', 'stage_in', 'Tasks', 'active', host, slog)
                    #     timings[tname][ntask][host].append(Tsi['total'])
                    #     ranges[tname][ntask][host] = Tsi['ranges']

                    # if tname == 'Tso':
                    #     Tso = get_ranges('Tasks', 'stage_out', 'Tasks', 'completed', host, slog)
                    #     timings[tname][ntask][host].append(Tso['total'])
                    #     ranges[tname][ntask][host] = Tso['ranges']

                    # if tname == 'Tq':
                    #     Tq = get_ranges('Blocks', 'requested', 'Blocks', 'active', host, slog)
                    #     timings[tname][ntask][host].append(Tq['total'])
                    #     ranges[tname][ntask][host] = Tq['ranges']

                    # if tname == 'Ta':
                    #     Ta = get_ranges('Blocks', 'active', 'Blocks', 'done', host, slog)
                    #     timings[tname][ntask][host].append(Ta['total'])
                    #     ranges[tname][ntask][host] = Ta['ranges']

                    # if tname == 'Tb':
                    #     Tb = get_ranges('Blocks', 'active', 'Workers', 'active', host, slog)
                    #     timings[tname][ntask][host].append(Tb['total'])
                    #     ranges[tname][ntask][host] = Tb['ranges']

                    # if tname == 'Twe':
                    #     Twe = get_ranges('Workers', 'active', 'Workers', 'shutdown', host, slog)
                    #     timings[tname][ntask][host].append(Twe['total'])
                    #     ranges[tname][ntask][host] = Twe['ranges']

    aggregate_timings(timings, ranges)
    write_timings_csv(timings, names)

    if DEBUG:
        print "\nDEBUG: Timings"
        pprint.pprint(timings)
