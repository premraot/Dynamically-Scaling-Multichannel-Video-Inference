#!/bin/bash

curr_dir=$(readlink -f $(dirname "${BASH_SOURCE[0]}"))
top_dir=$(dirname "${curr_dir}")
# pip mirror is used to accelerate the speed of python pip
pip_mirror="-i https://pypi.douban.com/simple"
action="all"
registry=""
container="all"
tag="latest"

function usage {
    cat << EOM
usage: $(basename "$0") [OPTION]...
    -a <build|publish|save|all>  all is default, which not include save. Please execute save explicity if need.
    -r <registry prefix> the prefix string for registry
    -c <css|fss|ois|wss|gws|all> the container to be built and published
    -g <tag> container image tag
EOM
    exit 0
}

function process_args {
    while getopts ":a:r:c:g:h" option; do
        case "${option}" in
            a) action=${OPTARG};;
            r) registry=${OPTARG};;
            c) container=${OPTARG};;
            g) tag=${OPTARG};;
            h) usage;;
        esac
    done

    if [[ "$action" =~ ^(build|publish|save|all) ]]; then
        :
    else
        echo "invalid type: $action"
        usage
    fi

    if [[ "$container" =~ ^(css|fss|ois|wss|gws|all) ]]; then
        :
    else
        echo "invalid container name: $container"
        usage
    fi

    if [[ "$registry" == "" ]]; then
        echo "Error: Please specify your docker registry via -r <registry prefix>."
        exit 1
    fi
}

function build_images {
    cd ${top_dir}

    if [[ "$container" =~ ^(css|all) ]]; then
        echo "Build camera stream service container..."
        sudo docker build \
            --no-cache \
            --build-arg http_proxy=$http_proxy \
            --build-arg https_proxy=$https_proxy \
            --build-arg pip_mirror="$pip_mirror" \
            -f container/ei-camera-stream-service.dockerfile . \
            -t ${registry}/ei-camera-stream-service:${tag}
    fi

    if [[ "$container" =~ ^(fss|all) ]]; then
        echo "Build file stream service container..."

        ${top_dir}/tools/download-sample-videos.sh
        sudo docker build \
            --build-arg http_proxy=$http_proxy \
            --build-arg https_proxy=$https_proxy \
            --build-arg pip_mirror="$pip_mirror" \
            -f container/ei-file-stream-service.dockerfile . \
            -t ${registry}/ei-file-stream-service:${tag}
    fi

    if [[ "$container" =~ ^(ois|all) ]]; then
        echo "Build openvino inference service container..."

        ${top_dir}/tools/download-models.sh
        sudo docker build \
            --build-arg http_proxy=$http_proxy \
            --build-arg https_proxy=$https_proxy \
            --build-arg pip_mirror="$pip_mirror" \
            -f container/ei-inference-service.dockerfile . \
            -t ${registry}/ei-inference-service:${tag}
    fi

    if [[ "$container" =~ ^(wss|all) ]]; then
        echo "Build websocket server container..."
        sudo docker build \
            --build-arg http_proxy=$http_proxy \
            --build-arg https_proxy=$https_proxy \
            --build-arg pip_mirror="$pip_mirror" \
            -f container/ei-websocket-server.dockerfile . \
            -t ${registry}/ei-websocket-server:${tag}
    fi

    if [[ "$container" =~ ^(gws|all) ]]; then
        echo "Build gateway server container..."

        if ! [ -x "$(command -v npm)" ]; then
            echo 'Error: npm is not installed.' >&2
            exit 1
        fi

        cd ${top_dir}/spa
        npm install
        npm run init
        npm run build

        cd ${top_dir}
        sudo docker build \
            --build-arg http_proxy=$http_proxy \
            --build-arg https_proxy=$https_proxy \
            --build-arg pip_mirror="$pip_mirror" \
            -f container/ei-gateway-server.dockerfile . \
            -t ${registry}/ei-gateway-server:${tag}
    fi
}

function publish_images {
    if [[ "$container" =~ ^(css|all) ]]; then
        echo "Publish camera service container ..."
        sudo docker push ${registry}/ei-camera-stream-service:${tag}
    fi

    if [[ "$container" =~ ^(fss|all) ]]; then
        echo "Publish file service container ..."
        sudo docker push ${registry}/ei-file-stream-service:${tag}
    fi

    if [[ "$container" =~ ^(ois|all) ]]; then
        echo "Publish openvino inference service container ..."
        sudo docker push ${registry}/ei-inference-service:${tag}
    fi

    if [[ "$container" =~ ^(wss|all) ]]; then
        echo "Publish websocket server container ..."
        sudo docker push ${registry}/ei-websocket-server:${tag}
    fi

    if [[ "$container" =~ ^(gws|all) ]]; then
        echo "Publish gateway server container ..."
        sudo docker push ${registry}/ei-gateway-server:${tag}
    fi
}

function save_images {
    echo 'Save image to file, please use "gunzip -c mycontainer.tgz | docker load" to restore.'

    if [[ "$container" =~ ^(css|all) ]]; then
        echo "Save camera stream service container ..."
        sudo docker save ${registry}/ei-camera-stream-service:${tag} | gzip > ${top_dir}/containers/${registry}/ei-camera-stream-service-${tag}.tgz
    fi

    if [[ "$container" =~ ^(fss|all) ]]; then
        echo "Save file stream service container ..."
        sudo docker save ${registry}/ei-file-stream-service:${tag} | gzip > ${top_dir}/containers/${registry}/ei-file-stream-service-${tag}.tgz
    fi

    if [[ "$container" =~ ^(ois|all) ]]; then
        echo "Save openvino inference service container ..."
        sudo docker save ${registry}/ei-inference-service:${tag} | gzip > ${top_dir}/containers/${registry}/ei-inference-service-${tag}.tgz
    fi

    if [[ "$container" =~ ^(wss|all) ]]; then
        echo "Save websocket server container ..."
        sudo docker save ${registry}/ei-websocket-server:${tag} | gzip > ${top_dir}/containers/${registry}/ei-websocket-server-${tag}.tgz
    fi

    if [[ "$container" =~ ^(gws|all) ]]; then
        echo "Save gateway server container ..."
        sudo docker save ${registry}/ei-gateway-server:${tag} | gzip > ${top_dir}/containers/${registry}/ei-gateway-server-${tag}.tgz
    fi
}

process_args "$@"
echo ""
echo "-------------------------"
echo "action: ${action}"
echo "container: ${container}"
echo "tag: ${tag}"
echo "registry: ${registry}"
echo "-------------------------"
echo ""

if [[ "$action" =~ ^(build|all) ]]; then
    build_images
fi

if [[ "$action" =~ ^(publish|all) ]]; then
    publish_images
fi

if [[ "$action" =~ ^(save) ]]; then
    save_images
fi
