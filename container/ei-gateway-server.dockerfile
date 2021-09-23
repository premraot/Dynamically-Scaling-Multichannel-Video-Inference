FROM centos:8

ARG pip_mirror

RUN dnf install -y --nodocs python3 python3-pip nodejs && \
    dnf clean all && \
    rm -fr /var/cache/yum

COPY ./apps /apps
COPY ./spa/dist /dist

RUN pip3 install ${pip_mirror} --user redis flask

ENV STREAM_BROKER_HOST="127.0.0.1"
ENV STREAM_BROKER_PORT="6379"

EXPOSE 5000

HEALTHCHECK CMD curl --fail http://localhost:5000/ || exit 1

CMD ["/apps/gateway_server.py"]
