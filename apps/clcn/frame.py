"""
Manage frame queue on redis.

The frame queue is binding to specifc inference type, such as face, body, car
etc. A frame queue will receive same type input source from camera or videofile.

The inference engines will pickup the frames from frame queue one by one. There
might are more than one engines for same inference type. For example, there are
maybe two replicas of inference engines for body recoginition on k8s to
improve inference speed on. The number of replicas are depends on the computation
requirement of inference model.
"""
import logging
import time
import msgpack
from .appbase import CLCNTask

LOG = logging.getLogger(__name__)

class FrameMessage:
    """
    A frame message on message queue, including inference category, raw frame
    binary data and name.
    """

    def __init__(self, name, category, data):
        self._name = name
        self._category = category
        self._data = data

    @property
    def name(self):
        """
        Frame name
        """
        return self._name

    @property
    def category(self):
        """
        Inference category like face, people, car
        """
        return self._category

    @property
    def data(self):
        """
        Frame binary data
        """
        return self._data

    def to_binary(self):
        """
        Pack all frame message into binary packet
        """
        msg = {"name":self._name, "category":self._category, "data": self._data}
        return msgpack.packb(msg, use_bin_type=True)

    @staticmethod
    def from_binary(binary):
        """
        Decode frame message from binary packet
        """
        msg = msgpack.unpackb(binary, raw=False)
        return FrameMessage(msg["name"], msg["category"], msg["data"])

class FrameQueueBase:
    """
    Frame queue base.
    """

    def __init__(self, category="face"):
        self._category = category

    @property
    def name(self):
        """
        Frame queue's name
        """
        return "queue_" + self._category

    def push(self, stream_info, msg):
        """
        Push frame message into queue.
        """
        if stream_info.category != self._category:
            LOG.error("Invalid category for frame")
            return
        msg = FrameMessage(stream_info.name, stream_info.category, msg)
        self.push_on_queuer(stream_info, msg.to_binary())

    def pop(self):
        """
        Pop a frame message from frame's queue
        """
        binary = self.pop_on_queuer()
        if binary is None:
            return None
        return FrameMessage.from_binary(binary)

    def drop(self):
        """
        Drop overflow frame message from frame's queue
        """
        return self.drop_on_queuer()

    def is_stream_expired(self, info):
        """
        Judge whether a frame is expired on frame queue
        """
        raise NotImplementedError(
            "inherited class must implement this function.")

    def push_on_queuer(self, info, msg):
        """
        Push message to frame queue
        """
        raise NotImplementedError(
            "inherited class must implement this function.")

    def pop_on_queuer(self):
        """
        Pop message from frame queue
        """
        raise NotImplementedError(
            "inherited class must implement this function.")
    def drop_on_queuer(self):
        """
        Drop message from frame queue
        """
        raise NotImplementedError(
            "inherited class must implement this function.")

class FrameQueueProduceTask(CLCNTask):
    """
    Frame queue produce task to get framew fraom input queue and put into
    output queue.
    """

    def __init__(self, stream_info, in_queue, out_queue):
        CLCNTask.__init__(self)
        self._inq = in_queue
        self._outq = out_queue
        self._stream_info = stream_info

    def execute(self):
        """
        Task Entry
        """
        while not self.is_task_stopping:
            if self._inq.empty():
                time.sleep(0.01)
                continue
            msg = self._inq.get_nowait()
            if msg is None:
                continue
            self._outq.push(self._stream_info, msg)

class RedisFrameQueue(FrameQueueBase):
    """
    Redis based frame queue implementation.
    """

    def __init__(self, redis_conn, category="face"):
        FrameQueueBase.__init__(self, category)
        self._redis = redis_conn

    def push_on_queuer(self, info, msg):
        self._redis.rpush(self.name, msg)
        self._redis.setex(info.name + "_expire", "1", 2)

    def pop_on_queuer(self):
        return self._redis.lpop(self.name)

    def drop_on_queuer(self):
        msg_len = self._redis.llen(self.name)
        drop_frame = 0
        if msg_len > 32:
            self._redis.ltrim(self.name, -32, -1)
            drop_frame = msg_len - 32
        return drop_frame

    def is_stream_expired(self, info):
        if not self._redis.exists(info.name + "_expire"):
            LOG.debug("stream %s expired.", info.name)
            return True
        return False
