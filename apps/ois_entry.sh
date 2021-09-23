#!/bin/bash

source /opt/intel/openvino_2020.3.194/bin/setupvars.sh

_term() {
  echo "Caught SIGTERM signal!"
  kill -TERM "$child" 2>/dev/null
}

trap _term SIGTERM SIGINT SIGKILL

/usr/bin/python3 /apps/infer_service.py &

child=$!
wait "$child"

ret=$?
echo "Ret value: $ret"
exit $ret