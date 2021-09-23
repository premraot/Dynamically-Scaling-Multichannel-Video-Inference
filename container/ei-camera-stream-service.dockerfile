FROM centos:8

ARG pip_mirror

RUN dnf install -y --nodocs dnf-plugins-core && dnf config-manager --set-enabled PowerTools
RUN dnf install -y --nodocs opencv-devel opencv-core python3-pip && \
    dnf clean all && \
    rm -fr /var/cache/yum

COPY ./apps /apps

RUN pip3 install ${pip_mirror} --user asyncio redis prometheus_client msgpack opencv-python

# Camera device index, set to 0 for /dev/video0 by default
ENV CAMERA_INDEX=0
# Inference type, such as face/people/car
ENV INFER_TYPE="face-fp32"
# Customize stream name, otherwise is <ip-address>-<infer type>
ENV STREAM_NAME=""
# FPS for camera stream
ENV CAMERA_FPS=15
# Redis stream queue address
ENV QUEUE_HOST="127.0.0.1"
ENV QUEUE_PORT="6379"

CMD ["/apps/camera_stream_service.py"]
