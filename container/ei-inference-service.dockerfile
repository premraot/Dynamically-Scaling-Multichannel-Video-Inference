FROM openvino/ubuntu18_runtime:2020.3

USER root
ENV DEBIAN_FRONTEND=noninteractive
RUN apt update && apt install -y libopencv-dev && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ARG pip_mirror

COPY ./apps /apps
COPY ./models /models

RUN pip3 install ${pip_mirror} --user asyncio redis prometheus_client msgpack opencv-python

ENV INFER_MODEL_PATH="/models"
ENV INFER_MODEL_NAME="SqueezeNetSSD-5Class"
ENV INPUT_QUEUE_HOST="127.0.0.1"
ENV OUTPUT_BROKER_HOST="127.0.0.1"
ENV INFER_TYPE="people"

# for prometheums metrics
EXPOSE 8000

HEALTHCHECK CMD curl --fail http://localhost:8000/ || exit 1

CMD ["/apps/ois_entry.sh"]
