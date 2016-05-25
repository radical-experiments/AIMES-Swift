
export RADICAL_VERBOSE=DEBUG
export RADICAL_LOG_TGT=r.log
export RADICAL_PILOT_VERBOSE=DEBUG
export RADICAL_PILOT_LOG_TGT=rp.log
export RADICAL_PILOT_PROFILE=True
export RADICAL_PILOT_AGENT_VERBOSE=DEBUG
export RADICAL_PILOT_RECORD_SESSION=rp.rec
export SAGA_PTY_SSH_TIMEOUT=120
aimes-emgr-rest2 experiment.json 2>&1 > rest.log  & echo $! > rest.pid
swift            vivek.swift     2>&1 > swift.log & echo $! > swift.pid
tail -f rest.log

