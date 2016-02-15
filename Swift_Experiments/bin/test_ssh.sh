#!/bin/bash

stampede="stampede.tacc.utexas.edu"
gordon="gordon.sdsc.edu"


check() {
    site=$1
    ssh $1 "hostname -f" &> /dev/null
    if [[ "$?" != "0" ]]
    then
        echo "SSH: to $site       [FAIL]"
    else
        echo "SSH: to $site       [PASS]"
    fi
}


check $stampede
check $gordon
