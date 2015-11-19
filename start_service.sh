#!/bin/bash

killall -u $USER python -9
aimes-emgr-rest conf/yadu_test_config.json &> emgr.log &
sleep 2
echo "EMGR Started"
