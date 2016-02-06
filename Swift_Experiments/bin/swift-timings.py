"""
Extracts timings from the given Swift log json files. File created with
swift-timings.py
"""

import os
import sys
import csv
import json

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
        <dir>      : Directory with the files produced by swift-timings.py
        [<timing>] : optional -- type of timing

    The tool extracts timings from the Swift durations files in the given
    directory. By default, the tool output all the available timings. If a
    timing is specified, only that timing is outputed.

    Current timings are:
        - TTC : total time to completion of the whole session.

    """ % (sys.argv[0], sys.argv[0])

    if msg:
        sys.exit(1)

    if not noexit:
        sys.exit(0)


# -----------------------------------------------------------------------------
#
if __name__ == '__main__':

    timing = None
    timings = {}

    if len(sys.argv) <= 1:
        usage("insufficient arguments -- need dir of json files")

    if len(sys.argv) > 3:
        usage("too many arguments -- no more than 2")

    if len(sys.argv) > 2:
        timing = sys.argv[2]

    inputs = [f for f in os.listdir(sys.argv[1]) if os.path.isfile(os.path.join(sys.argv[1], f)) and '.json' in f]
    print "DEBUG: Selected input files = %s" % inputs
    timings = ['TTC']
    outputs = {}

    for timing in timings:
        outputs[timing] = {}

    for f in inputs:
        for t in timings:
            with open(f) as jdata:
                slog = json.load(jdata)
            ntasks = slog["Session"]["completed"]
            if t == 'TTC':
                TTC = slog["Session"]["finish"] - slog["Session"]["start"]
                if ntasks not in outputs['TTC'].keys():
                    outputs['TTC'][ntasks] = []
                outputs['TTC'][ntasks].append(TTC)

                keys = sorted(outputs['TTC'].keys())
                fcsv = t+'.csv'
                with open(fcsv, "wb") as outfile:
                    writer = csv.writer(outfile)
                    writer.writerow(keys)
                    writer.writerows(zip(*[outputs['TTC'][key] for key in keys]))

    print "DEBUG: Timings = %s" % outputs

