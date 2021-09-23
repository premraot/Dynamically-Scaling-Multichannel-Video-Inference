#!/bin/bash
###############################################################################
# Download the existing models into <top_dir>/models folders.
#
# Some models come from https://github.com/intel/Edge-optimized-models
# under the BSD license (https://github.com/intel/Edge-optimized-models/blob/master/LICENSE.txt)
#
# Some models come from https://download.01.org/opencv/2019/open_model_zoo
# under the Apache license (https://download.01.org/opencv/2019/open_model_zoo/R2/20190628_180000_models_bin/LICENSE)
###############################################################################
curr_dir=$(readlink -f $(dirname "${BASH_SOURCE[0]}"))
top_dir=$(dirname "${curr_dir}")

source ${curr_dir}/common.sh

download_url="https://download.01.org/opencv/2019/open_model_zoo/R2/20190628_180000_models_bin"

function download_models {
    pushd ${top_dir} &> /dev/null

    echo "Check local .cache for download files ..."
    mkdir -p ${top_dir}/.cache
    cd ${top_dir}/.cache

    download_file Edge-optimized-models.zip \
        https://github.com/intel/Edge-optimized-models/archive/0ec78aceb4d1b1da0dc24c4c81857221265a2020.zip \
        192bf51c36ba3d997750574e26e9cfca

    if [ ! -d Edge-optimized-models-0ec78aceb4d1b1da0dc24c4c81857221265a2020 ]; then
        unzip ${top_dir}/.cache/Edge-optimized-models.zip
    fi

    # download FP32 model
    download_file face-detection-retail-0005_FP32.xml \
        ${download_url}/face-detection-retail-0005/FP32/face-detection-retail-0005.xml \
        9fbd8c185636d59df95629339727c3d9
    download_file face-detection-retail-0005_FP32.bin \
        ${download_url}/face-detection-retail-0005/FP32/face-detection-retail-0005.bin \
        aa1d619fd0f905e3736c72969b4c6f0b

    # download INT8 model
    download_file face-detection-retail-0005_INT8.xml \
        ${download_url}/face-detection-retail-0005/INT8/face-detection-retail-0005.xml \
        05372d33c123c4c438e29dfb725314f0
    download_file face-detection-retail-0005_INT8.bin \
        ${download_url}/face-detection-retail-0005/INT8/face-detection-retail-0005.bin \
        902efc1432e0bf5842dde3b7a15b8297

    # download FP32 model
    download_file person-vehicle-bike-detection-crossroad-0078_FP32.xml \
        ${download_url}/person-vehicle-bike-detection-crossroad-0078/FP32/person-vehicle-bike-detection-crossroad-0078.xml \
        26105b046324e29bf937f25dcfaec760
    download_file person-vehicle-bike-detection-crossroad-0078_FP32.bin \
        ${download_url}/person-vehicle-bike-detection-crossroad-0078/FP32/person-vehicle-bike-detection-crossroad-0078.bin \
        9431d6a7d6d1f9b9b9d9742e0596fb64

    # download INT8 model
    download_file person-vehicle-bike-detection-crossroad-0078_INT8.xml \
        ${download_url}/person-vehicle-bike-detection-crossroad-0078/INT8/person-vehicle-bike-detection-crossroad-0078.xml \
        ecc8b3b0d711ce8660bcefb88c2189c3
    download_file person-vehicle-bike-detection-crossroad-0078_INT8.bin \
        ${download_url}/person-vehicle-bike-detection-crossroad-0078/INT8/person-vehicle-bike-detection-crossroad-0078.bin \
        28c297637d9efebd33cad3430f3f3d5c

    echo "Check extracted model files under ${top_dir}/models ..."
    if [ ! -d ${top_dir}/models ]; then
        mkdir -p ${top_dir}/models

        cp ${top_dir}/.cache/Edge-optimized-models-0ec78aceb4d1b1da0dc24c4c81857221265a2020/SqueezeNet\ 5-Class\ detection/FP32/* ${top_dir}/models
        cp ${top_dir}/.cache/Edge-optimized-models-0ec78aceb4d1b1da0dc24c4c81857221265a2020/MobileNet\ 5-Class\ detection/FP32/* ${top_dir}/models
        cp ${top_dir}/.cache/*.xml ${top_dir}/models
        cp ${top_dir}/.cache/*.bin ${top_dir}/models
    fi

    popd &> /dev/null
    echo "Success"
}

download_models
