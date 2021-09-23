"""
Base neural network classes to provide skeleton framework code for inference
from input processing, infering, output processing.

The default framework has some assumptions on input such as neural network blob
shape, your can create inherited class to overide process_input() method
if your model might requires different shape.
Also the default framework has some assumptions on ouput such as BB box for
detection results. you can create inherited class to overide process_output()
if your model's output is different.
"""
import os
import logging
import cv2
from openvino.inference_engine import IENetwork, IECore

LOG = logging.getLogger(__name__)

class NNBase:
    """
    NN base class to abstract the common infrastucture for NN infer.
    """

    def __init__(self, model_dir, model_name):
        self._batch_size = 0
        self._channel = 0
        self._height = 0
        self._weight = 0
        self._model_dir = model_dir
        self._model_name = model_name
        self._net = None

    @property
    def batch_size(self):
        """
        NN batch size.
        """
        return self._batch_size

    @batch_size.setter
    def batch_size(self, value):
        self._batch_size = value

    @property
    def channel(self):
        """
        NN channl number.
        """
        return self._channel

    @channel.setter
    def channel(self, value):
        self._channel = value

    @property
    def height(self):
        """
        Height of input layer
        """
        return self._height

    @height.setter
    def height(self, value):
        self._height = value

    @property
    def weight(self):
        """
        Weight of input layer.
        """
        return self._weight

    @weight.setter
    def weight(self, value):
        self._weight = value

    @property
    def model_xml_path(self):
        """
        model file path
        """
        path = os.path.join(self._model_dir, self._model_name + ".xml")
        return path

    @property
    def model_weight_path(self):
        """
        weight file path
        """
        path = os.path.join(self._model_dir, self._model_name + ".bin")
        return path

    @property
    def net(self):
        """
        NN network
        """
        return self._net

    @property
    def input_blob(self):
        """
        Input blob
        """
        return next(iter(self.net.inputs))

    @property
    def output_blob(self):
        """
        Output blob
        """
        return next(iter(self.net.outputs))

    def load(self):
        """
        Load NN weight file.
        """
        LOG.debug("Model XML: %s", self.model_xml_path)
        LOG.debug("Model weight: %s", self.model_weight_path)

        #self._net = IENetwork(
        #    model=self.model_xml_path, weights=self.model_weight_path)
        ie = IECore()
        self._net = ie.read_network(model=self.model_xml_path, weights=self.model_weight_path)

        # Read and pre-process input image
        self.batch_size, self.channel, self.height, self.weight = \
            self._net.inputs[self.input_blob].shape
        LOG.debug("Network input shape: %s",
                  str(self._net.inputs[self.input_blob].shape))
        LOG.debug("Network output shape: %s",
                  str(self._net.outputs[self.output_blob].shape))

    def process_input(self, frame):
        """
        Process input
        """
        in_frame = cv2.resize(frame, (self.weight, self.height))
        # Change data layout from HWC to CHW
        in_frame = in_frame.transpose((2, 0, 1))
        in_frame = in_frame.reshape(
            (self.batch_size, self.channel, self.height, self.weight))
        return in_frame

    def process_output(self, frame, result):
        """
        Process ouput
        """
        orig_height, orig_weight, _ = frame.shape
        for obj in result[self.output_blob][0][0]:
            if obj[2] > 0.5:
                xmin = int(obj[3] * orig_weight)
                ymin = int(obj[4] * orig_height)
                xmax = int(obj[5] * orig_weight)
                ymax = int(obj[6] * orig_height)
                class_id = int(obj[1])
                color = (0, 255, 0)
                cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), color, 2)
                det_label = str(class_id)
                cv2.putText(
                    frame,
                    det_label + ' ' + str(round(obj[2] * 100, 1)) + ' %',
                    (xmin, ymin - 7),
                    cv2.FONT_HERSHEY_COMPLEX, 0.6, (255, 0, 0), 1)
        return frame

class NNGeneralDetection(NNBase):
    """
    Generate detection with comon input and BB box output.
    """

    def __init__(self, model_dir, model_name):
        NNBase.__init__(self, model_dir, model_name)
