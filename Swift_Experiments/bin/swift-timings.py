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
    usage   : %s <dir> [<timing>]
    example : %s durations.json [TTC]

    arguments
        <dir>      : Directory with the JSON files produced by swift-timings.py
        [<timing>] : optional -- type of timing (**not implemented yet**)

    The tool extracts timings from the Swift durations files in the given
    directory. By default, the tool output all the available timings. If a
    timing is specified, only that timing is outputted.
    """ % (sys.argv[0], sys.argv[0])

    if msg:
        sys.exit(1)

    if not noexit:
        sys.exit(0)


# -----------------------------------------------------------------------------
def collapse_ranges(ranges):
    '''
    Input:  [[%f,%f],[%f,%f],[%f,%f], ...]
    Output: ((%f,%f), (%f,%f), ...)

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
    return final


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

    1. Ranges must be unique as ranges with same start and end precisely
       collapse one on another. By using a set, we guarantee the uniqueness of
       each range.
    2. sort ranges into a copy list. Transform immutable tuples to mutable lists
       when needed. Ranges and every range can be immutable as we do not alter
       them.
    3. While there are bases, loop on the ranges to subtract from the bases
       their overlaps.
    4. When the range ends after the base there is some overlapping. Overlap can
       be: (i) partial on the side of the base end; (iii) partial within the
       base start; (iv) and total.
    5. When the range starts within the duration of the base, there is an
       overlap. Overlap can be: (ii) partial on the side of the base start;
       (iii) partial within the base start and end; (iv) total.
    6. When the overlap is partial on the side of the base start: (i.i) the
       range ends before the base
    7. Total overlapping = total subtraction. Move to the next comparison.
    8. Partial overlap, new base = remainder subtraction range from base. Drop
       the range as there will be no more overlap (sorted bases).
    9. When the range ends within the duration of the base, The portion between
       the start of the base and the start of the range is added to final
       because there cannot be other ranges overlapping with that portion of the
       base (bases and ranges are sorted).
    10. Total overlapping for the rest of the base. Delete current base and move
        to the next one.
    11. Partial overlap, new base = remainder subtraction range from base.
    12. When the range starts from the end or after the end of the base, the
        base is added to final because there cannot be any overlapping, i.e.,
        ranges and bases are sorted. rang[0] >= base[1]:
    13. When the range ends before the base there is nothing to subtract from
        the base. Drop the range, the bases are sorted so there cannot be any
        base before the current one. We add bases but only beyond the current
        base start. rang[1] <= bases[0]
    14. Terminate when no more range are left, add all the remaining bases.
    '''

    final = set()
    bases = sorted([list(b) for b in bases], key=lambda x: x[0])   # Tw
    rangs = sorted([list(b) for b in rangs], key=lambda x: x[0])   # Te

    print "DEBUG sorted bases: bases %s" % bases
    print "DEBUG sorted rangs: rangs %s\n" % rangs

    while bases:
        base = bases[0]
        print "\n\n-----------------------------------------------------------"
        print "DEBUG while bases: base %s" % base

        while rangs:
            rang = rangs[0]
            print "DEBUG while rangs: rang %s\n" % rang

            if rang[1] > base[0]:
                if rang[0] < base[1]:
                    if rang[0] <= base[0]:
                        if rang[1] >= base[1]:
                            del bases[0]
                            print "DEBUG: if rang[1] >= base[1]: bases %s\n" % bases
                            break

                        else:
                            del bases[0]
                            bases.insert(0, [rang[1], base[1]])
                            del rangs[0]
                            print "DEBUG: if rang[1] < base[1]: bases %s; rangs %s\n" % (bases, rangs)
                            break

                    else:

                        final.add(tuple([base[0], rang[0]]))
                        print "DEBUG: if rang[1] >= base[1]: final 1 %s" % final

                        if rang[1] >= base[1]:
                            del bases[0]
                            del rangs[0]
                            print "DEBUG: if rang[1] >= base[1]: bases %s; rangs %s\n" % (bases, rangs)
                            break

                        else:
                            del bases[0]
                            bases.insert(0, [rang[1], base[1]])
                            print "DEBUG: if rang[1] < base[1]: bases %s\n" % bases
                            break

                else:
                    final.add(tuple(base))
                    del bases[0]
                    print "DEBUG: if rang[0] < base[1]: final 2 %s; bases %s\n" % (final, bases)
                    break

            else:
                del rangs[0]
                print "DEBUG: if rang[1] < bases[0]: rangs %s\n" % rangs
                break

        if not rangs:
            for b in bases:
                final.add(tuple(b))
            bases = []
            print "DEBUG: while rangs: final 3 %s" % final
            print "DEBUG: while rangs: bases %s" % bases
            print "DEBUG: while rangs: rangs %s\n" % rangs

    return final


# -----------------------------------------------------------------------------
def get_ranges(s_entities, s_state_name, e_entities, e_state_name, host, log):
    # timings = {'name': {'ntasks': {'host|total': [int, int, int, ...]}}}
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
        print "DEBUG: get_ranges\n\tstart entities: %s;\n\tstart state name: %s;\n\tend entities: %s;\n\tend state name: %s;\n\thost: %s;\n\tranges: %s" % \
            (s_entities, s_state_name, e_entities, e_state_name, host, ranges)

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

    # Swift fails to log some of the stage_in time stamps. When the task has
    # executed successfully, i.e. the end state is present, we use the time
    # stamp of the nearest adjacent state, i.e. 'active' instead of 'stage_in'.
    # This heuristic should be revised for data intensive experiments.
    if not start and end:
        if s_state_name == 'stage_in':
            s_state_name = 'active'
            start = log[s_entities][seid]['states']['active']
    if start and not end:
        if e_state_name == 'stage_in':
            e_state_name == 'active'
            end = log[e_entities][eeid]['states']['active']

    if start and end:
        overlap = [start, end]
    else:
        if DEBUG:
            sw = "\n\tEntity '%s' state '%s' is %s" % (seid, s_state_name, start)
            ew = "\n\tEntity '%s' state '%s' is %s" % (eeid, e_state_name, end)
            print "\nDEBUG: undefined entities %s%s" % (sw, ew)
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
def csv_append_property(prop, host, properties, store):

    # TODO: Rewrite assuming we have each property for each host used by the
    # experiment.

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
def nentities_per_host(entities, host, slog):
    nentities = 0
    for eid in slog[entities].keys():
        if slog[entities][eid]['host'] == host:
            nentities += 1
    return nentities


# -----------------------------------------------------------------------------
def nentities_per_entity_per_host(entities, entity, host, slog):
    nentity = 0.0
    for eid in slog[entity].keys():
        if slog[entity][eid]['host'] == host:
            nentity += len(slog[entity][eid][entities])
    return float(nentity)/float(len(slog[entity].keys()))


# -----------------------------------------------------------------------------
def aggregate(elements, aggregates, ranges):
    # {'name': {'ntasks': {'host|total': [int, int, int, ...]}}}
    # {'Pw': {'2048' : {'stampede': [66], 'gordon': [63]}}}

    print "\nDEBUG: measures %s" % elements
    print "DEBUG: ranges %s" % ranges
    print "DEBUG: aggregates %s" % aggregates

    for element in elements:
        for measure, values in element.iteritems():
            print "\nmeasure %s" % measure
            print "\tvalues %s" % values
            if measure not in aggregates.keys():
                aggregates[measure] = {}

            for size, hosts in values.iteritems():
                print "\tsize %s" % size
                print "\thosts %s" % hosts
                if size not in aggregates[measure].keys():
                    aggregates[measure][size] = []
                partial = 0.0
                partials = []

                for host, measurements in hosts.iteritems():
                    print "\thost %s" % host
                    print "\tmeasurements %s" % measurements

                    for measurement in measurements:
                        print "\tmeasurement %s" % measurement

                        if measure == 'Ptw':
                            partial += measurement/float(len(hosts.keys()))
                            print "\tpartial %s" % partial

                        if measure in ['Pb', 'Pw', 'Pt']:
                            partial += measurement
                            print "\tpartial %s" % partial

                        if measure == 'TTC':
                            partial = ranges[measure][size][host]

                        if measure in ['Tss', 'Tse', 'Tw', 'Te', 'Tsi', 'Tso', 'Tq', 'Ta', 'Tb', 'Twe']:
                            for _range in ranges[measure][size][host]:
                                partials.append([r for r in _range])

                if partials:
                    for r in collapse_ranges(partials):
                        partial += r[1] - r[0]
                    print "\tpartial %s" % partial

                aggregates[measure][size].append(partial)
                print "\taggregates %s" % aggregates
    return aggregates

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
    pnames = {'Pb' : 'Blocks_per_exp'  , 'Pt' : 'Tasks_per_host',
              'Pw' : 'Workers_per_exp' , 'Ptw': 'Tasks_per_worker'}

    tnames = {'TTC': 'TTC'             , 'Tss': 'Setting_up'          ,
              'Tse': 'Executing_job'   , 'Tw' : 'Submitting_task'     ,
              'Te' : 'Executing_task'  , 'Tsi': 'Staging_in_task'     ,
              'Tso': 'Staging_out_task', 'Tq' : 'Queuing_block'       ,
              'Ta' : 'Executing_block' , 'Tb' : 'Bootstrapping_worker',
              'Twe': 'Executing_worker'}

    # Make a list of the JSON files in the given directory.
    inputs = [f for f in os.listdir(sys.argv[1])
              if os.path.isfile(os.path.join(sys.argv[1], f)) and '.json' in f]
    if DEBUG:
        print "DEBUG: Selected input files = %s" % inputs

    # We collect properties and timings we measure for each experiment in two
    # data structures. Measurements are organized by name of the property,
    # number of tasks of the experiment, and hosts on which each experiment has
    # been run. Note: this works also for experiments with a single host.
    # properties = {'name': {'ntasks': {'host': [int, int, int, ...]}}}
    properties = {}
    # timings = {'name': {'ntasks': {'host': [int, int, int, ...]}}}
    timings = {}

    # We want the aggregated value for some measurements. We create a data
    # structure as those for properties and timings but without the host
    # parameters. A dedicated function is used to aggregate the properties and
    # timings we need.
    # aggregates = {'name': {'ntasks': [int, int, int, ...]}}}
    aggregates  = {}

    # We store the ranges of the timings we calculate for each host. We then sum
    # them instead of collapsing them so to avoid counting the time spent
    # waiting between one timing and the other.
    ranges = {}

    # Read through all the JSON file in the given directory. One JSON file for
    # each experiment.
    for f in inputs:
        with open(f) as jdata:
            slog = json.load(jdata)

        # Get the size of the workload.
        ntask = slog['Session']['tasks_completed']

        # Get the host(s) on which the workload has been executed.
        hosts = slog['Session']['hosts']

        # Derive the properties of each experiment. Note: Due to how information
        # is extracted from Swift logs, a host is recorded for a block only when
        # at least a task has been run by its worker(s). We can extract only
        # Workers per host, not blocks per host.
        for pname in pnames.keys():
            properties[pname] = {}
            properties[pname][ntask] = {}

            for host in hosts:
                properties[pname][ntask][host] = []

                if pname == 'Pb':
                    Pb = nentities_per_host('Blocks', host, slog)
                    properties[pname][ntask][host].append(Pb)

                if pname == 'Pw':
                    Pw = nentities_per_host('Workers', host, slog)
                    properties[pname][ntask][host].append(Pw)

                if pname == 'Pt':
                    Pt = nentities_per_host('Tasks', host, slog)
                    properties[pname][ntask][host].append(Pt)

                if pname == 'Ptw':
                    Ptw = nentities_per_entity_per_host('tasks', 'Workers', host, slog)
                    properties[pname][ntask][host].append(Ptw)

                # if pname == 'Pbr':
                #     Pbr = get_blocks_per_host(slog)
                #     store_property(Pbr, pnames[pname], ntask, outputs)
                #     csv_append_property(outputs, properties, pnames[pname])

        # Derive the timings of each experiment.
        for tname in tnames.keys():
            timings[tname] = {}
            ranges[tname] = {}
            timings[tname][ntask] = {}
            ranges[tname][ntask] = {}

            for host in hosts:
                timings[tname][ntask][host] = []
                ranges[tname][ntask][host] = None

                if tname == 'TTC':
                    TTC = get_range('Session', 'start', 'finish', host, slog)
                    timings[tname][ntask][host].append(TTC)
                    ranges[tname][ntask][host] = TTC

                if tname == 'Tss':
                    Tss = get_ranges('Jobs', 'init', 'Jobs', 'task', host, slog)
                    timings[tname][ntask][host].append(Tss['total'])
                    ranges[tname][ntask][host] = Tss['ranges']

                if tname == 'Tse':
                    Tse = get_ranges('Jobs', 'task', 'Jobs', 'end', host, slog)
                    timings[tname][ntask][host].append(Tse['total'])
                    ranges[tname][ntask][host] = Tse['ranges']

                if tname == 'Tw':
                    Tw = get_ranges('Jobs', 'task', 'Tasks', 'stage_in', host, slog)
                    timings[tname][ntask][host].append(Tw['total'])
                    ranges[tname][ntask][host] = Tw['ranges']

                if tname == 'Te':
                    Te = get_ranges('Tasks', 'stage_in', 'Tasks', 'completed', host, slog)
                    timings[tname][ntask][host].append(Te['total'])
                    ranges[tname][ntask][host] = Te['ranges']

                if tname == 'Tsi':
                    Tsi = get_ranges('Tasks', 'stage_in', 'Tasks', 'active', host, slog)
                    timings[tname][ntask][host].append(Tsi['total'])
                    ranges[tname][ntask][host] = Tsi['ranges']

                if tname == 'Tso':
                    Tso = get_ranges('Tasks', 'stage_out', 'Tasks', 'completed', host, slog)
                    timings[tname][ntask][host].append(Tso['total'])
                    ranges[tname][ntask][host] = Tso['ranges']

                if tname == 'Tq':
                    Tq = get_ranges('Blocks', 'requested', 'Blocks', 'active', host, slog)
                    timings[tname][ntask][host].append(Tq['total'])
                    ranges[tname][ntask][host] = Tq['ranges']

                if tname == 'Ta':
                    Ta = get_ranges('Blocks', 'active', 'Blocks', 'done', host, slog)
                    timings[tname][ntask][host].append(Ta['total'])
                    ranges[tname][ntask][host] = Ta['ranges']

                if tname == 'Tb':
                    Tb = get_ranges('Blocks', 'active', 'Workers', 'active', host, slog)
                    timings[tname][ntask][host].append(Tb['total'])
                    ranges[tname][ntask][host] = Tb['ranges']

                if tname == 'Twe':
                    Twe = get_ranges('Workers', 'active', 'Workers', 'shutdown', host, slog)
                    timings[tname][ntask][host].append(Twe['total'])
                    ranges[tname][ntask][host] = Twe['ranges']

    aggregates = aggregate([properties, timings], aggregates, ranges)

    if DEBUG:
        print "\nDEBUG: Properties"
        pprint.pprint(properties)
        print "\nDEBUG: Timings"
        pprint.pprint(timings)
        print "\nDEBUG: Aggregates"
        pprint.pprint(aggregates)
