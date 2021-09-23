#!/bin/bash
###############################################################################
# Download the existing models into <top_dir>/sample-videos folders.
#
# These videos come from https://github.com/intel-iot-devkit/sample-videos/
# under the Attribution 4.0 license (https://github.com/intel-iot-devkit/sample-videos/blob/master/LICENSE)
###############################################################################
curr_dir=$(readlink -f $(dirname "${BASH_SOURCE[0]}"))
top_dir=$(dirname "${curr_dir}")

source ${curr_dir}/common.sh

mkdir -p ${top_dir}/.cache
cd ${top_dir}/.cache

download_file sample-videos.zip \
    https://github.com/intel-iot-devkit/sample-videos/archive/d20c7b4201789c190428dfb858c7a19cf0517a98.zip \
    26ac9b6ff9e1ca8ca67e0694c570dbac

if [ ! -d ${top_dir}/.cache/sample-videos-d20c7b4201789c190428dfb858c7a19cf0517a98 ]; then
    unzip sample-videos.zip
fi

if [ ! -d ${top_dir}/sample-videos ]; then
    mkdir -p ${top_dir}/sample-videos
    cp ${top_dir}/.cache/sample-videos-d20c7b4201789c190428dfb858c7a19cf0517a98/* ${top_dir}/sample-videos -r
fi

echo "Success"

