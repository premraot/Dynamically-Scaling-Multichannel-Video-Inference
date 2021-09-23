#!/bin/bash
#
# Run Websocket Server Service via direct docker approach
#
curr_dir=$(readlink -f $(dirname "${BASH_SOURCE[0]}"))
top_dir=$(readlink -f ${curr_dir}/../)

DEBUG_MODE=false
STREAM_BROKER_REDIS_HOST="127.0.0.1"
STREAM_BROKER_REDIS_PORT="6379"

REGISTRY="docker.io/bluewish"

function usage {
    cat << EOM
Usage: $(basename "$0") [OPTION]...

  -d Debug mode that using local source to override container
  -i <stream broker host>
  -p <stream broker port>
  -y <container registry>
EOM
    exit 0
}

function process_args {
    while getopts ":i:p:y:dh" option; do
        case "${option}" in
            i) STREAM_BROKER_REDIS_HOST=${OPTARG};;
            p) STREAM_BROKER_REDIS_PORT=${OPTARG};;
            y) REGISTRY=${OPTARG};;
            d) DEBUG_MODE=true;;
            h) usage;;
        esac
    done
}

process_args "$@"
echo ""
echo "================================"
echo "Debug mode: ${DEBUG_MODE}"
echo "broker host: ${STREAM_BROKER_REDIS_HOST}"
echo "Registry: ${REGISTRY}"
echo "================================"
echo ""

if [ "$DEBUG_MODE" == true ]; then
    # in dev mode, map local app source into docker image and run this copy
    # instead of default one in container
    sudo docker run \
        -v ${top_dir}/apps/:/apps \
        -p 31611:31611 \
        -e STREAM_BROKER_REDIS_HOST=${STREAM_BROKER_REDIS_HOST} \
        -e STREAM_BROKER_REDIS_PORT=${STREAM_BROKER_REDIS_PORT} \
        --restart on-failure:5 \
        ${REGISTRY}/ei-websocket-server \
        /apps/websocket_server.py
else
    # in release mode, just use docker image's default entry
    sudo docker run \
        -p 31611:31611 \
        -e STREAM_BROKER_REDIS_HOST=${STREAM_BROKER_REDIS_HOST} \
        -e STREAM_BROKER_REDIS_PORT=${STREAM_BROKER_REDIS_PORT} \
        --restart on-failure:5 \
        ${REGISTRY}/ei-websocket-server
fi
