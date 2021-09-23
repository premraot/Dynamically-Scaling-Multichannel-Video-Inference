"""
Manage streams on redis based stream broker.

The initial camere or videofile streams were inferenced by infer engine, then
will be published on stream broker for next step action such as displaying on
stream dashboard or trigger FaaS actions.
"""
import logging
import time
import redis.exceptions
import sys
from .appbase import CLCNTask

LOG = logging.getLogger(__name__)

class StreamInfo:
    """
    Stream information structure.
    """

    def __init__(self, name, category, status="origin"):
        self._category = category
        self._name = name
        self._status = status

    @property
    def id(self):       # pylint: disable=invalid-name
        """
        Stream ID
        """
        return self._name + ":" + self._category + ":" + self._status

    @property
    def category(self):
        """
        Stream inference type like face, people, car
        """
        return self._category

    @property
    def name(self):
        """
        Stream's name
        """
        return self._name

    @property
    def status(self):
        """
        Stream status in origin or inferred
        """
        return self._status

    @staticmethod
    def from_id(sid):
        """
        Create stream object from stream ID
        """
        try:
            name, category, status = sid.split(":")
        except ValueError:
            LOG.error("Incorrect stream id: %s", sid)
            return None
        return StreamInfo(name, category, status)

class StreamBrokerBase:
    """
    Stream broker base class.
    """

    def __init__(self, on_add_stream_fn=None, on_del_stream_fn=None):
        self._streams = {}
        self._on_add_stream_fn = on_add_stream_fn
        self._on_del_stream_fn = on_del_stream_fn

    @property
    def streams(self):
        """
        Property of stream list
        """
        return self._streams

    # virtual function must be implemented by inherited class
    def add_stream_on_broker(self, info):
        """
        Add stream on stream broker
        """
        raise NotImplementedError(
            "inherited class must implement this function.")

    # virtual function must be implemented by inherited class
    def del_stream_on_broker(self, info):
        """
        Delete stream on stream broker
        """
        raise NotImplementedError(
            "inherited class must implement this function.")

    # virtual function must be implemented by inherited class
    def publish_frame_on_broker(self, info, msg):
        """
        Publish a frame to stream broker.
        """
        raise NotImplementedError(
            "inherited class must implement this function.")

    # virtual function must be implemented by inherited class
    def sync_streams_from_broker(self):
        """
        Sync stream list from broker.
        """
        raise NotImplementedError(
            "inherited class must implement this function.")

    def on_add_stream(self, info):
        """
        Callback function for adding a stream
        """
        LOG.debug("on_add_stream: %s", info.id)
        if info.id in list(self._streams):
            LOG.warning("Stream %s already exist.", info.id)
            return

        self._streams[info.id] = info
        if self._on_add_stream_fn is not None:
            self._on_add_stream_fn(info)

    def on_del_stream(self, info):
        """
        Callback function for deleting a stream
        """
        LOG.debug("on_del_stream: %s", info.id)
        if info.id not in list(self._streams):
            LOG.warning("Stream %s does not exist.", info.id)
            return

        del self._streams[info.id]
        if self._on_del_stream_fn is not None:
            self._on_del_stream_fn(info)

    def register_stream(self, info):
        """
        Registry a stream on stream broker
        """
        LOG.debug("Register new stream: %s", info.id)
        if info.id in list(self.streams):
            LOG.error("Stream %s already exists!", info.id)
            return False
        self.add_stream_on_broker(info)
        self._streams[info.id] = info
        return True

    def unregister_stream(self, info):
        """
        Unregister a stream
        """
        LOG.debug("Unregister stream: %s", info.id)
        if info.id not in list(self.streams):
            LOG.error("Stream %s does not exist!", info.id)
            return False
        del self._streams[info.id]
        self.del_stream_on_broker(info)
        return True

    def publish(self, stream_info, frame_byte):
        """
        Publish a frame to stream broker
        """
        self.publish_frame_on_broker(stream_info, frame_byte)

class RedisStreamBroker(StreamBrokerBase):
    """
    Redis based stream broker.
    """

    _KEY_STREAM_NAMES = "streams"

    def __init__(self, redis_conn, on_add_stream_fn=None,
                 on_del_stream_fn=None, on_failure=None):
        StreamBrokerBase.__init__(self, on_add_stream_fn, on_del_stream_fn)
        self._redis = redis_conn
        self._on_failure = on_failure
        self._streams_monitor_task = \
            CLCNTask("pubsub", self._stream_monitor_run, False)
        self.sync_streams_from_broker()

    def start_streams_monitor_task(self):
        """
        Start stream monitor task
        """
        self._streams_monitor_task.start()

    @property
    def redis(self):
        """
        Redis instance
        """
        return self._redis

    @property
    def pubsub(self):
        """
        Pubsub instance
        """
        return self._redis.pubsub()

    def _stream_monitor_run(self, task_obj):
        """
        Task entry for stream monitor.
        """
        pubsub = self.pubsub
        pubsub.psubscribe('__keyevent@0__:*')
        while not task_obj.is_task_stopping:
            try:
                message = pubsub.get_message()
            except redis.exceptions.ConnectionError:
                LOG.error("Remote redis connection closed.", exc_info=True)
                if self._on_failure != None:
                    self._on_failure()
                return
            if message is not None:
                LOG.debug(str(message))
                if message["channel"].decode("utf-8") == "__keyevent@0__:srem":
                    for sid in list(self.streams):
                        if bytes(sid, 'utf-8') not in \
                            self._redis.smembers(self._KEY_STREAM_NAMES):
                            self.on_del_stream(StreamInfo.from_id(sid))
                    LOG.debug("streams: %s", str(self.streams))
                elif message["channel"].decode("utf-8") == "__keyevent@0__:sadd":
                    for sid in self._redis.smembers(self._KEY_STREAM_NAMES):
                        sid = sid.decode("utf-8")
                        if sid not in list(self.streams):
                            self.on_add_stream(StreamInfo.from_id(sid))
                    LOG.debug("streams: %s", str(self.streams))
            time.sleep(0.1)

    def sync_streams_from_broker(self):
        """
        Sync stream list from broker
        """
        self.streams.clear()
        for sid in self._redis.smembers(self._KEY_STREAM_NAMES):
            sid = sid.decode("utf-8")
            info = StreamInfo.from_id(sid)
            if info is not None:
                self.streams[sid] = info

    def add_stream_on_broker(self, info):
        """
        Add stream on broker
        """
        self._redis.sadd(self._KEY_STREAM_NAMES, info.id)

    def del_stream_on_broker(self, info):
        """
        Delete stream on broker
        """
        self._redis.srem(self._KEY_STREAM_NAMES, info.id)

    def publish_frame_on_broker(self, info, msg):
        """
        Publish stream on broker
        """
        self._redis.publish(info.id, msg)
