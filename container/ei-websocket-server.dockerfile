FROM centos:8

ARG pip_mirror

RUN dnf install -y --nodocs python3 python3-pip && \
    dnf clean all && \
    rm -fr /var/cache/yum

COPY ./apps /apps

RUN pip3 install ${pip_mirror} --user asyncio websockets aioredis

ENV STREAM_BROKER_REDIS_HOST="127.0.0.1"
ENV STREAM_BROKER_REDIS_PORT="6379"

# for websocket port
EXPOSE 31611

CMD ["/apps/websocket_server.py"]
