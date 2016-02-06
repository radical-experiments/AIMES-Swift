#!/usr/bin/env python

import os
import json
import pickle
import sys
import datetime
from datetime import datetime

filename = sys.argv[1]

f = open(filename, 'r');
data = f.readlines()

start = data[0]
end   = data[1]
tasks = data[2]


t0 = datetime.strptime(start[0:20], "%Y-%m-%d %H:%M:%S,")
tn = datetime.strptime(end[0:20], "%Y-%m-%d %H:%M:%S,")
ntasks = tasks.split(':')[-1].strip().strip(',')

delta = tn-t0
print "{0}, {1}".format(ntasks, delta.seconds)
