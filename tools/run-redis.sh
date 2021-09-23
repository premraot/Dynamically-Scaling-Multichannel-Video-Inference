#!/bin/bash
#
# Run redis service via direct docker approach
#
curr_dir=$(readlink -f $(dirname "${BASH_SOURCE[0]}"))

if [ ! -f ${curr_dir}/redis.conf ]; then
    echo "protected-mode no
notify-keyspace-events \"Es\"">> ${curr_dir}/redis.conf
fi

sudo docker run \
    -p 6379:6379 \
    -v ${curr_dir}/redis.conf:/etc/redis.conf \
    --restart on-failure:5 \
    redis:6.0 \
    redis-server /etc/redis.conf
