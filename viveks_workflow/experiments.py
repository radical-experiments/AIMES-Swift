#!/usr/bin/env python

import os
import sys

input_names    = 'input_shared_*.txt'
config_name    = 'experiment.json'
workload_name  = 'vivek.swift'
swift_cfg_name = 'swift.conf'
runme_name     = 'runme.sh'
makefile_name  = 'makefile'

with open('experiments.ctrl', 'r') as ctrl:

    for line in ctrl:

        line = line.strip()

        if line.startswith('#'):
            continue

        if not line:
            continue

        num, res, size = line.split()

        num        = int(num)
        size       = int(size)
        res        = int(res)
        chunk_size = 8
        n_chunks   = int(size / chunk_size)
        e_name     = 'data.%02d.%05d.%03d' % (res, size, num)

        if os.path.isdir('%s/run001' % e_name):
            print 'skip       %s' % e_name
            continue

        if os.path.isdir(e_name):
            print 'refresh    %s' % e_name
            os.system('rm -rf %s' % e_name)

        else:
            print 'create     %s' % e_name

        sed = 'sed -e "s/###size###/%s/g; s/###chunk_size###/%s/g; s/###n_chunks###/%s/g"' \
              % (size, chunk_size, n_chunks)

        # prepare experiment
        os.system('mkdir -p %s' % e_name)
        os.system('cp  %s %s/' % (input_names, e_name))
        os.system('cd  %s ; ln -s ../conf .' % (e_name))
        os.system('cat templates/%s | %s > %s/%s' % (runme_name    , sed, e_name, runme_name    ))
        os.system('cat templates/%s | %s > %s/%s' % (config_name,    sed, e_name, config_name   ))
        os.system('cat templates/%s | %s > %s/%s' % (workload_name,  sed, e_name, workload_name ))
        os.system('cat templates/%s | %s > %s/%s' % (swift_cfg_name, sed, e_name, swift_cfg_name))
        os.system('cat templates/%s | %s > %s/%s' % (makefile_name , sed, e_name, makefile_name ))


