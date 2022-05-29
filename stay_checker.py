#!/usr/bin/env python3

import os
import sys
import time
import cv2
import threading
import numpy as np

from yolo_v5_detector import YOLO_V5
from slack_webhook import SlackWebhook
from hue_client import HueClient
from ir_sensor import IR_Sensor

AWAY_TIMEOUT = 10*60 # The room will be assumed empty when the detector keeping find no-one for this time
CAPTURE_INTERVAL = 1.0 # Camera captureing period [s]
INFER_INTERVAL = 60.0 # Human detection period [s]

class HumanDetector:
  def __init__(self, timeout=3 * 60):
    classFile = 'coco.names'
    modelWeights = 'yolov5n.onnx'
    self.yolo = YOLO_V5(classFile, modelWeights)

    self.prev_with_human = False
    self.time_human_left = 0
    self.current_state = 'out'

    self.timeout = timeout # 10 min

    self.mutex = threading.Lock()
    self.async_working = False
    self.async_result = None

  def check_human(self, image, make_preview=False):
    outputs = self.yolo.infer(frame)
    prev = None
    if make_preview:
      prev = self.yolo.draw_bboxes(frame.copy(), outputs)

    with_human = False
    state_changed = False

    for i in outputs[0]:
      if i == 0:
        with_human = True
        break

    if with_human:
      if not self.prev_with_human:
        if self.current_state != 'in':
          state_changed = True
        self.current_state = 'in'
    else:
      if self.prev_with_human:
        self.time_human_left = time.time()

      elapsed = time.time() - self.time_human_left
      if elapsed > self.timeout:
        if self.current_state != 'out':
          state_changed = True
        self.current_state = 'out'

    self.prev_with_human = with_human

    return self.current_state if state_changed else '', prev

  def _async_impl(self, image, make_preview):
    detection, prev = self.check_human(image, make_preview)

    self.mutex.acquire()
    self.async_result = (detection, prev)
    self.async_working = False
    self.mutex.release()

  def check_human_async(self, image, make_preview=False):
    self.mutex.acquire()
    async_working = self.async_working
    self.mutex.release()
    if async_working:
      return

    self.mutex.acquire()
    self.async_working = True
    self.mutex.release()

    thread = threading.Thread(target=self._async_impl, args=(image.copy(), make_preview))
    thread.start()

  def is_working(self):
    self.mutex.acquire()
    working = self.async_working
    self.mutex.release()
    return working

  def pop_result(self):
    self.mutex.acquire()
    res = self.async_result
    self.async_result = None
    self.mutex.release()

    return res


if __name__ == '__main__':

  slack_uri_fn = sys.argv[1]
  hue_config_fn = sys.argv[2]

  human_detector = HumanDetector(AWAY_TIMEOUT)
  slack_webhook = SlackWebhook(slack_uri_fn)
  hue_client = HueClient(hue_config_fn)
  ir_sensor = IR_Sensor()

  gui_available = False

  if os.getenv('DISPLAY') != '':
    try:
      cv2.namedWindow('prev', cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
      cv2.namedWindow('infer', cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)

      dummy = np.zeros((480, 640), np.uint8)
      cv2.imshow('prev', dummy)
      cv2.imshow('infer', dummy)
      cv2.waitKey(1000)
      gui_available = True
      print('Start with GUI mode')
    except:
      pass

  if not gui_available:
    print('Start with headless mode')

  cam = cv2.VideoCapture(0)

  last_infer_req = 0

  if not cam.isOpened():
    print("Camera couldn't bt opened")
    exit(1)

  ir_sensor.start()

  while True:
    try:
      _, frame = cam.read()
      if frame is None:
        continue

      res = human_detector.pop_result()
      prev = None

      if res is not None:
        detection = res[0]
        prev = res[1]
        if detection != '':
          res = slack_webhook.send_message(f'camera: {detection}')
          print(f'camera: {detection}')

        if detection == 'out':
          hue_client.set_on(False)

      if not human_detector.is_working() \
          and time.time() - last_infer_req > INFER_INTERVAL:
        human_detector.check_human_async(frame, make_preview=True)
        last_infer_req = time.time()

      if ir_sensor.get():
        res = slack_webhook.send_message(f'IR: in')
        hue_client.set_on(True)
        print(f'IR: in')

      if gui_available:
        cv2.imshow('prev', frame)
        if prev is not None:
          cv2.imshow('infer', prev)

        key = cv2.waitKey(int(CAPTURE_INTERVAL * 1000))
        if key == 113:
          break
      else:
        time.sleep(CAPTURE_INTERVAL)

    except:
      import traceback
      traceback.print_exc()
      break

  ir_sensor.stop()

