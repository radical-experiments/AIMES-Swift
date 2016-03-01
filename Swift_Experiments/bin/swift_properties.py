"""
Extracts timings from the given Swift log JSON files. File created with
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

DEBUG = False


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
def write_run_report(slog, session, f):
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


# -----------------------------------------------------------------------------
def write_properties_csv(elements, names):
    # {'Pb' : {2048: {u'stampede': [66],                u'gordon': [63]}},
    #  'Ptw': {2048: {u'stampede': [8.178294573643411], u'gordon': [7.69]}}

    entries = {}
    mnames = []
    ntasks = []

    print elements
    print names

    for name, scales in elements.iteritems():
        for scale, hosts in scales.iteritems():
            if scale not in ntasks:
                ntasks.append(scale)
            for host, measurements in hosts.iteritems():
                mname = "%s-%s-%s" % (name, names[name], host)
                if mname not in mnames:
                    mnames.append(mname)
                if mname not in entries.keys():
                    entries[mname] = {}
                if scale not in entries[mname].keys():
                    entries[mname][scale] = []
                for measurement in measurements:
                    entries[mname][scale].append(measurement)

    keys = sorted(ntasks)

    for nm in mnames:
        with open(nm+'.csv', "wb") as outfile:
            writer = csv.writer(outfile)
            writer.writerow(keys)
            writer.writerows(zip(*[entries[nm][key] for key in keys]))


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
def aggregate_properties(elements):
    '''
    elements
    --------
    type:    {'names': {'ntasks': {'hosts': [int, ...], host: [int, ...], ...}}}
    example: {'Pw': {'2048' : {'stampede': [66], 'gordon': [63]}}}
    '''

    for name, ntasks in elements.iteritems():
        for ntask, hosts in ntasks.iteritems():
            hostnames = ''
            for host in hosts:
                if hostnames == '':
                    hostnames = host
                else:
                    hostnames = hostnames+'_'+host
            if hostnames not in elements[name][ntask].keys():
                elements[name][ntask][hostnames] = [0.0]*len(elements.keys())
                print elements[name][ntask][hostnames]
            for host, measurements in hosts.iteritems():
                for idx, measurement in enumerate(measurements):
                    if name == 'Ptw':
                        elements[name][ntask][hostnames][idx] += measurement/float(len(hosts.keys()))
                    if name in ['Pb', 'Pw', 'Pt']:
                        elements[name][ntask][hostnames][idx] += measurement

    return elements


# -----------------------------------------------------------------------------
if __name__ == '__main__':
    '''
    TODO:
    - Calculate the ideal Te by fetching the workload properties.
    '''

    if len(sys.argv) <= 1:
        usage("insufficient arguments -- need dir of JSON files")

    if len(sys.argv) > 3:
        usage("too many arguments -- no more than 2")

    if len(sys.argv) > 2:
        timing = sys.argv[2]

    names = {'Pb' : 'Blocks_per_exp'  , 'Pt' : 'Tasks_per_host',
             'Pw' : 'Workers_per_exp' , 'Ptw': 'Tasks_per_worker'}

    inputs = [f for f in os.listdir(sys.argv[1])
              if os.path.isfile(os.path.join(sys.argv[1], f)) and '.json' in f]
    if DEBUG:
        print "DEBUG: Selected input files = %s" % inputs

    # {'name': {'ntasks': {'host': [int, int, int, ...]}}}
    properties = {}

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
        for pname in names.keys():
            if pname not in properties.keys():
                properties[pname] = {}
            if ntask not in properties[pname].keys():
                properties[pname][ntask] = {}

            for host in hosts:
                if host not in properties[pname][ntask].keys():
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

    aggregate_properties(properties)
    write_properties_csv(properties, names)

    if DEBUG:
        print "\nDEBUG: Properties"
        pprint.pprint(properties)
