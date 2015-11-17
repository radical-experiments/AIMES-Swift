#!/usr/bin/env python

'''description

   TODO:

       "swift": {
        "workload": {
            "duration": {
                "max": 1800,
                "min": 60,
                "avg": 900,
                "std": 300
            }
        }
'''

import sys
import random
import Queue

import radical.utils as ru

__author__ = "Matteo Turilli"
__copyright__ = "Copyright 2015, The AIMES Project"
__license__ = "MIT"


# -----------------------------------------------------------------------------
def usage(msg=None, noexit=False):

    if msg:
        print "\nError: %s" % msg

    print """
    usage   : %s experiment.json aimes.json

    """ % (sys.argv[0])

    if msg:
        sys.exit(1)

    if not noexit:
        sys.exit(0)


# -----------------------------------------------------------------------------
def run_sequence(scales, bindings, uniformities, iterations, cores):
    '''Returns a randomized sequence of experimental runs.
    '''

    sequence = list()
    rerun    = '0'

    # Create the list of run parameters.
    for scale in scales:
        for binding in bindings:
            for uniformity in uniformities:
                for iteration in iterations:
                    sequence.append([scale, binding, uniformity, iteration,
                                     rerun, cores])

    # Shuffle sequence.
    random.shuffle(sequence)

    return sequence


# -----------------------------------------------------------------------------
def mkedir(rcfg):
    '''TODO.
    '''
    pass


# -----------------------------------------------------------------------------
def wswift(template, edir):
    '''TODO.
    '''
    pass


# -----------------------------------------------------------------------------
def arest(command, acfg):
    '''TODO.
    '''
    pass


# =============================================================================
# EXPERIMENT
# =============================================================================
if __name__ == '__main__':

    # Get configuraiton file.
    if len(sys.argv) <= 2:
        usage("insufficient arguments: need experiment and AIMES config files")

    if len(sys.argv) > 3:
        usage("too many arguments -- no more than 2")

    ecfg = ru.read_json(sys.argv[1])
    acfg = ru.read_json(sys.argv[2])

    # Execution queue.
    queue = Queue.Queue()

    # Derive randomized run sequence and populate the default queue.
    for run_cfg in run_sequence(ecfg["n_tasks"],
                                ecfg["bindings"],
                                ecfg["tasks"]["duration"]["distribution"],
                                ecfg["iterations"],
                                ecfg["tasks"]["cores"]["number"]):
        queue.put(run_cfg)

    # Execute the queued runs.
    tracker = 0

    while not queue.empty():

        tracker += 1

        rcfg = queue.get()

        # Make experiment directory
        edir = mkedir(rcfg)

        # Write swift executable
        workflow = wswift(ecfg["swift_template"], edir)

        # Start AIMES REST service
        aendpoint = arest("start", acfg)

        # Execute Swift workflow
        run = "TODO"

        if run['state'] == 'FAILED' and run['rerun'] < ecfg["attempts"]:

            # reschedule once more
            run['rerun'] += 1
            queue.put(run_cfg)
