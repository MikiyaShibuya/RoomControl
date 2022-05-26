#!/usr/bin/env python3

import sys
import time
import cv2
import threading
import numpy as np

from yolo_v5_detector import YOLO_V5
from slack_webhook import SlackWebhook
from hue_client import HueClient
from ir_sensor import IR_Sensor

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

  def _async_impl(self, image, callback, make_preview):
    detection, prev = self.check_human(image, make_preview)
    callback(detection, prev)

    self.mutex.acquire()
    self.async_working = False
    self.mutex.release()

  def check_human_async(self, image, callback, make_preview=False):
    self.mutex.acquire()
    async_working = self.async_working
    self.mutex.release()
    if async_working:
      return

    self.mutex.acquire()
    self.async_working = True
    self.mutex.release()

    thread = threading.Thread(target=self._async_impl, args=(image, callback, make_preview))
    thread.start()


if __name__ == '__main__':

  slack_uri_fn = sys.argv[1]
  hue_config_fn = sys.argv[2]

  human_detector = HumanDetector(1 * 60)
  slack_webhook = SlackWebhook(slack_uri_fn)
  hue_client = HueClient(hue_config_fn)
  ir_sensor = IR_Sensor()
  ir_sensor.start()

  gui_available = False
  try:
    cv2.namedWindow('prev', cv2.WINDOW_AUTOSIZE)

    dummy = np.zeros((480, 640), np.uint8)
    cv2.imshow('prev', dummy)
    cv2.waitKey(1000)
    gui_available = True
  except:
    pass

  cam = cv2.VideoCapture(0)

  mutex = threading.Lock()
  preview = None

  def callback(detection, prev):
    global preview
    global mutex
    global hue_client

    if detection != '':
      res = slack_webhook.send_message(f'camera: {detection}')
      print(f'camera: {detection}')

    mutex.acquire()
    preview = prev
    mutex.release()

    if detection == 'out':
      hue_client.set_on(False)

  while True:
    _, frame = cam.read()
    if frame is None:
      continue

    human_detector.check_human_async(frame, callback, make_preview=True)

    if ir_sensor.get():
      res = slack_webhook.send_message(f'IR: in')
      hue_client.set_on(True)
      print(f'IR: in')

    if gui_available:
      mutex.acquire()
      if preview is not None:
        cv2.imshow('prev', cv2.hconcat([frame, preview]))
      else:
        cv2.imshow('prev', frame)
      mutex.release()

      key = cv2.waitKey(20)
      if key == 113:
        break

