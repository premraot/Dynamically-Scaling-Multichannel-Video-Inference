"""
Application template for Clear Linux Cloud Native (CLCN) Solutions.
"""
import os
import sys
import logging
import asyncio
import threading

LOG = logging.getLogger(__name__)

class CLCNTask(threading.Thread):
    """
    Threading based Task.

    In general, a cloud native app may consists several threading tasks.
    """

    _task_list = []

    def __init__(self, name=None, exec_func=None, is_asyncio=False):
        threading.Thread.__init__(self)
        self._is_asyncio = is_asyncio
        self._exec_func = exec_func
        self._event_loop = None
        self._is_task_stopping = False
        self._name = name
        if self not in CLCNTask._task_list:
            CLCNTask._task_list.append(self)

    @property
    def name(self):
        if self._name is None:
            self._name = self.__class__.__name__
        return self._name

    @classmethod
    def stop_all_tasks(cls):
        """
        Stops all tasks.
        """
        for task in CLCNTask._task_list:
            if task.isAlive():
                task.stop()

    @classmethod
    def wait_all_tasks_end(cls):
        """
        Wait all task end.
        """
        for task in CLCNTask._task_list:
            if task.isAlive():
                task.join()
        LOG.info("All task stopped! Bye~~~")

    def run(self):
        """
        Main entry for a task.
        """
        if self._is_asyncio:
            self._event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._event_loop)

        LOG.info("[Task-%s] starting!", self.name)
        try:
            if self._exec_func is not None:
                # pass task object to callback function
                self._exec_func(self)
            else:
                self.execute()
        except:         # pylint: disable=bare-except
            LOG.error("[Task-%s] Failed!", self.name, exc_info=True)
            CLCNTask.stop_all_tasks()
            sys.exit(1)
            return
        LOG.info("[Task - %s] Completed!", self.name)

    def execute(self):
        """
        Inherited class should implement customized task logic.
        """
        raise NotImplementedError("inherited class must implement this")

    @property
    def is_task_stopping(self):
        """
        Judge whether task is requested to stop.
        """
        return self._is_task_stopping

    def stop(self):
        """
        Stop a running task.
        """
        LOG.info("Stopping Task - %s", self.name)
        if self._is_asyncio:
            try:
                self._event_loop.stop()
            except:     # pylint: disable=bare-except
                LOG.error("Fail to stop event loop", exc_info=True)
        self._is_task_stopping = True

class CLCNAppBase:
    """
    A cloud native application should accept the parameters from environment
    variable. There might be one or more tasks. Accept the interrupt for
    kubernete liftcycle management, etc.
    """

    def __init__(self):
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)-15s %(levelname)-6s [%(module)-6s] %(message)s')
        self.init()

    def init(self):     # pylint: disable=no-self-use
        """
        Initalization entry for an application instance.
        """
        LOG.debug("Init function is used to collect parameter from "
                  "environment variable, inhertied class could overide it")

    @staticmethod
    def get_env(key, default=None):
        """
        Get environment variable.
        """
        if key not in os.environ:
            LOG.warning("Cloud not find the key %s in environment, use "
                        "default value %s", key, str(default))
            return default
        return os.environ[key]

    def run_and_wait_task(self):
        """
        Run and wait all tasks
        """
        try:
            if not self.run():
                CLCNTask.stop_all_tasks()
                CLCNTask.wait_all_tasks_end()
                sys.exit(1)
        except:
            LOG.error("Fail to run.", exc_info=True)
            CLCNTask.stop_all_tasks()
            CLCNTask.wait_all_tasks_end()
            sys.exit(1)
        CLCNTask.wait_all_tasks_end()

    def run(self):
        """
        Application main logic provided by inherited class.
        """
        raise NotImplementedError("Inherited class must implement this.")

    def stop(self):     # pylint: disable=no-self-use
        """
        Stop an application instance
        """
        CLCNTask.stop_all_tasks()
        CLCNTask.wait_all_tasks_end()
