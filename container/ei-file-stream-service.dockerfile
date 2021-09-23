FROM centos:8

ARG pip_mirror

RUN dnf install -y --nodocs dnf-plugins-core && dnf config-manager --set-enabled PowerTools
RUN dnf install -y --nodocs opencv-devel opencv-core python3-pip && \
    dnf clean all && \
    rm -fr /var/cache/yum

RUN useradd developer
USER developer

COPY ./apps /apps
COPY ./sample-videos /sample-videos

RUN pip3 install ${pip_mirror} --user asyncio redis prometheus_client msgpack opencv-python

ENV VIDEO_FILE="head-pose-face-detection-female-and-male.mp4"
ENV QUEUE_HOST="127.0.0.1"
ENV QUEUE_PORT="6379"
ENV INFER_TYPE="face-fp32"
ENV STREAM_NAME=""

CMD ["/apps/file_stream_service.py"]
