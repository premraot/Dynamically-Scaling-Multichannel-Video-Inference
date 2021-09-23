#!/bin/bash
#
# Run Openvino based Inference Service via direct docker way
#
curr_dir=$(readlink -f $(dirname "${BASH_SOURCE[0]}"))
top_dir=$(readlink -f ${curr_dir}/../)

DEBUG_MODE=false
INFER_TYPE="people"
MODEL_NAME="SqueezeNetSSD-5Class"
INPUT="127.0.0.1"
OUTPUT="127.0.0.1"
PROMETHEUS_PORT=8000
REGISTRY="docker.io/bluewish"

function usage {
    cat << EOM
Usage: $(basename "$0") [OPTION]...

  -d Debug mode that using local source to override container
  -t [face-fp32|face-int8|car-int8|car-fp32|people] infererence type, default is people for body detection
  -i <input queue host>
  -o <output broker host>
  -p <prometheus port>
  -y <container registry>
EOM
    exit 0
}

function process_args {
    while getopts ":t:i:o:p:y:dh" option; do
        case "${option}" in
            t) INFER_TYPE=${OPTARG};;
            i) INPUT=${OPTARG};;
            o) OUTPUT=${OPTARG};;
            p) PROMETHEUS_PORT=${OPTARG};;
            y) REGISTRY=${OPTARG};;
            d) DEBUG_MODE=true;;
            h) usage;;
        esac
    done

    case ${INFER_TYPE} in
        people)
            MODEL_NAME="SqueezeNetSSD-5Class"
            ;;
        face)
            MODEL_NAME="face-detection-retail-0005"
            ;;
        car)
            MODEL_NAME="person-vehicle-bike-detection-crossroad-0078"
            ;;
    esac
}

process_args "$@"
echo ""
echo "================================"
echo "Debug mode: ${DEBUG_MODE}"
echo "Infer: ${INFER_TYPE}"
echo "Model: ${MODEL_NAME}"
echo "Input queue: ${INPUT}"
echo "Output broker: ${OUTPUT}"
echo "Prometheus port: ${PROMETHEUS_PORT}"
echo "Registry: ${REGISTRY}"
echo "================================"
echo ""

if [ "$DEBUG_MODE" == true ]; then
    ${top_dir}/tools/download-models.sh
    # in dev mode, map local app source into docker image and run this copy
    # instead of default one in container
    sudo docker run \
        -v ${top_dir}/apps/:/apps \
        -v ${top_dir}/models/:/models \
        -p ${PROMETHEUS_PORT}:8000 \
        -e MODEL_NAME=${MODEL_NAME} \
        -e INPUT_QUEUE_HOST=${INPUT} \
        -e OUTPUT_BROKER_HOST=${OUTPUT} \
        -e INFER_TYPE=${INFER_TYPE} \
        --restart on-failure:5 \
        ${REGISTRY}/ei-inference-service \
        /apps/ois_entry.sh
else
    # in release mode, just use docker image's default entry
    sudo docker run \
        -p ${PROMETHEUS_PORT}:8000 \
        -e MODEL_NAME=${MODEL_NAME} \
        -e INPUT_QUEUE_HOST=${INPUT} \
        -e OUTPUT_BROKER_HOST=${OUTPUT} \
        -e INFER_TYPE=${INFER_TYPE} \
        --restart on-failure:5 \
        ${REGISTRY}/ei-inference-service
fi
