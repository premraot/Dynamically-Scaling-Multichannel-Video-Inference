#!/usr/bin/python3
"""
WebSocket Server

It subscribe all inferred stream from redis broker and host websocket server to
publish the streams to HTML5 based front-end SPA(Single Page Application).

It is based on aysncio and coroutine programming model since most of operations
are IO bound.
"""
import os
import sys
import asyncio
import logging
import signal
import aioredis
import aioredis.errors
import websockets
import websockets.exceptions
LOG = logging.getLogger(__name__)

STREAM_WEBSOCKET_PORT = 31611

class StreamWebSocketServer:
    """
    Stream websocket Server to publish streams via web socket from broker.
    """

    def __init__(self):
        self._stream_broker_redis_host = self._get_env(
            "STREAM_BROKER_REDIS_HOST", "127.0.0.1")
        self._stream_broker_redis_port = int(self._get_env(
            "STREAM_BROKER_REDIS_PORT", "6379"))
        self._streams = {}
        self._users = {}

    @staticmethod
    def _get_env(key, default=None):
        if key not in os.environ:
            LOG.warning("Cloud not find the key %s in environment, "
                        "use default value %s", key, str(default))
            return default
        return os.environ[key]

    def _add_stream(self, sid):
        LOG.info("add stream: %s", sid)
        self._streams[sid] = asyncio.get_event_loop().create_task(
            self._stream_publish_task(sid))

    def _del_stream(self, sid):
        LOG.info("remove stream: %s", sid)
        self._streams[sid].cancel()
        del self._streams[sid]

    def _on_update(self, stream_list):
        for new_item in stream_list:
            if new_item not in list(self._streams.keys()):
                self._add_stream(new_item)

        for old_item in list(self._streams.keys()):
            if old_item not in stream_list:
                self._del_stream(old_item)

    async def _websocket_server_task(self, wsobj, path):
        LOG.info("Websocket server task start: %s path: %s", str(wsobj), path)
        target = path[1:]  # skip / prefix

        if len(list(self._users.keys())) > 100:
            LOG.error("Exceed the max number of client connection: 100.")
            return

        self._users[wsobj] = target
        while True:
            try:
                _ = await wsobj.recv()
            except asyncio.CancelledError:
                LOG.error("Websocket task cancelled, %s", target)
                break
            except websockets.exceptions.ConnectionClosedError:
                LOG.error("Websocket connection closed.[error], %s", target)
                break
            except websockets.exceptions.ConnectionClosedOK:
                LOG.error("Websocket connection closed.[ok] %s", target)
                break
        del self._users[wsobj]
        LOG.info("Websocket server task stop.")

    async def _stream_status_monitor_task(self):
        LOG.info("Task stream status monitor task start.")

        try:
            read_obj = await aioredis.create_redis(
                (self._stream_broker_redis_host,
                self._stream_broker_redis_port),
                encoding='utf-8')
        except ConnectionRefusedError:
            LOG.error("Fail to connect redis host.", exc_info=True)
            sys.exit(1)
            return
        _ = [self._add_stream(item) for item in await read_obj.smembers("streams")]

        try:
            while True:
                try:
                    self._on_update(await read_obj.smembers("streams"))
                except aioredis.errors.ConnectionClosedError:
                    LOG.error("Redis host closed.", exc_info=True)
                    sys.exit(1)
                await asyncio.sleep(1)
        finally:
            read_obj.close()
        LOG.info("Task stream status monitor task stop.")

    async def _stream_publish_task(self, sid):
        LOG.info("stream publish task start: %s", sid)
        stream_sub_obj = await aioredis.create_redis(
            (self._stream_broker_redis_host,
             self._stream_broker_redis_port))
        ret = await stream_sub_obj.subscribe(sid)
        stream_channel = ret[0]

        while True:
            msg = await stream_channel.get()
            if msg is None:
                break
            if isinstance(msg, bytes):
                for user in list(self._users.keys()):
                    if user not in self._users:
                        continue
                    if self._users[user] != sid:
                        continue

                    try:
                        await user.send(msg)
                    except websockets.exceptions.ConnectionClosedOK:
                        LOG.error("[%s] fail to send due to websocket exception [cc_ok]",
                                  sid)
                    except websockets.exceptions.ConnectionClosedError:
                        LOG.error("[%s] fail to send due to websocket exception [cc_error]",
                                  sid)
                    except websockets.exceptions.WebSocketException:
                        LOG.error("[%s] Uncatched websockets error",
                                  sid, exc_info=True)

        stream_sub_obj.close()
        LOG.info("stream publish task stop for sid: %s", sid)

    async def _start_ws_server(self):
        ws_server = await websockets.serve(
                        self._websocket_server_task,
                        "0.0.0.0",
                        STREAM_WEBSOCKET_PORT)
        await ws_server.wait_closed()

    async def _shutdown(self, sigobj, loop):
        LOG.info("Received exit signal %s...", sigobj.name)
        tasks = [task for task in asyncio.Task.all_tasks() if task is not
                 asyncio.tasks.Task.current_task()]
        list(map(lambda task: task.cancel(), tasks))
        results = await asyncio.gather(*tasks, return_exceptions=True)
        LOG.info('finished awaiting cancelled tasks, results: %s', results)
        loop.stop()

    def run(self):
        """
        Main entry.
        """
        loop = asyncio.get_event_loop()
        signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
        for sigobj in signals:

            loop.add_signal_handler(
                sigobj,
                lambda sigobj=sigobj: loop.create_task(
                    self._shutdown(sigobj, loop)))

        try:
            loop.create_task(self._stream_status_monitor_task())
            loop.create_task(self._start_ws_server())
            loop.run_forever()
        finally:
            loop.close()
        logging.info("Successfully shutdown.")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(threadName)s %(message)s")
    SWSS = StreamWebSocketServer()
    SWSS.run()
