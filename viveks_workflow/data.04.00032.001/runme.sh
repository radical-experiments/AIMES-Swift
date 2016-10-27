
export RADICAL_VERBOSE=DEBUG
export RADICAL_LOG_TGT=r.log
export RADICAL_PILOT_VERBOSE=DEBUG
export RADICAL_PILOT_LOG_TGT=rp.log
export RADICAL_PILOT_PROFILE=True
export RADICAL_PILOT_AGENT_VERBOSE=DEBUG
export RADICAL_PILOT_RECORD_SESSION=rp.rec

export SWIFT_AIMES_VERBOSE=DEBUG
export SWIFT_AIMES_LOG_TGT=sa.log
export AIMES_SWIFT_VERBOSE=DEBUG
export AIMES_SWIFT_LOG_TGT=sa.log
export SAGA_PTY_SSH_TIMEOUT=120

aimes-emgr-rest2 experiment.json 2>&1 > rest.log  & AIMES_PID=$!
swift            vivek.swift     2>&1 > swift.log & SWIFT_PID=$!

echo $AIMES_PID > rest.pid
echo $SWIFT_PID > swift.pid

echo "waiting on $SWIFT_PID"
wait $SWIFT_PID
tail swift.log

echo 'fetching profiles'
SESSION_IDS=`grep 'new session' rest.log | cut -f 5 -d '[' | cut -f 1 -d ']'`
for sid in $SESSION_IDS
do
  radicalpilot-fetch-profiles $sid
  radicalpilot-fetch-json     $sid
done

echo 'all done'

