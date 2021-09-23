#!/bin/bash
#
# Run Gateway Service via direct docker way
#

curr_dir=$(readlink -f $(dirname "${BASH_SOURCE[0]}"))
top_dir=$(readlink -f ${curr_dir}/../)

DEBUG_MODE=false
STREAM_BROKER_HOST="127.0.0.1"
STREAM_BROKER_PORT="6379"

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
            i) STREAM_BROKER_HOST=${OPTARG};;
            p) STREAM_BROKER_PORT=${OPTARG};;
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
echo "broker host: ${STREAM_BROKER_HOST}"
echo "broker port: ${STREAM_BROKER_PORT}"
echo "Registry: ${REGISTRY}"
echo "================================"
echo ""

if [ "$DEBUG_MODE" == true ]; then
    # in dev mode, map local app source into docker image and run this copy
    # instead of default one in container
    sudo docker run \
        -v ${top_dir}/apps/:/apps \
        -v ${top_dir}/spa/dist/:/dist \
        -p 5000:5000 \
        -e STREAM_BROKER_HOST=${STREAM_BROKER_HOST} \
        -e STREAM_BROKER_PORT=${STREAM_BROKER_PORT} \
        --restart on-failure:5 \
        ${REGISTRY}/ei-gateway-server \
        /apps/gateway_server.py
else
    # in release mode, just use docker image's default entry
    sudo docker run \
        -p 5000:5000 \
        -e STREAM_BROKER_HOST=${STREAM_BROKER_HOST} \
        -e STREAM_BROKER_PORT=${STREAM_BROKER_PORT} \
        --restart on-failure:5 \
        ${REGISTRY}/ei-gateway-server
fi
