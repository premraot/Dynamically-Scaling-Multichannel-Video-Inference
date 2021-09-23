"""
Manage video stream input from webcam or file.

Capture video frames from webcam or files, publish to frame queue according to
inference type.
"""
import os
import logging
import time
from random import randrange
import cv2
from .appbase import CLCNTask

LOG = logging.getLogger(__name__)


class Camera:
    """
    Camera object manage V4L2 device
    """

    def __init__(self, devnum=0, width=320, height=240, fps=15,
                 report_interval=5):
        self._dev_num = devnum
        self._dev_obj = None
        self._capture_task = None
        self._interval_report_start = 0
        self._interval_report_frame_no = 0
        self._report_interval = report_interval
        self._width = width
        self._height = height
        self._fps = fps
        self._frame_queue = None

    def open(self):
        """
        Open the camera device
        """
        self._dev_obj = cv2.VideoCapture(self._dev_num)
        if not self._dev_obj.isOpened():
            LOG.error("Fail to open the camera, number: %d", self._dev_num)
            return False

        self._dev_obj.set(cv2.CAP_PROP_FRAME_WIDTH, self._width)
        self._dev_obj.set(cv2.CAP_PROP_FRAME_HEIGHT, self._height)
        self._dev_obj.set(cv2.CAP_PROP_FPS, self._fps)

        LOG.info("Frame width: %d", self._width)
        LOG.info("Frame height: %d", self._height)

        return True

    def read(self):
        """
        Read frame
        """
        return self._dev_obj.read()

    def close(self):
        """
        Close the camera device
        """
        if self._dev_obj is not None:
            self._dev_obj.release()
        else:
            LOG.warning("Device is not opened!")

class WebCamCaptureTask(CLCNTask):
    """
    WebCam caputure task.
    """

    def __init__(self, cam_num, fps, out_frame_queue):
        CLCNTask.__init__(self)
        self._device_name = "/dev/video%d" % cam_num
        self._camera = Camera(cam_num, fps=fps)
        self._out_frame_queue = out_frame_queue
        self._fps_start_time = 0
        self._fps_end_time = 0
        self._fps_no = 0

    def execute(self):
        """
        Task entry
        """
        LOG.debug("start capture from device: %s", self._device_name)

        if not self._camera.open():
            LOG.error("Fail to open camera: %s", self._device_name)
            return

        while not self.is_task_stopping:
            ret, frame = self._camera.read()
            if ret:
                if self._out_frame_queue.full():
                    self._out_frame_queue.get()
                _, jpeg = cv2.imencode('.jpg', frame)
                self._out_frame_queue.put_nowait(jpeg.tobytes())
                self._report_fps()
            else:
                LOG.error("Fail to capture")
                break

    def stop(self):
        CLCNTask.stop(self)
        self._camera.close()

    def _report_fps(self):
        if self._fps_start_time == 0:
            self._fps_start_time = time.time()
            self._fps_no = 0
            return

        now = time.time()
        duration = now - self._fps_start_time
        self._fps_no += 1
        if duration > 10:
            LOG.info("Capture speed: %.02f FPS", float(self._fps_no / duration))
            self._fps_start_time = time.time()
            self._fps_no = 0

class VideoFileTask(CLCNTask):
    """
    Video File task.
    """

    def __init__(self, output_queue, filedir="/sample-videos",
                 filename="classroom.mp4", fps=30, random=False):
        CLCNTask.__init__(self)
        self._output_queue = output_queue
        self._filedir = filedir
        self._filename = os.path.join(filedir, filename)
        self._is_random = random
        self._fps = fps
        if self._is_random:
            self._filename = self._get_random_video_file()

    def execute(self):
        LOG.info("Stream the video file: %s", self._filename)

        cap = cv2.VideoCapture(self._filename)

        frame_counter = 0
        while not self.is_task_stopping and cap.isOpened():
            ret, frame = cap.read()
            frame = cv2.resize(frame, (320, 240))
            if not ret:
                LOG.error("Fail to read video file.")
                break

            frame_counter += 1
            if frame_counter == cap.get(cv2.CAP_PROP_FRAME_COUNT):
                frame_counter = 0
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

            if self._output_queue.full():
                self._output_queue.get()

            _, jpeg = cv2.imencode('.jpg', frame)
            self._output_queue.put_nowait(jpeg.tobytes())
            time.sleep(float(1/self._fps))

    def _get_random_video_file(self):
        if not os.path.exists(self._filedir):
            LOG.error("Directory %s does not exist!!!", self._filedir)
            return None

        video_files = []
        for item in os.listdir(self._filedir):
            if item.endswith(".mp4"):
                video_files.append(os.path.join(self._filedir, item))

        index = randrange(len(video_files) - 1)
        return video_files[index]
