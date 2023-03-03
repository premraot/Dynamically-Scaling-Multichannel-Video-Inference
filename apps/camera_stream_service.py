#!/usr/bin/python3
"""
Camera Stream Service.

It collect the frames from camera and send to redis based frame queue after
compression.

 +-------------+       +---------------------+
 | /dev/videoX | ====> | Frame Queue (redis) |
 +-------------+  |    +---------------------+
                  |
                  |    +-----------------------------+
                  |==> | Dropped frames (prometheus) |
                       +-----------------------------+
"""
import logging
import signal
import queue
import os
import sys
import socket
import redis


# add current path into PYTHONPATH
APP_PATH = os.path.dirname(__file__)
sys.path.append(APP_PATH)

from clcn.appbase import CLCNAppBase        # pylint: disable=wrong-import-position
from clcn.video import WebCamCaptureTask    # pylint: disable=wrong-import-position
from clcn.stream import StreamInfo          # pylint: disable=wrong-import-position
from clcn.frame import FrameQueueProduceTask, RedisFrameQueue   # pylint: disable=wrong-import-position

LOG = logging.getLogger(__name__)

class CameraServiceApp(CLCNAppBase):
    """
    Camera Stream Service
    """

    def init(self):
        self._redis_host = self.get_env("QUEUE_HOST", "127.0.0.1")
        self._redis_port = int(self.get_env("QUEUE_PORT", "6379"))
        self._infer_type = self.get_env("INFER_TYPE", "face")
        self._camera_number = int(self.get_env("CAMERA_INDEX", "0"))
        self._camera_fps = int(self.get_env("CAMERA_FPS", "15"))
        stream_name = self.get_env("STREAM_NAME", "")
        if len(stream_name) == 0:
            stream_name = "%s-%d" % (
                socket.gethostbyname(socket.gethostname()),
                self._camera_number)
        self._stream_info = StreamInfo(stream_name, self._infer_type)
        LOG.info("Stream ID: %s" % self._stream_info.id)

    def run(self):
        redis_conn = redis.StrictRedis(self._redis_host, self._redis_port)
        try:
            redis_conn.ping()
        except redis.exceptions.ConnectionError:
            LOG.error("Fail to connect redis server.", exc_info=True)
            return False

        out_queue = RedisFrameQueue(redis_conn, self._infer_type)

        frame_queue = queue.Queue(10)
        capture_task = WebCamCaptureTask(self._camera_number, self._camera_fps,
                                         frame_queue)
        publisher_task = FrameQueueProduceTask(self._stream_info, frame_queue,
                                               out_queue)
        capture_task.start()
        publisher_task.start()
        return True

def start_app():
    """
    App entry
    """
    app = CameraServiceApp()

    def signal_handler(num, _):
        LOG.error("signal %d", num)
        app.stop()
        sys.exit(1)

    # setup the signal handler
    signames = ['SIGINT', 'SIGHUP', 'SIGQUIT', 'SIGUSR1']
    for name in signames:
        signal.signal(getattr(signal, name), signal_handler)

    app.run_and_wait_task()

if __name__ == "__main__":
    start_app()
