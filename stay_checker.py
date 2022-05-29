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

AWAY_TIMEOUT = 10 * 60.0 # The room will be assumed empty when the detector keeping find no-one for this time
INFER_INTERVAL = 1 * 60.0 # Human detection period [s]
CONTROL_INTERVAL = 0.3 # Interval of control [s]

DEBUG = False

if DEBUG:
  INFER_INTERVAL = 10.0
  AWAY_TIMEOUT = 60

class HumanDetector:
  def __init__(self, interval=1 * 60, make_preview=False):
    self.cam = cv2.VideoCapture(0)
    self.cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    if not self.cam.isOpened():
      print("Camera couldn't bt opened")
      exit(1)

    classFile = 'coco.names'
    modelWeights = 'yolov5n.onnx'
    self.yolo = YOLO_V5(classFile, modelWeights)
    self.interval = interval
    self.make_preview = make_preview

    self.mutex = threading.Lock()
    self.ts = 0
    self.human = False
    self.prev = None
    self.terminate = True

  def _loop(self):
    while True:
      t0 = time.time()
      det = False

      frame = None
      while time.time() - t0 < 0.1:
        r, f = self.cam.read()
        if r:
          frame = f

      if frame is None:
        continue

      outputs = self.yolo.infer(frame)

      for i in outputs[0]:
        if i == 0:
          det = True

      prev = None
      if self.make_preview:
        prev = self.yolo.draw_bboxes(frame.copy(), outputs)
        prev = cv2.hconcat([frame, prev])

      if DEBUG:
        print(f'debug: obj-det: {det}')

      self.mutex.acquire()
      terminate = self.terminate
      self.ts = t0
      self.human = det
      self.prev = prev
      self.mutex.release()

      if terminate:
        break

      t1 = time.time()
      if t1 - t0 < self.interval:
        time.sleep(self.interval - (t1 - t0))

  def start(self):
    self.mutex.acquire()
    if not self.terminate:
        return
    self.terminate = False
    self.mutex.release()

    thread = threading.Thread(target=self._loop)
    thread.start()

  def stop(self):
    self.mutex.acquire()
    self.terminate = True
    self.mutex.release()

  def get(self):
    self.mutex.acquire()
    ts = self.ts
    human = self.human
    prev = self.prev
    self.ts = 0
    self.human = False
    self.prev = None
    self.mutex.release()

    return ts, human, prev


if __name__ == '__main__':

  slack_uri_fn = sys.argv[1]
  hue_config_fn = sys.argv[2]

  slack_webhook = SlackWebhook(slack_uri_fn)
  hue_client = HueClient(hue_config_fn)

  gui_available = False

  if os.getenv('DISPLAY') != '':
    try:
      cv2.namedWindow('infer', cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)

      dummy = np.zeros((480, 640), np.uint8)
      cv2.imshow('infer', dummy)
      cv2.waitKey(1000)
      gui_available = True
      print('Start with GUI mode')
    except:
      pass

  if not gui_available:
    print('Start with headless mode')

  last_human_det_time = 0
  staying = False

  human_detector = HumanDetector(INFER_INTERVAL, gui_available)
  ir_sensor = IR_Sensor()
  ir_sensor.start()

  while True:
    try:
      current_time = time.time()

      ts, cam_det, prev = human_detector.get()
      ir_det = ir_sensor.get()

      if DEBUG and ir_det:
        print('debug: ir_det')

      if staying:
        if cam_det or ir_det:
          last_human_det_time = current_time
        else:
          if current_time - last_human_det_time > AWAY_TIMEOUT:
            staying = False
            hue_client.set_on(False)
            human_detector.stop()
            slack_webhook.send_message('out');
            print('out');
      # Not staying
      else:
        if ir_det:
          staying = True
          hue_client.set_on(True)
          human_detector.start()
          slack_webhook.send_message('in');
          print('in');

      if gui_available:
        if prev is not None:
          cv2.imshow('infer', prev)
          key = cv2.waitKey(1)
          if key == 113:
            break

      time.sleep(CONTROL_INTERVAL)

    except:
      import traceback
      traceback.print_exc()
      break

  ir_sensor.stop()
  human_detector.stop()

