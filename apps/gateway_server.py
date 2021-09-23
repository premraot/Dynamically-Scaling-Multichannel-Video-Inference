#!/usr/bin/python3
"""
Gateway Server provides Restful API and dashboard SPA.

            +-----------------+
            | Gateway (Flask) |
            +-----------------+
              //           \\
             //             \\
     +-------------+    +--------------+
     |   (/api)    |    |     (/)      |     +------------------------------------+
     | Restful API |    | Single Page  | ==> | ws://<ws server:31611>/<stream_id> |
     +-------------+    |  Application |     |     Stream WebSocket Server        |
                        +--------------+     +------------------------------------+
"""
import os
import sys
import logging
import signal
import redis
import redis.exceptions
from clcn.appbase import CLCNTask
from multiprocessing import Process

from flask import Flask, jsonify, render_template, make_response, request

APP_PATH = os.path.dirname(__file__)
sys.path.append(APP_PATH)

from clcn.stream import RedisStreamBroker   # pylint: disable=wrong-import-position

LOG = logging.getLogger(__name__)

DEFAULT_STREAM_BROKER_HOST = "127.0.0.1"
DEFAULT_STREAM_BROKER_PORT = "6379"

WEB_APP = Flask(__name__,
                root_path="/dist",
                static_folder="",
                template_folder="/dist")
WEB_APP.config.from_object(__name__)
server = Process(target=WEB_APP.run, args=('0.0.0.0',))

def _get_env(key, default=None):
    if key not in os.environ:
        LOG.warning("Cloud not find the key %s in environment, "
                    "use default value %s", key, str(default))
        return default
    return os.environ[key]

class StreamBrokerClient:
    """
    Stream broker client to monitor the stream list.
    """

    _instance = None

    def __init__(self):
        redis_conn = redis.Redis(
            _get_env("STREAM_BROKER_HOST", DEFAULT_STREAM_BROKER_HOST),
            int(_get_env("STREAM_BROKER_PORT", DEFAULT_STREAM_BROKER_PORT)))
        try:
            redis_conn.ping()
        except redis.exceptions.ConnectionError:
            LOG.error("Fail to connect redis server.", exc_info=True)
            sys.exit(1)
            return False
        self.broker = RedisStreamBroker(redis_conn, on_failure=self._on_broker_failure)
        self.broker.start_streams_monitor_task()

    @property
    def streams(self):
        """
        Stream List property
        """
        return self.broker.streams

    @staticmethod
    def inst():
        """
        Singleton instance
        """
        if StreamBrokerClient._instance is None:
            StreamBrokerClient._instance = StreamBrokerClient()
        return StreamBrokerClient._instance

    def _on_broker_failure(self):
        server.terminate()

@WEB_APP.route('/api/streams', methods=['GET'])
def api_get_stream_list():
    """
    Restful API for getting stream list.
    """
    return jsonify({"streams": list(StreamBrokerClient.inst().streams.keys())})

@WEB_APP.route("/", methods=['GET'])
def index():
    """
    Web server for dashboard SPA
    """
    resp = make_response(render_template("index_prod.html"))
    resp.headers.set('X-Content-Type-Options', 'nosniff')
    resp.headers.set('X-Frame-Options', 'SAMEORIGIN')
    resp.headers.set(
        'Content-Security-Policy',
        "default-src * 'unsafe-inline' 'unsafe-eval'; \
         script-src * 'unsafe-inline' 'unsafe-eval'; \
         connect-src * 'unsafe-inline'; \
         img-src * data: blob: 'unsafe-inline'; \
         frame-src *; \
         style-src * 'unsafe-inline'; ")
    return resp

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(threadName)s %(message)s")

    StreamBrokerClient.inst()
    server.start()

    def signal_handler(num, _):
        LOG.error("signal %d", num)
        CLCNTask.stop_all_tasks()
        server.terminate()
        sys.exit(1)
        return

    # setup the signal handler
    signames = ['SIGINT', 'SIGHUP', 'SIGQUIT', 'SIGUSR1']
    for name in signames:
        signal.signal(getattr(signal, name), signal_handler)

    server.join()
