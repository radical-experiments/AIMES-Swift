#!/usr/bin/env python
"""Extracts timings from the given Swift log.
"""

import os
import sys
import json

__author__ = "Matteo Turilli"
__copyright__ = "Copyright 2015, The AIMES Project"
__license__ = "MIT"


# -----------------------------------------------------------------------------
def usage(msg=None, noexit=False):

    if msg:
        print "\n      Error: %s" % msg

    print """
    usage   : %s <swift-log-file> [<timing>]
    example : %s swift.1449746828531345000.log [TTC]

    arguments
        <swift-log-file>: Log file as produced by the AIMES Swift connector
        [<timing>]      : optional -- type of timing

    The tool extracts timings from the given Swift log file. By default, the
    tool output all the available timings. If a timing is specified, only that
    timing is outputed. Valid timings are:

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
        usage("insufficient arguments -- need log file")

    if len(sys.argv) > 3:
        usage("too many arguments -- no more than 2")

    if len(sys.argv) > 2:
        timing = sys.argv[2]

    # Load timings from Swift log file
    with open(sys.argv[1]) as json_data:
        slog = json.load(json_data)

    timings['TTC'] = slog["Run"]["Finish"] - slog["Run"]["Start"]

    ts = ["%s:%s" % (k, v) for k, v in timings.iteritems()]
    out = ",".join(str(e) for e in ts)

    print out
